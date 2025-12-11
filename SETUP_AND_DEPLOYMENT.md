# Setup and Deployment Guide

## Overview

This guide walks you through setting up the Ace Cloud Hosting Support Bot with Zoho API integration.

**Status**: ✅ Ready for deployment
**Components**: 
- FastAPI bot with LLM (GPT-4o-mini)
- Zoho SalesIQ integration (Instant Chat)
- Zoho Desk integration (Callbacks & Tickets)

---

## Step 1: Get Zoho API Credentials

### For Zoho SalesIQ (Instant Chat)

1. Go to https://salesiq.zoho.com
2. Click **Settings** → **API**
3. Generate API Key
4. Get your **Department ID** from Settings → Departments
5. Save these values:
   - `SALESIQ_API_KEY`
   - `SALESIQ_DEPARTMENT_ID`

### For Zoho Desk (Callbacks & Tickets)

1. Go to https://desk.zoho.com
2. Click **Settings** → **API** → **OAuth Tokens**
3. Generate OAuth Token
4. Get your **Organization ID** from Settings → Organization
5. Save these values:
   - `DESK_OAUTH_TOKEN`
   - `DESK_ORGANIZATION_ID`

---

## Step 2: Update Environment Variables

### Local Development

Create or update `.env` file:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Zoho SalesIQ API (for Instant Chat transfers)
SALESIQ_API_KEY=your-salesiq-api-key-here
SALESIQ_DEPARTMENT_ID=your-salesiq-department-id-here

# Zoho Desk API (for Callback & Support Tickets)
DESK_OAUTH_TOKEN=your-desk-oauth-token-here
DESK_ORGANIZATION_ID=your-desk-organization-id-here

# Port (Railway sets this automatically)
PORT=8000
```

### Railway Deployment

1. Go to your Railway project
2. Click **Variables**
3. Add each environment variable:
   - `OPENAI_API_KEY`
   - `SALESIQ_API_KEY`
   - `SALESIQ_DEPARTMENT_ID`
   - `DESK_OAUTH_TOKEN`
   - `DESK_ORGANIZATION_ID`

---

## Step 3: Test Locally

### Start the Bot

```bash
python fastapi_chatbot_hybrid.py
```

Expected output:
```
======================================================================
ACE CLOUD HOSTING - SUPPORT BOT (HYBRID LLM)
======================================================================

🚀 Starting FastAPI server on port 8000...
📍 Endpoint: http://0.0.0.0:8000
📖 Docs: http://0.0.0.0:8000/docs

✅ Ready to receive webhooks from n8n!
======================================================================
```

### Run Tests

In a new terminal:

```bash
python test_bot_comprehensive.py
```

Expected output:
```
======================================================================
COMPREHENSIVE BOT TESTING SUITE
======================================================================
Start time: 2025-12-11 10:30:00
Base URL: http://localhost:8000

✓ Health Check
✓ Bot Greeting
✓ QuickBooks Frozen
✓ Password Reset
✓ Escalation - Instant Chat
✓ Escalation - Schedule Callback
✓ Escalation - Create Ticket
✓ Email/O365 Issue
✓ Low Disk Space Issue

======================================================================
TEST SUMMARY
======================================================================
✓ - Health Check
✓ - Bot Greeting
✓ - QuickBooks Frozen
✓ - Password Reset
✓ - Escalation - Instant Chat
✓ - Escalation - Schedule Callback
✓ - Escalation - Create Ticket
✓ - Email/O365 Issue
✓ - Low Disk Space Issue

======================================================================
Total: 9/9 tests passed
Success rate: 100.0%
End time: 2025-12-11 10:30:15
======================================================================
```

---

## Step 4: Test API Integration

### Test 1: Instant Chat Transfer

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-chat-001",
    "message": {"text": "My QuickBooks is frozen"},
    "visitor": {"id": "user-123"}
  }'
```

Then:

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-chat-001",
    "message": {"text": "Still not working"},
    "visitor": {"id": "user-123"}
  }'
```

Then:

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-chat-001",
    "message": {"text": "option 1"},
    "visitor": {"id": "user-123"}
  }'
```

