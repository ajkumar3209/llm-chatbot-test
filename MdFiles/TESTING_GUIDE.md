# Testing Guide: System Prompt & Escalation Options

## Overview

This guide explains how to test:
1. **System Prompt** - Top 10 resolution steps
2. **3 Escalation Options** - Instant Chat, Callback, Ticket
3. **API Integration** - Proper response formats

---

## Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Start the Bot Locally
```bash
python fastapi_chatbot_hybrid.py
```

You should see:
```
ACE CLOUD HOSTING - SUPPORT BOT (HYBRID LLM)
🚀 Starting FastAPI server on port 8000...
📍 Endpoint: http://0.0.0.0:8000
📖 Docs: http://0.0.0.0:8000/docs
✅ Ready to receive webhooks from n8n!
```

---

## Comprehensive Testing

### Run All Tests
```bash
python test_bot_comprehensive.py
```

This runs 9 tests covering:
1. Health check
2. Bot greeting
3. QuickBooks frozen issue
4. Password reset issue
5. Escalation - Instant Chat
6. Escalation - Schedule Callback
7. Escalation - Create Ticket
8. Email/O365 issue
9. Low disk space issue

---

## Manual Testing

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "openai": "connected",
  "active_sessions": 0
}
```

### Test 2: QuickBooks Frozen Issue

**Message 1: User reports QB frozen**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-qb-001",
    "message": {"text": "My QuickBooks is frozen"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Are you using a dedicated server or a shared server?"],
  "session_id": "test-qb-001"
}
```

**Message 2: User specifies server type**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-qb-001",
    "message": {"text": "Dedicated server"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Step 1: Right click and open Task Manager on the server..."],
  "session_id": "test-qb-001"
}
```

### Test 3: Password Reset Issue

**Message 1: User asks about password reset**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-pwd-001",
    "message": {"text": "I need to reset my password"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Are you enrolled in the Selfcare Portal?"],
  "session_id": "test-pwd-001"
}
```

**Message 2: User says they are enrolled**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-pwd-001",
    "message": {"text": "Yes, I'm enrolled"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Step 1: Go to selfcare.acecloudhosting.com..."],
  "session_id": "test-pwd-001"
}
```

### Test 4: Escalation - Instant Chat

**Message 1: User reports issue**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-chat-001",
    "message": {"text": "My server is not responding"},
    "visitor": {"id": "user-123"}
  }'
```

**Message 2: User says not resolved**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-chat-001",
    "message": {"text": "Still not working"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["I understand this is frustrating. Here are 3 ways I can help:\n\n1. **Instant Chat** - Connect with a human agent now\n2. **Schedule Callback** - We'll call you back at a convenient time\n3. **Create Support Ticket** - We'll create a detailed ticket and follow up"],
  "session_id": "test-esc-chat-001"
}
```

**Message 3: User selects Instant Chat (Option 1)**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-chat-001",
    "message": {"text": "option 1"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "test-esc-chat-001",
  "conversation_history": "User: My server is not responding\nBot: ...\nUser: Still not working\nBot: ...",
  "replies": ["Connecting you with a support agent..."]
}
```

**Key Points:**
- ✅ Action is "transfer"
- ✅ transfer_to is "human_agent"
- ✅ conversation_history includes full chat
- ✅ Conversation continues with agent

### Test 5: Escalation - Schedule Callback

**Message 1-2: Same as above (report issue, say not resolved)**

**Message 3: User selects Schedule Callback (Option 2)**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-callback-001",
    "message": {"text": "option 2"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a callback request for you...\n\nPlease provide:\n1. Your preferred time\n2. Your phone number\n\nOur support team will call you back..."],
  "session_id": "test-esc-callback-001"
}
```

**Key Points:**
- ✅ Action is "reply" (not transfer)
- ✅ Chat auto-closes (session cleared)
- ✅ Ticket created automatically
- ✅ Support team calls user

**Verify Auto-Close:**
```bash
# Send another message to same session
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-callback-001",
    "message": {"text": "Hello again"},
    "visitor": {"id": "user-123"}
  }'
```

Expected: New conversation starts (greeting message)

### Test 6: Escalation - Create Support Ticket

**Message 1-2: Same as above (report issue, say not resolved)**

**Message 3: User selects Create Ticket (Option 3)**
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-ticket-001",
    "message": {"text": "option 3"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a support ticket for you...\n\nPlease provide:\n1. Your name\n2. Your email\n3. Your phone number\n4. Brief description\n\nA ticket has been created..."],
  "session_id": "test-esc-ticket-001"
}
```

**Key Points:**
- ✅ Action is "reply" (not transfer)
- ✅ Chat auto-closes (session cleared)
- ✅ Ticket created automatically
- ✅ Support team emails user

**Verify Auto-Close:**
```bash
# Send another message to same session
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-esc-ticket-001",
    "message": {"text": "Hello again"},
    "visitor": {"id": "user-123"}
  }'
```

Expected: New conversation starts (greeting message)

---

## Expected Test Results

### System Prompt Tests
- ✅ QuickBooks frozen - Bot asks about server type
- ✅ Password reset - Bot asks about Selfcare enrollment
- ✅ Email issue - Bot provides troubleshooting steps
- ✅ Disk space - Bot provides cleanup steps

### Escalation Tests
- ✅ Instant Chat - Returns "transfer" action with conversation history
- ✅ Schedule Callback - Returns "reply" action, auto-closes chat
- ✅ Create Ticket - Returns "reply" action, auto-closes chat

### API Integration Tests
- ✅ All responses have correct JSON format
- ✅ session_id is preserved
- ✅ conversation_history is included for transfers
- ✅ replies array contains bot messages

---

## Troubleshooting

### Issue: Bot not responding
```bash
# Check if bot is running
curl http://localhost:8000/health

# Check logs in terminal where bot is running
# Look for error messages
```

### Issue: Wrong response format
```bash
# Verify response structure
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": {"text": "hello"}, "visitor": {"id": "user"}}' \
  | python -m json.tool
```

### Issue: Escalation not working
```bash
# Check that session_id is consistent
# Check that "option 1/2/3" is recognized
# Check logs for error messages
```

### Issue: Auto-close not working
```bash
# Verify that conversation history is cleared
# Send message to same session_id
# Should get greeting, not continuation
```

---

## Success Criteria

### System Prompt
- ✅ Bot recognizes all 10 issue types
- ✅ Bot asks clarifying questions when needed
- ✅ Bot provides step-by-step guidance
- ✅ Bot gives one step at a time

### Escalation - Instant Chat
- ✅ Returns "transfer" action
- ✅ Includes full conversation history
- ✅ transfer_to is "human_agent"
- ✅ Conversation continues with agent

### Escalation - Schedule Callback
- ✅ Returns "reply" action
- ✅ Confirms callback request
- ✅ Auto-closes chat (session cleared)
- ✅ Ticket created automatically

### Escalation - Create Ticket
- ✅ Returns "reply" action
- ✅ Confirms ticket creation
- ✅ Auto-closes chat (session cleared)
- ✅ Ticket created automatically

---

## Next Steps

1. **Run comprehensive tests**: `python test_bot_comprehensive.py`
2. **Review test results**: Check for any failures
3. **Fix any issues**: Update code if needed
4. **Deploy to Railway**: Push to production
5. **Monitor in production**: Track metrics

---

**Status**: Ready for Testing
**Confidence**: HIGH
