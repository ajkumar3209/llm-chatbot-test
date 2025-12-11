# API Integration Plan - 3 Escalation Options

## Current Status

### What's Done ✅
- System prompt with top 10 issues
- Escalation logic (detects when to escalate)
- Response format for each option
- Test suite for local testing

### What's NOT Done ❌
- **Zoho SalesIQ API** - Instant Chat integration
- **Zoho Desk API** - Callback ticket creation
- **Zoho Desk API** - Support ticket creation
- **Authentication** - API keys and OAuth
- **Error handling** - API failures
- **Webhook callbacks** - Receiving responses from APIs

---

## 3 Escalation Options - What Needs to Be Done

### Option 1: Instant Chat (Transfer to Human Agent)

**Current Status**: ❌ NOT INTEGRATED
- Bot detects "option 1" or "instant chat"
- Returns `"action": "transfer"` with conversation history
- **Missing**: Actually creates SalesIQ chat session

**What Needs to Be Done**:
1. Get Zoho SalesIQ API credentials
2. Call SalesIQ API to create new chat session
3. Pass conversation history to agent
4. Return session ID to SalesIQ widget

**API Endpoint**:
```
POST https://salesiq.zoho.com/api/v2/chats
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json
Body:
{
  "visitor_id": "{visitor_id}",
  "department_id": "{department_id}",
  "conversation_history": "{full_chat_history}",
  "transfer_to": "human_agent"
}
```

**Expected Response**:
```json
{
  "status": "success",
  "chat_session_id": "chat-12345",
  "agent_assigned": "John Doe",
  "message": "Connecting to agent..."
}
```

---

### Option 2: Schedule Callback (Auto-Closes Chat)

**Current Status**: ❌ NOT INTEGRATED
- Bot detects "option 2" or "callback"
- Collects preferred time and phone number
- Auto-closes chat
- **Missing**: Creates ticket in Zoho Desk

**What Needs to Be Done**:
1. Get Zoho Desk API credentials
2. Collect user's preferred time and phone
3. Create callback ticket in Zoho Desk
4. Send confirmation to user
5. Auto-close chat

**API Endpoint**:
```
POST https://desk.zoho.com/api/v1/tickets
Headers:
  Authorization: Zoho-oauthtoken {access_token}
  Content-Type: application/json
Body:
{
  "subject": "Callback Request",
  "description": "User requested callback at {preferred_time}",
  "phone": "{phone_number}",
  "email": "{user_email}",
  "priority": "medium",
  "status": "open",
  "type": "callback",
  "custom_fields": {
    "callback_time": "{preferred_time}",
    "issue_description": "{issue_summary}"
  }
}
```

**Expected Response**:
```json
{
  "code": 0,
  "message": "The ticket has been created successfully",
  "data": {
    "ticketNumber": "TICKET-12345",
    "id": "123456789"
  }
}
```

---

### Option 3: Create Support Ticket (Auto-Closes Chat)

**Current Status**: ❌ NOT INTEGRATED
- Bot detects "option 3" or "ticket"
- Collects name, email, phone, description
- Creates ticket in Zoho Desk
- Auto-closes chat
- **Missing**: Actually creates ticket in Zoho Desk

**What Needs to Be Done**:
1. Get Zoho Desk API credentials
2. Collect user details (name, email, phone, description)
3. Create ticket in Zoho Desk
4. Send confirmation to user
5. Auto-close chat

**API Endpoint**:
```
POST https://desk.zoho.com/api/v1/tickets
Headers:
  Authorization: Zoho-oauthtoken {access_token}
  Content-Type: application/json
Body:
{
  "subject": "{issue_summary}",
  "description": "{full_description}",
  "email": "{user_email}",
  "phone": "{phone_number}",
  "name": "{user_name}",
  "priority": "medium",
  "status": "open",
  "type": "support",
  "custom_fields": {
    "issue_type": "{issue_type}",
    "conversation_history": "{chat_history}"
  }
}
```

**Expected Response**:
```json
{
  "code": 0,
  "message": "The ticket has been created successfully",
  "data": {
    "ticketNumber": "TICKET-12346",
    "id": "123456790"
  }
}
```

---

## Implementation Steps

### Step 1: Get API Credentials

**For Zoho SalesIQ**:
1. Go to https://salesiq.zoho.com
2. Settings → API → Generate API Key
3. Get: `salesiq_api_key`, `salesiq_department_id`

**For Zoho Desk**:
1. Go to https://desk.zoho.com
2. Settings → API → OAuth Tokens
3. Generate OAuth token
4. Get: `desk_oauth_token`, `desk_organization_id`

### Step 2: Update Environment Variables

```bash
# .env file
SALESIQ_API_KEY=your-salesiq-api-key
SALESIQ_DEPARTMENT_ID=your-department-id
DESK_OAUTH_TOKEN=your-desk-oauth-token
DESK_ORGANIZATION_ID=your-organization-id
```

### Step 3: Create API Integration Module

**File**: `zoho_api_integration.py`

