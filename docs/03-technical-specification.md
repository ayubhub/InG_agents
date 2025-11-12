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
    def read_uncontacted_leads(self) -> List[Lead]  # Reads from Google Sheets
    def analyse_lead(self, lead: Lead) -> Lead  # Analyses existing lead data
    def classify_prospect(self, lead: Lead) -> str
    def calculate_quality_score(self, lead: Lead) -> float
    def update_lead_classification(self, lead: Lead) -> bool  # Updates in Google Sheets
```

**Note**: Agent reads leads that are already in Google Sheets (imported from Clay.com or other sources). Agent does not search LinkedIn.

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

**Provider**: Google Gemini Preview API (primary)

**Usage by Agent**:
- Sales Manager: Gemini Pro (strategic decisions, report insights)
- Lead Finder: Gemini Pro (profile analysis, edge case classification)
- Outreach: Gemini Pro (message generation, sentiment analysis - 10% error rate acceptable)

**Fallback**: Rule-based logic if API unavailable

---

## Message Queue Interface (File-Based)

### MessageQueue

```python
class MessageQueue:
    def __init__(self, queue_directory: str = "data/queue", sqlite_db: str = "data/state/agents.db")
    def publish(self, event: Dict) -> None
    def subscribe(self, event_types: List[str], callback: Callable, agent_name: str) -> None
    def process_messages(self, agent_name: str) -> None
    def _save_event_to_file(self, event: Dict) -> str  # Returns file path
    def _load_events_from_directory(self, directory: str) -> List[Dict]
```

**Implementation**:
- Events stored as JSON files in `data/queue/pending/`
- SQLite index tracks event status
- Agents poll directory for new events
- Processed events moved to `data/queue/processed/`
- Failed events moved to `data/queue/failed/`

**Event Types**: `lead_discovered`, `lead_allocation`, `message_sent`, `response_received`, `agent_error`

---

## State Manager Interface

### StateManager

```python
class StateManager:
    def __init__(self, google_sheets_client, sqlite_db_path: str = "data/state/agents.db")
    def read_leads(self, filters: Dict) -> List[Lead]  # From Google Sheets
    def update_lead(self, lead_id: str, updates: Dict) -> bool  # Update Google Sheets
    def allocate_leads(self, lead_ids: List[str], agent: str) -> bool
    def save_agent_context(self, agent_name: str, context: Dict) -> None  # To SQLite + files
    def get_agent_context(self, agent_name: str, context_type: str) -> Dict
    def acquire_lock(self, resource_id: str, agent_name: str) -> bool  # SQLite-based lock
    def release_lock(self, resource_id: str) -> None
```

**Storage**:
- **Google Sheets**: Primary database for leads
- **SQLite**: Local state (agent state, locks, rate limiter, queue index)
- **File System**: Context cache, knowledge base, LLM response cache

**Features**: Optimistic locking (SQLite), conflict resolution, version tracking

---

## Configuration

### agents.yaml

```yaml
sales_manager:
  llm_provider: "google"
  llm_model: "gemini-pro"
  coordination_time: "09:00"
  report_time: "09:15"
  include_self_review: true

lead_finder:
  llm_provider: "google"
  llm_model: "gemini-pro"
  lead_source: "google_sheets"  # CSV import or manual entry
  max_leads_per_day: 100
  quality_threshold: 6.0
  classification_mode: "rule_based_enhanced"

outreach:
  llm_provider: "google"
  llm_model: "gemini-pro"
  rate_limit_daily: 45
  rate_limit_interval: "5-15 minutes"
  rate_limit_window: "09:00-17:00"
  linkedin_accounts: 1  # Single account
  response_check_interval: "2 hours"
  acceptable_error_rate: 0.10  # 10% for sentiment analysis

storage:
  data_directory: "data"  # Local data directory
  sqlite_db: "data/state/agents.db"
  queue_directory: "data/queue"
  cache_directory: "data/cache"
  events_directory: "data/events"
```

---

## Dependencies

See `requirements.txt`:
- LLM: `google-generativeai` (Gemini API)
- Database: `gspread`, `google-auth`
- Local Storage: SQLite (built-in Python), file system (JSON files)
- Scheduling: `APScheduler`
- Configuration: `PyYAML`, `python-dotenv`

**Note**: No Redis or external servers needed. All storage is local (SQLite + files).

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

## Quality Scoring Algorithm (Simple)

```python
def calculate_quality_score(lead: Lead) -> float:
    """
    Simple quality scoring (1-10 scale).
    
    Factors:
    - Position match: 0-4 (exact match = 4, partial = 2-3)
    - Company relevance: 0-3 (based on company size/type)
    - Profile completeness: 0-3 (based on available data)
    """
    position_score = calculate_position_match(lead.position)  # 0-4
    company_score = calculate_company_relevance(lead.company)  # 0-3
    completeness_score = calculate_completeness(lead)  # 0-3
    
    total = position_score + company_score + completeness_score
    return min(10.0, max(1.0, total))
```

## Message Templates (Innovators Guild Templates)

**Speaker Template**:
```
Hi [Name],

We're hosting an Innovators Guild event on [Date] - a curated gathering of the most ambitious engineers, founders, and innovators building the future.

Your work at [Company] leading [specific area] is exactly the kind of perspective our community needs to hear. I think you'd be a perfect fit.

Interested in speaking?

Best,

Ayub

Innovators Guild

https://innovators.london
```

**Sponsor Template**:
```
Hi [Name],

I've been following [Company]'s work in [one thing they're known for] - really impressed!

We run Innovators Guild events that bring together ambitious leaders and emerging companies. I think your team would find real value in being part of it.

Would you be open to a quick chat about sponsoring or collaborating on an event?

Best,

Ayub

Innovators Guild

https://innovators.london
```

**Template Variables**:
- `[Name]` - Lead's first name
- `[Company]` - Lead's company name
- `[Position]` - Lead's position/title
- `[Date]` - Event date
- `[specific area]` - For Speakers: their area of expertise (derived from position)
- `[one thing they're known for]` - For Sponsors: what company is known for (derived from company/position)

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Senior Developer**: _________________ Date: _______
