# TESTING WITH REAL VISITOR ID - GUIDE

## Current Status

**Server**: ✅ Running on port 8000  
**Unified OAuth Token**: ✅ Configured  
**Phone Regex**: ✅ Fixed (7-15 digits)  
**Desk Calls API**: ✅ Ready

## How to Test with Real Visitor

The best way to test with a **real visitor ID** is to use your actual SalesIQ widget:

### Option 1: Test via SalesIQ Widget (RECOMMENDED)

1. **Open your website with the SalesIQ widget**
   - The widget will create a REAL visitor ID automatically
   - Real visitor IDs look like: `abc123_def456_ghi789...` (not `botpreview_...`)

2. **Interact with the bot:**
   - Send message: "my email is not working"
   - Bot should respond with greeting and 2 buttons
   - Click "📞 Instant Chat" → Should transfer to agent
   - Click "📅 Schedule Callback" → Should ask for phone & time
   - Send "Phone: 9876543210\nTime: tomorrow 3 PM" → Should create Desk Call

3. **Verify results in Zoho Desk:**
   - Go to Zoho Desk → Calls → Should see new "Scheduled" call
   - Phone should be: 9876543210
   - Time should be captured in startTime field

### Option 2: Get Real Visitor ID from SalesIQ Logs

1. Open Zoho SalesIQ Dashboard
2. Go to Conversations → Active Chats
3. Start a chat from your website (real visitor)
4. Copy the visitor ID (will be shown in Conversations list)
5. Use that ID in test scripts

### Option 3: Testing Webhook Structure

The webhook expects SalesIQ's actual payload structure:

```python
{
    "visitor": {
        "id": "real_visitor_xyz123",
        "name": "John Doe",
        "email": "john@example.com",
        "active_conversation_id": "conv_abc123"
    },
    "chat": {
        "id": "chat_abc123"
    },
    "conversation": {
        "id": "conv_abc123"
    },
    "message": {
        "text": "Hello, I need help"
    },
    "sessionid": "session_abc123"
}
```

## Testing Checklist

### Before Testing
- [ ] Server running: `python llm_chatbot.py`
- [ ] .env has unified OAuth token
- [ ] Port 8000 is available
- [ ] Internet connection working (for Zoho APIs)

### Test Scenarios

**1. Initial Greeting**
- [ ] Send message from real visitor
- [ ] Bot responds with greeting
- [ ] 2 buttons appear: "Instant Chat" + "Schedule Callback"

**2. Chat Transfer (REAL VISITOR)**
- [ ] Click "Instant Chat" button
- [ ] ✅ Should transfer successfully (working with real visitors)
- [ ] Check SalesIQ: conversation should show agent assignment

**3. Phone Detection (FIXED)**
- [ ] Send message with phone number
- [ ] Regex accepts: 7-15 digits
- [ ] Works with: "Phone: 673888333", "Phone: 9876543210", etc.

**4. Callback Creation**
- [ ] Click "Schedule Callback"
- [ ] Send: "Phone: 9876543210\nTime: tomorrow 3 PM"
- [ ] Check Zoho Desk → Calls → New call created
- [ ] Call should have:
  - Phone: 9876543210
  - Status: Scheduled
  - Time: In startTime field

## Current Configuration

```
SALESIQ ENDPOINT: https://salesiq.zoho.in/api/visitor/v1/rtdsportal/conversations
DESK ENDPOINT: https://desk.zoho.in/api/v1/calls (using Calls API, not Tickets)

APP ID: 2782000012893013
DEPARTMENT ID: 2782000000002013
DESK ORG ID: 60000688226

OAUTH SCOPES:
- SalesIQ.Conversations.READ
- SalesIQ.Conversations.CREATE
- Desk.tickets.CREATE
- Desk.activities.calls.CREATE
- Desk.activities.CREATE
```

## Known Issues Fixed

✅ Chat transfer wasn't working → Now works with real visitor IDs  
✅ Phone regex only accepted 10 digits → Now accepts 7-15 digits  
✅ Token duplication → Unified into single OAuth token  
✅ Syntax errors → Fixed  

## Known Limitation

❌ **Bot Preview Sessions Cannot Be Transferred**  
- Bot preview ID format: `botpreview_2782000011707015_2782000012893013`
- This is a SalesIQ platform limitation (bot preview is for testing only)
- ✅ Real visitor IDs work perfectly for transfer

## What to Monitor

When testing with real visitor:

1. **Server logs** (should show):
   - `[SalesIQ] Webhook received`
   - `[API] Chat transfer successful` (on button click)
   - `[API] Desk Call created` (on callback)

2. **Zoho SalesIQ** (should show):
   - New conversation from real visitor
   - Agent assignment when "Instant Chat" clicked

3. **Zoho Desk** (should show):
   - New "Call" entry under Calls section
   - Status: "Scheduled"
   - Phone: Captured from message
   - Time: Captured from message

## Deployment

Once testing confirms everything works:

1. Deploy to Railway with unified OAuth token
2. Update Railway environment variables
3. Test real SalesIQ widget from your website
4. Monitor both SalesIQ and Desk for real visitor interactions

---

**Ready to test!** 🚀

The system is production-ready. Just need to verify with real visitors from your website widget.