```python
import requests
import os
from typing import Dict, Optional

class ZohoSalesIQAPI:
    """Zoho SalesIQ API Integration"""
    
    def __init__(self):
        self.api_key = os.getenv("SALESIQ_API_KEY")
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID")
        self.base_url = "https://salesiq.zoho.com/api/v2"
    
    def create_chat_session(self, visitor_id: str, conversation_history: str) -> Dict:
        """Create new chat session and transfer to agent"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "visitor_id": visitor_id,
            "department_id": self.department_id,
            "conversation_history": conversation_history,
            "transfer_to": "human_agent"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chats",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ZohoDeskAPI:
    """Zoho Desk API Integration"""
    
    def __init__(self):
        self.oauth_token = os.getenv("DESK_OAUTH_TOKEN")
        self.org_id = os.getenv("DESK_ORGANIZATION_ID")
        self.base_url = "https://desk.zoho.com/api/v1"
    
    def create_callback_ticket(self, 
                              user_email: str,
                              phone: str,
                              preferred_time: str,
                              issue_summary: str) -> Dict:
        """Create callback ticket"""
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subject": "Callback Request",
            "description": f"User requested callback at {preferred_time}",
            "email": user_email,
            "phone": phone,
            "priority": "medium",
            "status": "open",
            "type": "callback",
            "customFields": {
                "callback_time": preferred_time,
                "issue_description": issue_summary
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/tickets",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "ticket_number": response.json().get("data", {}).get("ticketNumber"),
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_support_ticket(self,
                             user_name: str,
                             user_email: str,
                             phone: str,
                             description: str,
                             issue_type: str,
                             conversation_history: str) -> Dict:
        """Create support ticket"""
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subject": f"Support Request - {issue_type}",
            "description": description,
            "email": user_email,
            "phone": phone,
            "name": user_name,
            "priority": "medium",
            "status": "open",
            "type": "support",
            "customFields": {
                "issue_type": issue_type,
                "conversation_history": conversation_history
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/tickets",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "ticket_number": response.json().get("data", {}).get("ticketNumber"),
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### Step 4: Update Bot Code

**In `fastapi_chatbot_hybrid.py`**:

```python
from zoho_api_integration import ZohoSalesIQAPI, ZohoDeskAPI

salesiq_api = ZohoSalesIQAPI()
desk_api = ZohoDeskAPI()

# For Instant Chat
if "instant chat" in message_lower or "option 1" in message_lower:
    # Create SalesIQ chat session
    result = salesiq_api.create_chat_session(
        visitor_id=session_id,
        conversation_history=conversation_text
    )
    
    if result["success"]:
        return {
            "action": "transfer",
            "transfer_to": "human_agent",
            "session_id": session_id,
            "conversation_history": conversation_text,
            "replies": ["Connecting you with a support agent..."]
        }
    else:
        return {
            "action": "reply",
            "replies": ["Sorry, unable to connect to agent. Please try again."],
            "session_id": session_id
        }

# For Schedule Callback
if "callback" in message_lower or "option 2" in message_lower:
    # Create Desk callback ticket
    result = desk_api.create_callback_ticket(
        user_email=user_email,
        phone=phone_number,
        preferred_time=preferred_time,
        issue_summary=issue_summary
    )
    
    if result["success"]:
        return {
            "action": "reply",
            "replies": [f"Callback scheduled! Ticket: {result['ticket_number']}"],
            "session_id": session_id
        }
    else:
        return {
            "action": "reply",
            "replies": ["Sorry, unable to schedule callback. Please try again."],
            "session_id": session_id
        }

# For Create Ticket
if "ticket" in message_lower or "option 3" in message_lower:
    # Create Desk support ticket
    result = desk_api.create_support_ticket(
        user_name=user_name,
        user_email=user_email,
        phone=phone_number,
        description=issue_description,
        issue_type=issue_type,
        conversation_history=conversation_text
    )
    
    if result["success"]:
        return {
            "action": "reply",
            "replies": [f"Ticket created! Ticket: {result['ticket_number']}"],
            "session_id": session_id
        }
    else:
        return {
            "action": "reply",
            "replies": ["Sorry, unable to create ticket. Please try again."],
            "session_id": session_id
        }
```

---

## Testing API Integration

### Test 1: Instant Chat API
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-api-1",
    "message": {"text": "option 1"},
    "visitor": {"id": "user-123"}
  }'
```

Expected: SalesIQ creates new chat session

### Test 2: Callback API
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-api-2",
    "message": {"text": "option 2"},
    "visitor": {"id": "user-123"}
  }'
```

Expected: Zoho Desk creates callback ticket

### Test 3: Support Ticket API
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-api-3",
    "message": {"text": "option 3"},
    "visitor": {"id": "user-123"}
  }'
```

Expected: Zoho Desk creates support ticket

---

## Error Handling

### What Can Go Wrong
1. API credentials invalid
2. API rate limit exceeded
3. Network timeout
4. Invalid user data
5. API service down

### How to Handle
```python
try:
    result = api.create_ticket(...)
    if result["success"]:
        # Success
    else:
        # API error - return fallback message
        return {"action": "reply", "replies": ["Please try again later"]}
except Exception as e:
    # Network error - return fallback message
    return {"action": "reply", "replies": ["Connection error. Please try again"]}
```

---

## Deployment Checklist

- [ ] Get Zoho SalesIQ API credentials
- [ ] Get Zoho Desk API credentials
- [ ] Create `zoho_api_integration.py`
- [ ] Update `.env` with API keys
- [ ] Update `fastapi_chatbot_hybrid.py` with API calls
- [ ] Test each escalation option
- [ ] Deploy to Railway
- [ ] Monitor API calls
- [ ] Handle errors gracefully

---

## Summary

**Current Status**: Logic is ready, APIs are NOT integrated
**What's Needed**: 
1. API credentials from Zoho
2. API integration module
3. Updated bot code with API calls
4. Error handling
5. Testing

**Timeline**: 2-3 hours to implement
**Complexity**: Medium (straightforward API calls)

---

**Status**: ❌ NOT INTEGRATED YET
**Next Step**: Get Zoho API credentials and implement integration
