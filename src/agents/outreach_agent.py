"""
Outreach Agent - Sends messages and monitors responses.
"""

import time
from datetime import datetime, timedelta, timezone
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
        
        # Track last process time to process only new leads
        self.last_process_time = datetime.now(timezone.utc) - timedelta(days=1)  # Process all on first run
        
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
        """Setup periodic tasks."""
        # Process allocated leads
        process_interval = self.config_section.get("process_interval_minutes", 2)
        self.scheduler.add_job(
            self.process_allocated_leads,
            trigger=IntervalTrigger(minutes=process_interval),
            id='process_leads',
            next_run_time=datetime.now(timezone.utc)  # Run immediately on startup
        )
        
        # Check responses
        response_hours = self.config_section.get("response_check_interval_hours", 2)
        self.scheduler.add_job(
            self.monitor_responses,
            trigger=IntervalTrigger(hours=response_hours),
            id='check_responses',
            next_run_time=datetime.now(timezone.utc)  # Run immediately on startup
        )
        
        # Check pending invitations (for Unipile)
        invitation_hours = self.config_section.get("invitation_check_interval_hours", 6)
        self.scheduler.add_job(
            self.check_pending_invitations,
            trigger=IntervalTrigger(hours=invitation_hours),
            id='check_invitations',
            next_run_time=datetime.now(timezone.utc)  # Run immediately on startup
        )
        
        self.logger.info(f"Scheduler: process every {process_interval} min")
    
    def run(self) -> None:
        """Main agent loop."""
        self.logger.info("Outreach Agent running")
        
        # Check pending invitations immediately on startup (don't wait for first scheduled run)
        self.logger.info("Checking pending invitations on startup...")
        try:
            self.check_pending_invitations()
        except Exception as e:
            self.logger.error(f"Error checking invitations on startup: {e}")
        
        self.scheduler.start()
    
    def process_allocated_leads(self) -> None:
        """Process allocated leads that haven't been sent yet."""
        self.logger.info("Processing allocated leads")
        
        try:
            # Read allocated leads
            filters = {"contact_status": "Allocated", "allocated_to": "Outreach"}
            leads = self.state_manager.read_leads(filters)
            self.logger.info(f"Found {len(leads)} allocated leads")
            
            # Filter: only leads without message_sent (haven't been processed yet)
            pending_leads = [
                lead for lead in leads 
                if not lead.message_sent  # No message sent yet
            ]
            
            # Also include newly allocated leads (for immediate processing)
            # Normalize datetimes to timezone-aware (UTC) before comparison
            def normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            
            last_process_utc = normalize_dt(self.last_process_time)
            new_leads = [
                lead for lead in pending_leads
                if lead.allocated_at and normalize_dt(lead.allocated_at) > last_process_utc
            ]
            
            if pending_leads:
                self.logger.info(f"Found {len(pending_leads)} pending leads ({len(new_leads)} newly allocated)")
            else:
                self.logger.debug("No pending leads to process")
                return
            
            for lead in pending_leads:
                try:
                    self.logger.info(f"Processing lead {lead.id}: {lead.name} (allocated at: {lead.allocated_at})")
                    
                    # Check rate limit
                    if not self.rate_limiter.can_send():
                        self.logger.warning(f"Rate limit check failed for {lead.name}. Check logs above for details.")
                        break
                    
                    # Generate message
                    self.logger.debug(f"Generating message for {lead.name}")
                    message = self.generate_message(lead)
                    
                    # Send message
                    self.logger.debug(f"Sending message to {lead.name} via {self.linkedin_sender.service}")
                    result = self.send_message(lead, message)
                    
                    # Check invitation sent first (success=False but status='invitation_sent')
                    if result.status == "invitation_sent":
                        # Message is already truncated to 200 chars in LinkedInSender
                        updates = {
                            "contact_status": "Invitation Sent",
                            "message_sent": message,  # Already truncated to 200 chars in LinkedInSender
                            "message_sent_at": result.timestamp.isoformat() if result.timestamp else datetime.now(timezone.utc).isoformat(),
                            "notes": f"Invitation ID: {result.message_id}, Waiting for acceptance. URL: {lead.linkedin_url}",
                            "last_updated": datetime.now(timezone.utc).isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        self.logger.info(f"→ Invitation sent to {lead.name} (ID: {result.message_id})")
                        wait_time = self.rate_limiter.record_send()
                        time.sleep(wait_time)
                        
                    elif result.status == "invitation_already_sent":
                        # Invitation was already sent recently (422 error from Unipile)
                        # Update status if not already set
                        if lead.contact_status != "Invitation Sent":
                            updates = {
                                "contact_status": "Invitation Sent",
                                "notes": f"Invitation already sent recently. Waiting for acceptance. URL: {lead.linkedin_url}",
                                "last_updated": datetime.now(timezone.utc).isoformat()
                            }
                            self.state_manager.update_lead(lead.id, updates)
                            self.logger.info(f"→ Invitation already sent to {lead.name} (updating status)")
                        else:
                            self.logger.debug(f"Invitation already sent to {lead.name} (status already set)")
                        
                    elif result.success:
                        updates = {
                            "contact_status": "Message Sent",
                            "message_sent": message,
                            "message_sent_at": result.timestamp.isoformat() if result.timestamp else datetime.now(timezone.utc).isoformat(),
                            "last_updated": datetime.now(timezone.utc).isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        
                        wait_time = self.rate_limiter.record_send()
                        self.logger.info(f"✓ Message sent to {lead.name}")
                        time.sleep(wait_time)
                        
                    else:
                        # Failed to send - do NOT update message_sent or message_sent_at
                        error_note = f"Failed: {result.error_message}" if result.error_message else "Unknown error"
                        updates = {
                            "contact_status": "Allocated",  # Keep as allocated to retry later
                            "notes": error_note,
                            "last_updated": datetime.now(timezone.utc).isoformat()
                            # Note: We intentionally do NOT update message_sent or message_sent_at on failure
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        self.logger.error(f"Failed to send message/invitation to {lead.name}: {result.error_message}")
                        
                except RateLimitExceededError:
                    self.logger.info("Rate limit exceeded, stopping")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing lead {lead.id}: {e}")
                    continue
            
            # Update last check time
            self.last_process_time = datetime.now(timezone.utc)
                    
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
    
    def check_pending_invitations(self) -> None:
        """Check status of pending invitations (Unipile polling)."""
        self.logger.info("Checking pending invitations")
        
        try:
            filters = {"contact_status": "Invitation Sent"}
            pending_leads = self.state_manager.read_leads(filters)
            
            for lead in pending_leads:
                try:
                    invite_id = self._extract_invite_id(lead.notes)
                    status = self.linkedin_sender.check_invitation_status(invite_id, lead.linkedin_url)
                    
                    now = datetime.now(timezone.utc)
                    
                    if status == "accepted":
                        self.logger.info(f"✓ Invitation accepted: {lead.name}")
                        
                        # Reset to Allocated for message sending
                        updates = {
                            "contact_status": "Allocated",
                            "allocated_to": "Outreach",
                            "allocated_at": now.isoformat(),
                            "notes": f"Invitation accepted at {now.isoformat()}. Ready to send message.",
                            "last_updated": now.isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        self.logger.info(f"→ Lead {lead.id} ready for message sending")
                        # Will be picked up on next process_allocated_leads() cycle
                        
                    elif status == "declined":
                        self.logger.warning(f"Invitation declined: {lead.name}")
                        updates = {
                            "contact_status": "Failed",
                            "notes": f"Invitation declined at {now.isoformat()}",
                            "last_updated": now.isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        
                    elif status == "expired":
                        self.logger.warning(f"Invitation expired: {lead.name}")
                        updates = {
                            "contact_status": "Allocated",  # Retry invitation
                            "notes": f"Invitation expired at {now.isoformat()}. Will retry.",
                            "last_updated": now.isoformat()
                        }
                        self.state_manager.update_lead(lead.id, updates)
                        
                    # If status is "pending", no update needed - will check again next time
                        
                except Exception as e:
                    self.logger.error(f"Error checking invitation {lead.id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in check_pending_invitations: {e}")
    
    def _extract_invite_id(self, notes: Optional[str]) -> Optional[str]:
        """Extract invite_id from notes."""
        if not notes:
            return None
        import re
        # Try new format: "Invitation ID: ..."
        match = re.search(r'Invitation ID: ([^,\n]+)', notes)
        if match:
            return match.group(1).strip()
        # Try old format: "Invite ID: ..."
        match = re.search(r'Invite ID: ([^,\n]+)', notes)
        if match:
            return match.group(1).strip()
        return None

