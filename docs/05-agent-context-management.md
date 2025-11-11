# Agent Context Management and Sharing

## Document Information
- **Document Type**: Technical Architecture - Context Management
- **Target Audience**: Developers, Architects, Technical Team
- **Version**: 1.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent System

---

## Executive Summary

This document explains how AI agents in the sales department preserve their working context (memory, decision history, learning) and share this context with each other. The system uses a multi-layered approach combining persistent storage, event-driven communication, and shared knowledge bases to enable agents to maintain continuity and learn from each other's experiences.

---

## Context Types

### 1. Operational Context (Short-term)
**What it is**: Current state of work in progress
- Which leads are being processed
- Current allocation status
- Active tasks and their progress
- Rate limiter state
- Recent decisions and their rationale

**Storage**: 
- **In-Memory**: Agent's runtime state
- **Redis Cache**: Fast access for coordination
- **Google Sheets**: Persistent backup

**Lifetime**: Hours to days

---

### 2. Historical Context (Long-term)
**What it is**: Complete history of actions and outcomes
- All leads processed
- All messages sent and responses received
- Performance metrics over time
- Success/failure patterns
- Learning from past decisions

**Storage**:
- **Google Sheets**: Primary persistent storage
- **Log Files**: Detailed audit trail
- **Analytics Database**: Aggregated metrics (future)

**Lifetime**: Permanent (for analysis and learning)

---

### 3. Knowledge Context (Learning)
**What it is**: Accumulated knowledge and patterns
- What message templates work best
- Which lead characteristics convert
- Optimal timing for outreach
- Classification patterns
- Quality scoring improvements

**Storage**:
- **Configuration Files**: Updated templates and rules
- **ML Models**: Trained models (future)
- **Knowledge Base**: Documented patterns and insights

**Lifetime**: Evolves continuously

---

### 4. Strategic Context (Decision-making)
**What it is**: High-level strategy and reasoning
- Why certain decisions were made
- Performance analysis insights
- Optimisation recommendations
- Strategic adjustments

**Storage**:
- **Sales Manager Agent**: Maintains strategic context
- **Reports**: Documented in daily reports
- **Decision Log**: LLM reasoning captured

**Lifetime**: Weeks to months

---

## Context Storage Architecture

### Layer 1: Google Sheets (Primary Persistent Storage)

**Purpose**: Single source of truth for all lead data and operational state

**What's Stored**:

```
┌─────────────────────────────────────────────────────────┐
│                    Google Sheets                        │
│                                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  Leads Sheet (Main Database)                  │    │
│  │  - Lead information                           │    │
│  │  - Contact status                             │    │
│  │  - Messages sent                              │    │
│  │  - Responses received                         │    │
│  │  - Classification and quality scores          │    │
│  └──────────────────────────────────────────────┘    │
│                                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  Agent Context Sheet (NEW)                    │    │
│  │  - Agent decisions log                        │    │
│  │  - LLM reasoning snapshots                    │    │
│  │  - Performance context                         │    │
│  │  - Learning insights                          │    │
│  └──────────────────────────────────────────────┘    │
│                                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  Analytics Sheet                              │    │
│  │  - Daily metrics                              │    │
│  │  - Performance trends                         │    │
│  │  - Conversion data                             │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Agent Context Sheet Schema**:

| Column | Type | Description |
|--------|------|-------------|
| Timestamp | DateTime | When context was saved |
| Agent | String | Which agent (sales_manager/lead_finder/outreach) |
| Context Type | String | operational/historical/knowledge/strategic |
| Context Key | String | Unique identifier for this context |
| Context Data | JSON | Actual context data (JSON string) |
| Related Lead ID | String | If context relates to specific lead |
| LLM Reasoning | String | LLM's reasoning for decision (if applicable) |
| Performance Impact | String | How this context affected outcomes |

**Example Context Entry**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "agent": "sales_manager",
  "context_type": "strategic",
  "context_key": "allocation_strategy_2025-01-15",
  "context_data": {
    "decision": "Prioritise high-quality speakers",
    "reasoning": "Analysis shows 15% higher response rate for quality score > 8",
    "leads_allocated": ["123", "124", "125"],
    "expected_outcome": "Higher conversion rate"
  },
  "llm_reasoning": "Based on historical data, leads with quality scores above 8.0 have shown 15% higher response rates. Prioritising these leads should improve overall conversion.",
  "performance_impact": "TBD - will be updated after results"
}
```

