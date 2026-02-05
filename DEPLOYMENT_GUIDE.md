# Production Deployment & Testing Guide

## Quick Start

### Step 1: Deploy to Production Server
```bash
cd /path/to/refactored/code
bash deploy_to_prod.sh
```

This script will:
- ✅ Validate local files
- ✅ Check Python syntax
- ✅ Create automatic backup
- ✅ Copy files to production
- ✅ Restart the service with rollback capability

### Step 2: Run Test Suite
```bash
python3 test_responses.py
```

This will test:
- 🧪 Natural language variations (password reset)
- 🧪 Account access issues
- 🧪 Technical support requests
- 🧪 Escalation requests
- 🧪 Billing questions
- 🧪 General inquiries
- 🧪 Greetings

### Step 3: Monitor Real-Time Logs
```bash
python3 monitor_logs.py
```

This will show:
- 📊 LLM classification metrics
- 📊 API transfer success rates
- 📊 Response time statistics
- 📊 Error tracking
- 📊 Intent distribution

---

## Pre-Deployment Checklist

### ✅ Local Validation
```bash
# 1. Check Python syntax
python3 -m py_compile llm_chatbot.py
python3 -m py_compile zoho_api_simple.py

# 2. Run quick import test
python3 -c "import llm_chatbot; print('✓ Imports successful')"
```

### ✅ Production Server Verification
```bash
ssh ubuntu@acebuddy

# Check service status
sudo systemctl status llm-chatbot.service

# Check environment variables
env | grep -i salesiq
env | grep -i openrouter

# Check service is running
curl http://localhost:8000/

# Check logs for errors
sudo journalctl -u llm-chatbot.service -n 20 --no-pager
```

---

## Deployment Process

### Safe Deployment Steps

1. **Backup Current Version**
   ```bash
   ssh ubuntu@acebuddy "cd /opt/llm-chatbot && cp llm_chatbot.py llm_chatbot_backup_$(date +%Y%m%d_%H%M%S).py"
   ```

2. **Copy New Files**
   ```bash
   scp llm_chatbot.py ubuntu@acebuddy:/opt/llm-chatbot/
   scp zoho_api_simple.py ubuntu@acebuddy:/opt/llm-chatbot/
   ```

3. **Verify Syntax on Production**
   ```bash
   ssh ubuntu@acebuddy "cd /opt/llm-chatbot && python3 -m py_compile llm_chatbot.py"
   ```

4. **Restart Service**
   ```bash
   ssh ubuntu@acebuddy "sudo systemctl restart llm-chatbot.service"
   ```

5. **Wait for Startup**
   ```bash
   sleep 3
   ssh ubuntu@acebuddy "sudo systemctl status llm-chatbot.service --no-pager"
   ```

6. **Check Logs for Errors**
   ```bash
   ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service -n 30 --no-pager"
   ```

### Rollback Procedure (If needed)
```bash
ssh ubuntu@acebuddy

# Find the latest backup
ls -lh /opt/llm-chatbot/llm_chatbot_backup_*.py | tail -1

# Restore backup
cp /opt/llm-chatbot/llm_chatbot_backup_20260204_160000.py /opt/llm-chatbot/llm_chatbot.py

# Restart service
sudo systemctl restart llm-chatbot.service

# Verify
sudo systemctl status llm-chatbot.service --no-pager
```

---

## Testing Strategy

### Test 1: Natural Language Variations
**Goal**: Verify LLM correctly classifies intent regardless of phrasing

**Test Cases**:
```
"I forgot my password"
"Can't log in to my account"
"My credential doesn't work"
"I'm locked out of my server"
```

**Expected Result**: ✅ All should return password reset guidance

---

### Test 2: API Failure Handling
**Goal**: Verify bot handles API failures gracefully

**Test Cases**:
1. Disconnect network during transfer
2. Simulate API timeout
3. Invalid API credentials

**Expected Result**: ✅ Bot returns honest error message with contact info

---

### Test 3: Retry Logic
**Goal**: Verify transient failures are retried automatically

**Test Cases**:
1. Simulate transient 500 error
2. Simulate connection reset
3. Simulate timeout on first attempt

**Expected Result**: ✅ API call succeeds after retry, logs show retry attempt

---

### Test 4: Response Quality
**Goal**: Verify LLM responses are natural and contextual

