# Google Sheets Schema Specification

## Document Information
- **Document Type**: Data Schema Specification
- **Target Audience**: Developers, Data Analysts
- **Version**: 1.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - Google Sheets Database Schema

---

## Executive Summary

Detailed schema for Google Sheets used as primary database. Includes exact column names, data types, formats, and validation rules.

---

## Leads Sheet (Primary)

**Sheet Name**: `Leads`

**Purpose**: Store all lead data, classification, messages, and responses.

### Column Schema

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| **Lead ID** | Text | Yes | Unique identifier (UUID or sequential) | `lead_001` |
| **Name** | Text | Yes | Full name of the lead | `John Doe` |
| **Position** | Text | Yes | Job title/position | `CTO` |
| **Company** | Text | Yes | Company name | `Tech Corp` |
| **LinkedIn URL** | URL | Yes | LinkedIn profile URL | `https://linkedin.com/in/johndoe` |
| **Classification** | Text | No | Auto-classified: `Speaker`, `Sponsor`, `Other` | `Speaker` |
| **Quality Score** | Number | No | Score 1-10 (calculated) | `7.5` |
| **Contact Status** | Text | Yes | Status: `Not Contacted`, `Allocated`, `Message Sent`, `Responded`, `Closed` | `Not Contacted` |
| **Allocated To** | Text | No | Agent name if allocated | `Outreach` |
| **Allocated At** | DateTime | No | When lead was allocated | `2025-01-15 09:30:00` |
| **Message Sent** | Text | No | Message text sent to lead | `Hi John! We're organising...` |
| **Message Sent At** | DateTime | No | When message was sent | `2025-01-15 10:15:00` |
| **Response** | Text | No | Response text from lead | `Thanks, interested!` |
| **Response Received At** | DateTime | No | When response was received | `2025-01-15 14:30:00` |
| **Response Sentiment** | Text | No | LLM analysis: `positive`, `negative`, `neutral` | `positive` |
| **Response Intent** | Text | No | LLM analysis: `interested`, `not_interested`, `requesting_info` | `interested` |
| **Created At** | DateTime | Yes | When lead was added | `2025-01-15 08:00:00` |
| **Last Updated** | DateTime | Yes | Last modification timestamp | `2025-01-15 14:30:00` |
| **Notes** | Text | No | Human notes or agent self-review flags | `Unclear position - review needed` |

### Data Validation Rules

1. **LinkedIn URL**: Must be valid LinkedIn URL format
2. **Contact Status**: Must be one of: `Not Contacted`, `Allocated`, `Message Sent`, `Responded`, `Closed`
3. **Classification**: Must be one of: `Speaker`, `Sponsor`, `Other` (or empty)
4. **Quality Score**: Must be between 1.0 and 10.0 (or empty)
5. **Response Sentiment**: Must be one of: `positive`, `negative`, `neutral` (or empty)
6. **Response Intent**: Must be one of: `interested`, `not_interested`, `requesting_info` (or empty)

### Example Row

```
Lead ID: lead_001
Name: John Doe
Position: CTO
Company: Tech Corp
LinkedIn URL: https://linkedin.com/in/johndoe
Classification: Speaker
Quality Score: 7.5
Contact Status: Message Sent
Allocated To: Outreach
Allocated At: 2025-01-15 09:30:00
Message Sent: Hi John! We're organising a tech event on 2025-11-20. Given your experience at Tech Corp as CTO, we think you'd be perfect as a speaker. Interested in sharing your insights?
Message Sent At: 2025-01-15 10:15:00
Response: (empty)
Response Received At: (empty)
Response Sentiment: (empty)
Response Intent: (empty)
Created At: 2025-01-15 08:00:00
Last Updated: 2025-01-15 10:15:00
Notes: (empty)
```

---

## Agent Context Sheet (Optional)

**Sheet Name**: `Agent Context`

**Purpose**: Store agent context snapshots, decisions, and reasoning.

### Column Schema

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| **Timestamp** | DateTime | Yes | When context was saved | `2025-01-15 09:00:00` |
| **Agent** | Text | Yes | Agent name: `SalesManager`, `LeadFinder`, `Outreach` | `LeadFinder` |
| **Context Type** | Text | Yes | Type: `operational`, `historical`, `knowledge`, `strategic` | `operational` |
| **Context Data** | Text (JSON) | Yes | JSON string with context data | `{"leads_processed": 10}` |
| **LLM Reasoning** | Text | No | LLM reasoning/explanation | `Classified as Speaker because...` |
| **Related Lead ID** | Text | No | Related lead ID if applicable | `lead_001` |
| **Performance Impact** | Text | No | Impact on performance metrics | `Improved classification accuracy` |

---

## Google Sheets Setup Instructions

### 1. Create Spreadsheet

1. Create new Google Spreadsheet
2. Name it: `InG Sales Department - Leads Database`
3. Get Spreadsheet ID from URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 2. Create Leads Sheet

1. Rename first sheet to `Leads`
2. Add header row with all column names (see schema above)
3. Freeze first row
4. Format columns:
   - **Lead ID**: Text
   - **Name**: Text
   - **Position**: Text
   - **Company**: Text
   - **LinkedIn URL**: Hyperlink
   - **Classification**: Dropdown (Speaker, Sponsor, Other)
   - **Quality Score**: Number (1 decimal place)
   - **Contact Status**: Dropdown (Not Contacted, Allocated, Message Sent, Responded, Closed)
   - **Allocated To**: Text
   - **Allocated At**: Date time
   - **Message Sent**: Text
   - **Message Sent At**: Date time
   - **Response**: Text
   - **Response Received At**: Date time
   - **Response Sentiment**: Dropdown (positive, negative, neutral)
   - **Response Intent**: Dropdown (interested, not_interested, requesting_info)
   - **Created At**: Date time
   - **Last Updated**: Date time
   - **Notes**: Text

### 3. Create Agent Context Sheet (Optional)

1. Create new sheet named `Agent Context`
2. Add header row with column names
3. Format columns appropriately

### 4. Set Permissions

1. Share spreadsheet with service account email (from Google credentials)
2. Grant "Editor" permissions
3. Keep spreadsheet link for human team access

---

## API Access

**Library**: `gspread`

**Authentication**: Service account JSON credentials file

**Example Code**:
```python
import gspread
from google.oauth2.service_account import Credentials

# Authenticate
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('config/google-credentials.json', scopes=scope)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key(SPREADSHEET_ID)
leads_sheet = spreadsheet.worksheet('Leads')

# Read leads
leads = leads_sheet.get_all_records()

# Update lead
leads_sheet.update('G2', 'Speaker')  # Update Classification in row 2
```

---

## Data Import from Clay.com

1. Export leads from Clay.com to CSV
2. CSV columns should map to: Name, Position, Company, LinkedIn URL
3. Import CSV to Google Sheets (File → Import)
4. Add remaining columns (Lead ID, Contact Status, Created At, etc.)
5. Lead Finder Agent will process and fill Classification, Quality Score

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Data Analyst**: _________________ Date: _______

