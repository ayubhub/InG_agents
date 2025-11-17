# Setup Guide - Account Configuration for Testing

## Document Information
- **Document Type**: Setup and Configuration Guide
- **Target Audience**: Developers, DevOps, Testers
- **Version**: 1.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - Account Setup Instructions

---

## Executive Summary

This guide provides step-by-step instructions for setting up all required accounts and API keys needed to test the InG AI Sales Department application. Follow this guide before running the application for the first time.

---

## Quick Start Checklist

Minimum required accounts for testing:

- [ ] Google Gemini API key
- [ ] Google Sheets API credentials (Service Account JSON)
- [ ] Google Spreadsheet created and shared with Service Account
- [ ] LinkedIn automation service account (**Gojiberry recommended** - Dripify does NOT support API for sending messages)
- [ ] SMTP email credentials (for daily reports)

**Estimated Setup Time**: 30-60 minutes

---

## 1. Google Gemini API

### Where to Get

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the generated API key

### Where to Configure

**File**: `.env` (create from `config/env.example.txt`)

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### Verification

```bash
# Test API key (optional)
python3 -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
```

### Notes

- Free tier: 15 requests per minute
- Paid tier: Higher limits (check current documentation)
- API key is required for all LLM operations

---

## 2. Google Sheets API

### Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Note the project name/ID

### Step 2: Enable Google Sheets API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click "Enable"

### Step 3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - **Service account name**: `ing-sales-department` (or your choice)
   - **Service account ID**: Auto-generated
   - **Description**: "Service account for InG Sales Department"
4. Click "Create and Continue"
5. Skip "Grant access" (optional)
6. Click "Done"

### Step 4: Create and Download JSON Key

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create"
6. JSON file will download automatically

### Step 5: Save Credentials File

1. Move downloaded JSON file to: `config/google-credentials.json`
2. **Important**: Add `config/google-credentials.json` to `.gitignore` (already included)

### Step 6: Create Google Spreadsheet

1. Go to: https://sheets.google.com/
2. Create a new spreadsheet
3. Name it: `InG Sales Department - Leads Database`
4. Get Spreadsheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
   ```
   Example: If URL is `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit`, then ID is `1a2b3c4d5e6f7g8h9i0j`

### Step 7: Share Spreadsheet with Service Account

1. In spreadsheet, click "Share" button
2. Get service account email from JSON file (field: `client_email`)
   - Example: `ing-sales-department@your-project.iam.gserviceaccount.com`
3. Paste service account email in "Share" dialog
4. Set permission to "Editor"
5. Uncheck "Notify people" (service account doesn't need email)
6. Click "Share"

### Step 8: Create Leads Sheet

1. In spreadsheet, rename first sheet to "Leads"
2. Add header row with columns (see `docs/08-google-sheets-schema.md` for full schema):
   - Lead ID, Name, Position, Company, LinkedIn URL
   - Classification, Quality Score, Contact Status
   - Allocated To, Allocated At
   - Message Sent, Message Sent At
   - Response, Response Received At
   - Response Sentiment, Response Intent
   - Created At, Last Updated, Notes

### Where to Configure

**File**: `.env`

```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=config/google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

### Verification

```python
# Test Google Sheets access (optional)
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables from .env
load_dotenv()

# Get credentials path and spreadsheet ID from .env
creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'config/google-credentials.json')
spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

if not spreadsheet_id:
    print("ERROR: GOOGLE_SHEETS_SPREADSHEET_ID not set in .env")
    exit(1)

# Authenticate
creds = Credentials.from_service_account_file(creds_path, 
                                              scopes=['https://www.googleapis.com/auth/spreadsheets'])
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(spreadsheet_id)
print(f"Access OK: {spreadsheet.title}")
```

---

## 3. LinkedIn Automation Service

⚠️ **Important**: Choose a service that provides **REST API for sending messages**. 

**Recommended**: **Gojiberry** (see Option B below)

**Not Recommended**: **Dripify** - does NOT support API for sending messages (only webhooks for receiving data)

### ⚠️ Important: Dripify API Limitation

