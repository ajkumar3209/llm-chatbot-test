# SalesIQ Chat Transfer Test Guide

## ✅ Ready to Test Real Chat Transfers

### **Configuration Applied:**
```env
SALESIQ_ACCESS_TOKEN=1000.21a18fe9ce30e588db59c39b4524a22a.87a0b3df50ec313a84b5e92479c659c3
SALESIQ_DEPARTMENT_ID=Support(QB & App Hosting)
```

### **API Endpoint:**
```
POST https://salesiq.zoho.in/api/v2/chats
Authorization: Bearer 1000.21a18fe9ce30e588db59c39b4524a22a.87a0b3df50ec313a84b5e92479c659c3
```

---

## 🧪 Test Steps

### **Step 1: Deploy to Railway**
Your code is already pushed to GitHub. Railway should auto-deploy.

**Monitor deployment:**
```bash
# Check Railway dashboard or logs
railway logs --follow
```

**Look for:**
```
[SalesIQ] API configured with Indian domain
INFO: Uvicorn running on 0.0.0.0:8000
```

### **Step 2: Test Chat Transfer (Option 1)**

**In your SalesIQ widget:**
```
1. User: "QuickBooks is frozen"
2. Bot: "Are you on dedicated or shared server?"
3. User: "Dedicated"
4. Bot: "Step 1: Right-click taskbar..."
5. User: "Still not working"
6. Bot: Shows 3 options with 1️⃣ 2️⃣ 3️⃣
7. User: "1" or "instant chat"
8. Bot: "Connecting you with a support agent..."
```

**Expected Real API Call:**
```http
POST https://salesiq.zoho.in/api/v2/chats
{
  "visitor_id": "session_123",
  "department_id": "Support(QB & App Hosting)",
  "conversation_history": "User: QuickBooks frozen\nBot: Are you on dedicated server?...",
  "transfer_to": "human_agent"
}
```

### **Step 3: Check SalesIQ Dashboard**

**Login to:** https://salesiq.zoho.in

**Check for:**
- ✅ **New chat assigned** to available operator
- ✅ **Conversation history** transferred
- ✅ **Department routing** to "Support(QB & App Hosting)"
- ✅ **Operator notification** received

### **Step 4: Monitor Railway Logs**

**Expected success logs:**
```
[SalesIQ] User selected: Instant Chat Transfer
[SalesIQ] Creating chat session for visitor session_123
[SalesIQ] Chat session created successfully
[SalesIQ] API result: {"success": true, "data": {...}}
```

**If API fails (graceful degradation):**
```
[SalesIQ] API error: 401 - Unauthorized
[SalesIQ] API disabled - simulating transfer for visitor session_123
```

---

## 🔍 Troubleshooting

### **If Transfer Fails:**

**Check 1: Token Expiry**
- Token expires in 1 hour (3600 seconds)
- If expired, you'll get 401 Unauthorized
- Need to refresh token from manager

**Check 2: Department ID Format**
- Current: `Support(QB & App Hosting)`
- May need to be numeric ID instead
- Check SalesIQ Settings → Departments for exact format

**Check 3: API Domain**
- Using: `https://salesiq.zoho.in` (Indian)
- Verify this matches your account region

### **Common Error Responses:**

**401 Unauthorized:**
```json
{"error": "invalid_token", "error_description": "Access token expired"}
```
**Solution:** Refresh token

**400 Bad Request:**
```json
{"error": "invalid_department", "message": "Department not found"}
```
**Solution:** Check department ID format

**403 Forbidden:**
```json
{"error": "insufficient_scope", "message": "Missing required scope"}
```
**Solution:** Verify token has `SalesIQ.conversations.ALL` scope

---

## 📊 Test Results Expected

### **Successful Transfer:**
1. ✅ **Bot sends transfer request** to SalesIQ API
2. ✅ **SalesIQ finds available operator** in "Support(QB & App Hosting)"
3. ✅ **Operator gets notification** with full conversation
4. ✅ **Chat widget shows** "Connected to agent"
5. ✅ **Operator can continue** helping user
6. ✅ **Complete transcript preserved** in SalesIQ

### **Callback/Ticket Options (Simulated for now):**
- Option 2 (Callback): Creates simulated ticket, closes chat
- Option 3 (Ticket): Creates simulated ticket, closes chat
- Both work normally, just no real Desk integration yet

---

## 🎯 Next Steps After Testing

### **If SalesIQ Transfer Works:**
1. ✅ **Celebrate!** Real operator handover is working
2. ✅ **Train operators** on new bot handovers
3. ✅ **Monitor chat quality** and resolution rates
4. ✅ **Add Desk integration** later for real tickets

### **If SalesIQ Transfer Fails:**
1. 🔧 **Check token expiry** and refresh if needed
2. 🔧 **Verify department ID** format in SalesIQ dashboard
3. 🔧 **Test API directly** with curl commands
4. 🔧 **Check Railway logs** for specific error messages

---

## 🚀 Test Now!

**Your bot is deployed and ready to test real SalesIQ chat transfers!**

**Go to your SalesIQ widget and try the escalation flow.**

**Monitor both:**
- Railway logs for API calls
- SalesIQ dashboard for operator notifications

**Let me know the results!** 🎉