---

### Layer 2: Redis Cache (Fast Access & Coordination)

**Purpose**: Fast, shared memory for real-time coordination

**What's Stored**:

```python
# Agent Runtime State
redis.set(f"agent:{agent_name}:state", {
    "current_task": "processing_leads",
    "leads_in_progress": ["123", "124"],
    "last_activity": "2025-01-15T10:30:00Z",
    "status": "active"
}, ex=3600)  # Expires in 1 hour

# Shared Knowledge Cache
redis.set("knowledge:best_message_templates", {
    "speaker_template_v2": {
        "response_rate": 0.12,
        "usage_count": 45,
        "last_updated": "2025-01-14"
    }
}, ex=86400)  # Expires in 24 hours

# Coordination Locks
redis.set(f"lock:lead:123", "outreach_agent", ex=300)  # 5 min lock

# Recent Events (for context sharing)
redis.lpush("events:recent", json.dumps({
    "type": "lead_discovered",
    "agent": "lead_finder",
    "data": {...},
    "timestamp": "2025-01-15T10:30:00Z"
}), maxlen=100)  # Keep last 100 events
```

**Key Patterns**:
- `agent:{agent_name}:state` - Current agent state
- `knowledge:{topic}` - Shared knowledge cache
- `lock:{resource}` - Coordination locks
- `events:recent` - Recent events for context
- `context:{agent_name}:{context_key}` - Agent-specific context

---

### Layer 3: Log Files (Audit Trail)

**Purpose**: Detailed, searchable history of all agent activities

**What's Stored**:
- All agent decisions with full context
- LLM prompts and responses
- Error conditions and recovery
- Performance metrics
- Inter-agent communications

**Format**: Structured JSON logs

**Example Log Entry**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "agent": "outreach",
  "level": "INFO",
  "action": "generate_message",
  "context": {
    "lead_id": "123",
    "lead_name": "John Doe",
    "classification": "Speaker",
    "quality_score": 8.5,
    "previous_messages": [],
    "llm_prompt": "Generate personalised message...",
    "llm_response": "Hi John! We're organising...",
    "message_generated": "Hi John! We're organising a tech event..."
  },
  "outcome": "success"
}
```

---

## Context Sharing Mechanisms

### Mechanism 1: Event-Driven Context Sharing

**How it works**: Agents publish context-rich events that other agents can consume

**Flow**:

```
┌─────────────────┐
│ Lead Finder     │
│ Agent           │
└────────┬────────┘
         │
         │ Publishes event with context
         │
         ▼
┌─────────────────────────────────────┐
│  Event: lead_discovered              │
│  {                                   │
│    "lead_id": "123",                 │
│    "context": {                       │
│      "profile_analysis": "...",      │
│      "classification_reasoning": "...",│
│      "quality_score_factors": {...}  │
│    }                                 │
│  }                                   │
└────────┬─────────────────────────────┘
         │
         │ Redis Pub/Sub
         │
         ▼
┌─────────────────┐
│ Sales Manager   │
│ Agent           │
│                 │
│ Receives event  │
│ + context       │
│                 │
│ Uses context to │
│ make decision   │
└─────────────────┘
```

**Implementation**:

```python
# Lead Finder Agent publishes context-rich event
def publish_lead_discovered(self, lead: Lead, analysis_context: Dict):
    event = {
        "type": "lead_discovered",
        "agent": "lead_finder",
        "data": {
            "lead_id": lead.id,
            "lead_data": lead.to_dict()
        },
        "context": {
            # Share analysis context
            "profile_analysis": analysis_context["profile_summary"],
            "classification_reasoning": analysis_context["why_speaker"],
            "quality_score_breakdown": analysis_context["score_factors"],
            "llm_insights": analysis_context["llm_insights"]
        },
        "timestamp": datetime.now().isoformat()
    }
    self.message_queue.publish(event)

