# ⚡ Railway Test - 5 Hour Quick Deploy Guide

## 🚀 Step 1: Deploy (2 minutes)

Choose ONE method:

### Method A: Git Push (if Railway is linked to GitHub)
```powershell
git add llm_chatbot.py
git commit -m "Fix: @dataclass ClassificationResult"
git push
```

### Method B: Railway CLI
```powershell
railway login
railway link
railway up
```

### Method C: Manual - Edit in Dashboard
1. Go to https://railway.app
2. Open your project
3. Paste new `llm_chatbot.py` content
4. Deploy button appears automatically

---

## ⏱️ Step 2: Wait for Build (5 minutes)

- Go to Railway dashboard
- Click Deployments tab
- Wait for green checkmark
- Check Logs for: **"Expert prompt loaded successfully"**

---

## ✅ Step 3: Test (2 minutes)

### Option A: Run Python Test Script
```powershell
python test_railway.py
```

### Option B: Manual Test
```powershell
$url = "https://your-app.up.railway.app/health"
curl $url  # Should return {"status":"healthy",...}
```

### Option C: Open Chat Widget
1. Go to your SalesIQ chat widget
2. Send: "hi i am alice"
3. Should get LLM response (NOT "technical difficulties")

---

## 📊 What You're Testing

| Test | Expected | Bad Sign |
|------|----------|----------|
| **Greeting** | "Hi! I'm AceBuddy..." | Empty message |
| **User message** | LLM response with help | "experiencing technical difficulties" |
| **Logs** | No ClassificationResult errors | Exception in stderr |
| **Response time** | < 5 seconds | Timeout or 500 error |

---

## 🐛 Troubleshooting

### Build Failed
```
❌ Check: Python syntax errors
❌ Check: requirements.txt is valid
✅ Our fix shouldn't cause build errors
```

### Chat returns error message
```
❌ ClassificationResult fix didn't deploy
✅ Solution: Redeploy llm_chatbot.py
```

### Service won't start
```
❌ Check: OPENROUTER_API_KEY is set
❌ Check: All required env vars exist
```

---

## 📝 Files You Need

- ✅ `llm_chatbot.py` - Already fixed with @dataclass
- ✅ `requirements.txt` - No changes needed
- ✅ `Procfile` - No changes needed
- ✅ `railway.json` - No changes needed

---

## 🎯 Success Criteria

✅ All of these must be true:

1. Railway build succeeds (green checkmark)
2. Service shows "healthy" status
3. Chat widget greeting works
4. Message "hi i am alice" gets LLM response
5. No error messages in logs
6. Response time < 5 seconds

---

## ⏳ Timeline

```
0 min   - Run deployment command
0-2 min - Push to Railway
2-5 min - Build in progress
5-10 min - Service restarts
10+ min - Ready for testing
```

---

## 🔗 Useful Links

- Railway Dashboard: https://railway.app
- Your Project Logs: https://railway.app/project/[YOUR_ID]
- Health Endpoint: https://your-app.up.railway.app/health

---

## 📞 If Test Fails

Before office (5 hours):
1. ✅ Verify llm_chatbot.py has @dataclass on ClassificationResult
2. ✅ Check OPENROUTER_API_KEY is set in Railway env vars
3. ✅ Redeploy if needed (git push)
4. ✅ Run test script again

At office (after network access):
1. SSH to production server
2. Check logs for actual error messages
3. Deploy to production with `deploy_fix.ps1`

---

**Good luck! You've got this! 🚀**
