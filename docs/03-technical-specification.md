# Technical Specification - AI Sales Department

## Document Information
- **Document Type**: Technical Specification
- **Target Audience**: Software Developer, Implementation Team
- **Version**: 2.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Implementation guide for three AI agents with inter-agent communication, LLM integration, and shared state management. See Technical Solution (02) for architecture details.

---

## Project Structure

```
src/
├── agents/
│   ├── base_agent.py              # Base class
│   ├── sales_manager_agent.py     # Sales Manager
│   ├── lead_finder_agent.py       # Lead Finder
│   └── outreach_agent.py          # Outreach
├── core/
│   ├── lead_classifier.py         # Classification
│   ├── quality_scorer.py          # Quality scoring
│   ├── message_generator.py       # Message generation
│   ├── response_analyser.py       # Response analysis
│   └── rate_limiter.py            # Rate limiting
├── integrations/
│   ├── google_sheets_io.py        # Database
│   ├── linkedin_sender.py         # LinkedIn API
│   ├── llm_client.py              # LLM API
│   └── email_service.py           # Email
├── communication/
│   ├── message_queue.py           # Redis queue
│   ├── event_bus.py               # Pub/Sub
│   └── state_manager.py           # State management
└── utils/
    ├── config_loader.py
    ├── logger.py
    └── validators.py
```

---

## Core Interfaces

### BaseAgent

```python
class BaseAgent(ABC):
    def __init__(self, agent_name, config, state_manager, message_queue, llm_client)
    def start(self) -> None
    def stop(self) -> None
    def process_message(self, message: Dict) -> None
    def health_check(self) -> Dict
    def publish_event(self, event_type: str, data: Dict) -> None
    def subscribe_to_events(self, event_types: List[str], callback: Callable) -> None
```

### Sales Manager Agent

```python
class SalesManagerAgent(BaseAgent):
    def coordinate_daily_operations(self) -> None
    def allocate_leads(self, max_leads: int = 50) -> List[Lead]
    def monitor_performance(self) -> Dict
    def generate_daily_report(self) -> None
    def optimise_strategy(self) -> Dict
```

### Lead Finder Agent

```python
class LeadFinderAgent(BaseAgent):
    def search_for_leads(self, criteria: Dict) -> List[Lead]
    def analyse_profile(self, profile_data: Dict) -> Lead
    def classify_prospect(self, lead: Lead) -> str
    def calculate_quality_score(self, lead: Lead) -> float
```

### Outreach Agent

```python
class OutreachAgent(BaseAgent):
    def process_allocated_leads(self) -> None
    def generate_message(self, lead: Lead) -> str
    def send_message(self, lead: Lead, message: str) -> SendResult
    def monitor_responses(self) -> None
    def analyse_response(self, response_text: str) -> ResponseAnalysis
```

---

## Data Models

### Lead

```python
@dataclass
class Lead:
    id: str
    name: str
    position: str
    company: str
    linkedin_url: str
    classification: Optional[str]  # "Speaker", "Sponsor", "Other"
    quality_score: Optional[float]  # 1-10
    contact_status: str  # "Not Contacted", "Allocated", "Message Sent", "Responded"
    message_sent: Optional[str]
    response: Optional[str]
    response_sentiment: Optional[str]  # "positive", "negative", "neutral"
    response_intent: Optional[str]  # "interested", "not_interested", "requesting_info"
    created_at: datetime
    last_updated: datetime
```

### SendResult

```python
@dataclass
class SendResult:
    success: bool
    message_id: Optional[str]
    timestamp: datetime
    error_message: Optional[str]
    service_used: Optional[str]
```

### ResponseAnalysis

```python
@dataclass
class ResponseAnalysis:
    sentiment: str  # "positive", "negative", "neutral"
    intent: str  # "interested", "not_interested", "requesting_info"
    key_info: str
    confidence: float  # 0.0-1.0
```

---

## LLM Integration

### LLMClient Interface

```python
class LLMClient:
    def __init__(self, config: Dict)
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ) -> str
```

**Supported Providers**: OpenAI, Anthropic, Local LLM

**Usage by Agent**:
- Sales Manager: GPT-4/Claude (strategic decisions)
- Lead Finder: GPT-3.5 (classification)
- Outreach: GPT-3.5 (messages, analysis)

---

## Message Queue Interface

### MessageQueue

```python
class MessageQueue:
    def __init__(self, redis_config: Dict)
    def publish(self, event: Dict) -> None
    def subscribe(self, event_types: List[str], callback: Callable, agent_name: str) -> None
    def process_messages(self, agent_name: str) -> None
```

**Event Types**: `lead_discovered`, `lead_allocation`, `message_sent`, `response_received`, `agent_error`

---

## State Manager Interface

### StateManager

```python
class StateManager:
    def read_leads(self, filters: Dict) -> List[Lead]
    def update_lead(self, lead_id: str, updates: Dict) -> bool
    def allocate_leads(self, lead_ids: List[str], agent: str) -> bool
    def save_agent_context(self, agent_name: str, context: Dict) -> None
    def get_agent_context(self, agent_name: str, context_type: str) -> Dict
```

**Features**: Optimistic locking, conflict resolution, version tracking

---

## Configuration

### agents.yaml

```yaml
sales_manager:
  llm_provider: "openai"
  llm_model: "gpt-4"
  coordination_time: "09:00"
  report_time: "09:15"

lead_finder:
  llm_provider: "openai"
  llm_model: "gpt-3.5-turbo"
  search_time: "10:00"
  max_leads_per_day: 100
  quality_threshold: 6.0

outreach:
  llm_provider: "openai"
  llm_model: "gpt-3.5-turbo"
  rate_limit_daily: 45
  rate_limit_interval: "5-15 minutes"
  response_check_interval: "2 hours"
```

---

## Dependencies

See `requirements.txt`:
- LLM: `openai`, `anthropic`
- Database: `gspread`, `google-auth`
- Message Queue: `redis`
- Scheduling: `APScheduler`
- Configuration: `PyYAML`, `python-dotenv`

---

## Error Handling

### Exception Hierarchy

```python
class OutreachAgentError(Exception): pass
class GoogleSheetsError(OutreachAgentError): pass
class LinkedInAPIError(OutreachAgentError): pass
class ConfigValidationError(OutreachAgentError): pass
class RateLimitExceededError(OutreachAgentError): pass
```

### Error Strategy
- Transient errors: Retry with exponential backoff (max 3)
- Permanent errors: Log and skip
- Critical errors: Stop and alert

---

## Testing Requirements

- Unit tests: >80% code coverage per agent
- Integration tests: Agent-to-agent, agent-to-services
- System tests: End-to-end workflows
- See Test Plan (04) for detailed test cases

---

## Questions

**Q1**: LLM API rate limits and costs management?  
**Q2**: State management concurrency handling?  
**Q3**: Agent failure recovery strategy?

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Senior Developer**: _________________ Date: _______
