# Zoho API Clarification - SalesIQ vs Desk

## Quick Answer

**Different APIs are required:**
- ✅ **Zoho SalesIQ API** - For Instant Chat (Option 1)
- ✅ **Zoho Desk API** - For Callback & Ticket (Options 2 & 3)

They are **separate products** with **separate APIs**.

---

## Zoho Ecosystem Overview

```
Zoho Suite
├── Zoho SalesIQ (Chat Widget)
│   ├── API: SalesIQ API
│   ├── Purpose: Live chat, visitor tracking
│   └── Use Case: Transfer chat to agent
│
├── Zoho Desk (Ticketing System)
│   ├── API: Desk API
│   ├── Purpose: Support tickets, issue tracking
│   └── Use Case: Create tickets, manage support
│
└── Zoho CRM (Customer Management)
    ├── API: CRM API
    ├── Purpose: Customer data, leads
    └── Use Case: Store customer info
```

---

## API Details

### 1. Zoho SalesIQ API

**What It Does**:
- Manages live chat conversations
- Transfers chats to agents
- Tracks visitor information
- Sends messages

**When You Use It**:
- User selects "Instant Chat" (Option 1)
- Bot needs to transfer conversation to human agent
- Chat continues in SalesIQ widget

**API Endpoint**:
```
POST https://salesiq.zoho.com/api/v2/chats
```

**What You Need**:
- SalesIQ API Key
- Department ID
- Visitor ID

**Example**:
```python
# Transfer chat to agent
response = requests.post(
    "https://salesiq.zoho.com/api/v2/chats",
    headers={"Authorization": f"Bearer {salesiq_api_key}"},
    json={
        "visitor_id": "user-123",
        "department_id": "dept-456",
        "transfer_to": "human_agent",
        "conversation_history": "..."
    }
)
```

---

### 2. Zoho Desk API

**What It Does**:
- Creates support tickets
- Manages ticket lifecycle
- Tracks customer issues
- Sends notifications

**When You Use It**:
- User selects "Schedule Callback" (Option 2)
- User selects "Create Ticket" (Option 3)
- Bot needs to create ticket in support system

**API Endpoint**:
```
POST https://desk.zoho.com/api/v1/tickets
```

**What You Need**:
- Desk OAuth Token
- Organization ID

**Example**:
```python
# Create callback ticket
response = requests.post(
    "https://desk.zoho.com/api/v1/tickets",
    headers={"Authorization": f"Zoho-oauthtoken {desk_oauth_token}"},
    json={
        "subject": "Callback Request",
        "email": "user@example.com",
        "phone": "+1-555-1234",
        "description": "User requested callback at 2 PM"
    }
)

# Create support ticket
response = requests.post(
    "https://desk.zoho.com/api/v1/tickets",
    headers={"Authorization": f"Zoho-oauthtoken {desk_oauth_token}"},
    json={
        "subject": "QuickBooks Frozen",
        "email": "user@example.com",
        "phone": "+1-555-1234",
        "description": "QuickBooks application is frozen"
    }
)
```

---

## How They Work Together

### Current Setup (What You Have)

```
Zoho SalesIQ Widget
├── Bot Chat (Our Bot)
└── Agent Chat (Human Agent)
```

### With API Integration

```
Zoho SalesIQ Widget
├── Bot Chat (Our Bot)
│   ├── Option 1: Instant Chat
│   │   └── Calls SalesIQ API → Creates Agent Chat
│   ├── Option 2: Schedule Callback
│   │   └── Calls Desk API → Creates Callback Ticket
│   └── Option 3: Create Ticket
│       └── Calls Desk API → Creates Support Ticket
│
└── Agent Chat (Human Agent)
    └── Receives transferred conversation
```

---

## API Credentials You Need

### For SalesIQ (Instant Chat)

**Where to Get**:
1. Go to https://salesiq.zoho.com
2. Settings → API → API Keys
3. Generate new API key

**What You Get**:
```
SALESIQ_API_KEY = "your-api-key-here"
SALESIQ_DEPARTMENT_ID = "123456789"
```

