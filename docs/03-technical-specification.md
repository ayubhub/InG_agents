# Technical Specification - AI Sales Department

## Document Information
- **Document Type**: Technical Specification
- **Target Audience**: Software Developer, Implementation Team
- **Version**: 2.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

This document provides detailed technical specifications for implementing the AI-powered sales department with three specialised AI agents. It includes agent specifications, inter-agent communication protocols, data models, API contracts, LLM integration details, and implementation guidelines. This specification serves as the implementation guide for developers building the multi-agent system.

---

## Project Structure

```
InG_agents/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Base class for all agents
│   │   ├── sales_manager_agent.py     # Sales Manager Agent
│   │   ├── lead_finder_agent.py      # Lead Finder Agent
│   │   └── outreach_agent.py          # Outreach Agent
│   ├── core/
│   │   ├── __init__.py
│   │   ├── lead_classifier.py        # Classification logic
│   │   ├── quality_scorer.py         # Lead quality scoring
│   │   ├── message_generator.py      # Message generation
│   │   ├── response_analyser.py      # Response analysis
│   │   └── rate_limiter.py           # Rate limiting
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── google_sheets_io.py       # Database interface
│   │   ├── linkedin_client.py        # LinkedIn API client
│   │   ├── linkedin_sender.py        # Message sending
│   │   ├── llm_client.py             # LLM API client
│   │   └── email_service.py          # Email reporting
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── message_queue.py          # Message queue interface
│   │   ├── event_bus.py              # Event pub/sub
│   │   └── state_manager.py          # Shared state management
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       ├── logger.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_sales_manager_agent.py
│   │   ├── test_lead_finder_agent.py
│   │   ├── test_outreach_agent.py
│   │   ├── test_lead_classifier.py
│   │   ├── test_message_generator.py
│   │   └── test_response_analyser.py
│   └── integration/
│       ├── test_agent_communication.py
│       ├── test_workflow.py
│       └── test_integrations.py
├── config/
│   ├── config.yaml
│   ├── agents.yaml
│   ├── llm.yaml
│   ├── templates.yaml
│   └── .env.example
├── logs/
│   └── .gitkeep
├── main.py                           # Main entry point
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Base Agent Architecture

### `src/agents/base_agent.py`

**Purpose**: Base class providing common functionality for all agents.

**Class Definition**:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class BaseAgent(ABC):
    """Base class for all AI agents in the sales department."""
    
    def __init__(
        self,
        agent_name: str,
        config: Dict[str, Any],
        state_manager: 'StateManager',
        message_queue: 'MessageQueue',
        llm_client: Optional['LLMClient'] = None
    ) -> None:
        """
        Initialise base agent.
        
        Args:
            agent_name: Unique name for this agent
            config: Agent-specific configuration
            state_manager: Shared state manager instance
            message_queue: Message queue for inter-agent communication
            llm_client: Optional LLM client for AI capabilities
        """
        self.agent_name = agent_name
        self.config = config
        self.state_manager = state_manager
        self.message_queue = message_queue
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.is_running = False
    
    @abstractmethod
    def start(self) -> None:
        """Start the agent's main loop."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the agent gracefully."""
        pass
    
    @abstractmethod
    def process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message from message queue."""
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Dictionary with health status and metrics
        """
        return {
            "agent": self.agent_name,
            "status": "healthy" if self.is_running else "stopped",
            "timestamp": datetime.now().isoformat()
        }
    
    def publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish event to message queue.
        
        Args:
            event_type: Type of event (e.g., "lead_discovered")
            data: Event data
        """
        event = {
            "type": event_type,
            "agent": self.agent_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.message_queue.publish(event)
        self.logger.info(f"Published event: {event_type}")
    
    def subscribe_to_events(self, event_types: List[str], callback: Callable) -> None:
        """
        Subscribe to specific event types.
        
        Args:
            event_types: List of event types to subscribe to
            callback: Callback function to handle events
        """
        self.message_queue.subscribe(event_types, callback, self.agent_name)
```

---

## Agent Specifications

### 1. Sales Manager Agent

**File**: `src/agents/sales_manager_agent.py`

**Purpose**: Coordinates sales department operations, allocates leads, monitors performance, and generates reports.

