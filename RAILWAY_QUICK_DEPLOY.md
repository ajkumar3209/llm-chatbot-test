# 🚀 Quick Railway Deployment - 5 Hour Test

## Option 1: Direct Git Push (Fastest - 2 minutes)

```powershell
# Initialize git if not already done
git init
git remote add railway https://github.com/<your-repo>.git

# Or if already set up:
git add llm_chatbot.py
git commit -m "Fix: Add @dataclass decorator to ClassificationResult"
git push railway main
```

## Option 2: Using Railway CLI (5 minutes)

```powershell
# Install Railway CLI if not already installed
npm install -g @railway/cli
# or
winget install Railway.Railway

# Login to Railway
railway login

# Link to your existing project
railway link

# Deploy
railway up

# Check logs
railway logs -f
```

## Option 3: Manual Upload via Railway Dashboard (3 minutes)

1. Go to https://railway.app
2. Open your project "AceBuddy" or "llm-chatbot"
3. Upload/Replace `llm_chatbot.py` directly in the code editor
4. Deploy triggers automatically

## Option 4: Use Git GitHub (Most Reliable)

```powershell
# Push to your GitHub repo
git add llm_chatbot.py
git commit -m "Fix: Add @dataclass decorator to ClassificationResult"
git push origin main

# Railway will auto-deploy if GitHub integration is set up
```

## Verify Deployment

1. **Check Health Endpoint:**
   ```powershell
   $url = "https://your-railway-app.up.railway.app/health"
   curl $url
   # Should return: {"status":"healthy","mode":"production",...}
   ```

2. **Check Logs:**
   - Go to Railway dashboard → Logs tab
   - Look for: "Expert prompt loaded successfully"
   - Should NOT see any ClassificationResult errors

3. **Test Chat Widget:**
   - Open your SalesIQ chat widget
   - Send: "hi i am alice"
   - Should get LLM response (not error message)

## Environment Variables Needed on Railway

Make sure these are set in Railway dashboard:

```
OPENROUTER_API_KEY=sk-or-v1-...
SALESIQ_CLIENT_ID=1005.xxxxx
SALESIQ_CLIENT_SECRET=xxxxx
SALESIQ_REFRESH_TOKEN=1005.xxxxx
SALESIQ_DEPARTMENT_ID=xxxxx
SALESIQ_APP_ID=xxxxx
SALESIQ_SCREEN_NAME=rtdsportal
```

## Troubleshooting

### If build fails:
```
Check logs for:
- Python syntax errors (shouldn't have any now)
- Missing dependencies in requirements.txt
```

### If chat returns error:
```
Check Railway logs for:
- ClassificationResult instantiation errors (should be fixed)
- Gemini API key errors
- JSON parsing errors
```

### If UI says "Insufficient data":
```
This means the old issue. The fix should resolve it.
Check logs: grep "Webhook received" in logs
```

## Quick Test Commands

```powershell
# Test if service is up
Invoke-WebRequest -Uri "https://your-app.up.railway.app/health" | Select-Object StatusCode, Content

# Check if LLM is working
curl -X POST "https://your-app.up.railway.app/webhook/salesiq" `
  -H "Content-Type: application/json" `
  -d '{
    "handler": "SalesIQ",
    "request": {},
    "org_id": "test",
    "visitor": {"id": "alice", "name": "Alice", "email": "alice@test.com"},
    "chat": {"id": "chat123"},
    "message": {"text": "hi i am alice"}
  }'
```

## Expected Response

```json
{
  "action": "reply",
  "replies": ["[LLM-generated response about helping with account/billing/technical issue]"],
  "session_id": "alice"
}
```

## Timeline

- **0-2 min**: Push code to Railway
- **2-5 min**: Railway detects and starts build
- **5-10 min**: Build completes, service restarts
- **10+ min**: Start testing chat widget

## Success Indicators ✅

- [ ] Build succeeds (no Python syntax errors)
- [ ] Service starts (health endpoint returns 200)
- [ ] Chat widget shows greeting
- [ ] Message "hi i am alice" gets LLM response (not error)
- [ ] Logs show no ClassificationResult exceptions

---

**Run one of the deployment options above, then test the chat widget!**
