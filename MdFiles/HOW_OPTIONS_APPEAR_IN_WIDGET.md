# How 3 Escalation Options Appear in SalesIQ Chat Widget

## The Flow

### Current SalesIQ Widget Behavior
```
┌─────────────────────────────────┐
│  Ace Cloud Hosting Support      │
├─────────────────────────────────┤
│                                 │
│  Bot: "How can I help you?"     │
│                                 │
│  User: "My QB is frozen"        │
│                                 │
│  Bot: "Step 1: Open Task..."    │
│                                 │
│  User: "Still not working"      │
│                                 │
│  Bot: "Here are 3 options:      │
│       1. Instant Chat           │
│       2. Schedule Callback      │
│       3. Create Ticket"         │
│                                 │
│  [User sees text message]       │
│  [User types response]          │
│                                 │
└─────────────────────────────────┘
```

---

## How Options Appear

### Option 1: Plain Text (Current)
Bot sends message as plain text:
```
"Here are 3 options:
1. Instant Chat - Connect with a human agent now
2. Schedule Callback - We'll call you back
3. Create Support Ticket - We'll follow up via email

Which option would you like?"
```

User types: "option 1" or "1" or "instant chat"

---

### Option 2: With Hyperlinks (Better)
Bot sends message with clickable links:
```
"Here are 3 options:

1. Instant Chat - Connect with a human agent now
   https://your-domain.com/escalate/chat

2. Schedule Callback - We'll call you back
   https://your-domain.com/escalate/callback

3. Create Support Ticket - We'll follow up via email
   https://your-domain.com/escalate/ticket

Or just type 'option 1', 'option 2', or 'option 3'"
```

User can:
- Click the link (opens in new tab)
- Or type "option 1"

---

### Option 3: With Rich Formatting (Best)
SalesIQ supports rich text formatting:
```
Bot sends formatted message:

"I understand this is frustrating. Here are 3 ways I can help:

**1. Instant Chat** 💬
Connect with a human agent right now. Your conversation history will be shared.
[Click here to connect]

**2. Schedule Callback** 📞
We'll call you back at a time that works for you.
[Schedule a callback]

**3. Create Support Ticket** 📧
We'll create a detailed ticket and follow up via email within 24 hours.
[Create a ticket]

Or just reply with 'option 1', 'option 2', or 'option 3'"
```

---

## Current Implementation (What We Have)

### Bot Response Format
```python
{
  "action": "reply",
  "replies": [
    "I understand this is frustrating. Here are 3 ways I can help:\n\n" +
    "1. **Instant Chat** - Connect with a human agent now\n" +
    "   https://your-domain.com/escalate/chat\n\n" +
    "2. **Schedule Callback** - We'll call you back at a convenient time\n" +
    "   https://your-domain.com/escalate/callback\n\n" +
    "3. **Create Support Ticket** - We'll create a detailed ticket and follow up\n" +
    "   https://your-domain.com/escalate/ticket\n\n" +
    "Which option would you like?"
  ],
  "session_id": "session-123"
}
```

### How It Appears in Widget
```
┌─────────────────────────────────┐
│  Ace Cloud Hosting Support      │
├─────────────────────────────────┤
│                                 │
│  Bot: "I understand this is     │
│       frustrating. Here are 3   │
│       ways I can help:          │
│                                 │
│       1. Instant Chat           │
│       https://your-domain...    │
│                                 │
│       2. Schedule Callback      │
│       https://your-domain...    │
│                                 │
│       3. Create Support Ticket  │
│       https://your-domain...    │
│                                 │
│       Which option would you    │
│       like?"                    │
│                                 │
│  [User sees clickable links]    │
│  [User can click or type]       │
│                                 │
│  User: "option 1"              │
│                                 │
└─────────────────────────────────┘
```

---

## User Interaction Options

### Option A: User Clicks Link
```
User clicks: "https://your-domain.com/escalate/chat"
↓
Opens new page/form
↓
Handles escalation
↓
Returns to chat or closes
```

### Option B: User Types Response
```
User types: "option 1"
↓
Bot receives message
↓
Bot detects "option 1"
↓
Bot calls SalesIQ API
↓
Chat transfers to agent
```

### Option C: User Types Alternative
```
User types: "instant chat" or "1" or "chat"
↓
Bot receives message
↓
Bot detects keyword
↓
Bot calls SalesIQ API
↓
Chat transfers to agent
```

---

## What Happens After User Selects Option

### Option 1: Instant Chat
```
User: "option 1"
↓
Bot: Calls SalesIQ API
↓
SalesIQ: Creates new chat session
↓
Agent: Receives chat with history
↓
Widget: Shows agent's message
↓
Conversation: Continues with agent
```