**Test Cases**:
```
User: "I forgot my password"
Expected: Contextual guidance on password reset process

User: "My website is down"
Expected: Technical troubleshooting steps

User: "I need to speak with someone"
Expected: Escalation with success confirmation
```

**Expected Result**: ✅ Responses are natural, relevant, and helpful

---

## Performance Monitoring

### Key Metrics to Track

1. **Response Time**
   - Target: < 3 seconds per message
   - Monitor: Average, P95, P99 response times

2. **Classification Accuracy**
   - Monitor: Confidence scores
   - Alert: If average confidence < 0.7

3. **API Success Rate**
   - Target: > 99% success rate
   - Monitor: Failures and retries

4. **Error Rate**
   - Target: < 0.1% error rate
   - Monitor: Error types and frequency

### Monitoring Commands

```bash
# View last 50 log entries
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service -n 50 --no-pager"

# Follow live logs (Ctrl+C to exit)
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service -f --no-pager"

# Count recent errors
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep ERROR | wc -l"

# Show only LLM classifications
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep 'LLM\|Intent'"

# Check memory usage
ssh ubuntu@acebuddy "ps aux | grep '[l]lm_chatbot'"
```

---

## Troubleshooting

### Issue: Service won't start
```bash
# Check syntax error
ssh ubuntu@acebuddy "python3 -m py_compile /opt/llm-chatbot/llm_chatbot.py"

# Check service logs
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service -n 100 --no-pager"

# Check if port is in use
ssh ubuntu@acebuddy "sudo netstat -tulpn | grep 8000"

# Rollback to previous version
ssh ubuntu@acebuddy "cd /opt/llm-chatbot && cp llm_chatbot_backup_*.py llm_chatbot.py && sudo systemctl restart llm-chatbot.service"
```

### Issue: LLM not responding
```bash
# Check if OPENROUTER_API_KEY is set
ssh ubuntu@acebuddy "echo $OPENROUTER_API_KEY"

# Check logs for API errors
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service --since '5 minutes ago' | grep -i 'gemini\|openrouter'"

# Test API key manually
ssh ubuntu@acebuddy "curl -H 'Authorization: Bearer YOUR_KEY' https://openrouter.ai/api/v1/models"
```

### Issue: API transfers failing
```bash
# Check Zoho credentials
ssh ubuntu@acebuddy "env | grep -i salesiq"

# Check recent transfer attempts
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep -i 'transfer\|escalation'"

# Verify retry logic is working
ssh ubuntu@acebuddy "sudo journalctl -u llm-chatbot.service --since '1 hour ago' | grep 'Retry'"
```

---

## Sign-Off Checklist

After deployment and testing, verify:

- [ ] Service is running: `systemctl status llm-chatbot.service`
- [ ] No syntax errors in logs: `grep -i "syntaxerror" logs`
- [ ] LLM classifications working: `grep "\[LLM\] Intent" logs | head -10`
- [ ] API transfers working: `grep "Transfer successful" logs`
- [ ] Response times < 3s: `grep "elapsed" logs`
- [ ] No critical errors: `grep "CRITICAL" logs`
- [ ] Password reset responses correct
- [ ] Escalation requests handled properly
- [ ] Error handling works (disconnect test)
- [ ] All tests in test_responses.py pass

---

## Rollback Timeline

| Time Since Deployment | Action | Confidence |
|----------------------|--------|------------|
| < 5 minutes | Immediate rollback | High |
| 5-30 minutes | Review logs first, then rollback if needed | Medium |
| 30 minutes - 2 hours | Contact support, assess impact | Low |
| > 2 hours | Investigate issue before rollback | Very Low |

---

## Support & Escalation

### If deployment fails:
1. Check syntax: `python3 -m py_compile llm_chatbot.py`
2. Review logs: `sudo journalctl -u llm-chatbot.service -n 50`
3. Rollback: `cp llm_chatbot_backup_*.py llm_chatbot.py`
4. Restart: `sudo systemctl restart llm-chatbot.service`

### For ongoing issues:
- Monitor: `python3 monitor_logs.py`
- Test: `python3 test_responses.py`
- Debug: SSH into production and check logs manually

---

**Deployment Version**: 4.0 (LLM-First Edition)
**Last Updated**: February 2026