**Dripify does NOT provide traditional REST API for sending messages.**

According to Dripify support, they use **webhook integrations** (via Zapier/Make) that work **one-way only** (from Dripify to external tools, not the other way around). This means:

- ❌ **Cannot send messages** via API to Dripify
- ✅ Can only **receive data** from Dripify via webhooks
- ⚠️ **Dripify is NOT compatible** with this application's requirements

**Recommendation**: Use **Gojiberry** (Option B) or find an alternative LinkedIn automation service that provides REST API for sending messages.

### Option A: Dripify (⚠️ Not Recommended - API Not Available)

**Status**: Dripify does not support API-based message sending. They only provide webhook integrations for receiving data.

If you still want to explore Dripify:
1. Visit: https://dripify.io
2. Sign up for an account
3. Check if they have any API documentation (currently they only support webhooks via Zapier/Make)

**Note**: This application requires the ability to **send messages via API**, which Dripify does not support. Consider using Gojiberry instead.

### Option B: Gojiberry (✅ Recommended)

#### Where to Get

1. Visit: https://gojiberry.com
2. Sign up for an account
3. Go to API/Settings section (or Dashboard → API/Integrations)
4. Generate API key
5. Verify that Gojiberry provides REST API for sending LinkedIn messages

#### Where to Configure

**File**: `.env`

```bash
LINKEDIN_SERVICE=gojiberry
GOJIBERRY_API_KEY=your_gojiberry_api_key_here
GOJIBERRY_API_URL=https://api.gojiberry.com/v1
```

**Note**: 
- Verify the actual API URL and endpoints in Gojiberry documentation
- Ensure Gojiberry supports **sending messages via API** (not just webhooks)
- If Gojiberry also doesn't support API, you'll need to find an alternative service

#### Alternative Services

If neither Dripify nor Gojiberry provide API access, consider these alternatives:

- **Phantombuster** (https://phantombuster.com) - Provides LinkedIn API
- **LinkedIn Sales Navigator API** (official, but requires approval)
- **Other LinkedIn automation tools** that provide REST API for message sending

**Important**: Before choosing a service, verify that it provides:
- ✅ REST API for **sending** LinkedIn messages
- ✅ API authentication (API key or OAuth)
- ✅ Ability to send messages to specific LinkedIn profile URLs

### Verification

- Check API key format (usually alphanumeric string)
- Verify account is active in service dashboard
- Test API connection (if service provides test endpoint)

---

## 4. SMTP Email (for Daily Reports)

### Option A: Gmail

#### Setup Steps

1. **Enable 2-Factor Authentication**:
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter name: "InG Sales Department"
   - Click "Generate"
   - Copy the 16-character password (spaces will be removed automatically)

3. **Use App Password**:
   - Use your Gmail address as `SMTP_USER`
   - Use the generated app password as `SMTP_PASSWORD`

#### Where to Configure

**File**: `.env`

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM=your_email@gmail.com
SMTP_TO=reports@yourcompany.com
```

### Option B: Other SMTP Providers

Use your provider's SMTP settings:

**Common Providers**:
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Check with your email provider

#### Where to Configure

**File**: `.env`

```bash
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=your_email@domain.com
SMTP_TO=reports@yourcompany.com
```

### Verification

```python
# Test SMTP connection (optional)
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Test email")
msg['Subject'] = "Test"
msg['From'] = "your_email@gmail.com"
msg['To'] = "reports@yourcompany.com"

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
server.send_message(msg)
server.quit()
print("Email test OK")
```

---

## 5. Event Information (for Message Templates)

### Where to Configure

**File**: `.env`

```bash
EVENT_DATE=2025-11-20
EVENT_NAME=Tech Event 2025
```

**Format**: 
- `EVENT_DATE`: YYYY-MM-DD format
- `EVENT_NAME`: Any descriptive name

---

## Complete Configuration File Example

Create `.env` file in project root:

```bash
# Google Gemini API
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Google Sheets API
GOOGLE_SHEETS_CREDENTIALS_PATH=config/google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j

# LinkedIn Automation Service
# Note: Dripify does NOT support API for sending messages - use Gojiberry instead
LINKEDIN_SERVICE=gojiberry
GOJIBERRY_API_KEY=your_gojiberry_api_key_here
GOJIBERRY_API_URL=https://api.gojiberry.com/v1
# OR if using Dripify (not recommended - API not available):
# LINKEDIN_SERVICE=dripify
# DRIPIFY_API_KEY=your_dripify_api_key_here
# DRIPIFY_API_URL=https://api.dripify.io/v1
# DRIPIFY_ACCOUNT_ID=your_account_id_here

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_FROM=your_email@gmail.com
SMTP_TO=reports@yourcompany.com

# Application Settings
LOG_LEVEL=INFO
LOG_FILE=data/logs/agents.log
DATA_DIRECTORY=data

# Event Information
EVENT_DATE=2025-11-20
EVENT_NAME=Tech Event 2025
```

---

## Verification Steps

### 1. Check Environment Variables

```bash
# Load and check .env file
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'MISSING')"
```

### 2. Test Configuration Loading

```bash
# Test config loading
python -c "from src.utils.config_loader import load_config; config = load_config(); print('Config loaded:', 'OK' if config else 'ERROR')"
```

### 3. Test Google Sheets Access

```bash
# Test Google Sheets (if gspread installed)
python -c "from src.integrations.google_sheets_io import GoogleSheetsIO; import os; from dotenv import load_dotenv; load_dotenv(); gs = GoogleSheetsIO({'google_sheets': {'spreadsheet_id': os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'), 'credentials_path': os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')}}); print('Google Sheets OK')"
```

### 4. Run Application

```bash
# Start application
python main.py
```

Check logs for any configuration errors.

---

## Common Issues and Solutions

### Issue: "GEMINI_API_KEY environment variable not set"

**Solution**: 
- Check `.env` file exists in project root
- Verify variable name is exactly `GEMINI_API_KEY`
- Ensure no extra spaces around `=`

### Issue: "Google credentials file not found"

**Solution**:
- Verify file path: `config/google-credentials.json`
- Check file exists and is readable
- Ensure JSON file is valid (not corrupted)

### Issue: "Permission denied" when accessing Google Sheets

**Solution**:
- Verify spreadsheet is shared with service account email
- Check service account has "Editor" permission
- Ensure Google Sheets API is enabled in Google Cloud Console

### Issue: "SMTP authentication failed"

**Solution**:
- For Gmail: Use App Password, not regular password
- Verify 2FA is enabled (required for App Passwords)
- Check SMTP host and port are correct
- Try different port (587 or 465)

### Issue: "LinkedIn API key not set"

**Solution**:
- Check `LINKEDIN_SERVICE` matches chosen service (`dripify` or `gojiberry`)
- Verify corresponding API key variable is set (`DRIPIFY_API_KEY` or `GOJIBERRY_API_KEY`)
- For Dripify: Ensure `DRIPIFY_ACCOUNT_ID` is also set
- **Note**: Dripify does not support API for sending messages - use Gojiberry or alternative service

### Issue: "Dripify API not available for sending messages"

**Solution**:
- Dripify only supports webhook integrations (one-way, from Dripify to external tools)
- Switch to `LINKEDIN_SERVICE=gojiberry` or use an alternative service that provides REST API
- Update `.env` file to use Gojiberry or another compatible service

---

## Security Best Practices

1. **Never commit `.env` file** to version control (already in `.gitignore`)
2. **Never commit `config/google-credentials.json`** (already in `.gitignore`)
3. **Use App Passwords** for Gmail (not regular passwords)
4. **Rotate API keys** periodically
5. **Limit service account permissions** to minimum required
6. **Use separate accounts** for testing and production

---

## Next Steps

After completing setup:

1. Review `docs/08-google-sheets-schema.md` for spreadsheet structure
2. Add test leads to Google Sheets (optional)
3. Run `python main.py` to start agents
4. Check `data/logs/agents.log` for any errors
5. Review `docs/06-deployment-and-running.md` for deployment options

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **DevOps Engineer**: _________________ Date: _______