# Sales Manager Agent receives and uses context
def handle_lead_discovered(self, event: Dict):
    lead_data = event["data"]
    context = event.get("context", {})
    
    # Use shared context for better decision-making
    if context.get("quality_score_breakdown"):
        # Adjust allocation priority based on quality factors
        priority = self.calculate_priority(lead_data, context)
    
    # Store context for future reference
    self.save_context("lead_discovered", context, lead_data["lead_id"])
```

---

### Mechanism 2: Shared Knowledge Base

**How it works**: Agents read and write to a shared knowledge base that accumulates learnings

**Knowledge Base Structure**:

```python
class SharedKnowledgeBase:
    """Shared knowledge that all agents can access and update."""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.redis_cache = RedisClient()
    
    def get_message_template_performance(self, template_id: str) -> Dict:
        """Get performance metrics for a message template."""
        # Check cache first
        cached = self.redis_cache.get(f"knowledge:template:{template_id}")
        if cached:
            return json.loads(cached)
        
        # Query from persistent storage
        performance = self.state_manager.query_analytics({
            "metric": "message_template_performance",
            "template_id": template_id
        })
        
        # Cache for future use
        self.redis_cache.set(
            f"knowledge:template:{template_id}",
            json.dumps(performance),
            ex=3600
        )
        
        return performance
    
    def update_learning(self, topic: str, learning: Dict):
        """Update shared knowledge with new learning."""
        # Update persistent storage
        self.state_manager.update_knowledge_base(topic, learning)
        
        # Invalidate cache
        self.redis_cache.delete(f"knowledge:{topic}")
        
        # Notify other agents
        self.publish_knowledge_update(topic, learning)
```

**Example Usage**:

```python
# Outreach Agent learns which messages work
def learn_from_response(self, lead: Lead, response: Response):
    if response.sentiment == "positive":
        # Update knowledge: this message template worked
        template_id = lead.message_template_used
        self.knowledge_base.update_learning(
            f"template:{template_id}",
            {
                "success_count": +1,
                "response_rate": self.calculate_new_rate(template_id),
                "last_success": datetime.now().isoformat()
            }
        )

# Sales Manager Agent uses this knowledge
def allocate_leads(self, leads: List[Lead]):
    for lead in leads:
        # Check which templates work best for this classification
        template_performance = self.knowledge_base.get_message_template_performance(
            f"{lead.classification}_template"
        )
        
        # Prioritise leads where we have proven templates
        if template_performance["response_rate"] > 0.10:
            lead.priority += 2