**Class Definition**:

```python
from src.agents.base_agent import BaseAgent
from typing import List, Dict, Any
from datetime import datetime

class SalesManagerAgent(BaseAgent):
    """Coordinates sales department operations."""
    
    def __init__(self, config: Dict[str, Any], state_manager, message_queue, llm_client):
        super().__init__("sales_manager", config, state_manager, message_queue, llm_client)
        self.performance_analyser = PerformanceAnalyser()
        self.allocation_strategy = AllocationStrategy(config.get("allocation_strategy", "quality_priority"))
    
    def start(self) -> None:
        """Start coordination loop."""
        self.is_running = True
        self.logger.info("Sales Manager Agent started")
        
        # Schedule daily operations
        scheduler = APScheduler()
        scheduler.add_job(self.coordinate_daily_operations, 'cron', hour=9, minute=0)
        scheduler.add_job(self.generate_daily_report, 'cron', hour=9, minute=15)
        scheduler.add_job(self.monitor_performance, 'interval', minutes=60)
        
        # Subscribe to agent events
        self.subscribe_to_events(
            ["lead_discovered", "message_sent", "response_received", "agent_error"],
            self.handle_agent_event
        )
        
        scheduler.start()
    
    def coordinate_daily_operations(self) -> None:
        """
        Main coordination function - runs daily at 9:00 AM.
        """
        self.logger.info("Starting daily coordination")
        
        # 1. Review current state
        current_state = self.state_manager.get_current_state()
        
        # 2. Request new leads from Lead Finder if needed
        if current_state["uncontacted_leads"] < 50:
            self.request_lead_search()
        
        # 3. Allocate leads to Outreach Agent
        leads_to_allocate = self.allocate_leads()
        if leads_to_allocate:
            self.publish_event("lead_allocation", {
                "lead_ids": [lead.id for lead in leads_to_allocate],
                "priority": "normal"
            })
        
        # 4. Check for escalations
        self.handle_escalations()
    
    def allocate_leads(self, max_leads: int = 50) -> List['Lead']:
        """
        Allocate leads to Outreach Agent based on priority.
        
        Args:
            max_leads: Maximum number of leads to allocate
            
        Returns:
            List of allocated leads
        """
        # Get uncontacted leads
        uncontacted_leads = self.state_manager.read_leads({
            "contact_status": "Not Contacted"
        })
        
        # Use LLM to prioritise if enabled
        if self.config.get("use_llm_for_allocation", False):
            prioritised = self._llm_prioritise_leads(uncontacted_leads, max_leads)
        else:
            prioritised = self.allocation_strategy.prioritise(uncontacted_leads, max_leads)
        
        # Update lead status
        for lead in prioritised:
            self.state_manager.update_lead(lead.id, {
                "contact_status": "Allocated",
                "allocated_at": datetime.now().isoformat(),
                "allocated_by": "sales_manager"
            })
        
        return prioritised
    
    def _llm_prioritise_leads(self, leads: List['Lead'], max_count: int) -> List['Lead']:
        """
        Use LLM to intelligently prioritise leads.
        
        Args:
            leads: List of leads to prioritise
            max_count: Maximum number to select
            
        Returns:
            Prioritised list of leads
        """
        # Prepare context for LLM
        context = {
            "leads": [lead.to_dict() for lead in leads],
            "max_count": max_count,
            "current_metrics": self.performance_analyser.get_current_metrics()
        }
        
        prompt = f"""
        Analyse the following leads and select the top {max_count} leads to contact today.
        Consider:
        - Lead quality scores
        - Classification (Speakers vs Sponsors)
        - Recent performance trends
        - Response rates by lead type
        
        Leads:
        {json.dumps(context['leads'], indent=2)}
        
        Return a JSON array of lead IDs in priority order.
        """
        
        response = self.llm_client.generate(prompt, temperature=0.3)
        selected_ids = json.loads(response)
        
        # Map IDs back to Lead objects
        lead_dict = {lead.id: lead for lead in leads}
        return [lead_dict[id] for id in selected_ids if id in lead_dict]
    
    def monitor_performance(self) -> Dict[str, Any]:
        """
        Monitor performance metrics and agent health.
        
        Returns:
            Performance metrics dictionary
        """
        metrics = self.performance_analyser.collect_metrics()
        
        # Check for anomalies
        if metrics["error_rate"] > 0.1:
            self.publish_event("performance_alert", {
                "metric": "error_rate",
                "value": metrics["error_rate"],
                "threshold": 0.1
            })
        
        return metrics
    
    def generate_daily_report(self) -> None:
        """Generate and send daily report."""
        report = self._build_report()
        email_service = EmailService(self.config["email"])
        email_service.send_report(report, self.config["report_recipients"])
        
        self.logger.info("Daily report generated and sent")
    
    def _build_report(self) -> str:
        """Build comprehensive daily report."""
        metrics = self.performance_analyser.collect_metrics()
        
        # Use LLM to generate insights
        insights_prompt = f"""
        Analyse the following sales metrics and provide 3-5 key insights and recommendations:
        
        {json.dumps(metrics, indent=2)}
        
        Format as bullet points.
        """
        
        insights = self.llm_client.generate(insights_prompt, temperature=0.7)
        
        report = f"""
📊 Daily Sales Department Report - {datetime.now().strftime('%Y-%m-%d')}

🎯 LEAD FINDER AGENT
✅ New leads discovered: {metrics['lead_finder']['leads_discovered']}
📈 Average quality score: {metrics['lead_finder']['avg_quality_score']:.1f}
🎤 Speakers found: {metrics['lead_finder']['speakers']}
💼 Sponsors found: {metrics['lead_finder']['sponsors']}

📧 OUTREACH AGENT
✅ Messages sent today: {metrics['outreach']['messages_sent']}
📊 Remaining in queue: {metrics['outreach']['queue_size']}
🔄 Responses received: {metrics['outreach']['responses']}
📈 Response rate: {metrics['outreach']['response_rate']:.1f}%
👍 Positive responses: {metrics['outreach']['positive_responses']}
👎 Negative responses: {metrics['outreach']['negative_responses']}

📊 OVERALL METRICS
📈 Total leads in database: {metrics['overall']['total_leads']}
🎯 Qualified opportunities: {metrics['overall']['qualified_opportunities']}

💡 INSIGHTS & RECOMMENDATIONS
{insights}
"""
        return report
    
    def optimise_strategy(self) -> Dict[str, Any]:
        """
        Analyse performance and optimise strategy.
        
        Returns:
            Strategy updates to apply
        """
        performance_data = self.performance_analyser.get_historical_data(days=14)
        
        optimisation_prompt = f"""
        Based on the following performance data, suggest strategy optimisations:
        
        {json.dumps(performance_data, indent=2)}
        
        Consider:
        - Message template effectiveness
        - Lead quality thresholds
        - Allocation strategies
        - Timing optimisations
        
        Return JSON with specific recommendations.
        """
        
        recommendations = json.loads(self.llm_client.generate(optimisation_prompt))
        
        # Apply safe recommendations automatically
        # Flag significant changes for human approval
        return recommendations
    
    def handle_agent_event(self, event: Dict[str, Any]) -> None:
        """Handle events from other agents."""
        event_type = event["type"]
        
        if event_type == "agent_error":
            self.logger.error(f"Agent error: {event['data']}")
            # Decide on escalation or retry
        
        elif event_type == "response_received":
            response_data = event["data"]
            if response_data["sentiment"] == "positive":
                # Notify human team
                self._notify_human_team(response_data)
```

