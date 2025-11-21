# Technical Solution Architecture - AI Sales Department

## Document Information
- **Document Type**: Technical Solution Architecture
- **Target Audience**: Solution Architect, Technical Lead
- **Version**: 2.3 (Updated - Local Storage)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Multi-agent architecture with three AI agents: **Sales Manager** (coordinates), **Lead Finder** (discovers), **Outreach** (messages). Uses Google Sheets as single source of truth, **local file-based storage** (SQLite + JSON files) for caching, **Google Gemini Preview API** for LLM intelligence.

**Design Principle**: Simple solution based on Google Sheets polling, no event files, no servers, no over-engineering.

**Architecture**: Polling-Only (Simple & Reliable)
- Agents poll Google Sheets every 2-10 minutes
- Agents track `last_check_time` to process only new/updated leads
- Lead status (`contact_status`) determines which agent should process it
- No event files needed - Google Sheets is the single source of truth

---

## Architecture Overview

### System Components

```
Human Interface (Reports/Dashboards)
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
Sales Mgr  Lead Finder  Outreach  (Agents)
    │         │          │          │
    └─────────┼──────────┼──────────┘
              │          │
    ┌─────────▼──────────▼──────────┐
    │  Shared State & Communication  │
    │  - Google Sheets (Single Source)│
    │  - SQLite (Rate Limiting)       │
    │  - JSON Files (Cache Only)      │
    └─────────┬──────────────────────┘
              │
    ┌─────────▼──────────┐
    │  External Services  │
    │  - LinkedIn APIs    │
    │  - Google Gemini    │
    │  - Email            │
    └─────────────────────┘
```

### Technology Stack
- **Language**: Python 3.10+
- **LLM**: **Google Gemini Preview API** (cost-effective, high quality)
- **Database**: Google Sheets (primary), **SQLite** (local state, no server needed)
- **Message Queue**: **File-based** (JSON files in `data/queue/` directory)
- **Cache**: **File-based** (JSON files in `data/cache/` directory)
- **Scheduling**: APScheduler
- **LinkedIn**: Dripify/Gojiberry API (single account)

---

## Agent Responsibilities

### Sales Manager Agent
- Coordinates daily operations (9:00 AM)
- Allocates leads (prioritises by quality/classification)
- Monitors performance metrics
- Generates daily reports (9:15 AM) with **Agent Self-Review** section
- Optimises strategy using LLM analysis
- **No escalation**: Only reports, flags uncertain decisions for human review

