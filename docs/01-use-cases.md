# Use Cases for AI-Powered Sales Department

## Document Information
- **Document Type**: Use Cases Specification
- **Target Audience**: Business Analyst, Product Owner, Sales Management
- **Version**: 2.2 (Updated with Stakeholder Feedback)
- **Date**: January 2025
- **Project**: InG AI Sales Department - LinkedIn Outreach System

---

## Executive Summary

AI-powered sales department with three specialised agents: **Sales Manager Agent** (coordinates, allocates, monitors), **Lead Finder Agent** (discovers and qualifies leads), and **Outreach Agent** (sends messages, analyses responses). Human team focuses on deal closure.

**Key Metrics**: 200+ messages/week, 8-10% response rate, 10x volume increase.

**LLM Provider**: Google Gemini Preview API (cost-effective, high quality)

---

## Business Context

### Current State
- Manual prospecting: 8-16 hours/week per person
- ~20 contacts/week manually
- Not scalable
- Working with lead lists from Clay.com or similar sources

### Desired State
- Fully automated prospecting and outreach
- 200+ personalised messages/week
- 15-20 responses/week (8-10% response rate)
- Human team focuses on closing deals
- Simple solution based on Google Sheets

---

## Core Use Cases

### UC-01: Lead Finder - Read and Classify Prospects
**Actor**: Lead Finder Agent

**Flow**: Read uncontacted leads from Google Sheets → Analyse profiles (LLM) → Classify (Speaker/Sponsor) → Calculate quality score → Update database

**Note**: Lead Finder **does not search LinkedIn**. Leads are already in Google Sheets (imported from Clay.com, LinkedIn Sales Navigator, Apollo.io, or manual entry). Agent processes existing leads.

**Lead Sources** (imported to Google Sheets):
- **Clay.com**: Export to CSV, import to Google Sheets (current source, Sprint 1)
  - **Future**: Automatic API synchronization (see Future Enhancements)
- **Google Sheets**: Manual entry or CSV import (simplest, recommended for Sprint 1)
- **LinkedIn Sales Navigator**: Export to CSV, import to Google Sheets
- **Apollo.io**: Export contacts to CSV
- **Lusha/Hunter.io**: Export to CSV
- **Any CSV-compatible source**: Export → Import to Google Sheets

**Classification Rules** (from requirements):
- **Speaker**: Founder, Co-founder, CTO, Engineer, Technical Lead, VP Engineering
- **Sponsor**: C-level executives (CEO, CTO, CFO, CMO), VP, Director, Head of Business Development
- **Priority**: If position matches both, classify as "Speaker"

**Key Rules**: 
- Quality threshold: 6.0+
- Daily limit: 100 leads
- Duplicate detection by LinkedIn URL
- Simple rule-based classification enhanced with LLM for edge cases

---

### UC-02: Sales Manager - Allocate Leads
**Actor**: Sales Manager Agent

**Flow**: Review uncontacted leads → Prioritise (quality, classification) → Allocate 30-50 leads/day → Publish allocation event

**Key Rules**:
- Prioritise quality score ≥ 7
- Balance Speakers/Sponsors (60/40)
- Respect daily limits
- **No escalation**: Agent only reports, doesn't escalate issues

**Daily Report Includes**:
- Standard metrics (leads, messages, responses)
- **Agent Self-Review**: "I didn't select X leads - please check if I was right" (for human review)
- Uncertain classifications flagged for human validation

---

### UC-03: Outreach - Generate and Send Messages
**Actor**: Outreach Agent

**Flow**: Get allocated leads → Check if user in contacts → If not: Get LinkedIn ID → Send invitation → Update status to "Invitation Sent" → Wait for acceptance → If accepted or already in contacts: Generate personalised messages (LLM) → Check rate limiter → Send via LinkedIn → Log actions

**Rate Limiting** (from requirements):
- 30-50 messages per day
- Evenly distributed across 8 hours (9:00-17:00)
- Pauses 5-15 minutes between sends (randomised)
- **Single LinkedIn account** (no multi-account strategy)

