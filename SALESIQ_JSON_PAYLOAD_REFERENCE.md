# SalesIQ JSON Payload Reference

## Overview

This document explains the exact JSON payload format that SalesIQ sends to your bot and how your bot responds.

---

## Request Payload Format (SalesIQ → Your Bot)

### Complete Payload Structure

```json
{
  "session_id": "unique-session-id-12345",
  "chat_id": "chat-12345",
  "message": {
    "text": "QuickBooks is frozen",
    "type": "text"
  },
  "visitor": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "id": "visitor-123",
    "active_conversation_id": "conv-456"
  },
  "timestamp": "2025-12-03T10:30:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Unique identifier for the chat session |
| `chat_id` | string | No | Alternative session identifier |
| `message.text` | string | Yes | User's message text |
| `message.type` | string | No | Message type (usually "text") |
| `visitor.name` | string | No | Visitor's name |
| `visitor.email` | string | No | Visitor's email |
| `visitor.phone` | string | No | Visitor's phone number |
| `visitor.id` | string | No | Visitor's unique ID |
| `visitor.active_conversation_id` | string | No | Active conversation ID |
| `timestamp` | string | No | ISO 8601 timestamp |

---

## Response Payload Format (Your Bot → SalesIQ)

### Standard Reply Response

```json
{
  "action": "reply",
  "replies": [
    "I can help with that! Is your QuickBooks on a dedicated or shared server?"
  ],
  "session_id": "unique-session-id-12345"
}
```

### Transfer to Agent Response

```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "unique-session-id-12345",
  "conversation_history": "User: QuickBooks is frozen\nBot: Is your QuickBooks on a dedicated or shared server?\nUser: Dedicated server",
  "replies": [
    "Connecting you with a support agent..."
  ]
}
```

### Multi-line Reply Response

```json
{
  "action": "reply",
  "replies": [
    "I'm here to help! Let's tackle them one at a time.",
    "What's the first issue you're experiencing?"
  ],
  "session_id": "unique-session-id-12345"
}
```

### Error Response

```json
{
  "action": "reply",
  "replies": [
    "I'm having technical difficulties. Please contact support at 1-888-415-5240"
  ],
  "session_id": "unique-session-id-12345"
}
```

---

## How Your Bot Handles the Payload

### Step 1: Extract Session ID

```python
# Your bot tries these in order:
session_id = (
    visitor.get('active_conversation_id') or  # First priority
    request.get('session_id') or              # Second priority
    visitor.get('id') or                      # Third priority
    'unknown'                                 # Fallback
)
```

### Step 2: Extract Message Text

```python
# Your bot handles multiple message formats:
message_obj = request.get('message', {})

if isinstance(message_obj, dict):
    message_text = message_obj.get('text', '').strip()
else:
    message_text = str(message_obj).strip()
```

### Step 3: Process Message

```python
# Your bot:
# 1. Checks for greetings
# 2. Checks for contact requests
# 3. Checks for escalation keywords
# 4. Calls OpenAI LLM with embedded resolution steps
# 5. Returns response in correct format
```

### Step 4: Return Response

```python
return {
    "action": "reply",
    "replies": [response_text],
    "session_id": session_id
}
```

---

## Complete Working Examples

### Example 1: Simple Greeting

**Request from SalesIQ:**
```json
{
  "session_id": "sess_abc123",
  "message": {
    "text": "Hello"
  },
  "visitor": {
    "id": "user-001"
  }
}
```

**Response from Bot:**
```json
{
  "action": "reply",
  "replies": [
    "Hello! How can I assist you today?"
  ],
  "session_id": "sess_abc123"
}
```

---

### Example 2: QuickBooks Issue

**Request from SalesIQ:**
```json
{
  "session_id": "sess_qb456",
  "chat_id": "chat_qb456",
  "message": {
    "text": "QuickBooks company file won't open",
    "type": "text"
  },
  "visitor": {
    "name": "Jane Smith",
    "email": "jane@company.com",
    "id": "user-002"
  },
  "timestamp": "2025-12-03T14:22:15Z"
}
```

**Response from Bot:**
```json
{
  "action": "reply",
  "replies": [
    "I can help with that! Is your QuickBooks on a dedicated or shared server?"
  ],
  "session_id": "sess_qb456"
}
```

---

### Example 3: Escalation - Instant Chat

**Request from SalesIQ:**
```json
{
  "session_id": "sess_esc789",
  "message": {
    "text": "option 1"
  },
  "visitor": {
    "id": "user-003"
  }
}
```

**Response from Bot:**
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "sess_esc789",
  "conversation_history": "User: My QuickBooks is frozen\nBot: Is your QuickBooks on a dedicated or shared server?\nUser: Dedicated\nBot: Step 1: Right click and open Task Manager...\nUser: Still not working\nBot: Here are 3 options...\nUser: option 1",
  "replies": [
    "Connecting you with a support agent..."
  ]
}
```

---

### Example 4: Escalation - Schedule Callback

**Request from SalesIQ:**
```json
{
  "session_id": "sess_callback001",
  "message": {
    "text": "option 2"
  },
  "visitor": {
    "id": "user-004"
  }
}
```

**Response from Bot:**
```json
{
  "action": "reply",
  "replies": [
    "Perfect! I'm creating a callback request for you.\n\nPlease provide:\n1. Your preferred time (e.g., 'tomorrow at 2 PM')\n2. Your phone number\n\nOur support team will call you back at that time."
  ],
  "session_id": "sess_callback001"
}
```

---

### Example 5: Escalation - Create Ticket

**Request from SalesIQ:**
```json
{
  "session_id": "sess_ticket002",
  "message": {
    "text": "option 3"
  },
  "visitor": {
    "id": "user-005"
  }
}
```