### For Desk (Callback & Ticket)

**Where to Get**:
1. Go to https://desk.zoho.com
2. Settings → API → OAuth Tokens
3. Generate new OAuth token

**What You Get**:
```
DESK_OAUTH_TOKEN = "your-oauth-token-here"
DESK_ORGANIZATION_ID = "987654321"
```

---

## Environment Variables Needed

```bash
# .env file

# SalesIQ API (for Instant Chat)
SALESIQ_API_KEY=your-salesiq-api-key
SALESIQ_DEPARTMENT_ID=your-department-id

# Desk API (for Callback & Ticket)
DESK_OAUTH_TOKEN=your-desk-oauth-token
DESK_ORGANIZATION_ID=your-organization-id
```

---

## Code Structure

### Single API Module with Both APIs

```python
# zoho_api_integration.py

class ZohoSalesIQAPI:
    """Handles SalesIQ API calls"""
    def create_chat_session(self, ...):
        # Calls SalesIQ API
        pass

class ZohoDeskAPI:
    """Handles Desk API calls"""
    def create_callback_ticket(self, ...):
        # Calls Desk API
        pass
    
    def create_support_ticket(self, ...):
        # Calls Desk API
        pass
```

### Usage in Bot

```python
# fastapi_chatbot_hybrid.py

from zoho_api_integration import ZohoSalesIQAPI, ZohoDeskAPI

salesiq_api = ZohoSalesIQAPI()  # Uses SALESIQ_API_KEY
desk_api = ZohoDeskAPI()         # Uses DESK_OAUTH_TOKEN

# Option 1: Instant Chat
if "option 1" in message:
    result = salesiq_api.create_chat_session(...)  # SalesIQ API

# Option 2: Schedule Callback
if "option 2" in message:
    result = desk_api.create_callback_ticket(...)  # Desk API

# Option 3: Create Ticket
if "option 3" in message:
    result = desk_api.create_support_ticket(...)   # Desk API
```

---

## Summary Table

| Feature | API | Endpoint | Purpose |
|---------|-----|----------|---------|
| Instant Chat | SalesIQ | `/api/v2/chats` | Transfer to agent |
| Schedule Callback | Desk | `/api/v1/tickets` | Create callback ticket |
| Create Ticket | Desk | `/api/v1/tickets` | Create support ticket |

---

## Do You Already Have These?

### Check Your Current Setup

**For SalesIQ**:
- Do you have SalesIQ chat widget on your website?
- If yes, you likely have SalesIQ API access

**For Desk**:
- Do you have Zoho Desk for support tickets?
- If yes, you likely have Desk API access

**If You Have Both**:
- ✅ You can implement all 3 options
- ✅ You have both APIs available

**If You Only Have SalesIQ**:
- ✅ You can implement Option 1 (Instant Chat)
- ❌ You cannot implement Options 2 & 3 (need Desk)

**If You Only Have Desk**:
- ❌ You cannot implement Option 1 (need SalesIQ)
- ✅ You can implement Options 2 & 3 (Callback & Ticket)

---

## Next Steps

### 1. Check What You Have
- Do you have SalesIQ?
- Do you have Zoho Desk?
- Do you have both?

### 2. Get API Credentials
- If you have SalesIQ: Get SalesIQ API Key
- If you have Desk: Get Desk OAuth Token

### 3. Provide Credentials
- Share the credentials (or tell me where to find them)
- I'll implement the API integration

---

## Important Notes

### SalesIQ API
- Used for **live chat transfer**
- Requires **SalesIQ subscription**
- Transfers conversation to human agent
- Agent sees full chat history

### Desk API
- Used for **ticket creation**
- Requires **Zoho Desk subscription**
- Creates support tickets
- Support team follows up via email/phone

### They Are Separate
- Different APIs
- Different authentication
- Different purposes
- Both needed for full functionality

---

**Status**: Clarified
**Next Action**: Tell me which Zoho products you have (SalesIQ, Desk, or both)