**Key Rules**:
- Messages follow Innovators Guild template format (includes signature)
- Working hours: 9:00-17:00

**Improved Message Templates** (initial versions):

**Speaker Template**:
"Hi [Name],

Thanks for connecting! I noticed your role at [Company] and your bio line about [short phrase from their bio]. You're clearly working on something interesting in the tech world.

I'm part of the Innovators Guild, and on [Date] we're bringing together engineers and scientists tackling tough problems in [Prospect's industry]. I don't know much about your work yet, but if you're open to it, I'd love to hear your story, and see if speaking at this event might be a good fit.

No pressure at all. If you're interested, let me know and we can set up a quick chat. Either way, I'm looking forward to learning more about what you do."

**Sponsor Template**:
"Hi [Name],

Thanks for connecting! I've noticed [Company]'s focus on [one thing they're known for], it looks impressive and definitely relevant to some of the challenges we tackle with the Innovators Guild.

We organise events that gather ambitious leaders and emerging companies who are passionate about commercialising deep-tech and innovation. Since you clearly have insight into this space, I wondered if it might make sense to chat about ways [Company] could get involved, whether through sponsorship or collaboration.

No pressure at all, but if you're curious, I'd love to schedule a quick call to swap ideas and see if there's a fit."

---

### UC-04: Outreach - Monitor and Analyse Responses
**Actor**: Outreach Agent

**Flow**: Check responses (every 2h) → Analyse sentiment/intent (LLM) → Update lead status → Notify human team if positive

**Key Rules**:
- Analysis within 4 hours
- Positive responses → immediate human notification
- All responses logged
- **Acceptable error rate**: 10% false positive/negative in sentiment analysis

---

### UC-05: Sales Manager - Generate Daily Reports
**Actor**: Sales Manager Agent

**Flow**: Collect metrics from all agents → Calculate KPIs → Generate insights (LLM) → Send email report (9:15 AM)

**Report Includes**: 
- Leads discovered, messages sent, responses, response rates
- **Agent Self-Review Section**: Uncertain decisions flagged for human review
  - Example: "I didn't select 3 leads (IDs: 123, 124, 125) - please check if classification was correct"
  - Example: "2 leads had unclear positions - marked for review"
- Recommendations

---

### UC-06: Sales Manager - Optimise Strategy
**Actor**: Sales Manager Agent

**Flow**: Analyse performance (2+ weeks data) → Identify opportunities → Adjust templates/criteria → Monitor impact

**Key Rules**: Data-driven changes, human approval for significant changes

---

### UC-07: Human Team - Close Deals
**Actor**: Human Sales Representative

**Flow**: Receive interested lead notification → Review context → Contact lead → Update status → Log interactions

**Statuses**: In Discussion → Meeting Scheduled → Proposal Sent → Closed Won/Lost

---

## Success Metrics

**Lead Finder**: 50-100 leads/day, quality score ≥ 7.0, 85%+ classification accuracy

**Outreach**: 200+ messages/week, 8-10% response rate, 60%+ positive responses

**Sales Manager**: 5%+ conversion rate, <24h to first response

**Overall**: 10-15 qualified opportunities/week, 20%+ closure rate, 16+ hours saved/week

---

## Resolved Questions

**Q1**: Lead source alternatives to Clay.com
- **Answer**: Google Sheets with CSV import (simplest), LinkedIn Sales Navigator export, Apollo.io, Lusha/Hunter.io
- **Recommendation**: Start with Google Sheets + CSV import for simplicity

**Q2**: Lead quality scoring algorithm
- **Answer**: Based on position match, company relevance, profile completeness
- **Recommendation**: Simple scoring (1-10) based on position keywords, company size indicators, profile completeness percentage

**Q3**: Human oversight points
- **Answer**: Agents don't escalate, only report. Daily report includes "Agent Self-Review" section with uncertain decisions flagged for human validation

**Q4**: Multi-account strategy
- **Answer**: Single LinkedIn account only (for Sprint 1)
- **Future Enhancement**: Multi-account support with priority-based routing (see Future Enhancements section)

**Q5**: LLM response analysis accuracy
- **Answer**: 10% error rate acceptable (false positive/negative)

---

## Resolved Concerns

**C1**: LinkedIn account suspension risk
- **Mitigation**: Strict rate limiting (30-50/day, 5-15 min intervals, 8-hour window) as per requirements

**C2**: Agent coordination complexity
- **Solution**: Simplest approach based on Google Sheets as single source of truth, **file-based message queue** (no servers needed)

**C3**: Data quality and error reduction
- **Solution**: 
  - Enhanced data validation rules
  - LLM-assisted classification for edge cases
  - Quality score based on multiple factors
  - Agent flags uncertain cases in daily report for human review
  - Pattern analysis: track which lead sources/characteristics convert best

**C4**: LLM API dependency
- **Solution**: Google Gemini Preview API (cost-effective, high quality)
- **Fallback**: Rule-based logic if API unavailable

**C5**: Message template effectiveness
- **Solution**: Improved initial templates provided (see UC-03)
- **Future**: Regular template review based on response rates

---

## Improvement Suggestions

**I1**: Machine learning for lead scoring
- **Status**: Approved if solution is simple
- **Approach**: Simple scoring algorithm based on conversion data, can be enhanced later

**I2-I8**: Not for this stage
- **Status**: Deferred to future sprints

---

## Future Enhancements (Post-Sprint 1)

### FE-01: Clay.com API Integration

**Current State**: Clay.com leads are exported to CSV and manually imported to Google Sheets.

**Future Enhancement**: Automatic synchronization from Clay.com API to Google Sheets.

**Approach**:
- Lead Finder Agent continues to read from Google Sheets (no change to agent logic)
- Separate synchronization process/script automatically syncs Clay.com → Google Sheets
- Optional: Direct Clay.com API integration in Lead Finder Agent (alternative approach)

**Benefits**: 
- Eliminates manual CSV export/import step
- Real-time lead updates
- Reduced human intervention

**Status**: Optional enhancement, not required for Sprint 1

---

### FE-02: Multi-Account LinkedIn Strategy

**Current State**: Single LinkedIn account with 30-50 messages/day limit.

**Future Enhancement**: Support for multiple LinkedIn accounts with priority-based routing.

**Strategy**:
- **Priority Account + Reserve Accounts**: Primary account used first, switches to reserve accounts when daily limit reached
- **Independent Rate Limits**: Each account has its own rate limiter (e.g., 45 messages/day per account)
- **Account Configuration**: Each account has its own API key and account_id
  - Account 1 (Primary): `DRIPIFY_API_KEY_1`, `DRIPIFY_ACCOUNT_ID_1`
  - Account 2 (Reserve): `DRIPIFY_API_KEY_2`, `DRIPIFY_ACCOUNT_ID_2`
  - Account 3 (Reserve): `DRIPIFY_API_KEY_3`, `DRIPIFY_ACCOUNT_ID_3`
  - Account 4 (Reserve): `DRIPIFY_API_KEY_4`, `DRIPIFY_ACCOUNT_ID_4`

**Implementation Details**:
- Outreach Agent maintains account priority list
- When primary account reaches daily limit, automatically switches to next available account
- Each account tracks its own daily message count independently
- Total capacity: 4 accounts × 45 messages = 180 messages/day (if all accounts used)

**Configuration Example** (future):
```yaml
outreach:
  linkedin_accounts: 4
  account_priority: ["account_1", "account_2", "account_3", "account_4"]
  rate_limit_daily_per_account: 45
```

**Status**: Planned for implementation after successful Sprint 1 testing

---

## Document Approval

- **Business Analyst**: _________________ Date: _______
- **Product Owner**: _________________ Date: _______
- **Sales Manager**: _________________ Date: _______
