# External API Integrations Specification

## Document Information
- **Document Type**: API Integration Guide
- **Target Audience**: Developers
- **Version**: 1.0
- **Date**: January 2025
- **Project**: InG AI Sales Department - External API Integration Details

---

## Executive Summary

Detailed specifications for integrating with external APIs: Google Gemini, Google Sheets, LinkedIn automation services (Dripify/Gojiberry), and SMTP email.

---

## Google Gemini API

### Authentication

**API Key**: From environment variable `GEMINI_API_KEY`

**Library**: `google-generativeai`

**Setup**:
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')
```

### API Calls

**Generate Text**:
```python
def generate_text(prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 500) -> str:
    model = genai.GenerativeModel('gemini-pro')
    
    # Build full prompt
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    
    return response.text
```

**With Context (up to 200K tokens)**:
```python
def generate_with_context(prompt: str, context: Dict, max_context_tokens: int = 200000) -> str:
    # Summarize context if too large
    context_text = json.dumps(context)
    if estimate_tokens(context_text) > max_context_tokens:
        context_text = summarize_context(context)
    
    full_prompt = f"Context: {context_text}\n\nPrompt: {prompt}"
    return generate_text(full_prompt)
```

### Error Handling

```python
try:
    response = model.generate_content(prompt)
except Exception as e:
    # Fallback to rule-based logic
    logger.error(f"Gemini API error: {e}")
    return fallback_logic(prompt)
```

### Rate Limits

- **Free tier**: 15 requests per minute
- **Paid tier**: Higher limits (check current documentation)
- **Implementation**: Implement request throttling if needed

### Caching

Cache responses in `data/cache/llm_responses/{hash}.json`:
```python
import hashlib

def get_cached_response(prompt: str) -> Optional[str]:
    hash_key = hashlib.md5(prompt.encode()).hexdigest()
    cache_file = f"data/cache/llm_responses/{hash_key}.json"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)['response']
    return None
```

---

## Google Sheets API

### Authentication

**Service Account**: JSON credentials file at `config/google-credentials.json`

**Library**: `gspread` + `google-auth`

**Setup**:
```python
import gspread
from google.oauth2.service_account import Credentials

scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(
    'config/google-credentials.json',
    scopes=scope
)
client = gspread.authorize(creds)
```

### Accessing Spreadsheet

```python
# Open by ID
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Or by name
spreadsheet = client.open('InG Sales Department - Leads Database')

# Get worksheet
leads_sheet = spreadsheet.worksheet('Leads')
```

### Reading Data

```python
# Get all records as list of dicts
leads = leads_sheet.get_all_records()

# Get specific range
values = leads_sheet.get('A2:D10')

# Find row by value
cell = leads_sheet.find('lead_001')  # Find by Lead ID
row = cell.row
```

### Writing Data

```python
# Update single cell
leads_sheet.update('G2', 'Speaker')  # Update Classification

# Update multiple cells
leads_sheet.update('G2:H2', [['Speaker', 7.5]])  # Classification and Quality Score

# Append row
leads_sheet.append_row([
    'lead_002', 'Jane Doe', 'CEO', 'Corp Inc', 
    'https://linkedin.com/in/janedoe', '', '', 'Not Contacted'
])

# Update by row number
leads_sheet.update(f'A{row}:P{row}', [row_data])
```

### Error Handling

```python
try:
    leads_sheet.update('G2', 'Speaker')
except gspread.exceptions.APIError as e:
    if e.response.status_code == 429:  # Rate limit
        time.sleep(60)  # Wait and retry
        leads_sheet.update('G2', 'Speaker')
    else:
        raise
```

### Rate Limits

- **Read requests**: 300 per minute per project
- **Write requests**: 60 per minute per project
- **Implementation**: Implement retry with exponential backoff

---

## LinkedIn Automation APIs

### Dripify API

**Base URL**: `https://api.dripify.io/v1` (example, verify actual URL)

**Authentication**: API Key in header

**Setup**:
```python
import requests

headers = {
    'Authorization': f'Bearer {DRIPIFY_API_KEY}',
    'Content-Type': 'application/json'
}
```

**Send Message**:
```python
def send_linkedin_message_via_dripify(linkedin_url: str, message: str) -> SendResult:
    url = f"{DRIPIFY_API_URL}/messages/send"
    
    payload = {
        'linkedin_profile_url': linkedin_url,
        'message': message,
        'account_id': DRIPIFY_ACCOUNT_ID
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return SendResult(
            success=True,
            message_id=response.json().get('message_id'),
            timestamp=datetime.now(),
            service_used='dripify'
        )
    except requests.exceptions.RequestException as e:
        return SendResult(
            success=False,
            error_message=str(e),
            timestamp=datetime.now(),
            service_used='dripify'
        )
```