**Key Methods**:
- `coordinate_daily_operations()`: Main coordination loop
- `allocate_leads()`: Prioritise and allocate leads
- `monitor_performance()`: Collect and analyse metrics
- `generate_daily_report()`: Create comprehensive reports
- `optimise_strategy()`: Use LLM to improve strategy
- `handle_agent_event()`: Process events from other agents

---

### 2. Lead Finder Agent

**File**: `src/agents/lead_finder_agent.py`

**Purpose**: Searches LinkedIn for prospects, analyses profiles, classifies leads, and adds them to database.

**Class Definition**:

```python
class LeadFinderAgent(BaseAgent):
    """Finds and qualifies leads on LinkedIn."""
    
    def __init__(self, config: Dict[str, Any], state_manager, message_queue, llm_client):
        super().__init__("lead_finder", config, state_manager, message_queue, llm_client)
        self.linkedin_client = LinkedInClient(config["linkedin"])
        self.classifier = LeadClassifier(llm_client)
        self.quality_scorer = QualityScorer()
        self.search_criteria = config.get("search_criteria", {})
    
    def start(self) -> None:
        """Start lead finding loop."""
        self.is_running = True
        
        # Schedule searches
        scheduler = APScheduler()
        scheduler.add_job(self.search_for_leads, 'cron', hour=10, minute=0)  # Daily at 10 AM
        
        # Subscribe to search requests
        self.subscribe_to_events(["search_request"], self.handle_search_request)
        
        scheduler.start()
    
    def search_for_leads(self, criteria: Optional[Dict] = None) -> List['Lead']:
        """
        Search LinkedIn for potential leads.
        
        Args:
            criteria: Optional search criteria (uses default if not provided)
            
        Returns:
            List of discovered leads
        """
        search_criteria = criteria or self.search_criteria
        self.logger.info(f"Searching LinkedIn with criteria: {search_criteria}")
        
        # Perform LinkedIn search
        profiles = self.linkedin_client.search_profiles(search_criteria)
        
        discovered_leads = []
        for profile in profiles:
            try:
                # Analyse profile using LLM
                lead = self.analyse_profile(profile)
                
                # Check for duplicates
                if not self.state_manager.lead_exists(lead.linkedin_url):
                    # Add to database
                    self.state_manager.add_lead(lead)
                    discovered_leads.append(lead)
                    
                    # Publish event
                    self.publish_event("lead_discovered", {
                        "lead_id": lead.id,
                        "name": lead.name,
                        "classification": lead.classification,
                        "quality_score": lead.quality_score
                    })
            except Exception as e:
                self.logger.error(f"Error processing profile: {e}")
        
        self.logger.info(f"Discovered {len(discovered_leads)} new leads")
        return discovered_leads
    
    def analyse_profile(self, profile_data: Dict[str, Any]) -> 'Lead':
        """
        Analyse LinkedIn profile and extract structured data.
        
        Args:
            profile_data: Raw profile data from LinkedIn
            
        Returns:
            Lead object with extracted information
        """
        # Use LLM to extract structured data
        extraction_prompt = f"""
        Extract the following information from this LinkedIn profile:
        - Full name
        - Current position/title
        - Company name
        - LinkedIn profile URL
        - Years of experience (if available)
        - Key skills or expertise
        
        Profile data:
        {json.dumps(profile_data, indent=2)}
        
        Return JSON with fields: name, position, company, linkedin_url, experience_years, skills
        """
        
        extracted = json.loads(self.llm_client.generate(extraction_prompt, temperature=0.1))
        
        # Create Lead object
        lead = Lead(
            name=extracted.get("name", ""),
            position=extracted.get("position", ""),
            company=extracted.get("company", ""),
            linkedin_url=extracted.get("linkedin_url", ""),
            contact_status="Not Contacted"
        )
        
        # Classify using LLM-enhanced classifier
        lead.classification = self.classifier.classify(lead, use_llm=True)
        
        # Calculate quality score
        lead.quality_score = self.quality_scorer.calculate_score(lead, profile_data)
        
        return lead
    
    def handle_search_request(self, event: Dict[str, Any]) -> None:
        """Handle search request from Sales Manager."""
        criteria = event["data"].get("criteria", {})
        self.search_for_leads(criteria)
```

