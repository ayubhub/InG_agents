"""
Outreach Agent - Sends messages and monitors responses.
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.agents.base_agent import BaseAgent
from src.core.models import Lead, SendResult, ResponseAnalysis
from src.core.message_generator import MessageGenerator
from src.core.response_analyser import ResponseAnalyser
from src.core.rate_limiter import RateLimiter, RateLimitExceededError
from src.integrations.linkedin_sender import LinkedInSender

class OutreachAgent(BaseAgent):
    """Outreach Agent for sending messages and analyzing responses."""
    
    def __init__(self, *args, **kwargs):
        """Initialize Outreach Agent."""
        super().__init__(*args, **kwargs)
        
        self.config_section = self.config.get("outreach", {})
        self.response_check_interval = self.config_section.get("response_check_interval", "2 hours")
        
        # Initialize components
        self.message_generator = MessageGenerator(llm_client=self.llm_client)
        self.response_analyser = ResponseAnalyser(llm_client=self.llm_client)
        
        storage = self.config.get("storage", {})
        sqlite_db = storage.get("sqlite_db", "data/state/agents.db")
        self.rate_limiter = RateLimiter(self.config, sqlite_db)
        
        self.linkedin_sender = LinkedInSender(self.config)
        
        self.scheduler = BlockingScheduler()
        self._setup_scheduler()
    
    def _setup_scheduler(self) -> None:
        """Setup scheduled tasks."""
        # Process allocated leads every 30 minutes
        self.scheduler.add_job(
            self.process_allocated_leads,
            trigger=IntervalTrigger(minutes=30),
            id='process_leads'
        )
        
        # Check responses every 2 hours
        hours = int(self.response_check_interval.split()[0])
        self.scheduler.add_job(
            self.monitor_responses,
            trigger=IntervalTrigger(hours=hours),
            id='check_responses'
        )
    
    def run(self) -> None:
        """Main agent loop."""
        self.logger.info("Outreach Agent running")
        self.scheduler.start()
    
    def process_allocated_leads(self) -> None:
        """Process allocated leads and send messages."""
        self.logger.info("Processing allocated leads")
        
        try:
            # Get allocated leads
            filters = {"contact_status": "Allocated", "allocated_to": "Outreach"}
            leads = self.state_manager.read_leads(filters)
            
            for lead in leads:
                try:
                    # Check rate limit
                    if not self.rate_limiter.can_send():
                        self.logger.info("Rate limit reached, stopping for today")
                        break
                    
                    # Generate message
                    message = self.generate_message(lead)
                    
                    # Send message
                    result = self.send_message(lead, message)
                    
                    if result.success:
                        # Update lead status
                        updates = {
                            "contact_status": "Message Sent",
                            "Message Sent": message,
                            "Message Sent At": datetime.now().isoformat(),
                            "Last Updated": datetime.now().isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        
                        # Publish event
                        self.publish_event("message_sent", {
                            "agent_to": "SalesManager",
                            "lead_id": lead.id,
                            "message_id": result.message_id
                        })
                        
                        # Wait before next send
                        wait_time = self.rate_limiter.record_send()
                        self.logger.info(f"Message sent to {lead.name}, waiting {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Failed to send message to {lead.name}: {result.error_message}")
                        
                except RateLimitExceededError:
                    self.logger.info("Rate limit exceeded, stopping")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing lead {lead.id}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in process_allocated_leads: {e}")
    
    def generate_message(self, lead: Lead) -> str:
        """
        Generate personalized message for lead.
        
        Args:
            lead: Lead object
        
        Returns:
            Message text
        """
        return self.message_generator.generate(lead)
    
    def send_message(self, lead: Lead, message: str) -> SendResult:
        """
        Send LinkedIn message.
        
        Args:
            lead: Lead object
            message: Message text
        
        Returns:
            SendResult object
        """
        return self.linkedin_sender.send_message(lead.linkedin_url, message)
    
    def monitor_responses(self) -> None:
        """Monitor for new responses."""
        self.logger.info("Checking for responses")
        
        try:
            # Get responses from LinkedIn service
            responses = self.linkedin_sender.check_responses()
            
            # Get leads with sent messages
            filters = {"contact_status": "Message Sent"}
            leads_with_messages = self.state_manager.read_leads(filters)
            
            # Match responses to leads
            for response_data in responses:
                # Find matching lead (by message_id or linkedin_url)
                lead = self._find_lead_for_response(response_data, leads_with_messages)
                
                if lead:
                    # Analyse response
                    analysis = self.analyse_response(
                        response_data.get("text", ""),
                        lead.message_sent
                    )
                    
                    # Update lead
                    updates = {
                        "contact_status": "Responded",
                        "Response": response_data.get("text", ""),
                        "Response Received At": datetime.now().isoformat(),
                        "Response Sentiment": analysis.sentiment,
                        "Response Intent": analysis.intent,
                        "Last Updated": datetime.now().isoformat()
                    }
                    self.state_manager.update_lead(lead.id, updates)
                    
                    # Publish event
                    self.publish_event("response_received", {
                        "agent_to": "SalesManager",
                        "lead_id": lead.id,
                        "sentiment": analysis.sentiment,
                        "intent": analysis.intent
                    })
                    
                    self.logger.info(f"Response received from {lead.name}: {analysis.sentiment} - {analysis.intent}")
            
        except Exception as e:
            self.logger.error(f"Error monitoring responses: {e}")
    
    def analyse_response(self, response_text: str, original_message: Optional[str] = None) -> ResponseAnalysis:
        """
        Analyse response for sentiment and intent.
        
        Args:
            response_text: Response text
            original_message: Optional original message
        
        Returns:
            ResponseAnalysis object
        """
        return self.response_analyser.analyse(response_text, original_message)
    
    def _find_lead_for_response(self, response_data: Dict, leads: List[Lead]) -> Optional[Lead]:
        """
        Find lead matching response data.
        
        Args:
            response_data: Response data from LinkedIn service
            leads: List of leads to search
        
        Returns:
            Matching lead or None
        """
        # Try to match by message_id
        message_id = response_data.get("message_id")
        if message_id:
            for lead in leads:
                if lead.message_sent and message_id in str(lead.message_sent):
                    return lead
        
        # Try to match by LinkedIn URL
        linkedin_url = response_data.get("linkedin_url")
        if linkedin_url:
            for lead in leads:
                if lead.linkedin_url == linkedin_url:
                    return lead
        
        return None

