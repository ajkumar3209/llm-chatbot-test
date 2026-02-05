# Production Status & Recent Changes
**Last Updated:** January 27, 2026  
**Current Status:** ✅ FULLY FUNCTIONAL  
**Live Server:** ubuntu@45.194.90.181:/opt/llm-chatbot

---

## ✅ FULLY WORKING FEATURES

### 1. Chat Transfer (Instant Chat Button)
- **How it works:** User clicks "📞 Instant Chat" → Bot transfers to agent via SalesIQ
- **API:** SalesIQ Visitor API - "forward" action
- **Token:** SALESIQ_VISITOR_ACCESS_TOKEN
- **Auto-refresh:** ✅ Yes (401/400 errors)
- **Status:** PRODUCTION READY
- **Last tested:** Jan 23, 2026

### 2. Callback Scheduling (Schedule Callback Button)
- **How it works:** User clicks "📅 Schedule Callback" → Bot asks for time & phone → Creates callback in Desk
- **APIs:** 
  - Desk Contacts API (get/create contact)
  - Desk Calls API (create callback)
- **Time parsing:** ✅ Handles "11:45pm today", "tomorrow at 2pm", etc. (IST timezone)
- **Subject line:** ✅ Shows actual issue (e.g., "Callback: login issue")
- **Phone extraction:** ✅ Properly parses "phone: 5544332211"
- **Auto-refresh:** ✅ Yes (401/400 errors)
- **Status:** PRODUCTION READY
- **Last tested:** Jan 23, 2026 ✅

### 3. Auto Chat Closure
- **How it works:** User says "issue is resolved" → Bot automatically closes chat in SalesIQ
- **API:** SalesIQ Chat Closure API - PUT /api/v2/{screen}/conversations/{id}/close
- **Auto-refresh:** ✅ Yes (401/400 errors)
- **Status:** PRODUCTION READY
- **Last tested:** Jan 22, 2026

