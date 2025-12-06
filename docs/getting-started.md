# Getting Started Guide

## 🚀 Quick Start

### ⚠️ IMPORTANT: How to Run the Application

**❌ DO NOT run:** `python main.py` directly (will cause ModuleNotFoundError)

**✅ ALWAYS use the wrapper script:**
```bash
python run_main.py
```

This ensures the application runs with the correct Python environment and all dependencies are loaded.

### Alternative Launch Methods

#### Method 1: Wrapper Script (RECOMMENDED)
```bash
python run_main.py
```
**This method works everywhere and always!**

#### Method 2: Direct venv Execution
```bash
.\venv\Scripts\python.exe main.py
```

#### Method 3: Platform-Specific Scripts
- **PowerShell:** `.\start_agents.ps1`
- **CMD/Batch:** `run.bat`
- **Git Bash:** `./run.sh` or `./run`

## Why the Error Occurs?

When you run `python main.py`, the system Python is used, which doesn't have access to packages from venv (psutil, gspread, etc.).

The `run_main.py` script automatically uses the correct Python from venv.

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using venv:
```bash
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 2. Configure Environment Variables

1. Copy `config/env.example.txt` to `.env` and fill in your values
2. Copy `config/agents.yaml.example` to `config/agents.yaml` and adjust as needed

Required environment variables:
- `GEMINI_API_KEY` - Google Gemini API key
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Your Google Sheets ID
- `GOOGLE_SHEETS_CREDENTIALS_PATH` - Path to Google service account JSON
- `UNIPILE_DSN` - Unipile DSN endpoint
- `UNIPILE_API_KEY` - Unipile API key
- `UNIPILE_ACCOUNT_ID` - LinkedIn account ID from Unipile

### 3. Set Up Google Sheets

#### Required Columns

Your Google Sheets must have these columns:

| Column | Required | Purpose |
|--------|----------|---------|
| **Lead ID** | Yes | Unique identifier for each lead |
| **Name** | Yes | Lead's name |
| **Position** | Yes | Lead's position |
| **Company** | Yes | Lead's company |
| **LinkedIn URL** | Yes | LinkedIn profile URL |
| **Classification** | No | Auto-filled by agents (Speaker/Sponsor) |
| **Quality Score** | No | Auto-calculated score 1-10 |
| **Contact Status** | Yes | Tracking status (Not Contacted, etc.) |
| **Allocated To** | No | Which agent is handling this lead |
| **Allocated At** | No | When lead was assigned |
| **Message Sent** | No | The actual message sent |
| **Message Sent At** | No | When message was sent |
| **Response** | No | Lead's response |
| **Response Received At** | No | When response came in |
| **Response Sentiment** | No | positive/negative/neutral |
| **Response Intent** | No | interested/not_interested |
| **Created At** | Yes | When lead was added |
| **Last Updated** | Yes | Last modification time |
| **Notes** | No | Additional notes |

#### Quick Setup Steps

1. Open your Google Sheet
2. Add the required column headers
3. For existing leads, fill in:
   - **Lead ID**: Unique identifier (e.g., `lead_001`)
   - **Contact Status**: `Not Contacted`
   - **Created At**: Current timestamp
   - **Last Updated**: Current timestamp

#### Optional: Set Up Dropdowns

- **Contact Status column**: Not Contacted, Allocated, Invitation Sent, Message Sent, Responded, Closed, Failed
- **Classification column**: Speaker, Sponsor, Other

### 4. Set Up Google Sheets Credentials

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download the JSON credentials file
5. Place it in `config/google-credentials.json`
6. Share your Google Sheet with the service account email

## Verification

### Check Installation

Verify that venv Python works:
```bash
.\venv\Scripts\python.exe -c "import psutil; print('OK')"
```

If you see "OK" - everything is ready!

### Check Application Start

Run:
```bash
python run_main.py
```

If you see "Starting InG AI Sales Department Agents..." - everything is working!

## Troubleshooting

### ModuleNotFoundError: No module named 'psutil'

**Problem:** You're using system Python instead of venv Python.

**Solution:**
1. Always use `python run_main.py` instead of `python main.py`
2. Or use `.\venv\Scripts\python.exe main.py`
3. Make sure dependencies are installed: `.\venv\Scripts\pip.exe install -r requirements.txt`

### Google Sheets Connection Issues

**Problem:** Agents can't find leads or update the sheet.

**Solution:**
1. Check that `GOOGLE_SHEETS_SPREADSHEET_ID` is set correctly in `.env`
2. Verify `config/google-credentials.json` exists and is valid
3. Ensure the service account email has access to your sheet
4. Check that all required columns exist in your sheet

### Agents Not Processing Leads

**Problem:** Leads are not being processed.

**Solution:**
1. Check that leads have required fields filled:
   - Lead ID
   - Contact Status = "Not Contacted"
   - Created At
   - Last Updated
2. Verify logs: `data/logs/agents.log`
3. Check agent status: `python tools/check_agent_status.py`

## What Happens Next?

Once everything is set up:

1. **LeadFinder Agent** will classify leads as Speaker/Sponsor
2. **SalesManager Agent** will allocate qualified leads to Outreach
3. **Outreach Agent** will send LinkedIn messages
4. All activity will be logged and tracked in Google Sheets

## Additional Resources

- See `docs/06-deployment-and-running.md` for detailed deployment information
- See `docs/configuration.md` for account configuration and API testing
- See `tools/README.md` for available utility scripts