**Key Methods**:
- `search_for_leads()`: Search LinkedIn based on criteria
- `analyse_profile()`: Extract and structure profile data using LLM
- `classify_prospect()`: Classify as Speaker/Sponsor
- `calculate_quality_score()`: Score lead quality (1-10)

---

### 3. Outreach Agent

**File**: `src/agents/outreach_agent.py`

**Purpose**: Generates messages, sends via LinkedIn, monitors responses, and analyses engagement.

**Class Definition**:

```python
class OutreachAgent(BaseAgent):
    """Handles messaging and response tracking."""
    
    def __init__(self, config: Dict[str, Any], state_manager, message_queue, llm_client):
        super().__init__("outreach", config, state_manager, message_queue, llm_client)
        self.message_generator = MessageGenerator(llm_client, config["messaging"])
        self.linkedin_sender = LinkedInSender(config["linkedin"])
        self.response_analyser = ResponseAnalyser(llm_client)
        self.rate_limiter = RateLimiter(config["rate_limiting"])
    
    def start(self) -> None:
        """Start outreach loop."""
        self.is_running = True
        
        scheduler = APScheduler()
        
        # Process allocated leads
        scheduler.add_job(self.process_allocated_leads, 'interval', minutes=30)
        
        # Monitor responses
        scheduler.add_job(self.monitor_responses, 'interval', hours=2)
        
        # Subscribe to lead allocations
        self.subscribe_to_events(["lead_allocation"], self.handle_lead_allocation)
        
        scheduler.start()
    
    def process_allocated_leads(self) -> None:
        """Process leads allocated by Sales Manager."""
        # Get allocated leads
        allocated_leads = self.state_manager.read_leads({
            "contact_status": "Allocated"
        })
        
        for lead in allocated_leads:
            try:
                # Check rate limiter
                if not self.rate_limiter.can_send():
                    wait_time = self.rate_limiter.get_time_until_next_send()
                    self.logger.info(f"Rate limit reached, waiting {wait_time}")
                    break
                
                # Generate message
                message = self.message_generator.generate(lead, use_llm=True)
                
                # Send message
                result = self.send_message(lead, message)
                
                if result.success:
                    # Update status
                    self.state_manager.update_lead(lead.id, {
                        "contact_status": "Message Sent",
                        "message_sent": message,
                        "sent_at": datetime.now().isoformat()
                    })
                    
                    # Publish event
                    self.publish_event("message_sent", {
                        "lead_id": lead.id,
                        "message_id": result.message_id
                    })
                    
                    # Record send
                    self.rate_limiter.record_send()
                
            except Exception as e:
                self.logger.error(f"Error processing lead {lead.id}: {e}")
    
    def generate_message(self, lead: 'Lead') -> str:
        """
        Generate personalised message using LLM.
        
        Args:
            lead: Lead object
            
        Returns:
            Personalised message string
        """
        # Use LLM for intelligent message generation
        prompt = f"""
        Generate a personalised LinkedIn message for this prospect:
        
        Name: {lead.name}
        Position: {lead.position}
        Company: {lead.company}
        Classification: {lead.classification}
        Quality Score: {lead.quality_score}
        
        Event: {self.config['event_name']}
        Event Date: {self.config['event_date']}
        
        Requirements:
        - Maximum 300 characters
        - Professional but friendly tone
        - Personalised (use their name and company)
        - Clear call to action
        - Appropriate for {lead.classification} classification
        
        Generate the message:
        """
        
        message = self.llm_client.generate(prompt, temperature=0.8, max_tokens=150)
        
        # Validate and clean
        message = message.strip()
        if len(message) > 300:
            message = message[:297] + "..."
        
        return message
    
    def send_message(self, lead: 'Lead', message: str) -> 'SendResult':
        """
        Send message via LinkedIn automation service.
        
        Args:
            lead: Lead object
            message: Message text
            
        Returns:
            SendResult object
        """
        try:
            result = self.linkedin_sender.send(lead.linkedin_url, message)
            return result
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return SendResult(success=False, error_message=str(e))
    
    def monitor_responses(self) -> None:
        """Monitor LinkedIn for responses."""
        # Get leads with sent messages
        sent_leads = self.state_manager.read_leads({
            "contact_status": "Message Sent"
        })
        
        for lead in sent_leads:
            # Check for response via LinkedIn API
            response = self.linkedin_sender.check_response(lead.linkedin_url)
            
            if response:
                # Analyse response
                analysis = self.analyse_response(response)
                
                # Update lead
                self.state_manager.update_lead(lead.id, {
                    "contact_status": "Responded",
                    "response": response,
                    "response_sentiment": analysis.sentiment,
                    "response_intent": analysis.intent,
                    "responded_at": datetime.now().isoformat()
                })
                
                # Publish event
                self.publish_event("response_received", {
                    "lead_id": lead.id,
                    "sentiment": analysis.sentiment,
                    "intent": analysis.intent,
                    "response_text": response
                })
                
                # Notify human team if positive
                if analysis.sentiment == "positive":
                    self._notify_human_team(lead, analysis)
    
    def analyse_response(self, response_text: str) -> 'ResponseAnalysis':
        """
        Analyse response using LLM.
        
        Args:
            response_text: Response message text
            
        Returns:
            ResponseAnalysis object
        """
        prompt = f"""
        Analyse this LinkedIn response message and determine:
        1. Sentiment: positive, negative, or neutral
        2. Intent: interested, not_interested, requesting_info, or unclear
        3. Key information: any questions, objections, or requirements mentioned
        
        Response: "{response_text}"
        
        Return JSON with fields: sentiment, intent, key_info, confidence
        """
        
        analysis_data = json.loads(self.llm_client.generate(prompt, temperature=0.3))
        
        return ResponseAnalysis(
            sentiment=analysis_data["sentiment"],
            intent=analysis_data["intent"],
            key_info=analysis_data.get("key_info", ""),
            confidence=analysis_data.get("confidence", 0.0)
        )
```

