# Test Plan and Methodology - AI Sales Department

## Document Information
- **Document Type**: Test Plan and Methodology
- **Target Audience**: QA Engineer, Test Team
- **Version**: 2.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - Multi-Agent LinkedIn Outreach System

---

## Executive Summary

Comprehensive test plan for three AI agents: unit, integration, system, and acceptance testing. Focus on agent coordination, **Google Gemini API** integration, and end-to-end workflows. **10% error rate acceptable** for sentiment analysis.

---

## Test Objectives

**Primary**:
1. Verify functional requirements for each agent
2. Ensure reliable inter-agent communication
3. Validate LLM integration and quality
4. Test agent failure recovery
5. Verify rate limiting compliance

**Success Criteria**:
- >80% code coverage per agent
- 99%+ message delivery reliability
- Zero duplicate contacts
- 200+ leads/week processed successfully

---

## Test Scope

**In Scope**: All three agents, inter-agent communication, LLM integration, shared state, external APIs, end-to-end workflows

**Out of Scope**: Extreme load testing, security penetration, multi-language, A/B testing framework

---

## Key Test Cases

### Unit Tests

**TC-01**: Classification - Speaker (CTO, Founder → "Speaker")  
**TC-02**: Classification - Sponsor (CEO, VP → "Sponsor")  
**TC-03**: Message Generation - Template variable replacement  
**TC-04**: Rate Limiter - Daily limit enforcement  
**TC-05**: Rate Limiter - Minimum interval (5 minutes)

### Integration Tests

**TC-10**: Google Sheets - Read/Write operations  
**TC-11**: LinkedIn Sender - Send message via API  
**TC-12**: Email Service - Send daily report  
**TC-26**: Sales Manager - Lead allocation  
**TC-28**: Lead Finder - Profile analysis with LLM  
**TC-30**: Outreach - LLM message generation  
**TC-31**: Outreach - Response analysis with LLM (10% error rate acceptable)

### Multi-Agent Tests

**TC-32**: Inter-Agent Communication - Message queue reliability  
**TC-34**: Shared State - Concurrent updates  
**TC-35**: Agent Failure Recovery  
**TC-36**: End-to-End Multi-Agent Workflow

### System Tests

**TC-17**: End-to-End - Single lead workflow  
**TC-18**: End-to-End - Multiple leads  
**TC-19**: Daily Report Generation  
**TC-20**: Error Recovery - Partial failures

---

## Test Execution Plan

### Phase 1: Unit Testing (Week 1)
- Core functionality tests (TC-01 to TC-05)
- Target: 80%+ code coverage
- All tests must pass

### Phase 2: Agent Integration (Week 1-2)
- Agent-specific tests (TC-26, TC-28, TC-30, TC-31)
- External service integration (TC-10, TC-11, TC-12)
- Mock LLM initially, real API in staging

### Phase 3: Multi-Agent Integration (Week 2)
- Inter-agent communication (TC-32, TC-34)
- LLM integration (TC-28, TC-30, TC-31)
- Agent coordination

### Phase 4: System Testing (Week 2-3)
- End-to-end workflows (TC-17, TC-18, TC-36)
- Failure recovery (TC-35, TC-20)
- Reporting (TC-19)

### Phase 5: Acceptance Testing (Week 3)
- Business requirement validation
- Human team acceptance
- Performance validation
- Sign-off required

---

## Test Environment

### Prerequisites
- Python 3.10+, Test Google Sheet
- Test API credentials (Google Sheets, LinkedIn, **Google Gemini API**)
- Test SMTP server
- **Single LinkedIn test account** (no multi-account testing)
- **No external servers needed** - all storage is local (SQLite + files)

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# No Redis or external servers needed
mkdir -p data/{state,queue,cache,events,logs}
# Configure .env.test with test credentials
pytest tests/ -v --cov=src --cov-report=html
```

---

## Test Data

**Required**:
- 50+ test leads (various positions, classifications)
- Leads with missing data (error handling)
- Invalid LinkedIn URLs
- Mock LinkedIn profiles
- Sample responses (positive/negative/neutral)
- Historical performance data (2+ weeks)

**Maintenance**: Reset test data between runs, clear `data/queue/` and `data/cache/` directories, maintain separate test accounts

---

## Questions

**Q1**: LLM testing strategy - how to test non-deterministic responses?  
**Answer**: Use mock Gemini responses for unit tests, real API for integration. Validate structure and quality, not exact text. **10% error rate acceptable** for sentiment analysis.

**Q2**: Inter-agent communication testing - how to test message queue reliability?  
**Answer**: Use file-based queue (`data/queue/`) for integration tests. Test failure scenarios. Monitor message delivery rates (target: 99%+). Verify file operations and SQLite index consistency.

**Q3**: State management testing - how to test concurrent updates?  
**Answer**: Test with multiple concurrent agents. Verify optimistic locking and conflict resolution work correctly.

---

## Concerns

**C1**: LLM API costs for testing  
**Mitigation**: Google Gemini API is cost-effective. Use mocks for most unit tests, limit real API calls in integration tests.

**C2**: Test environment complexity (multi-agent system)  
**Mitigation**: No external servers needed. Simple setup - Google Sheets + SQLite + local files. Automate directory creation and cleanup.

---

## Document Approval

- **QA Lead**: _________________ Date: _______
- **Test Engineer**: _________________ Date: _______
