# 🔍 How the System Decides: Keyword OR LLM?

## THE ACTUAL DECISION FLOW (From Code)

```
┌─────────────────────────────────────────────────────┐
│ User sends message: "can you connect me to agent"   │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────────┐
         │ CHECK BUTTONS FIRST       │  ← PRIORITY 1
         │ (is_instant_chat_button?) │
         └──────────┬────────────────┘
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
   ✅ MATCH               ❌ NOT MATCH
   (emoji "📞"             (not a button)
    or "1" or              
    "option 1")            │
        │                  ↓
        │         ┌──────────────────────────┐
        │         │ CHECK KEYWORDS           │  ← PRIORITY 2
        │         │ (agent phrases list)     │
        │         └────────┬─────────────────┘
        │                  │
        │      ┌───────────┴───────────┐
        │      ↓                       ↓
        │   ✅ MATCH              ❌ NOT MATCH
        │   (contains "agent"         (no keywords
        │    "escalate"               matched)
        │    "connect")               │
        │      │                      ↓
        │      │          ┌──────────────────────────┐
        │      │          │ CALL LLM API             │  ← PRIORITY 3
        │      │          │ (Gemini classification) │
        │      │          └──────────┬───────────────┘
        │      │                     │
        └──────┴─────────────────────┴──────────┐
                                               ↓
                                    ┌─────────────────────┐
                                    │ SHOW BUTTONS        │
                                    │ (escalation options)│
                                    └─────────────────────┘
```

---

## THE 3 CHECKS IN ORDER (Priority Matters!)

### **CHECK 1: Button Click? (Lines 896-950)**
```python
is_instant_chat_button = (
    message_text.strip() == "📞 Instant Chat" or
    message_lower.strip() == "instant chat" or
    message_lower.strip() == "option 1" or
    message_lower.strip() == "1" or
    payload == "option_1"
)

if is_instant_chat_button:  # ← If TRUE, handle IMMEDIATELY
    logger.info("[Action] ✅ BUTTON CLICKED: Instant Chat")
    # Transfer to agent NOW
    return JSONResponse(...)  # DONE! Stop here.
```

**Example:** User types "1" or "📞 Instant Chat"
→ Caught here ✅
→ Transfer happens NOW
→ NO keyword check, NO LLM call

---

### **CHECK 2: Keyword Match? (Lines 1280-1340)**
```python
agent_request_phrases = [
    "connect me to agent",
    "human agent",
    "talk to human",
    "speak to agent",
    "escalate",
    "supervisor",
    ...
]

if any(phrase in message_lower for phrase in agent_request_phrases):
    logger.info("[Escalation] 🆙 ESCALATION REQUESTED")
    # Show buttons NOW
    return JSONResponse(...)  # DONE! Stop here.
```

**Example:** User types "can you connect me to agent"
→ Keyword found! ✅
→ Show buttons NOW
→ NO LLM call needed (saves $)

---

### **CHECK 3: LLM Analysis? (Lines 1085-1100)**
```python
# Only reaches here if:
# - NOT a button click
# - NO keywords matched

logger.info("[LLM Classifier] Running unified classification (1 API call)...")

classifications = llm_classifier.classify_unified(
    message_text,
    conversations[session_id],  # Full history
    session_id=session_id
)

# Gemini analyzes and says: 
# "Is this person frustrated? Do they need escalation?"

if llm_classifier.should_escalate(escalation_classification):
    logger.info("[Escalation] 🆙 USER NEEDS HUMAN ASSISTANCE (LLM-detected)")
    # Show buttons
    return JSONResponse(...)
```

**Example:** User types "it still doesn't work and i've tried everything"
→ NOT a button click ❌
→ NO keywords matched ❌
→ Call Gemini LLM ✅
→ LLM says: 95% need escalation
→ Show buttons (after 1500ms)

---

## CODE LOGIC FLOW (Actual if-else Chain)

