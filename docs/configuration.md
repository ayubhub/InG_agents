# Configuration Guide

## LinkedIn Account Configuration

### Setting Up Multiple LinkedIn Accounts

The system supports multiple LinkedIn accounts for automatic failover when rate limits are reached.

#### Automatic Configuration Update

When a second LinkedIn account is added to Unipile, update the configuration automatically:

```bash
python tools/update_second_account.py
```

Or use the account checker:
```bash
python tools/check_and_update_accounts.py
```

These scripts will:
1. Fetch all LinkedIn accounts from Unipile API
2. Update `.env` file with both accounts
3. Configure Account_1 and Account_2

#### Manual Configuration

If automatic update doesn't work, add to `.env` file:

```env
# Primary LinkedIn Account
UNIPILE_DSN=api20.unipile.com:15052
UNIPILE_API_KEY=your_api_key_here
UNIPILE_ACCOUNT_ID=your_account_id_here

# Secondary LinkedIn Account
UNIPILE_DSN_2=api20.unipile.com:15052
UNIPILE_API_KEY_2=your_api_key_here
UNIPILE_ACCOUNT_ID_2=your_second_account_id_here
```

To get Account IDs, use:
```bash
python tools/check_and_update_accounts.py
```

#### Verify Configuration

After updating, verify the configuration:

```bash
python tools/verify_two_accounts.py
```

This script will show:
- ✅ Whether Account_1 is configured
- ✅ Whether Account_2 is configured
- ✅ State file status
- ✅ System readiness

### How Multi-Account System Works

1. **Automatic Failover**: If Account_1 reaches its limit, the system automatically switches to Account_2
2. **Rate Limiting**: Each account has its own limits (50 per day, 10 per hour by default)
3. **State Tracking**: The system tracks usage for each account separately
4. **Cooldown Management**: If both accounts are in cooldown, the system waits

### After Configuration Update

1. Restart the application:
   ```bash
   python run_main.py
   ```

2. Check logs - you should see:
   ```
   Initialized multi-account LinkedIn sender with 2 accounts
   ```

3. The system will automatically start using both accounts

### Troubleshooting Multi-Account Setup

**If Account_2 is not loading:**

1. Check `.env` file - all three variables must be set:
   - `UNIPILE_DSN_2`
   - `UNIPILE_API_KEY_2`
   - `UNIPILE_ACCOUNT_ID_2`

2. Verify Account ID is correct (from Unipile API)

3. Check startup logs - they contain information about account loading

**If you see "Account_2 ID missing - skipping Account_2":**
- Check that `UNIPILE_ACCOUNT_ID_2` is set in `.env`
- Ensure there are no typos in the variable name

**If you see "All LinkedIn accounts have reached their limits":**
- Check account status: `python tools/monitor_linkedin_limits.py`
- Reset limits if needed: `python tools/reset_accounts_complete.py`
- Verify accounts are configured: `python tools/check_linkedin_accounts.py`

## Gemini API Configuration

### Testing Gemini API Key

Test your Gemini API key:

```bash
python tools/test_gemini_api.py
```

### What the Test Checks

1. ✅ Presence of `GEMINI_API_KEY` in `.env`
2. ✅ Whether `google-generativeai` library is installed
3. ✅ API configuration
4. ✅ Model availability:
   - `gemini-2.5-flash-preview-09-2025` (from config)
   - `gemini-1.5-flash`
   - `gemini-1.5-pro`
   - `gemini-pro`
5. ✅ Test API call
6. ✅ Token usage

### Expected Results

**If everything works:**
```
✅ SUCCESS: Gemini API is working correctly!
```

**If there are problems:**
- ❌ API key not found - check `.env` file
- ❌ Failed to import - install: `pip install google-generativeai`
- ❌ API call failed - check key and quotas

### Installing Dependencies

If the library is not installed:
```bash
pip install google-generativeai
```

Or via venv:
```bash
.\venv\Scripts\pip install google-generativeai
```

### API Key Usage in Code

The API key is used in:
- `src/integrations/llm_client.py` - main LLM client
- Default model: `gemini-pro` (can be changed in `config/agents.yaml`)

Current model in config: `gemini-2.5-flash-preview-09-2025`

## Rate Limits Configuration

### Default Limits

- **Daily limit per account**: 50 messages
- **Hourly limit per account**: 10 messages

These can be configured in `.env`:
```env
LINKEDIN_DAILY_LIMIT=50
LINKEDIN_HOURLY_LIMIT=10
```

### Monitoring Limits

Check current limit status:
```bash
python tools/monitor_linkedin_limits.py
```

Reset limits if needed:
```bash
python tools/monitor_linkedin_limits.py reset
```

Or reset specific account:
```bash
python tools/monitor_linkedin_limits.py reset Account_1
```

## Account Management Utilities

### Check Account Status

```bash
python tools/check_linkedin_accounts.py
```

Shows:
- Configured accounts
- Account state files
- Rate limits
- Recommendations

### Show Account Configuration

```bash
python tools/show_account_config.py
```

Displays current account configuration from `.env`.

### Reset Accounts

Complete reset (clears all cooldowns):
```bash
python tools/reset_accounts_complete.py
```

Manual reset:
```bash
python tools/reset_linkedin_accounts.py
```

### Fix Single Account Setup

If you have only one account but system thinks there are two:
```bash
python tools/fix_single_account_complete.py
```

This will:
- Remove Account_2 from state if not configured
- Clear cooldowns
- Reset limits
- Ensure only Account_1 is used

## Environment Variables Reference

### Required Variables

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Google Sheets
GOOGLE_SHEETS_SPREADSHEET_ID=your_sheet_id
GOOGLE_SHEETS_CREDENTIALS_PATH=config/google-credentials.json

# Unipile - Primary Account
UNIPILE_DSN=api20.unipile.com:15052
UNIPILE_API_KEY=your_unipile_api_key
UNIPILE_ACCOUNT_ID=your_account_id

# Unipile - Secondary Account (optional)
UNIPILE_DSN_2=api20.unipile.com:15052
UNIPILE_API_KEY_2=your_unipile_api_key_2
UNIPILE_ACCOUNT_ID_2=your_account_id_2

# Rate Limits (optional, defaults shown)
LINKEDIN_DAILY_LIMIT=50
LINKEDIN_HOURLY_LIMIT=10
```

### Optional Variables

```env
# Email for reports (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password
REPORT_RECIPIENT=recipient@example.com
```

## Quick Configuration Checklist

- [ ] `.env` file created with all required variables
- [ ] Google Sheets credentials file placed in `config/google-credentials.json`
- [ ] Google Sheet shared with service account email
- [ ] Google Sheet has all required columns
- [ ] Gemini API key tested: `python tools/test_gemini_api.py`
- [ ] LinkedIn accounts configured: `python tools/verify_two_accounts.py`
- [ ] Application starts successfully: `python run_main.py`


