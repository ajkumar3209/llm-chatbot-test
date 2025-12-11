# Troubleshooting: "No Proper Response in Message Handler" Error

## Problem

You're seeing "no proper response in message handler error" in SalesIQ chat widget when the bot tries to respond.

---

## Root Causes & Solutions

### 1. Webhook Response Format Mismatch

**Symptom**: Bot responds but SalesIQ doesn't recognize the format

**Solution**:
Ensure response format is exactly:
```json
{
  "action": "reply",
  "replies": ["Your message here"],
  "session_id": "session-id-here"
}
```

OR for transfers:
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "session-id-here",
  "conversation_history": "...",
  "replies": ["Connecting you with a support agent..."]
}
```

**Check**: Look at bot logs to verify response format

---

### 2. Exception in Bot Code

**Symptom**: Bot crashes silently, SalesIQ shows error

**Solution**:
1. Check Railway logs:
   ```bash
   railway logs
   ```

2. Look for error messages like:
   - `KeyError: 'message'`
   - `AttributeError: 'NoneType'`
   - `OpenAI API error`

3. Fix the specific error

**Common errors**:
- Missing `message` field in webhook payload
- Invalid OpenAI API key
- Conversation history not initialized

---

### 3. Missing Environment Variables

**Symptom**: Bot starts but crashes on first message

**Solution**:
Verify all environment variables are set:
```bash
# Check local
cat .env

# Check Railway
railway variables
```

Required variables:
- `OPENAI_API_KEY` ✅
- `SALESIQ_API_KEY` (optional, will simulate if missing)
- `SALESIQ_DEPARTMENT_ID` (optional, will simulate if missing)
- `DESK_OAUTH_TOKEN` (optional, will simulate if missing)
- `DESK_ORGANIZATION_ID` (optional, will simulate if missing)

---

### 4. OpenAI API Error

**Symptom**: Bot responds with "I'm having technical difficulties"

**Solution**:
1. Verify OpenAI API key is valid:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. Check OpenAI account has credits
3. Check API rate limits not exceeded
4. Verify model `gpt-4o-mini` is available

---

### 5. Webhook URL Not Configured

**Symptom**: SalesIQ doesn't send messages to bot

**Solution**:
1. Go to SalesIQ Settings → Webhooks
2. Verify webhook URL is correct:
   - Local: `http://localhost:8000/webhook/salesiq`
   - Railway: `https://your-railway-url.railway.app/webhook/salesiq`
3. Verify webhook is enabled
4. Test webhook with curl:
   ```bash
   curl -X POST http://localhost:8000/webhook/salesiq \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test", "message": {"text": "hello"}, "visitor": {"id": "user-1"}}'
   ```

---

### 6. Message Parsing Error

**Symptom**: Bot receives message but can't parse it

**Solution**:
The bot now handles multiple message formats:
- `{"text": "message"}` ✅
- `"message"` ✅
- `{"content": "message"}` ✅

If still failing, check webhook payload format from SalesIQ

---

## Debug Steps

### Step 1: Check Bot is Running

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

### Step 2: Test Webhook Directly

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "debug-001",
    "message": {"text": "hello"},
    "visitor": {"id": "user-debug"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Hello! How can I assist you today?"],
  "session_id": "debug-001"
}
```

### Step 3: Check Logs

**Local**:
```bash
# Terminal where bot is running
# Look for [SalesIQ] messages
```

**Railway**:
```bash
railway logs --follow
```

Look for:
- `[SalesIQ] Webhook received` ✅
- `[SalesIQ] Session ID: ...` ✅
- `[SalesIQ] Message: ...` ✅
- `[SalesIQ] Response generated: ...` ✅
- `[SalesIQ] ERROR: ...` ❌

### Step 4: Test Each Escalation Option

```bash
# Test Instant Chat
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "message": {"text": "option 1"},
    "visitor": {"id": "user-1"}
  }'

# Test Callback
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-002",
    "message": {"text": "option 2"},
    "visitor": {"id": "user-2"}
  }'

# Test Ticket
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-003",
    "message": {"text": "option 3"},
    "visitor": {"id": "user-3"}
  }'
```

---

## Quick Fixes

### Fix 1: Restart Bot

```bash
# Local
Ctrl+C
python fastapi_chatbot_hybrid.py

# Railway
railway restart
```

### Fix 2: Clear Sessions

```bash
curl -X POST http://localhost:8000/reset/all
```

### Fix 3: Update Code

```bash
# Pull latest changes
git pull

# Reinstall dependencies
pip install -r requirements.txt

# Restart bot
python fastapi_chatbot_hybrid.py
```

### Fix 4: Check Logs for Specific Error

```bash
# Railway
railway logs | grep ERROR

# Local
# Look at terminal output for [SalesIQ] ERROR
```

---

## Common Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `KeyError: 'message'` | Missing message field | Check webhook payload format |
| `AttributeError: 'NoneType'` | Null value accessed | Check environment variables |
| `OpenAI API error: 401` | Invalid API key | Update OPENAI_API_KEY |
| `OpenAI API error: 429` | Rate limit exceeded | Wait and retry |
| `Connection refused` | Bot not running | Start bot: `python fastapi_chatbot_hybrid.py` |
| `Timeout` | Bot taking too long | Check OpenAI API status |

---

## Verification Checklist

- [ ] Bot is running: `curl http://localhost:8000/health`
- [ ] OpenAI API key is valid
- [ ] Webhook URL is correct in SalesIQ
- [ ] Environment variables are set
- [ ] Test webhook works: `curl -X POST http://localhost:8000/webhook/salesiq ...`
- [ ] Logs show `[SalesIQ] Webhook received`
- [ ] Response format is correct JSON
- [ ] No exceptions in logs

---

## Still Having Issues?

1. Check Railway logs: `railway logs --follow`
2. Run test suite: `python test_bot_comprehensive.py`
3. Test webhook directly with curl
4. Verify all environment variables
5. Check OpenAI API status: https://status.openai.com

If still stuck, contact support with:
- Error message from logs
- Webhook payload you're sending
- Expected vs actual response