**Check Response**:
```python
def check_linkedin_responses_via_dripify() -> List[Dict]:
    url = f"{DRIPIFY_API_URL}/messages/responses"
    params = {'account_id': DRIPIFY_ACCOUNT_ID}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json().get('responses', [])
```

**Note**: Actual Dripify API endpoints and format may vary. Consult Dripify documentation for current API specification.

---

### Gojiberry API

**Base URL**: `https://api.gojiberry.com/v1` (example, verify actual URL)

**Authentication**: API Key in header

**Setup**:
```python
headers = {
    'X-API-Key': GOJIBERRY_API_KEY,
    'Content-Type': 'application/json'
}
```

**Send Message**:
```python
def send_linkedin_message_via_gojiberry(linkedin_url: str, message: str) -> SendResult:
    url = f"{GOJIBERRY_API_URL}/send-message"
    
    payload = {
        'profile_url': linkedin_url,
        'text': message
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return SendResult(
            success=True,
            message_id=response.json().get('id'),
            timestamp=datetime.now(),
            service_used='gojiberry'
        )
    except requests.exceptions.RequestException as e:
        return SendResult(
            success=False,
            error_message=str(e),
            timestamp=datetime.now(),
            service_used='gojiberry'
        )
```

**Note**: Actual Gojiberry API endpoints and format may vary. Consult Gojiberry documentation for current API specification.

---

### Unipile API (Polling Mode)

**Base URL**: Unique DSN per account (e.g., `https://api1.unipile.com:13305/api/v1`)

**Authentication**: API Key in `X-API-KEY` header

**Overview**: Unipile is an API-first service for direct LinkedIn messaging. Uses **polling** for checking responses (webhooks not required).

#### Setup

```python
dsn = os.getenv("UNIPILE_DSN")  # e.g., "api1.unipile.com:13305"
api_key = os.getenv("UNIPILE_API_KEY")
account_id = os.getenv("UNIPILE_ACCOUNT_ID")

headers = {
    'X-API-KEY': api_key,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

base_url = f"https://{dsn}/api/v1"
```

#### Connection Flow

LinkedIn requires users to be connected before sending messages. Unipile handles this through invitations:

**1. Search for user in contacts**

```python
url = f"{base_url}/users"
params = {"account_id": account_id, "provider": "LINKEDIN"}
response = requests.get(url, headers=headers, params=params)
users = response.json().get("items", [])

# Find user by LinkedIn URL match
user = next((u for u in users if linkedin_url in u.get("provider_id", "")), None)
```

**2. Send invitation (if user not in contacts)**

```python
url = f"{base_url}/users/invite"
payload = {
    "account_id": account_id,
    "linkedin_url": linkedin_url,
    "message": message
}
response = requests.post(url, json=payload, headers=headers)
invite_id = response.json().get("id")

# Return special status
return SendResult(
    success=False,  # Not a message send
    message_id=invite_id,
    status='invitation_sent'
)
```

**3. Check invitation status (polling, every 6 hours)**

```python
# Re-search for user to see if now connected
user = find_user_by_linkedin_url(linkedin_url)
if user and user.get("connection_status") == "connected":
    return "accepted"
return "pending"
```

**4. Create or find chat**

```python
url = f"{base_url}/chats"
payload = {
    "account_id": account_id,
    "attendees_ids": [user_id],
    "provider": "LINKEDIN"
}
response = requests.post(url, json=payload, headers=headers)
chat_id = response.json().get("id")
```

**5. Send message**

```python
url = f"{base_url}/chats/{chat_id}/messages"
payload = {
    "account_id": account_id,
    "text": message,
    "type": "text"
}
response = requests.post(url, json=payload, headers=headers)
message_id = response.json().get("id")
```

#### Polling for Responses

**Endpoint**: `GET /api/v1/messages`

**Parameters**:
- `account_id`: LinkedIn account ID in Unipile
- `type=received`: Only incoming messages
- `since={ISO_timestamp}`: Only new messages since last check
- `limit=100`: Maximum messages to return

**Implementation**:

```python
def check_responses() -> List[Dict]:
    # Read timestamp of last check from file
    since = read_timestamp_from_file("data/state/unipile_last_check.txt")
    # Default: 2 hours ago if file doesn't exist
    
    url = f"{base_url}/messages"
    params = {
        "account_id": account_id,
        "type": "received",
        "since": since,
        "limit": 100
    }
    
    response = requests.get(url, headers=headers, params=params)
    messages = response.json().get("items", [])
    
    # Transform to unified format
    responses = []
    for msg in messages:
        # Get chat details to extract sender LinkedIn URL
        chat_id = msg.get("chat_id")
        chat_info = get_chat_info(chat_id)
        
        responses.append({
            "message_id": msg.get("id"),
            "text": msg.get("text", ""),
            "linkedin_url": chat_info.get("sender_linkedin_url"),
            "timestamp": msg.get("date")
        })
    
    # Update timestamp cache
    save_timestamp_to_file("data/state/unipile_last_check.txt", datetime.now())
    
    return responses
```

**Frequency**: Every 2 hours (configurable via `response_check_interval_hours`)

#### Rate Limits

- **Invitations**: 30-50 per day (recommended: 40)
- **Messages**: 100-150 per day (recommended: 45)
- **API Requests**: No official limits, but recommend polling no more than once per hour

#### Error Handling

- **429 Rate Limit**: Log and skip cycle
- **404 User Not Found**: Send invitation
- **400 Bad Request**: Check data format, log error
- **500 Server Error**: Retry with exponential backoff (max 3 attempts)

#### Cost

€49/month per account (includes all API features)

---

### LinkedIn Sender Abstraction

**Implementation**: Create unified interface for all services

```python
class LinkedInSender:
    def __init__(self, service: str, api_key: str, api_url: str):
        self.service = service  # "dripify", "gojiberry", or "unipile"
        self.api_key = api_key
        self.api_url = api_url
        
    def send_message(self, linkedin_url: str, message: str) -> SendResult:
        if self.service == "dripify":
            return send_linkedin_message_via_dripify(linkedin_url, message)
        elif self.service == "gojiberry":
            return send_linkedin_message_via_gojiberry(linkedin_url, message)
        elif self.service == "unipile":
            return send_linkedin_message_via_unipile(linkedin_url, message)
        else:
            raise ValueError(f"Unknown service: {self.service}")
```

---

## SMTP Email Service

### Configuration

**From environment variables**:
- `SMTP_HOST`: SMTP server (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: Port (587 for TLS, 465 for SSL)
- `SMTP_USER`: Email address
- `SMTP_PASSWORD`: App password (not regular password)
- `SMTP_FROM`: From address
- `SMTP_TO`: Recipient address(es)

### Implementation

**Library**: `smtplib` (built-in)

**Send Email**:
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_daily_report(subject: str, body: str, recipients: List[str]) -> bool:
    msg = MIMEMultipart()
    msg['From'] = SMTP_FROM
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # For TLS
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
```

### Gmail Setup

1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password (not regular password) in `SMTP_PASSWORD`

### Error Handling

```python
try:
    send_daily_report(subject, body, recipients)
except smtplib.SMTPException as e:
    logger.error(f"SMTP error: {e}")
    # Log to file as backup
    log_report_to_file(subject, body)
```

---

## API Error Handling Strategy

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def api_call_with_retry(func, *args, **kwargs):
    return func(*args, **kwargs)
```

### Common Error Codes

- **429 (Rate Limit)**: Wait and retry
- **401 (Unauthorized)**: Check credentials
- **500 (Server Error)**: Retry with backoff
- **400 (Bad Request)**: Log and skip (don't retry)

---

## Testing APIs

### Mock Services for Testing

```python
# Mock Gemini API
def mock_gemini_response(prompt: str) -> str:
    if "classify" in prompt.lower():
        return "Speaker"
    elif "generate message" in prompt.lower():
        return "Hi [Name]! We're organising..."
    return "Mock response"

# Mock LinkedIn API
def mock_linkedin_send(linkedin_url: str, message: str) -> SendResult:
    return SendResult(
        success=True,
        message_id="mock_123",
        timestamp=datetime.now(),
        service_used="mock"
    )
```

---

## Future API Integrations (Post-Sprint 1)

### Clay.com API Integration

**Current State**: CSV export/import method (Sprint 1).

**Future Enhancement**: Automatic synchronization from Clay.com API to Google Sheets.

**Approach**:
- Separate synchronization script/process (not part of agent system)
- Syncs Clay.com API → Google Sheets on schedule
- Lead Finder Agent continues reading from Google Sheets (no agent changes)

**API Details** (to be specified when implemented):
- Authentication: API key or OAuth
- Endpoints: Lead export, lead updates
- Rate limits: To be determined
- Error handling: Retry with exponential backoff

**Status**: Optional enhancement, not required for Sprint 1.

---

## Document Approval

- **Technical Lead**: _________________ Date: _______
- **Senior Developer**: _________________ Date: _______