### Lead Finder Agent
- **Reads uncontacted leads from Google Sheets** (leads already imported, agent doesn't search LinkedIn)
- Analyses profiles using LLM (Gemini)
- Classifies (Speaker/Sponsor/Other) - rule-based enhanced with LLM
- Calculates quality scores (1-10) - simple algorithm
- Updates lead records in database

**Lead Sources** (imported to Google Sheets before processing):
- Clay.com export (current source) - **recommended for Sprint 1**
- Google Sheets manual entry or CSV import
- LinkedIn Sales Navigator export
- Apollo.io, Lusha, Hunter.io exports
- Any CSV-compatible source

### Outreach Agent
- Processes allocated leads
- Generates personalised messages (LLM - Gemini)
- Sends via LinkedIn (rate-limited: 30-50/day, **single account**)
- Monitors responses (every 2 hours)
- Analyses sentiment/intent (LLM - Gemini, 10% error rate acceptable)

---

## Inter-Agent Communication

### Polling-Only Architecture (Simplified)

**Agents coordinate through Google Sheets as single source of truth:**
- Each agent polls Sheets every 2-10 minutes
- Agents track `last_check_time` to process only new/updated leads
- Lead status (`contact_status`) determines which agent should process it

**Flow**:
1. Lead Finder: `Not Contacted` → classify → `Not Contacted` (but with Classification)
2. Sales Manager: checks `last_updated` → allocates → `Allocated`
3. Outreach: checks `allocated_at` → sends → `Message Sent`

**Benefits**:
- ✅ Simple: one mechanism (Sheets)
- ✅ Reliable: no file sync issues
- ✅ Fast: 4-10 minutes end-to-end
- ✅ Debuggable: all state visible in Sheets

**No Event Files**: Agents previously used file-based events, but this was removed for simplicity. Google Sheets `last_updated` timestamps provide sufficient coordination.
- `agent_error` - Any agent → Sales Manager (logged, not escalated)

**Event Structure**:
```json
{
  "type": "event_type",
  "agent": "agent_name",
  "data": {...},
  "context": {...},
  "timestamp": "ISO8601",
  "event_id": "unique_id"
}
```

**Processing**:
- Agents poll `data/queue/pending/` directory for new events
- Process events matching subscribed types
- Move processed events to `processed/` directory
- Retry failed events (max 3 attempts)

### Event Bus (File-Based Pub/Sub)

**Location**: `data/events/` directory

**Structure**:
- `data/events/{agent_name}/{event_type}/` - Event files by agent and type
- Agents watch directories for new files
- File-based notifications (file creation triggers processing)

---

## Shared State Management

### Google Sheets (Primary Database)

**Leads Sheet** (Primary):
- Lead ID, Name, Position, Company, LinkedIn URL
- Classification, Quality Score
- Contact Status, Message Sent, Response
- Response Sentiment, Response Intent

**Agent Context Sheet** (Optional):
- Timestamp, Agent, Context Type
- Context Data (JSON), LLM Reasoning
- Related Lead ID

### SQLite (Local State Database)

**Location**: `data/state/agents.db`

**Tables**:
- `agent_state` - Current state of each agent
- `rate_limiter` - Rate limiting state
- `message_queue_index` - Index of queued messages
- `agent_context` - Agent context snapshots
- `locks` - Row-level locks for Google Sheets updates

**Schema**:
```sql
CREATE TABLE agent_state (
    agent_name TEXT PRIMARY KEY,
    state_data TEXT,  -- JSON
    last_updated TIMESTAMP
);

CREATE TABLE rate_limiter (
    id INTEGER PRIMARY KEY,
    daily_count INTEGER,
    last_send_time TIMESTAMP,
    last_reset_date DATE
);

CREATE TABLE message_queue_index (
    event_id TEXT PRIMARY KEY,
    event_type TEXT,
    agent_from TEXT,
    agent_to TEXT,
    status TEXT,  -- pending, processed, failed
    file_path TEXT,
    created_at TIMESTAMP
);
```

### File-Based Cache

**Location**: `data/cache/` directory

**Structure**:
- `data/cache/knowledge/{topic}.json` - Shared knowledge cache
- `data/cache/agent_context/{agent_name}.json` - Agent context cache
- `data/cache/llm_responses/{hash}.json` - Cached LLM responses

### State Manager
- **Simple approach**: Google Sheets as single source of truth
- SQLite for local state (locks, rate limiter, queue index)
- File-based message queue
- Optimistic locking with retry
- Conflict resolution

---

## LLM Integration

### Google Gemini Preview API

**Usage by Agent**:
- **Sales Manager**: Strategic decisions, lead prioritisation, performance analysis, report insights
- **Lead Finder**: Profile analysis, data extraction, classification for edge cases
- **Outreach**: Message generation, response sentiment analysis (10% error rate acceptable)

**Configuration**:
```yaml
llm:
  provider: "google"
  model: "gemini-pro"  # or "gemini-pro-vision"
  api_key: "${GEMINI_API_KEY}"
  temperature: 0.7
  max_tokens: 500
```

**Benefits**:
- Cost-effective
- High quality responses
- Good API reliability
- Reasonable rate limits

**Fallback**: Rule-based logic if API unavailable

**Caching**: LLM responses cached in `data/cache/llm_responses/` to reduce API calls

---

## Data Flow

### Daily Workflow
1. Sales Manager starts coordination (9:00 AM)
2. Lead Finder reads **uncontacted leads** from Google Sheets (leads already imported by human team)
3. Lead Finder analyses/classifies leads
4. Sales Manager allocates leads (30-50/day)
5. Outreach generates messages and sends (rate-limited, single account)
6. Outreach monitors responses (every 2h)
7. Sales Manager generates report (9:15 AM) with self-review section

### Error Handling
- Transient errors: Retry with exponential backoff (max 3)
- Permanent errors: Log and skip, continue processing
- **No escalation**: Errors logged in daily report for human review

---

## Configuration

### Agent Configuration
```yaml
sales_manager:
  llm_provider: "google"
  llm_model: "gemini-pro"
  coordination_time: "09:00"
  report_time: "09:15"
  include_self_review: true  # Flag uncertain decisions

lead_finder:
  llm_provider: "google"
  llm_model: "gemini-pro"
  lead_source: "google_sheets"  # CSV import or manual
  max_leads_per_day: 100
  quality_threshold: 6.0
  classification_mode: "rule_based_enhanced"  # Rules + LLM for edge cases

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

## Data Quality and Error Reduction

### Strategies

1. **Enhanced Validation**:
   - Required fields check (name, LinkedIn URL)
   - LinkedIn URL format validation
   - Position normalisation

2. **LLM-Assisted Classification**:
   - Rule-based for clear cases (CTO → Speaker, CEO → Sponsor)
   - LLM for edge cases (unclear positions)
   - Flag uncertain classifications for human review

3. **Quality Scoring** (Simple Algorithm):
   - Position match score (0-4): Exact match = 4, partial = 2-3
   - Company relevance (0-3): Based on company size/type
   - Profile completeness (0-3): Based on available data
   - Total: 1-10 scale

4. **Pattern Analysis**:
   - Track which lead sources convert best
   - Track which positions/companies respond
   - Track message template performance
   - Use patterns to improve scoring

5. **Agent Self-Review**:
   - Daily report includes uncertain decisions
   - Human feedback improves future decisions

---

## Local Storage Structure

### Directory Layout

```
data/
├── state/
│   └── agents.db              # SQLite database
├── queue/
│   ├── pending/               # Pending events
│   ├── processed/             # Processed events (archive)
│   └── failed/                # Failed events
├── cache/
│   ├── knowledge/             # Shared knowledge
│   ├── agent_context/        # Agent context cache
│   └── llm_responses/        # Cached LLM responses
├── events/
│   ├── sales_manager/        # Events for Sales Manager
│   ├── lead_finder/          # Events for Lead Finder
│   └── outreach/             # Events for Outreach
└── logs/
    └── agents.log             # Application logs
```

---

## Scalability

### Current (Sprint 1)
- Single instance per agent
- 200+ leads/week
- **Google Sheets as primary database** (simple, sufficient)
- **SQLite for local state** (no server needed)
- **File-based message queue** (no server needed)
- Single LinkedIn account
- No complex scaling needed
- **No separate servers** - everything runs locally

### Future Considerations (Post-Sprint 1)
- Database migration only if Google Sheets becomes bottleneck
- Keep architecture simple
- All storage remains local (no servers)

---

## Security & Compliance

- Credentials in environment variables
- API keys rotated every 90 days
- Encrypted communications (TLS)
- Audit logging to local files
- GDPR compliance
- LinkedIn ToS compliance (strict rate limiting)
- Local data directory permissions (restrict access)

---

## Resolved Questions

**Q1**: LLM API - **Google Gemini Preview API** (cost-effective, high quality) ✅

**Q2**: Inter-agent communication - **File-based message queue** (JSON files in `data/queue/`) with SQLite index ✅

**Q3**: Database consistency - Simple optimistic locking, Google Sheets sufficient, SQLite for local state ✅

**Q4**: LLM response quality - Gemini provides good quality, 10% error rate acceptable for sentiment analysis ✅

**Q5**: Agent failure recovery - State recovery from Google Sheets and SQLite on restart ✅

---

## Resolved Concerns

**C1**: Google Sheets scalability - **Sufficient for Sprint 1**, simple solution preferred ✅

**C2**: LLM API dependency - **Google Gemini** chosen, rule-based fallback available ✅

**C3**: Agent coordination - **Simplest approach** with Google Sheets + **SQLite + file-based queue** (no servers) ✅

**C4**: LinkedIn compliance - **Single account**, strict rate limiting (30-50/day, 5-15 min intervals) ✅

---

## Improvement Suggestions

**I1**: Machine learning for lead scoring - **Approved if simple solution**
- Simple scoring algorithm based on conversion patterns
- Can be enhanced later

**I2-I8**: **Deferred to future sprints** ✅

---

## Future Enhancements (Post-Sprint 1)

### FE-01: Clay.com API Integration

**Current State**: Clay.com leads exported to CSV, manually imported to Google Sheets.

**Future Enhancement**: Automatic synchronization from Clay.com API to Google Sheets.

**Architecture**:
- Separate synchronization process/script (not part of agent system)
- Syncs Clay.com API → Google Sheets on schedule (hourly/daily)
- Lead Finder Agent continues reading from Google Sheets (no changes needed)
- Optional: Direct API integration in Lead Finder Agent (alternative approach)

**Status**: Optional enhancement, not required for Sprint 1.

---

### FE-02: Multi-Account LinkedIn Strategy

**Current State**: Single LinkedIn account with 30-50 messages/day limit.

**Future Enhancement**: Support for multiple LinkedIn accounts with priority-based routing.

**Architecture**:
- **Priority-based routing**: Primary account used first, switches to reserve accounts when limit reached
- **Independent rate limiters**: Each account has its own rate limiter (45 messages/day per account)
- **Account configuration**: Each account has separate API key and account_id
- **Total capacity**: 4 accounts × 45 messages = 180 messages/day (if all used)

**Implementation**:
- Outreach Agent maintains account priority list
- Rate limiter tracks daily count per account independently
- Automatic failover when primary account reaches limit
- Configuration supports multiple accounts with individual settings

**Configuration Example** (future):
```yaml
outreach:
  linkedin_accounts: 4
  account_priority: ["account_1", "account_2", "account_3", "account_4"]
  rate_limit_daily_per_account: 45
```

**Environment Variables** (future):
```bash
# Account 1 (Primary)
DRIPIFY_API_KEY_1=...
DRIPIFY_ACCOUNT_ID_1=...

# Account 2 (Reserve)
DRIPIFY_API_KEY_2=...
DRIPIFY_ACCOUNT_ID_2=...
```

**Status**: Planned for implementation after successful Sprint 1 testing.

---

## Document Approval

- **Solution Architect**: _________________ Date: _______
- **Technical Lead**: _________________ Date: _______