```

---

### Mechanism 3: Context Snapshots

**How it works**: Agents periodically save complete context snapshots that other agents can query

**Snapshot Structure**:

```python
class ContextSnapshot:
    """Complete context snapshot at a point in time."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.timestamp = datetime.now()
        self.context = {}
    
    def capture(self):
        """Capture current agent context."""
        self.context = {
            "operational": {
                "current_tasks": self.get_current_tasks(),
                "leads_in_progress": self.get_leads_in_progress(),
                "rate_limiter_state": self.rate_limiter.get_state()
            },
            "strategic": {
                "current_strategy": self.get_current_strategy(),
                "recent_decisions": self.get_recent_decisions(),
                "performance_insights": self.get_performance_insights()
            },
            "knowledge": {
                "learned_patterns": self.get_learned_patterns(),
                "best_practices": self.get_best_practices()
            }
        }
    
    def save(self, state_manager):
        """Save snapshot to persistent storage."""
        state_manager.save_context_snapshot(
            agent_name=self.agent_name,
            timestamp=self.timestamp,
            context=self.context
        )
    
    def load(self, state_manager, timestamp: Optional[datetime] = None):
        """Load snapshot from storage."""
        snapshot = state_manager.load_context_snapshot(
            agent_name=self.agent_name,
            timestamp=timestamp
        )
        self.context = snapshot["context"]
        self.timestamp = snapshot["timestamp"]
```

**Usage**:

```python
# Sales Manager Agent saves context snapshot
def save_context_snapshot(self):
    snapshot = ContextSnapshot("sales_manager")
    snapshot.capture()
    snapshot.save(self.state_manager)
    
    # Also cache recent snapshot in Redis
    self.redis_cache.set(
        "context:snapshot:sales_manager:latest",
        json.dumps(snapshot.context),
        ex=3600
    )

# Outreach Agent can query Sales Manager's context
def get_sales_manager_context(self):
    # Get latest snapshot
    snapshot_data = self.redis_cache.get(
        "context:snapshot:sales_manager:latest"
    )
    
    if snapshot_data:
        return json.loads(snapshot_data)
    
    # Fallback to persistent storage
    return self.state_manager.load_latest_context_snapshot("sales_manager")
```

---

### Mechanism 4: LLM Context Window Management

**How it works**: When agents use LLM, they include relevant context from other agents in the prompt

**Context Injection**:

```python
class LLMContextManager:
    """Manages context for LLM prompts."""
    
    def __init__(self, state_manager, knowledge_base):
        self.state_manager = state_manager
        self.knowledge_base = knowledge_base
    
    def build_prompt_with_context(
        self,
        base_prompt: str,
        agent_name: str,
        context_types: List[str] = ["operational", "knowledge"]
    ) -> str:
        """Build LLM prompt with relevant context."""
        
        context_parts = []
        
        # Add operational context
        if "operational" in context_types:
            operational_context = self.get_operational_context(agent_name)
            context_parts.append(f"Current operational context: {operational_context}")
        
        # Add knowledge context
        if "knowledge" in context_types:
            relevant_knowledge = self.get_relevant_knowledge(base_prompt)
            context_parts.append(f"Relevant knowledge: {relevant_knowledge}")
        
        # Add historical context
        if "historical" in context_types:
            historical_context = self.get_historical_context(agent_name)
            context_parts.append(f"Historical patterns: {historical_context}")
        
        # Add other agents' context
        other_agents_context = self.get_other_agents_context(agent_name)
        if other_agents_context:
            context_parts.append(f"Other agents' insights: {other_agents_context}")
        
        # Combine
        full_prompt = f"""
{base_prompt}

