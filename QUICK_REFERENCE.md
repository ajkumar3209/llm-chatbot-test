# ⚡ Quick Deployment Reference Card

## 3-Step Deployment Process

### Step 1️⃣ - Validate Locally (2 minutes)
```bash
cd /path/to/code
python validate_before_deploy.py
# Should show: ✅ READY FOR DEPLOYMENT!
```

### Step 2️⃣ - Deploy to Production (5 minutes)
```bash
bash deploy_to_prod.sh
# Should show: ✅ DEPLOYMENT SUCCESSFUL!
# Backup: llm_chatbot_backup_20260204_232017.py
```

### Step 3️⃣ - Test & Verify (10 minutes)
```bash
# Terminal 1: Monitor logs
python monitor_logs.py

# Terminal 2: Run tests
python test_responses.py
# Should show: ✅ PASSED for all tests
```

---

## What Changed (Summary)

| Component | Before | After |
|-----------|--------|-------|
| Intent Detection | 900 lines of keywords | 1 LLM call |
| Natural Language | Limited | Excellent |
| Error Handling | Silent failures | Try-catch + Retry |
| Response Time | Variable | < 3 seconds |
| Secrets | Hardcoded in code | Environment vars only |

---

## Testing Quick Reference

### Test #1: Password Reset
```
Send: "I forgot my password"
Expect: Guidance on password reset process
```

### Test #2: Escalation
```
Send: "Can I speak with someone?"
Expect: Transfer with success confirmation
```

### Test #3: Technical Support
```
Send: "My website is down"
Expect: Troubleshooting steps
```

### Test #4: API Failure
```
Disconnect network, try transfer
Expect: Honest error message with phone number
```

---

## Monitoring Commands (Bookmark These!)

### Health Check
```bash
ssh ubuntu@acebuddy
sudo systemctl status llm-chatbot.service
```

### View Logs (Last 20 lines)
```bash
ssh ubuntu@acebuddy
sudo journalctl -u llm-chatbot.service -n 20 --no-pager
```

### Follow Live Logs
```bash
ssh ubuntu@acebuddy
sudo journalctl -u llm-chatbot.service -f --no-pager
```

### Count Errors in Last Hour
```bash
ssh ubuntu@acebuddy
sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep ERROR | wc -l
```

### Check LLM Classifications
```bash
ssh ubuntu@acebuddy
sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep Intent
```

---

## Emergency Rollback (30 seconds)

If something goes wrong:

```bash
ssh ubuntu@acebuddy
cd /opt/llm-chatbot

# Find latest backup
ls -lh llm_chatbot_backup_*.py | tail -1

# Restore (copy filename from above)
cp llm_chatbot_backup_20260204_160000.py llm_chatbot.py

# Restart
sudo systemctl restart llm-chatbot.service

# Verify
sudo systemctl status llm-chatbot.service
```

---

## Success Indicators ✅

After deployment, you should see in logs:

```
✅ [LLM] Classifying intent for message
✅ [LLM] Intent: password_reset (confidence: 0.95)
✅ [SalesIQ] ✓ Transfer successful
✅ [Retry] ✓ API call succeeded on attempt 1
✅ Response generated in 1.2s
```

❌ You should NOT see:

```
❌ Syntax Error
❌ Missing module
❌ Hardcoded credential
❌ Unhandled exception
❌ Silent failure
```

---

## Contact Quick Links

| Need | Action |
|------|--------|
| Service won't start | Check syntax: `python3 -m py_compile llm_chatbot.py` |
| LLM not responding | Check API key: `echo $OPENROUTER_API_KEY` |
| Transfers failing | Check credentials: `env \| grep -i salesiq` |
| Emergency help | Call 1-888-415-5240 |
| Need to rollback | See "Emergency Rollback" above |

---

## Files You Need

```
✓ llm_chatbot.py          ← Main application (refactored)
✓ zoho_api_simple.py      ← API integration
✓ validate_before_deploy.py
✓ deploy_to_prod.sh       ← Run this to deploy
✓ test_responses.py       ← Run this to test
✓ monitor_logs.py         ← Run this to monitor
```

---

## Expected Results

### Response Time
- Target: < 3 seconds per message
- Average should be: 1-2 seconds

### Classification Accuracy
- Confidence scores should be > 0.8
- Intents should match user intent

### API Success Rate
- Transfers should succeed on first attempt
- If fail, retry should succeed (3 max retries)

### Error Rate
- Should be < 0.1%
- No unhandled exceptions
- All errors logged with context

---

**Version**: 4.0 (LLM-First Edition)  
**Deployment Date**: February 4, 2026  
**Status**: ✅ READY

Print this card and keep it handy during deployment! 🚀
