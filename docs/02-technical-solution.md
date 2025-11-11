# Technical Solution Architecture - AI Sales Department

## Document Information
- **Document Type**: Technical Solution Architecture
- **Target Audience**: Solution Architect, Technical Lead
- **Version**: 2.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Multi-agent, event-driven architecture with three AI agents: **Sales Manager** (coordinates), **Lead Finder** (discovers), **Outreach** (messages). Uses Google Sheets as database, Redis for messaging, LLM APIs for intelligence.

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
    │  - LLM APIs         │
    │  - Email            │
    └─────────────────────┘
```

### Technology Stack
- **Language**: Python 3.10+
- **LLM**: OpenAI GPT-3.5/GPT-4, Anthropic Claude
- **Database**: Google Sheets (primary), Redis (cache)
- **Message Queue**: Redis Pub/Sub
- **Scheduling**: APScheduler
- **LinkedIn**: Dripify/Gojiberry API

---

## Agent Responsibilities

### Sales Manager Agent
- Coordinates daily operations (9:00 AM)
- Allocates leads (prioritises by quality/classification)
- Monitors performance metrics
- Generates daily reports (9:15 AM)
- Optimises strategy using LLM analysis

### Lead Finder Agent
- Searches LinkedIn (daily at 10:00 AM)
- Analyses profiles using LLM
- Classifies (Speaker/Sponsor/Other)
- Calculates quality scores (1-10)
- Adds to database

### Outreach Agent
- Processes allocated leads
- Generates personalised messages (LLM)
- Sends via LinkedIn (rate-limited: 30-50/day)
- Monitors responses (every 2 hours)
- Analyses sentiment/intent (LLM)

---

## Inter-Agent Communication

### Message Queue (Redis)
**Event Types**:
- `lead_discovered` - Lead Finder → Sales Manager
- `lead_allocation` - Sales Manager → Outreach
- `message_sent` - Outreach → Sales Manager
- `response_received` - Outreach → Sales Manager
- `agent_error` - Any agent → Sales Manager

**Event Structure**:
```json
{
  "type": "event_type",
  "agent": "agent_name",
  "data": {...},
  "context": {...},  // Optional context sharing
  "timestamp": "ISO8601"
}
```

### Event Bus (Pub/Sub)
- Channels: `agent.{agent_name}.{event_type}`
- Real-time notifications
- State synchronisation

---

## Shared State Management

### Google Sheets Schema

**Leads Sheet**:
- Lead ID, Name, Position, Company, LinkedIn URL
- Classification, Quality Score
- Contact Status, Message Sent, Response
- Response Sentiment, Response Intent

**Agent Context Sheet** (NEW):
- Timestamp, Agent, Context Type
- Context Data (JSON), LLM Reasoning
- Related Lead ID, Performance Impact

### State Manager
- Row-level locking for concurrent updates
- Optimistic locking with retry
- Conflict resolution
- Version tracking

---

## LLM Integration

### Usage by Agent

**Sales Manager**: Strategic decisions, lead prioritisation, performance analysis, report insights, strategy optimisation

**Lead Finder**: Profile analysis, data extraction, intelligent classification, quality scoring

**Outreach**: Message generation, response sentiment analysis, intent detection

### Provider Strategy
- **Sales Manager**: GPT-4 or Claude (strategic)
- **Lead Finder**: GPT-3.5 or local LLM (classification)
- **Outreach**: GPT-3.5 (messages, analysis)

### Context Management
- Include relevant context from other agents in LLM prompts
- Cache common LLM responses
- Monitor token usage and costs

---

## Data Flow

### Daily Workflow
1. Sales Manager starts coordination (9:00 AM)
2. Requests Lead Finder to search if needed
3. Lead Finder discovers/analyses/classifies leads
4. Sales Manager allocates leads (30-50/day)
5. Outreach generates messages and sends
6. Outreach monitors responses (every 2h)
7. Sales Manager generates report (9:15 AM)

### Error Handling
- Transient errors: Retry with exponential backoff (max 3)
- Permanent errors: Log and skip, continue processing
- Critical errors: Stop and alert human team

---

## Configuration

### Agent Configuration
```yaml
sales_manager:
  llm_model: "gpt-4"
  coordination_time: "09:00"
  report_time: "09:15"

lead_finder:
  llm_model: "gpt-3.5-turbo"
  search_time: "10:00"
  max_leads_per_day: 100
  quality_threshold: 6.0

outreach:
  llm_model: "gpt-3.5-turbo"
  rate_limit_daily: 45
  rate_limit_interval: "5-15 minutes"
  response_check_interval: "2 hours"
```

---

## Scalability

### Current (Sprint 1)
- Single instance per agent
- 200+ leads/week
- Google Sheets as database

### Future Options
- Horizontal scaling (multiple agent instances)
- Database migration (PostgreSQL)
- Distributed state (Redis Cluster)
- Microservices architecture

---

## Security & Compliance

- Credentials in environment variables
- API keys rotated every 90 days
- Encrypted communications (TLS)
- Audit logging
- GDPR compliance
- LinkedIn ToS compliance

---

## Questions

**Q1**: LLM API costs and rate limits - how to manage?  
**Q2**: Inter-agent communication reliability - what if message queue fails?  
**Q3**: Database consistency with concurrent updates?  
**Q4**: LLM response quality and consistency?  
**Q5**: Agent failure recovery?

---

## Concerns

**C1**: Google Sheets may not scale as primary database  
**C2**: LLM API dependency and costs  
**C3**: Agent coordination complexity  
**C4**: LinkedIn API changes and compliance

---

## Improvement Suggestions

**I1**: Agent learning and feedback loops  
**I2**: Real-time dashboard  
**I3**: Advanced analytics and predictive modelling  
**I4**: Multi-account LinkedIn strategy  
**I5**: CRM integration

---

## Document Approval

- **Solution Architect**: _________________ Date: _______
- **Technical Lead**: _________________ Date: _______
