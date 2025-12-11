# Payload Validation Guide

## Quick Validation

### ✅ Valid Request Payloads

Your bot accepts all these formats:

**Format 1: Minimal (Required fields only)**
```json
{
  "session_id": "sess_123",
  "message": {"text": "hello"}
}
```

**Format 2: With visitor info**
```json
{
  "session_id": "sess_123",
  "message": {"text": "hello"},
  "visitor": {"id": "user_123"}
}
```

**Format 3: Complete (All fields)**
```json
{
  "session_id": "sess_123",
  "chat_id": "chat_123",
  "message": {"text": "hello", "type": "text"},
  "visitor": {
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "active_conversation_id": "conv_123"
  },
  "timestamp": "2025-12-03T10:30:00Z"
}
```

**Format 4: Alternative session ID**
```json
{
  "chat_id": "chat_123",
  "message": {"text": "hello"},
  "visitor": {"active_conversation_id": "conv_123"}
}
```

---

## ✅ Valid Response Formats

### Reply Response (Standard)
```json
{
  "action": "reply",
  "replies": ["Your message here"],
  "session_id": "sess_123"
}
```

### Reply Response (Multiple messages)
```json
{
  "action": "reply",
  "replies": [
    "First message",
    "Second message"
  ],
  "session_id": "sess_123"
}
```

### Transfer Response
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "sess_123",
  "conversation_history": "User: hello\nBot: Hi there",
  "replies": ["Connecting you with an agent..."]
}
```

---

## ❌ Invalid Payloads (Bot Handles Gracefully)

### Missing session_id
```json
{
  "message": {"text": "hello"}
}
```
**Bot handles**: Uses 'unknown' as session_id, still responds

### Missing message text
```json
{
  "session_id": "sess_123",
  "message": {}
}
```
**Bot handles**: Sends greeting message

### Empty message
```json
{
  "session_id": "sess_123",
  "message": {"text": ""}
}
```
**Bot handles**: Sends greeting message

### Null message
```json
{
  "session_id": "sess_123",
  "message": null
}
```
**Bot handles**: Sends greeting message

### String message (not object)
```json
{
  "session_id": "sess_123",
  "message": "hello"
}
```
**Bot handles**: Extracts text correctly

---

## Testing Payloads

### Test 1: Minimal Valid Payload

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_001",
    "message": {"text": "hello"}
  }'
```

**Expected**: 200 OK with reply

---

### Test 2: Complete Valid Payload

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_002",
    "chat_id": "chat_002",
    "message": {
      "text": "QuickBooks is frozen",
      "type": "text"
    },
    "visitor": {
      "id": "user_002",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "555-1234",
      "active_conversation_id": "conv_002"
    },
    "timestamp": "2025-12-03T10:30:00Z"
  }'
```

**Expected**: 200 OK with reply about QuickBooks

---

### Test 3: Missing session_id (Bot Handles)

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "message": {"text": "hello"},
    "visitor": {"id": "user_003"}
  }'
```

**Expected**: 200 OK with reply (session_id will be 'user_003')

---

### Test 4: Empty Message (Bot Handles)

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_004",
    "message": {"text": ""}
  }'
```

**Expected**: 200 OK with greeting

---

### Test 5: Null Message (Bot Handles)

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_005",
    "message": null
  }'
```

**Expected**: 200 OK with greeting

---

### Test 6: String Message (Bot Handles)

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_006",
    "message": "hello"
  }'
```

**Expected**: 200 OK with reply

---

### Test 7: Escalation - Option 1

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_007",
    "message": {"text": "option 1"},
    "visitor": {"id": "user_007"}
  }'
```

**Expected**: 200 OK with transfer action

---

### Test 8: Escalation - Option 2

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_008",
    "message": {"text": "option 2"},
    "visitor": {"id": "user_008"}
  }'
```

**Expected**: 200 OK with reply about callback

---

### Test 9: Escalation - Option 3

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_009",
    "message": {"text": "option 3"},
    "visitor": {"id": "user_009"}
  }'
```

**Expected**: 200 OK with reply about ticket

---

## Response Validation

### ✅ Valid Response

```json
{
  "action": "reply",
  "replies": ["Your message"],
  "session_id": "test_001"
}
```

**Checks**:
- [ ] `action` is "reply" or "transfer"
- [ ] `replies` is an array
- [ ] `session_id` matches request
- [ ] All strings are properly escaped
- [ ] Valid JSON format