**Key Methods**:
- `process_allocated_leads()`: Process leads from queue
- `generate_message()`: Generate personalised messages using LLM
- `send_message()`: Send via LinkedIn automation
- `monitor_responses()`: Check for responses
- `analyse_response()`: Analyse response sentiment and intent

---

## Inter-Agent Communication

### Message Queue Interface

**File**: `src/communication/message_queue.py`

```python
import redis
from typing import List, Callable, Dict, Any
import json

class MessageQueue:
    """Message queue for inter-agent communication."""
    
    def __init__(self, redis_config: Dict[str, Any]):
        self.redis_client = redis.Redis(**redis_config)
        self.subscribers = {}
    
    def publish(self, event: Dict[str, Any]) -> None:
        """
        Publish event to queue.
        
        Args:
            event: Event dictionary with type, agent, data, timestamp
        """
        channel = f"agent.{event['agent']}.{event['type']}"
        self.redis_client.publish(channel, json.dumps(event))
    
    def subscribe(self, event_types: List[str], callback: Callable, agent_name: str) -> None:
        """
        Subscribe to event types.
        
        Args:
            event_types: List of event type patterns (e.g., ["lead_discovered", "message_sent"])
            callback: Callback function to handle events
            agent_name: Name of subscribing agent
        """
        pubsub = self.redis_client.pubsub()
        
        for event_type in event_types:
            channel = f"agent.*.{event_type}"
            pubsub.psubscribe(channel)
        
        # Store subscriber
        self.subscribers[agent_name] = {
            "pubsub": pubsub,
            "callback": callback
        }
    
    def process_messages(self, agent_name: str) -> None:
        """Process incoming messages for agent."""
        if agent_name not in self.subscribers:
            return
        
        subscriber = self.subscribers[agent_name]
        pubsub = subscriber["pubsub"]
        callback = subscriber["callback"]
        
        for message in pubsub.listen():
            if message["type"] == "pmessage":
                event = json.loads(message["data"])
                callback(event)
```