**Response from Bot:**
```json
{
  "action": "reply",
  "replies": [
    "Perfect! I'm creating a support ticket for you.\n\nPlease provide:\n1. Your name\n2. Your email\n3. Your phone number\n4. Brief description of the issue\n\nA ticket has been created and you'll receive a confirmation email shortly."
  ],
  "session_id": "sess_ticket002"
}
```

---

## Testing with cURL

### Test 1: Basic Message

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_123",
    "message": {
      "text": "Hello"
    },
    "visitor": {
      "id": "user-test"
    }
  }'
```

**Expected Response:**
```json
{
  "action": "reply",
  "replies": ["Hello! How can I assist you today?"],
  "session_id": "test_123"
}
```

---

### Test 2: QuickBooks Issue

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_qb_456",
    "message": {
      "text": "QuickBooks is frozen"
    },
    "visitor": {
      "name": "Test User",
      "email": "test@example.com",
      "id": "user-test-2"
    }
  }'
```

**Expected Response:**
```json
{
  "action": "reply",
  "replies": ["Are you using a dedicated server or a shared server?"],
  "session_id": "test_qb_456"
}
```

---

### Test 3: Escalation Option 1

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_esc_789",
    "message": {
      "text": "option 1"
    },
    "visitor": {
      "id": "user-test-3"
    }
  }'
```

**Expected Response:**
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "test_esc_789",
  "conversation_history": "...",
  "replies": ["Connecting you with a support agent..."]
}
```

---

### Test 4: Escalation Option 2

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_callback_001",
    "message": {
      "text": "option 2"
    },
    "visitor": {
      "id": "user-test-4"
    }
  }'
```

**Expected Response:**
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a callback request for you..."],
  "session_id": "test_callback_001"
}
```

---

### Test 5: Escalation Option 3

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_ticket_002",
    "message": {
      "text": "option 3"
    },
    "visitor": {
      "id": "user-test-5"
    }
  }'
```

**Expected Response:**
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a support ticket for you..."],
  "session_id": "test_ticket_002"
}
```

---

## Python Implementation

### Receiving and Parsing Request

```python
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.post("/webhook/salesiq")
async def salesiq_webhook(request: Dict[str, Any]):
    """Handle SalesIQ webhook"""
    
    # Extract session ID
    visitor = request.get('visitor', {})
    session_id = (
        visitor.get('active_conversation_id') or 
        request.get('session_id') or 
        visitor.get('id') or
        'unknown'
    )
    
    # Extract message
    message_obj = request.get('message', {})
    if isinstance(message_obj, dict):
        message_text = message_obj.get('text', '').strip()
    else:
        message_text = str(message_obj).strip()
    
    # Extract visitor info (optional)
    visitor_name = visitor.get('name')
    visitor_email = visitor.get('email')
    visitor_phone = visitor.get('phone')
    
    # Process message
    response_text = process_message(message_text)
    
    # Return response
    return {
        "action": "reply",
        "replies": [response_text],
        "session_id": session_id
    }
```

### Sending Response

```python
def send_reply(session_id: str, message: str) -> Dict:
    """Send reply response"""
    return {
        "action": "reply",
        "replies": [message],
        "session_id": session_id
    }

def send_transfer(session_id: str, conversation_history: str) -> Dict:
    """Send transfer response"""
    return {
        "action": "transfer",
        "transfer_to": "human_agent",
        "session_id": session_id,
        "conversation_history": conversation_history,
        "replies": ["Connecting you with a support agent..."]
    }
```

---

## Common Issues & Solutions

### Issue 1: Session ID Not Found

**Problem**: `session_id` is None or 'unknown'

**Solution**: Ensure SalesIQ is sending one of these fields:
- `session_id`
- `visitor.active_conversation_id`
- `visitor.id`

**Debug**:
```python
logger.debug(f"Request: {request}")
logger.info(f"Session ID: {session_id}")
```

---

### Issue 2: Message Text Not Extracted

**Problem**: `message_text` is empty

**Solution**: Check message format:
```python
# Debug
logger.debug(f"Message object: {message_obj}")
logger.debug(f"Message type: {type(message_obj)}")
logger.info(f"Message text: {message_text}")
```

---

### Issue 3: Response Not Appearing in SalesIQ

**Problem**: Bot responds but message doesn't appear in widget

**Solution**: Verify response format:
```python
# Must have these fields:
response = {
    "action": "reply",           # Required
    "replies": [message],        # Required (array)
    "session_id": session_id     # Required (must match request)
}
```

---

### Issue 4: Transfer Not Working

**Problem**: Transfer response doesn't transfer to agent

**Solution**: Verify transfer response format:
```python
response = {
    "action": "transfer",                    # Must be "transfer"
    "transfer_to": "human_agent",            # Must be "human_agent"
    "session_id": session_id,                # Must match request
    "conversation_history": history_text,   # Include full history
    "replies": ["Connecting..."]             # Include message
}
```

---

## Validation Checklist

- [ ] Request has `session_id` or `visitor.id`
- [ ] Request has `message.text`
- [ ] Response has `action` field
- [ ] Response has `replies` array
- [ ] Response has `session_id` matching request
- [ ] Response is valid JSON
- [ ] No extra fields that break SalesIQ
- [ ] All strings are properly escaped
- [ ] Arrays are properly formatted

---

## Summary

**Request Format**:
```json
{
  "session_id": "...",
  "message": {"text": "..."},
  "visitor": {"id": "...", "name": "...", "email": "..."}
}
```

**Response Format**:
```json
{
  "action": "reply",
  "replies": ["..."],
  "session_id": "..."
}
```

**Key Points**:
- Always include `session_id` in response
- Always use `replies` as an array
- Use `action: "reply"` for normal responses
- Use `action: "transfer"` for agent transfers
- Keep response format consistent

