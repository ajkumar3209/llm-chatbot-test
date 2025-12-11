# Quick Test Guide - 5 Minutes

## Start the Bot

### Terminal 1: Start Bot
```bash
export OPENAI_API_KEY=sk-proj-your-key-here
python fastapi_chatbot_hybrid.py
```

Wait for:
```
✅ Ready to receive webhooks from n8n!
```

---

## Run Tests

### Terminal 2: Run Comprehensive Tests
```bash
python test_bot_comprehensive.py
```

This will run 9 tests automatically and show results.

---

## Manual Quick Tests (If Automated Tests Fail)

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: QuickBooks Issue
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-1",
    "message": {"text": "My QuickBooks is frozen"},
    "visitor": {"id": "user-1"}
  }'
```

Expected: Bot asks about server type (dedicated or shared)

### Test 3: Escalation - Instant Chat
```bash
# First message
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-2",
    "message": {"text": "My server is not responding"},
    "visitor": {"id": "user-2"}
  }'

# Second message - not resolved
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-2",
    "message": {"text": "Still not working"},
    "visitor": {"id": "user-2"}
  }'

# Third message - select option 1
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-2",
    "message": {"text": "option 1"},
    "visitor": {"id": "user-2"}
  }'
```

Expected: Response with `"action": "transfer"` and `"transfer_to": "human_agent"`

### Test 4: Escalation - Schedule Callback
```bash
# First message
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-3",
    "message": {"text": "I can'\''t access my account"},
    "visitor": {"id": "user-3"}
  }'

# Second message - not resolved
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-3",
    "message": {"text": "Still not working"},
    "visitor": {"id": "user-3"}
  }'

# Third message - select option 2
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-3",
    "message": {"text": "option 2"},
    "visitor": {"id": "user-3"}
  }'
```

Expected: Response with `"action": "reply"` and chat auto-closes

### Test 5: Escalation - Create Ticket
```bash
# First message
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-4",
    "message": {"text": "My email is not working"},
    "visitor": {"id": "user-4"}
  }'

# Second message - not resolved
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-4",
    "message": {"text": "Still not working"},
    "visitor": {"id": "user-4"}
  }'

# Third message - select option 3
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-4",
    "message": {"text": "option 3"},
    "visitor": {"id": "user-4"}
  }'
```

Expected: Response with `"action": "reply"` and chat auto-closes

---

## What to Check

### System Prompt Tests
- ✅ QB frozen: Bot asks about server type
- ✅ Password reset: Bot asks about Selfcare enrollment
- ✅ Email issue: Bot provides troubleshooting steps
- ✅ Disk space: Bot provides cleanup steps

### Escalation Tests
- ✅ Instant Chat: `"action": "transfer"` with conversation history
- ✅ Schedule Callback: `"action": "reply"` and chat auto-closes
- ✅ Create Ticket: `"action": "reply"` and chat auto-closes

### API Integration
- ✅ All responses have correct JSON format
- ✅ session_id is preserved
- ✅ conversation_history included for transfers
- ✅ replies array contains bot messages

---

## Expected Results

### All Tests Pass ✅
```
PASS - Health Check
PASS - Bot Greeting
PASS - QuickBooks Frozen
PASS - Password Reset
PASS - Escalation - Instant Chat
PASS - Escalation - Schedule Callback
PASS - Escalation - Create Ticket
PASS - Email/O365 Issue
PASS - Low Disk Space Issue

Total: 9/9 tests passed
Success rate: 100%
```

### If Tests Fail ❌
1. Check bot is running: `curl http://localhost:8000/health`
2. Check OPENAI_API_KEY is set
3. Check logs in bot terminal
4. Review error messages
5. Fix and retry

---

## Next Steps

1. ✅ Run tests
2. ✅ Verify all pass
3. ✅ Deploy to Railway
4. ✅ Monitor in production

---

**Time**: ~5 minutes
**Confidence**: HIGH