### Option 2: Schedule Callback
```
User: "option 2"
↓
Bot: "Please provide your preferred time and phone number"
↓
User: "Tomorrow at 2 PM, 555-1234"
↓
Bot: Calls Desk API
↓
Desk: Creates callback ticket
↓
Bot: "Callback scheduled! Ticket: TICKET-12345"
↓
Chat: Auto-closes
```

### Option 3: Create Ticket
```
User: "option 3"
↓
Bot: "Please provide your name, email, phone, and issue description"
↓
User: "John, john@example.com, 555-1234, QB frozen"
↓
Bot: Calls Desk API
↓
Desk: Creates support ticket
↓
Bot: "Ticket created! Ticket: TICKET-12346"
↓
Chat: Auto-closes
```

---

## SalesIQ Widget Capabilities

### What SalesIQ Widget Supports
- ✅ Plain text messages
- ✅ Hyperlinks (clickable)
- ✅ Line breaks and formatting
- ✅ Emojis
- ✅ Rich text (bold, italic)
- ✅ File attachments
- ✅ Images
- ✅ Custom buttons (if configured)

### What We're Using
- ✅ Plain text with hyperlinks
- ✅ Formatting for readability
- ✅ User can click or type

---

## Implementation Details

### In Bot Code
```python
# When user says "not working"
if "not working" in message_lower:
    response_text = """I understand this is frustrating. Here are 3 ways I can help:

1. **Instant Chat** - Connect with a human agent now
   https://your-domain.com/escalate/chat

2. **Schedule Callback** - We'll call you back at a convenient time
   https://your-domain.com/escalate/callback

3. **Create Support Ticket** - We'll create a detailed ticket and follow up
   https://your-domain.com/escalate/ticket

Which option would you like? (Reply with 'option 1', 'option 2', or 'option 3')"""
    
    return {
        "action": "reply",
        "replies": [response_text],
        "session_id": session_id
    }
```

### In SalesIQ Widget
```
Bot message appears with:
- Plain text
- Hyperlinks (clickable)
- Formatting
- User can click link or type response
```

---

## User Experience Flow

### Scenario 1: User Clicks Link
```
1. User sees message with 3 options
2. User clicks "Instant Chat" link
3. New tab opens (or modal)
4. Escalation happens
5. Chat transfers to agent
6. Conversation continues
```

### Scenario 2: User Types Response
```
1. User sees message with 3 options
2. User types "option 1"
3. Bot receives message
4. Bot detects "option 1"
5. Bot calls SalesIQ API
6. Chat transfers to agent
7. Conversation continues
```

### Scenario 3: User Types Alternative
```
1. User sees message with 3 options
2. User types "instant chat"
3. Bot receives message
4. Bot detects "instant chat"
5. Bot calls SalesIQ API
6. Chat transfers to agent
7. Conversation continues
```

---

## Visual Example

### What User Sees in Widget

```
┌──────────────────────────────────────┐
│  Ace Cloud Hosting Support           │
├──────────────────────────────────────┤
│                                      │
│  Bot: "My QuickBooks is frozen"     │
│                                      │
│  You: "My QuickBooks is frozen"     │
│                                      │
│  Bot: "Are you using a dedicated    │
│       server or a shared server?"   │
│                                      │
│  You: "Dedicated"                   │
│                                      │
│  Bot: "Step 1: Right click and      │
│       open Task Manager..."         │
│                                      │
│  You: "Still not working"           │
│                                      │
│  Bot: "I understand this is         │
│       frustrating. Here are 3       │
│       ways I can help:              │
│                                      │
│       1. Instant Chat               │
│       https://your-domain.com/...   │
│                                      │
│       2. Schedule Callback          │
│       https://your-domain.com/...   │
│                                      │
│       3. Create Support Ticket      │
│       https://your-domain.com/...   │
│                                      │
│       Which option would you like?" │
│                                      │
│  [Text input box]                   │
│  [User types or clicks]             │
│                                      │
└──────────────────────────────────────┘
```

---

## Summary

### How Options Appear
1. **Bot sends message** with 3 options
2. **Message appears in widget** as text with hyperlinks
3. **User can click link** or **type response**
4. **Bot detects choice** and calls appropriate API
5. **Escalation happens** (transfer, callback, or ticket)

### User Can
- ✅ Click hyperlink
- ✅ Type "option 1"
- ✅ Type "instant chat"
- ✅ Type "1"
- ✅ Type any variation

### Bot Detects
- ✅ "option 1" / "option 2" / "option 3"
- ✅ "instant chat" / "callback" / "ticket"
- ✅ "1" / "2" / "3"
- ✅ Hyperlink clicks (if configured)

---

## Next Steps

1. **Implement API integration** (call SalesIQ & Desk APIs)
2. **Test in SalesIQ widget** (see options appear)
3. **Test user interactions** (click or type)
4. **Deploy to production**

---

**Status**: Ready to implement
**Next Action**: Provide Zoho API credentials