---

## LLM Integration

### LLM Client

**File**: `src/integrations/llm_client.py`

```python
from typing import Dict, Any, Optional
import openai
import anthropic

class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=config["api_key"])
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=config["api_key"])
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            system = system_prompt or ""
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
```

---

## Data Models

### Lead Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Lead:
    """Represents a prospect lead."""
    id: str
    name: str
    position: str
    company: str
    linkedin_url: str
    classification: Optional[str] = None  # "Speaker", "Sponsor", "Other"
    quality_score: Optional[float] = None  # 1-10
    contact_status: str = "Not Contacted"  # "Not Contacted", "Allocated", "Message Sent", "Responded", "Closed"
    message_sent: Optional[str] = None
    response: Optional[str] = None
    response_sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    response_intent: Optional[str] = None  # "interested", "not_interested", "requesting_info"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "company": self.company,
            "linkedin_url": self.linkedin_url,
            "classification": self.classification,
            "quality_score": self.quality_score,
            "contact_status": self.contact_status,
            "message_sent": self.message_sent,
            "response": self.response,
            "response_sentiment": self.response_sentiment,
            "response_intent": self.response_intent,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
```

---

## Configuration

### Agent Configuration

```yaml
# config/agents.yaml

sales_manager:
  llm_provider: "openai"
  llm_model: "gpt-4"
  coordination_interval_minutes: 60
  report_time: "09:15"
  allocation_strategy: "quality_priority"
  use_llm_for_allocation: true
  report_recipients:
    - "sales-team@example.com"
  
