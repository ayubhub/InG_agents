# Technical Solution Architecture - AI Sales Department

## Document Information
- **Document Type**: Technical Solution Architecture
- **Target Audience**: Solution Architect, Technical Lead
- **Version**: 2.2 (Updated with Stakeholder Feedback)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Multi-agent, event-driven architecture with three AI agents: **Sales Manager** (coordinates), **Lead Finder** (discovers), **Outreach** (messages). Uses Google Sheets as database, Redis for messaging, **Google Gemini Preview API** for LLM intelligence.

**Design Principle**: Simple solution based on Google Sheets, no over-engineering.

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
    │  - Google Sheets (Database)     │
    │  - Redis (Message Queue)        │
    │  - Event Bus (Pub/Sub)          │
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
- **Database**: Google Sheets (primary, single source of truth)
- **Message Queue**: Redis Pub/Sub
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

### Message Queue (Redis)
**Event Types**:
- `lead_discovered` - Lead Finder → Sales Manager
- `lead_allocation` - Sales Manager → Outreach
- `message_sent` - Outreach → Sales Manager
- `response_received` - Outreach → Sales Manager
- `agent_error` - Any agent → Sales Manager (logged, not escalated)

**Event Structure**:
```json
{
  "type": "event_type",
  "agent": "agent_name",
  "data": {...},
  "context": {...},
  "timestamp": "ISO8601"
}
```

### Event Bus (Pub/Sub)
- Channels: `agent.{agent_name}.{event_type}`
- Real-time notifications
- State synchronisation

---

## Shared State Management

### Google Sheets Schema (Simple Approach)

**Leads Sheet** (Primary):
- Lead ID, Name, Position, Company, LinkedIn URL
- Classification, Quality Score
- Contact Status, Message Sent, Response
- Response Sentiment, Response Intent

**Agent Context Sheet** (Optional):
- Timestamp, Agent, Context Type
- Context Data (JSON), LLM Reasoning
- Related Lead ID

### State Manager
- **Simple approach**: Google Sheets as single source of truth
- Row-level locking for concurrent updates (Redis-based)
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

## Scalability

### Current (Sprint 1)
- Single instance per agent
- 200+ leads/week
- **Google Sheets as database** (simple, sufficient)
- Single LinkedIn account
- No complex scaling needed

### Future Considerations (Post-Sprint 1)
- Database migration only if Google Sheets becomes bottleneck
- Keep architecture simple

---

## Security & Compliance

- Credentials in environment variables
- API keys rotated every 90 days
- Encrypted communications (TLS)
- Audit logging
- GDPR compliance
- LinkedIn ToS compliance (strict rate limiting)

---

## Resolved Questions

**Q1**: LLM API - **Google Gemini Preview API** (cost-effective, high quality)

**Q2**: Inter-agent communication - Redis Pub/Sub with Google Sheets as backup

**Q3**: Database consistency - Simple optimistic locking, Google Sheets sufficient

**Q4**: LLM response quality - Gemini provides good quality, 10% error rate acceptable for sentiment analysis

**Q5**: Agent failure recovery - State recovery from Google Sheets on restart

---

## Resolved Concerns

**C1**: Google Sheets scalability - **Sufficient for Sprint 1**, simple solution preferred

**C2**: LLM API dependency - **Google Gemini** chosen, rule-based fallback available

**C3**: Agent coordination - **Simplest approach** with Google Sheets + Redis

**C4**: LinkedIn compliance - **Single account**, strict rate limiting (30-50/day, 5-15 min intervals)

---

## Improvement Suggestions

**I1**: Machine learning for lead scoring - **Approved if simple solution**
- Simple scoring algorithm based on conversion patterns
- Can be enhanced later

**I2-I8**: **Deferred to future sprints**

---

## Document Approval

- **Solution Architect**: _________________ Date: _______
- **Technical Lead**: _________________ Date: _______
