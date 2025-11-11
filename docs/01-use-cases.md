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
- **Clay.com**: Export to CSV, import to Google Sheets (current source)
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

**Flow**: Get allocated leads → Generate personalised messages (LLM) → Check rate limiter → Send via LinkedIn → Log actions

**Rate Limiting** (from requirements):
- 30-50 messages per day
- Evenly distributed across 8 hours (9:00-17:00)
- Pauses 5-15 minutes between sends (randomised)
- **Single LinkedIn account** (no multi-account strategy)

**Key Rules**:
- Max 300 characters
- Working hours: 9:00-17:00

**Improved Message Templates** (initial versions):

**Speaker Template**:
"Hi [Name]! We're organising a tech event on [Date]. Given your experience at [Company] as [Position], we think you'd be perfect as a speaker. Interested in sharing your insights?"

**Sponsor Template**:
"Hello [Name]! We're hosting a tech event on [Date] and looking for corporate sponsors. [Company] would be a great fit. Would you like to learn more about sponsorship opportunities?"

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
- **Answer**: Single LinkedIn account only

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

## Document Approval

- **Business Analyst**: _________________ Date: _______
- **Product Owner**: _________________ Date: _______
- **Sales Manager**: _________________ Date: _______