### ❌ Invalid Response (Bot Won't Send)

```json
{
  "action": "reply",
  "reply": "Your message",
  "session_id": "test_001"
}
```

**Problem**: `reply` should be `replies` (array)

---

## Debugging Payloads

### Enable Debug Logging

```python
# In fastapi_chatbot_hybrid.py
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

### Check Logs

```bash
# Local
# Look at terminal output for [SalesIQ] DEBUG messages

# Railway
railway logs --follow | grep DEBUG
```

### Log Output Example

```
[SalesIQ] Webhook received
[SalesIQ] Request payload: {'session_id': 'test_001', 'message': {'text': 'hello'}, ...}
[SalesIQ] Session ID: test_001
[SalesIQ] Message: hello
[SalesIQ] Response generated: Hello! How can I assist you today?
```

---

## Payload Size Limits

### Request Limits
- Max message length: 10,000 characters
- Max visitor name: 255 characters
- Max email: 255 characters
- Max phone: 20 characters

### Response Limits
- Max reply length: 4,096 characters per message
- Max replies array: 10 messages
- Max conversation history: 50,000 characters

---

## Common Payload Issues

### Issue 1: Invalid JSON

**Problem**: Malformed JSON in request

**Solution**: Validate JSON before sending
```bash
# Validate JSON
echo '{"session_id": "test"}' | jq .
```

---

### Issue 2: Missing Quotes

**Problem**: Unquoted strings in JSON

**Example (Invalid)**:
```json
{
  session_id: test,
  message: {text: hello}
}
```

**Solution**: Quote all strings
```json
{
  "session_id": "test",
  "message": {"text": "hello"}
}
```

---

### Issue 3: Wrong Data Types

**Problem**: String instead of object for message

**Example (Invalid)**:
```json
{
  "session_id": "test",
  "message": "hello"
}
```

**Solution**: Use object format
```json
{
  "session_id": "test",
  "message": {"text": "hello"}
}
```

**Note**: Bot handles this gracefully

---

### Issue 4: Special Characters

**Problem**: Unescaped special characters

**Example (Invalid)**:
```json
{
  "session_id": "test",
  "message": {"text": "It's not working"}
}
```

**Solution**: Escape quotes
```json
{
  "session_id": "test",
  "message": {"text": "It's not working"}
}
```

**Note**: Single quotes don't need escaping in JSON

---

### Issue 5: Unicode Characters

**Problem**: Non-ASCII characters

**Example (Valid)**:
```json
{
  "session_id": "test",
  "message": {"text": "Café is closed"}
}
```

**Solution**: UTF-8 encoding (automatic in most tools)

---

## Validation Checklist

### Before Sending Request
- [ ] JSON is valid (use `jq` or online validator)
- [ ] All strings are quoted
- [ ] All special characters are escaped
- [ ] `session_id` is present (or `visitor.id`)
- [ ] `message.text` is present
- [ ] No trailing commas
- [ ] Proper nesting of objects/arrays

### After Receiving Response
- [ ] Response is valid JSON
- [ ] `action` field is present
- [ ] `replies` is an array
- [ ] `session_id` matches request
- [ ] HTTP status is 200
- [ ] No error messages in response

---

## Quick Test Script

```bash
#!/bin/bash

# Test 1: Basic message
echo "Test 1: Basic message"
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_1", "message": {"text": "hello"}}'
echo ""

# Test 2: QuickBooks issue
echo "Test 2: QuickBooks issue"
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_2", "message": {"text": "QuickBooks frozen"}}'
echo ""

# Test 3: Escalation
echo "Test 3: Escalation"
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_3", "message": {"text": "option 1"}}'
echo ""

# Test 4: Health check
echo "Test 4: Health check"
curl http://localhost:8000/health
echo ""
```

---

## Summary

**Your bot accepts**:
- ✅ Minimal payloads (session_id + message.text)
- ✅ Complete payloads (all fields)
- ✅ Alternative session ID formats
- ✅ Multiple message formats
- ✅ Missing optional fields

**Your bot returns**:
- ✅ Valid JSON responses
- ✅ Correct action field
- ✅ Replies as array
- ✅ Matching session_id
- ✅ Graceful error handling

**Validation**:
- ✅ All payloads tested
- ✅ All edge cases handled
- ✅ Full logging enabled
- ✅ Ready for production