lead_finder:
  llm_provider: "openai"
  llm_model: "gpt-3.5-turbo"
  search_interval_hours: 24
  max_leads_per_day: 100
  quality_threshold: 6.0
  linkedin_service: "dripify"
  search_criteria:
    industries: ["Technology", "Software"]
    positions: ["CTO", "Founder", "VP Engineering"]
    company_size: "51-200"
  
outreach:
  llm_provider: "openai"
  llm_model: "gpt-3.5-turbo"
  message_generation_mode: "llm_enhanced"
  response_check_interval_hours: 2
  rate_limiting:
    daily_limit: 45
    min_interval_minutes: 5
    max_interval_minutes: 15
    working_hours_start: "09:00"
    working_hours_end: "17:00"
```

---

## Dependencies

### requirements.txt

```
# Core dependencies
python-dateutil==2.8.2
pytz==2024.1

# LLM APIs
openai==1.3.0
anthropic==0.7.0

# Google Sheets
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1

# Message Queue
redis==5.0.1

# HTTP requests
requests==2.31.0
urllib3==2.0.7

# Scheduling
APScheduler==3.10.4

# Configuration
PyYAML==6.0.1
python-dotenv==1.0.0

# Email
secure-smtplib==0.1.1

# Logging
colorlog==6.8.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
```

---

## Questions and Implementation Considerations

### Q1: LLM API Rate Limits and Costs
**Question**: How do we handle LLM API rate limits and manage costs as volume scales?

**Implementation Considerations**:
- Implement request queuing and throttling
- Cache similar LLM requests
- Use cheaper models (GPT-3.5) for simple tasks
- Monitor token usage and set budgets
- Implement fallback to rule-based logic if API unavailable

**Recommendation**: Start with GPT-3.5 for most operations, use GPT-4 only for Sales Manager strategic decisions. Implement caching layer for common requests.

---

### Q2: State Management Concurrency
**Question**: How do we handle concurrent updates to Google Sheets when multiple agents update the same lead?

**Implementation Considerations**:
- Implement optimistic locking with version numbers
- Use row-level locks (Redis-based)
- Retry on conflict with exponential backoff
- Consider eventual consistency model
- Plan migration to PostgreSQL for production scale

**Recommendation**: Implement optimistic locking with retry logic. For production, migrate to PostgreSQL with proper transaction support.

---

### Q3: Agent Failure Recovery
**Question**: How do agents recover state after failure or restart?

**Implementation Considerations**:
- Store all state changes in database
- Agents read current state on startup
- Implement idempotent operations
- Use message queue acknowledgements
- Health checks and automatic restart

**Recommendation**: Make agents stateless where possible. All state in database. Agents recover by reading current state on restart.

---

## Concerns and Technical Risks

### C1: LLM Response Quality
**Concern**: LLM-generated messages and classifications may be inconsistent or low quality.

**Mitigation**:
- Implement confidence scoring
- Human review for low-confidence outputs
- A/B test LLM vs. template-based approaches
- Use templates with LLM enhancement (hybrid approach)
- Continuous monitoring and feedback loops

---

### C2: Message Queue Reliability
**Concern**: Message queue failure could break agent coordination.

**Mitigation**:
- Use Redis with persistence or RabbitMQ HA
- Implement message acknowledgements
- Dead letter queues for failed messages
- Health monitoring and alerts
- Fallback to database polling if queue unavailable

---

## Improvement Suggestions

### I1: Implement Response Caching
**Suggestion**: Cache LLM responses for similar inputs to reduce API calls and costs.

**Implementation**: Use Redis to cache LLM responses keyed by input hash. Cache TTL: 24 hours.

---

### I2: Add Agent Health Monitoring
**Suggestion**: Implement comprehensive health checks and automatic recovery.

**Implementation**: Health check endpoints, process managers (systemd), automatic restart on failure.

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Senior Developer**: _________________ Date: _______
- **AI/ML Engineer**: _________________ Date: _______