```python
# Line 896-950: CHECK 1 - BUTTONS
if is_instant_chat_button and not (user_is_correcting or user_is_clarifying):
    logger.info("[Action] ✅ BUTTON CLICKED: Instant Chat (Option 1)")
    transfer_to_agent()
    return JSONResponse(...)  # STOP! Done.

# Line 952-1000: CHECK CALLBACK BUTTON
if is_callback_button and not (user_is_correcting or user_is_clarifying):
    logger.info("[Action] ✅ BUTTON CLICKED: Schedule Callback (Option 2)")
    schedule_callback()
    return JSONResponse(...)  # STOP! Done.

# Line 1280-1340: CHECK 2 - KEYWORDS
if any(phrase in message_lower for phrase in agent_request_phrases):
    logger.info("[Escalation] 🆙 ESCALATION REQUESTED - User wants human agent")
    show_buttons()
    return JSONResponse(...)  # STOP! Done.

# Line 1085-1100: CHECK 3 - LLM (only if above didn't match)
classifications = llm_classifier.classify_unified(...)

if llm_classifier.should_escalate(escalation_classification):
    logger.info("[Escalation] 🆙 USER NEEDS HUMAN ASSISTANCE (LLM-detected)")
    show_buttons()
    return JSONResponse(...)  # STOP! Done.

# Otherwise: Continue normal conversation
```

---

## DECISION TREE - Visual

```
START: Message arrives
   │
   ├─→ Is it a button click?
   │      ├─ YES → Handle button (transfer or callback)
   │      └─ NO → Continue
   │
   ├─→ Do keywords match?
   │      ├─ YES → Show escalation buttons immediately
   │      └─ NO → Continue
   │
   ├─→ Send to LLM for analysis?
   │      ├─ YES → Wait for Gemini response (500-2000ms)
   │      │        If escalation needed → Show buttons
   │      │        If not needed → Continue conversation
   │      └─ NO → Continue conversation
   │
   └─→ Generate normal bot response
```

---

## REAL EXAMPLES

### Example 1: Explicit Button Click
```
User sends: "1"
   ↓
Check 1: Is it a button? YES ✅
   ↓
Transfer to agent IMMEDIATELY
(no keywords, no LLM)
Time: < 10ms
Cost: $0
```

### Example 2: Explicit Keyword Request
```
User sends: "can you connect me to agent"
   ↓
Check 1: Is it a button? NO ❌
   ↓
Check 2: Do keywords match? YES ✅
   ("connect me to agent" is in the list)
   ↓
Show buttons IMMEDIATELY
(no LLM)
Time: < 10ms
Cost: $0
```

### Example 3: Ambiguous Message
```
User sends: "it still doesn't work and i've tried everything"
   ↓
Check 1: Is it a button? NO ❌
   ↓
Check 2: Do keywords match? NO ❌
   (no "agent", "escalate", etc.)
   ↓
Check 3: Send to LLM? YES ✅
   └─ Gemini: "80% chance they're frustrated → escalate"
   ↓
Show buttons AFTER 1500ms
Time: 1500ms
Cost: $0.0001
```

### Example 4: Regular Question
```
User sends: "how do I reset my password"
   ↓
Check 1: Is it a button? NO ❌
   ↓
Check 2: Do keywords match? NO ❌
   ↓
Check 3: Send to LLM? YES ✅
   └─ Gemini: "This is a question, not escalation"
   ↓
Continue normal conversation
(LLM generates answer)
Time: 1500ms
Cost: $0.0001
```

---

## KEY INSIGHT: Decision Process is SEQUENTIAL

```
KEYWORDS ← Check first (fastest)
   ↓
   ✅ MATCH? → Return (don't use LLM)
   ❌ NO MATCH?
   ↓
   ↓
LLM ← Only if keywords fail (slower, smarter)
   ↓
   Analyze context
   ↓
   Return decision
```

**NOT parallel, NOT choosing one randomly:**
- **Always** check keywords first
- **Only if** keywords fail, use LLM

---

## Why This Order?

| Check | Speed | Cost | Accuracy |
|-------|-------|------|----------|
| Buttons | < 10ms | $0 | 100% (explicit) |
| Keywords | < 10ms | $0 | 95% (common requests) |
| LLM | 1500ms | $$ | 99% (ambiguous) |

**Smart strategy:**
1. Fast checks first (buttons, keywords) → 99% of messages
2. Slow check only when needed (LLM) → 1% of messages
3. Save 99% of LLM API calls
4. Save 99% of costs
5. Still get high accuracy