CONTEXT:
{chr(10).join(context_parts)}
"""
        return full_prompt
    
    def get_other_agents_context(self, current_agent: str) -> str:
        """Get relevant context from other agents."""
        context_summary = []
        
        # Get Sales Manager's strategic context
        if current_agent != "sales_manager":
            sm_context = self.state_manager.get_agent_context(
                "sales_manager",
                context_type="strategic"
            )
            if sm_context:
                context_summary.append(
                    f"Sales Manager's current strategy: {sm_context.get('current_strategy')}"
                )
        
        # Get Lead Finder's recent discoveries
        if current_agent != "lead_finder":
            lf_context = self.state_manager.get_agent_context(
                "lead_finder",
                context_type="operational"
            )
            if lf_context:
                context_summary.append(
                    f"Recent lead discoveries: {lf_context.get('recent_discoveries')}"
                )
        
        # Get Outreach Agent's response patterns
        if current_agent != "outreach":
            oa_context = self.state_manager.get_agent_context(
                "outreach",
                context_type="knowledge"
            )
            if oa_context:
                context_summary.append(
                    f"Message performance insights: {oa_context.get('message_insights')}"
                )
        
        return "\n".join(context_summary) if context_summary else ""
```

**Example Usage**:

```python
# Outreach Agent generates message with full context
def generate_message(self, lead: Lead) -> str:
    base_prompt = f"Generate personalised message for {lead.name}..."
    
    # Include context from other agents
    full_prompt = self.llm_context_manager.build_prompt_with_context(
        base_prompt=base_prompt,
        agent_name="outreach",
        context_types=["operational", "knowledge", "historical"]
    )
    
    # LLM now has context about:
    # - What templates work best (from knowledge base)
    # - Recent successful messages (from Outreach Agent's history)
    # - Current strategy (from Sales Manager)
    # - Lead quality factors (from Lead Finder)
    
    message = self.llm_client.generate(full_prompt)
    return message
```

---

## Context Persistence and Recovery

### Agent Startup and Context Recovery

**When agent starts**:

```python
class BaseAgent:
    def start(self):
        """Start agent and recover context."""
        # 1. Load persistent state
        self.recover_state()
        
        # 2. Restore operational context
        self.restore_operational_context()
        
        # 3. Load shared knowledge
        self.load_shared_knowledge()
        
        # 4. Sync with other agents
        self.sync_with_other_agents()
        
        # 5. Start main loop
        self.main_loop()
    
    def recover_state(self):
        """Recover agent state from persistent storage."""
        # Load from Google Sheets
        last_state = self.state_manager.get_agent_last_state(self.agent_name)
        
        if last_state:
            # Restore rate limiter state
            if "rate_limiter" in last_state:
                self.rate_limiter.restore_state(last_state["rate_limiter"])
            
            # Restore in-progress tasks
            if "in_progress_tasks" in last_state:
                self.resume_tasks(last_state["in_progress_tasks"])
    
    def restore_operational_context(self):
        """Restore operational context from cache or storage."""
        # Try Redis cache first
        cached_context = self.redis_cache.get(
            f"agent:{self.agent_name}:context:operational"
        )
        
        if cached_context:
            self.operational_context = json.loads(cached_context)
        else:
            # Load from persistent storage
            self.operational_context = self.state_manager.get_agent_context(
                self.agent_name,
                context_type="operational"
            )
    
    def load_shared_knowledge(self):
        """Load shared knowledge base."""
        # Load from knowledge base
        self.shared_knowledge = self.knowledge_base.get_all_knowledge()
        
        # Cache in Redis
        self.redis_cache.set(
            "knowledge:shared",
            json.dumps(self.shared_knowledge),
            ex=3600
        )
    
    def sync_with_other_agents(self):
        """Sync context with other agents."""
        # Get latest context snapshots from other agents
        for other_agent in ["sales_manager", "lead_finder", "outreach"]:
            if other_agent != self.agent_name:
                other_context = self.get_agent_context_snapshot(other_agent)
                self.other_agents_context[other_agent] = other_context
```

---

### Periodic Context Saving

**Automatic context persistence**:

```python
class ContextPersistenceManager:
    """Manages periodic saving of agent context."""
    
    def __init__(self, agent, save_interval_minutes=15):
        self.agent = agent
        self.save_interval = save_interval_minutes
        self.scheduler = APScheduler()
    
    def start(self):
        """Start periodic context saving."""
        # Save context every 15 minutes
        self.scheduler.add_job(
            self.save_context,
            'interval',
            minutes=self.save_interval
        )
        
        # Save context on shutdown
        atexit.register(self.save_context)
        
        self.scheduler.start()
    
    def save_context(self):
        """Save current agent context."""
        context = {
            "operational": self.agent.get_operational_context(),
            "strategic": self.agent.get_strategic_context(),
            "knowledge": self.agent.get_knowledge_context(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to persistent storage
        self.agent.state_manager.save_agent_context(
            agent_name=self.agent.agent_name,
            context=context
        )
        
        # Update Redis cache
        self.agent.redis_cache.set(
            f"agent:{self.agent.agent_name}:context:latest",
            json.dumps(context),
            ex=3600
        )
```

---

## Context Sharing Examples

### Example 1: Lead Finder → Sales Manager → Outreach

**Scenario**: Lead Finder discovers a high-quality lead and shares context

```python
# 1. Lead Finder Agent discovers lead
lead = self.analyse_profile(profile_data)
context = {
    "profile_analysis": "Strong technical background, 10+ years experience",
    "classification_reasoning": "CTO position, technical expertise, speaking history",
    "quality_score_breakdown": {
        "position_score": 9.0,
        "company_score": 8.5,
        "profile_completeness": 9.5,
        "engagement_indicators": 8.0
    },
    "llm_insights": "Highly qualified speaker candidate with proven track record"
}

# Publish with full context
self.publish_event("lead_discovered", {
    "lead": lead.to_dict(),
    "context": context
})

# 2. Sales Manager Agent receives and uses context
def handle_lead_discovered(self, event):
    lead = event["data"]["lead"]
    context = event["data"]["context"]
    
    # Use quality score breakdown for prioritisation
    if context["quality_score_breakdown"]["position_score"] > 8.5:
        lead.priority = "high"
    
    # Store context for future reference
    self.save_context("lead_analysis", context, lead["id"])
    
    # Allocate with context
    self.allocate_lead(lead, context)

# 3. Outreach Agent receives allocation with context
def handle_lead_allocation(self, event):
    lead = event["data"]["lead"]
    context = event["data"].get("context", {})
    
    # Use context for better message generation
    if context.get("llm_insights"):
        # Include insights in LLM prompt
        message = self.generate_message_with_context(lead, context)
    else:
        message = self.generate_message(lead)
```

---

### Example 2: Outreach → Sales Manager (Learning)

**Scenario**: Outreach Agent learns which messages work and shares knowledge

```python
# 1. Outreach Agent analyses response
response_analysis = self.analyse_response(response_text)

if response_analysis.sentiment == "positive":
    # Update knowledge
    template_id = lead.message_template_used
    learning = {
        "template_id": template_id,
        "success": True,
        "response_rate_improvement": 0.02,
        "context": {
            "lead_classification": lead.classification,
            "lead_quality_score": lead.quality_score,
            "message_sentiment": "positive"
        }
    }
    
    # Update shared knowledge base
    self.knowledge_base.update_learning(
        f"template:{template_id}",
        learning
    )
    
    # Publish learning event
    self.publish_event("learning_update", {
        "type": "message_template_success",
        "learning": learning
    })

# 2. Sales Manager Agent receives learning
def handle_learning_update(self, event):
    learning = event["data"]["learning"]
    
    # Update allocation strategy based on learning
    if learning["success"]:
        # Prioritise similar leads for this template
        self.update_allocation_strategy(
            template_id=learning["template_id"],
            priority_boost=1.5
        )
    
    # Store in strategic context
    self.save_context("learning", learning)
```

---

## Best Practices

### 1. Context Granularity
- **Too much context**: Overwhelms LLM, increases costs, slows processing
- **Too little context**: Poor decisions, missed opportunities
- **Optimal**: Include only relevant, actionable context

### 2. Context Freshness
- **Operational context**: Update in real-time (Redis cache)
- **Knowledge context**: Update daily or on significant events
- **Strategic context**: Update weekly or when strategy changes

### 3. Context Privacy
- **Sensitive data**: Never share PII in context
- **Internal reasoning**: Can be shared between agents
- **Human interactions**: Require explicit sharing permission

### 4. Context Versioning
- **Version context snapshots**: Track changes over time
- **Rollback capability**: Can revert to previous context if needed
- **Audit trail**: Log all context changes

---

## Questions and Considerations

### Q1: Context Size and LLM Token Limits
**Question**: How do we manage context size when sharing with LLM?

**Answer**: 
- Use context summarisation for large histories
- Implement context compression (keep only key insights)
- Use embeddings for semantic search of relevant context
- Implement context window management (sliding window)

---

### Q2: Context Consistency
**Question**: How do we ensure all agents see consistent context?

**Answer**:
- Single source of truth (Google Sheets)
- Event ordering guarantees (message queue)
- Optimistic locking for updates
- Conflict resolution strategies

---

### Q3: Context Security
**Question**: How do we protect sensitive context data?

**Answer**:
- Encrypt context at rest
- Secure API communications (TLS)
- Access control per agent
- Audit logging for context access

---

## Future Enhancements

### 1. Vector Database for Semantic Context Search
- Store context as embeddings
- Semantic search for relevant context
- Better context retrieval

### 2. Context Compression and Summarisation
- Automatically summarise old context
- Keep only essential information
- Reduce storage and LLM costs

### 3. Context Learning and Adaptation
- ML models learn from context patterns
- Automatic context relevance scoring
- Predictive context loading

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Architect**: _________________ Date: _______
- **Security Review**: _________________ Date: _______