### 4. LLM-Triggered Actions
- **How it works:** If LLM detects callback/transfer request → Bot automatically initiates (doesn't wait for button click)
- **Example:** User says "can you connect me to someone" → Bot creates callback without button
- **Status:** PRODUCTION READY
- **Last tested:** Jan 23, 2026

### 5. Token Auto-Refresh (All APIs)
- **SalesIQ APIs:** ✅ Auto-refresh on 400/401
- **Desk APIs:** ✅ Auto-refresh on 400/401
- **Mechanism:** OAuth refresh_token grant on error, automatic retry
- **Coverage:**
  - ✅ create_chat_session()
  - ✅ close_chat()
  - ✅ get_or_create_contact()
  - ✅ create_callback_ticket()
- **Status:** PRODUCTION READY
- **Last tested:** Jan 23, 2026

### 6. Memory Management
- **Cleanup job:** ✅ Runs every 15 minutes
- **Session timeout:** ✅ 30 minutes inactivity
- **Lifecycle:**
  - ✅ Delete after transfer/callback/resolution (immediate)
  - ✅ Delete after 30 min inactivity (cleanup job)
  - ✅ Protect active sessions (keeps updating last_activity)
- **Memory efficiency:** ~5-10 KB per conversation, 1000 users = ~10 MB
- **Status:** PRODUCTION READY
- **Last tested:** Jan 24, 2026

---

## 📝 RECENT CHANGES (Last 7 Days)

### **Jan 27, 2026**
- ✅ Established git-based workflow for tracking changes
- ✅ Documented all working features

### **Jan 23, 2026**
- ✅ **Fixed callback subject line** - Now shows actual issue instead of "Callback: test - None"
  - Changed: `"subject": f"Callback: {visitor_name} - {phone}"` 
  - To: `"subject": f"Callback: {issue_summary}"` (extracts from conversation)
  - Files: `zoho_api_simple_prod2.py` line 445-475

### **Jan 23, 2026**
- ✅ **Fixed time parsing for callbacks** - Handles IST timezone properly
  - Added: `python-dateutil` for parsing "11:45pm today", "tomorrow at 2pm"
  - Converts IST → UTC for API
  - Explicitly checks for "today"/"tomorrow" keywords
  - Files: `zoho_api_simple_prod2.py` line 387-415, `llm_chatbot_prod.py` line 989-1000

### **Jan 22, 2026**
- ✅ **Fixed regex error in phone/time extraction**
  - Issue: `re.error: bad character range \s-+ at position 28`
  - Fix: Escaped hyphen properly in regex pattern
  - Files: `llm_chatbot_prod.py` line 989-1000

### **Jan 22, 2026**
- ✅ **Removed duplicate callback creation**
  - Issue: Callbacks were created twice (from button handler AND LLM handler)
  - Fix: Disabled duplicate creation in LLM response handler
  - Files: `llm_chatbot_prod.py` line 1598-1625

### **Jan 22, 2026**
- ✅ **Improved callback description**
  - Changed from: Full conversation history (too verbose)
  - Changed to: Customer info + requested time + last 5 messages (concise)
  - Files: `zoho_api_simple_prod2.py` line 445-475

### **Jan 21, 2026**
- ✅ **Added comprehensive token refresh** to ALL API operations
  - Added 401 error handling to: `get_or_create_contact()`, `create_callback_ticket()`, `close_chat()`
  - Changed `[400]` to `[400, 401]` across all methods
  - Removed duplicate token refresh code
  - Files: `zoho_api_simple_prod2.py` line 303-440

### **Jan 21, 2026**
- ✅ **Re-enabled LLM-triggered callbacks**
  - Issue: User typing "create callback" didn't work, only button clicks worked
  - Fix: Re-enabled `metadata.get("action") == "schedule_callback"` handler
  - Now both button clicks AND explicit requests work
  - Files: `llm_chatbot_prod.py` line 1598-1625

### **Jan 21, 2026**
- ✅ **Fixed variable name error** in callback logging
  - Changed: `preferred_time` (undefined)
  - To: `preferred_time_str` (correct variable)
  - Files: `zoho_api_simple_prod2.py` line 446

### **Jan 21, 2026**
- ✅ **Deployed comprehensive token refresh for ALL API calls**
  - Added `python-dateutil` to requirements.txt
  - Added IST timezone handling
  - Added auto-refresh to contact search, contact creation, callback creation
  - Files: requirements.txt, `zoho_api_simple_prod2.py`

---

## 🔧 TECHNICAL DETAILS

### Environment Variables (Production)
```
SALESIQ_ACCESS_TOKEN=1000.xxxxx (SalesIQ standard token)
SALESIQ_REFRESH_TOKEN=1000.xxxxx
SALESIQ_CLIENT_ID=1000.xxxxx
SALESIQ_CLIENT_SECRET=xxxxx
SALESIQ_VISITOR_APP_ID=2782000005628361
SALESIQ_VISITOR_DEPARTMENT=2782000000002013
SALESIQ_SCREEN_NAME=rtdsportal

DESK_ORG_ID=60000688226
DESK_DEPARTMENT_ID=3086000000010772
DESK_ACCESS_TOKEN=1000.xxxxx (Desk OAuth token)
DESK_REFRESH_TOKEN=1000.xxxxx
DESK_CLIENT_ID=1000.xxxxx
DESK_CLIENT_SECRET=xxxxx
```

### Key Files
| File | Purpose | Size | Status |
|------|---------|------|--------|
| `llm_chatbot_prod.py` | Main webhook handler | 107 KB | ✅ PRODUCTION |
| `zoho_api_simple_prod2.py` | API wrapper (SalesIQ + Desk) | 27 KB | ✅ PRODUCTION |
| `requirements.txt` | Python dependencies | 141 B | ✅ CURRENT |
| `.env` | Environment variables | - | ✅ ON SERVER |

### Deployment Process
```bash
# 1. Make changes locally in VS Code
# 2. Test if needed (optional)
# 3. Copy to production
scp llm_chatbot_prod.py ubuntu@45.194.90.181:/opt/llm-chatbot/llm_chatbot.py
scp zoho_api_simple_prod2.py ubuntu@45.194.90.181:/opt/llm-chatbot/zoho_api_simple.py

# 4. Restart service
ssh -i "acebuddy.key" ubuntu@45.194.90.181 "sudo systemctl restart llm-chatbot"

# 5. Verify status
ssh -i "acebuddy.key" ubuntu@45.194.90.181 "sudo systemctl status llm-chatbot"
```

---

## 📊 METRICS & MONITORING

### Memory Management
- **Cleanup frequency:** Every 15 minutes
- **Session timeout:** 30 minutes of inactivity
- **Current memory:** ~150 MB (process) + RAM for active sessions
- **Scaling:** Handles 1000+ concurrent users easily

### API Performance
| Operation | Avg Time | Status |
|-----------|----------|--------|
| Chat transfer | 1-2s | ✅ |
| Callback creation | 1-2s | ✅ |
| Chat closure | 500ms | ✅ |
| Token refresh | 750ms | ✅ |
| Contact lookup | 500ms | ✅ |

---

## 🐛 KNOWN ISSUES
- **None currently** ✅

---

## 📋 NEXT PRIORITIES

1. **Implement git workflow** - Track all changes via commits
2. **Add memory monitoring endpoint** - Optional but recommended
3. **Monitor production for 2 weeks** - Ensure stability
4. **Scale considerations** - Currently ready for 1000+ users

---

## 📞 SUPPORT & CONTACTS

**Production Server:**
- IP: 45.194.90.181
- Service: llm-chatbot (systemd)
- Logs: `sudo journalctl -u llm-chatbot -f`
- Status: `sudo systemctl status llm-chatbot`

**Critical Credentials Location:**
- Server: `/opt/llm-chatbot/.env`
- Local: Not in git (use `.env` file locally)

**Rollback if Needed:**
```bash
# Restore from backup
cp /opt/llm-chatbot/llm_chatbot.py.backup /opt/llm-chatbot/llm_chatbot.py
sudo systemctl restart llm-chatbot
```

---

## ✅ SIGN-OFF

**Tested by:** Aryan Gupta  
**Testing Date:** Jan 23-27, 2026  
**Features tested:** Transfer ✅, Callback ✅, Closure ✅, Token Refresh ✅, Memory ✅  
**Production Status:** READY FOR USE ✅  
**SLA:** All 6 core features working and tested

---
