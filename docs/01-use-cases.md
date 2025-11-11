# Use Cases for AI-Powered Sales Department

## Document Information
- **Document Type**: Use Cases Specification
- **Target Audience**: Business Analyst, Product Owner, Sales Management
- **Version**: 2.1 (Condensed)
- **Date**: January 2025
- **Project**: InG AI Sales Department - LinkedIn Outreach System

---

## Executive Summary

AI-powered sales department with three specialised agents: **Sales Manager Agent** (coordinates, allocates, monitors), **Lead Finder Agent** (discovers and qualifies leads), and **Outreach Agent** (sends messages, analyses responses). Human team focuses on deal closure.

**Key Metrics**: 200+ messages/week, 8-10% response rate, 10x volume increase.

---

## Business Context

### Current State
- Manual prospecting: 8-16 hours/week per person
- ~20 contacts/week manually
- Not scalable

### Desired State
- Fully automated prospecting and outreach
- 200+ personalised messages/week
- 15-20 responses/week (8-10% response rate)
- Human team focuses on closing deals

---

## Core Use Cases

### UC-01: Lead Finder - Discover and Classify Prospects
**Actor**: Lead Finder Agent

**Flow**: Search LinkedIn → Analyse profiles (LLM) → Classify (Speaker/Sponsor) → Calculate quality score → Add to database

**Key Rules**: 
- Quality threshold: 6.0+
- Daily limit: 100 leads
- Duplicate detection by LinkedIn URL

---

### UC-02: Sales Manager - Allocate Leads
**Actor**: Sales Manager Agent

**Flow**: Review uncontacted leads → Prioritise (quality, classification) → Allocate 30-50 leads/day → Publish allocation event

**Key Rules**:
- Prioritise quality score ≥ 7
- Balance Speakers/Sponsors (60/40)
- Respect daily limits

---

### UC-03: Outreach - Generate and Send Messages
**Actor**: Outreach Agent

**Flow**: Get allocated leads → Generate personalised messages (LLM) → Check rate limiter → Send via LinkedIn → Log actions

**Key Rules**:
- Max 300 characters
- Rate limit: 30-50/day, 5-15 min intervals
- Working hours: 9:00-17:00

---

### UC-04: Outreach - Monitor and Analyse Responses
**Actor**: Outreach Agent

**Flow**: Check responses (every 2h) → Analyse sentiment/intent (LLM) → Update lead status → Notify human team if positive

**Key Rules**:
- Analysis within 4 hours
- Positive responses → immediate human notification
- All responses logged

---

### UC-05: Sales Manager - Generate Daily Reports
**Actor**: Sales Manager Agent

**Flow**: Collect metrics from all agents → Calculate KPIs → Generate insights (LLM) → Send email report (9:15 AM)

**Report Includes**: Leads discovered, messages sent, responses, response rates, recommendations

---

### UC-06: Sales Manager - Optimise Strategy
**Actor**: Sales Manager Agent

**Flow**: Analyse performance (2+ weeks data) → Identify opportunities → Adjust templates/criteria → Monitor impact

**Key Rules**: Data-driven changes, human approval for significant changes, A/B testing recommended

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

## Questions

**Q1**: LinkedIn API access method? Official API vs third-party tools?  
**Q2**: Lead quality scoring algorithm - what factors and weights?  
**Q3**: Human oversight points - when should agents escalate?  
**Q4**: Multi-account strategy for increased capacity?  
**Q5**: LLM response analysis accuracy - acceptable false positive/negative rates?

---

## Concerns

**C1**: LinkedIn account suspension risk despite rate limiting  
**C2**: Agent coordination complexity - three agents must coordinate perfectly  
**C3**: Data quality depends on Lead Finder accuracy  
**C4**: LLM API dependency and costs  
**C5**: Message template effectiveness - initial templates may not work

---

## Improvement Suggestions

**I1**: Machine learning for lead scoring based on conversion data  
**I2**: Advanced response analysis with intent detection  
**I3**: Multi-channel outreach (email, Twitter/X)  
**I4**: Automated follow-up sequences (2-3 messages)  
**I5**: Real-time dashboard for monitoring  
**I6**: CRM integration (Salesforce, HubSpot)  
**I7**: Competitive intelligence integration  
**I8**: Predictive pipeline analytics

---

## Document Approval

- **Business Analyst**: _________________ Date: _______
- **Product Owner**: _________________ Date: _______
- **Sales Manager**: _________________ Date: _______
