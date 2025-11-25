# Technical Specification - AI Sales Department

## Document Information
- **Document Type**: Technical Specification
- **Target Audience**: Software Developer, Implementation Team
- **Version**: 2.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Implementation guide for three AI agents with simplified polling architecture, LLM integration, and Google Sheets as single source of truth. See Technical Solution (02) for architecture details.

### Scheduling Architecture

**All agents use IntervalTrigger with 2-10 minute intervals:**
- Lead Finder: Polls for uncontacted leads every 2 minutes
- Sales Manager: Polls for classified leads every 2 minutes, generates reports daily at 18:00
- Outreach: Polls for allocated leads every 2 minutes, checks responses every 2 hours

**Agents track `last_check_time` to avoid reprocessing:**
- Each agent remembers when it last checked Google Sheets
- Only processes leads updated since `last_check_time`
- Provides fast reaction (2-10 min) without event files

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
    contact_status: str  # "Not Contacted", "Allocated", "Invitation Sent", "Message Sent", "Responded", "Closed", "Failed"
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
  report_time: "09:15"  # Report covers previous day (00:00-23:59)
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
Hey [Name],

We've just connected, so here's the blunt truth: All I know is you're at [Company], and your bio says, "{short phrase}." That caught my attention - that's it.

I run a crew called Innovators Guild, where we get together and actually talk about what's tough, weird, or broken in [industry]. No selling, no bragging, just what's real. Next event's on [Date].

If you want to drop your story into the mix or just lurk and listen, you're invited.

If this sounds like LinkedIn spam, bin it. If not, send something back.

Aybulat
```

**Sponsor Template**:
```
Hi [Name],

Saw [Company] in the wild doing [one thing they're known for]. I'll be honest: I don't have some crafted pitch or research dossier.

Innovators Guild is about builders who actually do stuff - sometimes it works, sometimes it explodes. If you feel like getting involved (money, projects, experiments - whatever), ping me. If not, that's completely fine too.

No follow-ups, no nurture sequence, no "circle-back."

Aybulat
```

**Template Variables**:
- `[Name]` - Lead's first name
- `[Company]` - Lead's company name
- `[Position]` - Lead's position/title
- `[Date]` - Event date
- `[specific area]` - For Speakers: their area of expertise (derived from position)
- `[one thing they're known for]` - For Sponsors: what company is known for (derived from company/position)

---

## Future Enhancements (Post-Sprint 1)

### FE-01: Clay.com API Integration

**Current State**: CSV export/import method (Sprint 1).

**Future Enhancement**: Automatic Clay.com API → Google Sheets synchronization.

**Implementation**:
- Separate sync script/process (not part of agent codebase)
- Lead Finder Agent continues reading from Google Sheets (no changes)
- Optional: Direct API integration in Lead Finder Agent

**Status**: Optional, not required for Sprint 1.

---

### FE-02: Multi-Account LinkedIn Support

**Current State**: Single LinkedIn account (`linkedin_accounts: 1`).

**Future Enhancement**: Multiple accounts with priority-based routing.

**Configuration** (future):
```yaml
outreach:
  linkedin_accounts: 4
  account_priority: ["account_1", "account_2", "account_3", "account_4"]
  rate_limit_daily_per_account: 45
```

**Implementation**:
- Rate limiter tracks count per account independently
- Outreach Agent switches to next account when primary reaches limit
- Each account requires separate API key and account_id

**Status**: Planned after Sprint 1 testing.

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Senior Developer**: _________________ Date: _______
