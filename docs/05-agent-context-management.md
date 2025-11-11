# Agent Context Management and Sharing

## Document Information
- **Document Type**: Technical Architecture - Context Management
- **Target Audience**: Developers, Architects
- **Version**: 1.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent System

---

## Executive Summary

How AI agents preserve working context (memory, decisions, learning) and share it. Multi-layered approach: persistent storage, event-driven communication, shared knowledge base.

---

## Context Types

### 1. Operational Context (Short-term)
Current work state: active tasks, allocations, rate limiter state, recent decisions.

**Storage**: In-memory + Redis cache + Google Sheets backup  
**Lifetime**: Hours to days

### 2. Historical Context (Long-term)
Complete history: all leads, messages, responses, performance metrics, patterns.

**Storage**: Google Sheets (primary) + Log files  
**Lifetime**: Permanent

### 3. Knowledge Context (Learning)
Accumulated knowledge: best templates, lead patterns, optimal timing, classification rules.

**Storage**: Configuration files + Knowledge base  
**Lifetime**: Evolves continuously

### 4. Strategic Context (Decision-making)
High-level strategy: decision reasoning, performance insights, optimisations.

**Storage**: Sales Manager Agent + Reports  
**Lifetime**: Weeks to months

---

## Storage Architecture

### Layer 1: Google Sheets (Primary)

**Leads Sheet**: All lead data, status, messages, responses

**Agent Context Sheet** (NEW):
- Timestamp, Agent, Context Type
- Context Data (JSON), LLM Reasoning
- Related Lead ID, Performance Impact

### Layer 2: Local File Cache (Fast Access)

**Location**: `data/cache/` directory

**File Structure**:
- `data/cache/agent_state/{agent_name}.json` - Current agent state
- `data/cache/knowledge/{topic}.json` - Shared knowledge cache
- `data/cache/agent_context/{agent_name}_{key}.json` - Agent-specific context
- `data/cache/llm_responses/{hash}.json` - Cached LLM responses

**SQLite for Locks**:
- `data/state/agents.db` - Locks table for coordination
- `locks` table: resource_id, agent_name, acquired_at, expires_at

### Layer 3: Log Files (Audit Trail)

Structured JSON logs: all decisions, LLM prompts/responses, errors, communications.

---

## Context Sharing Mechanisms

### 1. Event-Driven Context Sharing

Agents publish context-rich events that others consume.

**Example**:
```python
# Lead Finder publishes with context
event = {
    "type": "lead_discovered",
    "data": {"lead_id": "123", ...},
    "context": {
        "profile_analysis": "...",
        "classification_reasoning": "...",
        "quality_score_breakdown": {...}
    }
}

# Sales Manager receives and uses context
def handle_lead_discovered(event):
    context = event["context"]
    # Use quality_score_breakdown for prioritisation
    priority = calculate_priority(lead, context)
```

### 2. Shared Knowledge Base

Agents read/write shared knowledge that accumulates learnings.

**Example**:
```python
# Outreach learns which templates work
knowledge_base.update_learning("template:speaker_v2", {
    "success_count": +1,
    "response_rate": 0.12
})

# Sales Manager uses this knowledge
template_perf = knowledge_base.get_template_performance("speaker_v2")
if template_perf["response_rate"] > 0.10:
    lead.priority += 2
```

### 3. Context Snapshots

Agents periodically save complete context snapshots.

**Usage**:
- Save every 15 minutes
- Other agents can query latest snapshot
- Used for recovery after restart

### 4. LLM Context Injection

When agents use LLM, they include relevant context from other agents.

**Example**:
```python
# Build prompt with context from other agents
prompt = llm_context_manager.build_prompt_with_context(
    base_prompt="Generate message...",
    agent_name="outreach",
    context_types=["operational", "knowledge", "historical"]
)
# LLM now has: template performance, recent successes, current strategy
```

---

## Context Persistence

### Agent Startup Recovery

```python
def start(self):
    # 1. Load persistent state
    self.recover_state()
    # 2. Restore operational context
    self.restore_operational_context()
    # 3. Load shared knowledge
    self.load_shared_knowledge()
    # 4. Sync with other agents
    self.sync_with_other_agents()
```

### Periodic Saving

- Save context every 15 minutes
- Save on shutdown
- Update file cache (`data/cache/`)
- Update SQLite database (`data/state/agents.db`)
- Store in Google Sheets (optional, for backup)

---

## Best Practices

1. **Context Granularity**: Include only relevant, actionable context
2. **Freshness**: Operational (real-time), Knowledge (daily), Strategic (weekly)
3. **Privacy**: Never share PII, require permission for human interactions
4. **Versioning**: Track changes, enable rollback, audit trail

---

## Questions

**Q1**: Context size and LLM token limits?  
**Answer**: Use summarisation, compression, embeddings for semantic search

**Q2**: Context consistency across agents?  
**Answer**: Single source of truth (Google Sheets), SQLite-based locking, file-based events with ordering, optimistic locking

**Q3**: Context security?  
**Answer**: Encrypt at rest, secure API (TLS), access control, audit logging

---

## Future Enhancements

1. Vector database for semantic context search
2. Context compression and summarisation
3. ML models for context relevance scoring

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Architect**: _________________ Date: _______