Expected response:
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "test-chat-001",
  "conversation_history": "User: My QuickBooks is frozen\nBot: ...\nUser: Still not working\nBot: ...",
  "replies": ["Connecting you with a support agent..."]
}
```

### Test 2: Schedule Callback

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-callback-001",
    "message": {"text": "option 2"},
    "visitor": {"id": "user-456"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a callback request for you..."],
  "session_id": "test-callback-001"
}
```

### Test 3: Create Support Ticket

```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-ticket-001",
    "message": {"text": "option 3"},
    "visitor": {"id": "user-789"}
  }'
```

Expected response:
```json
{
  "action": "reply",
  "replies": ["Perfect! I'm creating a support ticket for you..."],
  "session_id": "test-ticket-001"
}
```

---

## Step 5: Deploy to Railway

### Option A: Using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Deploy
railway up
```

### Option B: Using Git Push

```bash
# Add Railway remote
git remote add railway https://git.railway.app/your-project.git

# Push to Railway
git push railway main
```

### Option C: Using Railway Dashboard

1. Go to https://railway.app
2. Click your project
3. Click **Deploy**
4. Select your GitHub repository
5. Click **Deploy**

---

## Step 6: Configure SalesIQ Webhook

1. Go to https://salesiq.zoho.com
2. Click **Settings** → **Webhooks**
3. Add new webhook:
   - **URL**: `https://your-railway-url.railway.app/webhook/salesiq`
   - **Event**: Message received
   - **Method**: POST
4. Click **Save**

---

## Step 7: Test in SalesIQ Widget

1. Go to your website with SalesIQ widget
2. Start a chat
3. Test each scenario:
   - **Scenario 1**: Ask about QuickBooks frozen
     - Bot asks about server type
     - Provide steps
     - Say "still not working"
     - Select "option 1" for instant chat
     - Should transfer to agent
   
   - **Scenario 2**: Ask about password reset
     - Bot asks about Selfcare enrollment
     - Provide steps
     - Say "still not working"
     - Select "option 2" for callback
     - Chat auto-closes
   
   - **Scenario 3**: Ask about email issue
     - Bot provides troubleshooting steps
     - Say "still not working"
     - Select "option 3" for ticket
     - Chat auto-closes

---

## Troubleshooting

### Issue: "No proper response in message handler error"

**Cause**: Webhook response format mismatch or exception in bot code

**Solution**:
1. Check Railway logs: `railway logs`
2. Verify response format matches SalesIQ expectations
3. Ensure all environment variables are set
4. Check OpenAI API key is valid

### Issue: API calls failing

**Cause**: Invalid API credentials or network issue

**Solution**:
1. Verify API credentials in `.env`
2. Check API credentials are correct in Zoho
3. Verify network connectivity
4. Check API rate limits

### Issue: Bot not responding

**Cause**: OpenAI API error or bot crashed

**Solution**:
1. Check OpenAI API key is valid
2. Check OpenAI account has credits
3. Check Railway logs for errors
4. Restart bot: `railway restart`

---

## Monitoring

### Check Bot Health

```bash
curl https://your-railway-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "openai": "connected",
  "active_sessions": 5
}
```

### View Logs

```bash
# Local
tail -f bot.log

# Railway
railway logs
```

### Monitor API Calls

Check Zoho SalesIQ and Desk dashboards for:
- Chat transfers
- Callback tickets
- Support tickets

---

## Files Overview

| File | Purpose |
|------|---------|
| `fastapi_chatbot_hybrid.py` | Main bot server with LLM and escalation logic |
| `zoho_api_integration.py` | Zoho SalesIQ and Desk API integration |
| `config.py` | Configuration settings |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (local) |
| `.env.example` | Example environment variables |
| `test_bot_comprehensive.py` | Automated test suite |

---

## Next Steps

1. ✅ Get Zoho API credentials
2. ✅ Update `.env` with credentials
3. ✅ Test locally with `test_bot_comprehensive.py`
4. ✅ Deploy to Railway
5. ✅ Configure SalesIQ webhook
6. ✅ Test in SalesIQ widget
7. ✅ Monitor and optimize

---

## Support

For issues or questions:
- Check logs: `railway logs`
- Review API documentation: https://www.zoho.com/desk/api/
- Contact Ace Cloud Hosting support: support@acecloudhosting.com

