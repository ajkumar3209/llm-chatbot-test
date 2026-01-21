# 🧠 How Chat Escalation Works - Technical Deep Dive

## Overview
The chat escalation system is **NOT just keyword-based**. It's a sophisticated **state machine** with **memory**, **LLM intelligence**, and **multi-layered detection** working together.

---

## 1. THE MEMORY SYSTEM (Session State)

### Where Memory Lives:
```
Python Dictionary: conversations[session_id] = []
```

Every message in a chat is stored in RAM:
```python
conversations[session_id] = [
    {"role": "user", "content": "can you help me with password"},
    {"role": "assistant", "content": "I can help! Are you registered..."},
    {"role": "user", "content": "can you connect me to agent"},
    ...
]
```

**Key Point:** The entire chat history is kept in memory for the **ENTIRE session duration**.

### Session Tracking:
```python
# From state_manager.py

@dataclass
class ConversationSession:
    """Represents a single conversation session with state tracking"""
    session_id: str
    state: ConversationState = ConversationState.GREETING
    category: str = "other"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0                    # ← COUNTS MESSAGES
    troubleshooting_attempts: int = 0        # ← TRACKS ATTEMPTS
    escalation_attempts: int = 0             # ← TRACKS ESCALATIONS
    user_info: Dict[str, str] = {}           # ← STORES USER DATA
    state_history: List[Dict] = []           # ← LOGS TRANSITIONS
```

**Example: A session with memory:**
```
session_id: 2782000013425159
state: troubleshooting (started at 06:20)
message_count: 7 (user sent 7 messages)
troubleshooting_attempts: 2 (tried 2 different solutions)
escalation_attempts: 1 (tried escalating once)
category: "quickbooks" (bot knows what product)
state_history: [
    greeting → issue_gathering,
    issue_gathering → troubleshooting,
    troubleshooting → escalation_options
]
```

---

## 2. STATE MACHINE (How It Tracks Conversation Flow)

The conversation follows a **finite state machine** with strict transitions:

```
GREETING
   ↓ (user says hello)
ISSUE_GATHERING
   ↓ (user describes problem)
TROUBLESHOOTING
   ↓ (solution works?)
   ├→ SOLUTION WORKS → RESOLVED ✅
   ├→ SOLUTION FAILS → ESCALATION_OPTIONS
   └→ USER FRUSTRATED → ESCALATION_OPTIONS
       ↓ (user chooses option)
       ├→ INSTANT CHAT → ESCALATED (transfer to human)
       ├→ CALLBACK → CALLBACK_COLLECTION
       └→ TICKET → TICKET_COLLECTION
```

### Code Example - State Transitions:
```python
# From state_manager.py
TRANSITIONS = {
    ConversationState.GREETING: {
        TransitionTrigger.GREETING_RECEIVED: ConversationState.ISSUE_GATHERING,
        TransitionTrigger.ESCALATION_REQUESTED: ConversationState.ESCALATION_OPTIONS,
    },
    ConversationState.TROUBLESHOOTING: {
        TransitionTrigger.STEP_ACKNOWLEDGED: ConversationState.TROUBLESHOOTING,  # Stay in same state
        TransitionTrigger.SOLUTION_CONFIRMED: ConversationState.AWAITING_CONFIRMATION,
        TransitionTrigger.SOLUTION_FAILED: ConversationState.ESCALATION_OPTIONS,  # Move to escalation
        TransitionTrigger.USER_FRUSTRATED: ConversationState.ESCALATION_OPTIONS,  # Move to escalation
        TransitionTrigger.ESCALATION_REQUESTED: ConversationState.ESCALATION_OPTIONS,
    },
}

# When user clicks button:
def handle_button_click(session_id, button_type):
    session = state_manager.get_session(session_id)
    state_manager.transition(session_id, TransitionTrigger.AGENT_TRANSFER)
    # State: escalation_options → escalated
```

---

## 3. ESCALATION DETECTION - THREE LAYERS

### **Layer 1: Keyword Detection (Fastest)**
```python
# From llm_chatbot.py (lines 1280-1350)

agent_request_phrases = [
    # Direct agent requests
    "connect me to agent", "connect to agent", "human agent", "talk to human",
    "speak to agent", "speak to someone", "talk to someone",
    
    # Escalation language
    "escalate", "supervisor", "manager", "transfer me",
    
    # Help requests
    "need help now", "need immediate help", "can someone help",
    
    # Alternative phrasing
    "speak with agent", "chat with agent", "contact agent", "operator",
]

# Check if ANY phrase appears in user message
if any(phrase in message_lower for phrase in agent_request_phrases):
    logger.info(f"[Escalation] 🆙 ESCALATION REQUESTED - User wants human agent")
    state_manager.transition(session_id, TransitionTrigger.ESCALATION_REQUESTED)
    # Show 2 buttons immediately
```

**Speed:** < 10ms (just string matching)  
**Reliability:** High for explicit requests

---

### **Layer 2: LLM Classification (Intelligent)**
```python
# From gemini_classifier.py

class GeminiClassifier:
    def classify_message(self, message, conversation_history):
        """Use LLM to understand context and intent"""
        
        # Build a prompt with FULL conversation history
        prompt = f"""
        Conversation so far:
        {conversation_history}
        
        Latest user message: {message}
        
        Classify this message:
        1. RESOLUTION_CONFIDENCE: How solved is the issue? (0-100%)
        2. ESCALATION_NEEDED: Does user need human help? (true/false)
        3. INTENT: What does user want? (QUESTION, TRANSFER, FEEDBACK, etc.)
        4. REASONING: Why?
        """
        
        # Call Gemini 2.5 Flash LLM
        response = openrouter.call(prompt)
        
        return {
            "resolution": 95,           # 95% solved
            "escalation_needed": False,  # No escalation needed
            "intent": "QUESTION",        # User asking question
            "confidence": 85,            # 85% confident
            "reasoning": "User mentioned..."
        }
```

**Speed:** 500-2000ms (calls LLM API)  
**Reliability:** Very high (understands context)  
**Example:**

```
User message: "does that mean it's fixed now?"
LLM Analysis:
  - RESOLUTION: 95% (user thinks it's fixed)
  - ESCALATION: 5% (just confirming, not requesting help)
  - INTENT: QUESTION
  - Result: Continue troubleshooting, don't escalate
```

vs.

```
User message: "i've tried everything you said and it still doesn't work"
LLM Analysis:
  - RESOLUTION: 10% (nothing worked)
  - ESCALATION: 95% (user frustrated, needs help)
  - INTENT: TRANSFER
  - Result: Escalate to human immediately
```

---

### **Layer 3: Button Clicks (User Decision)**
```python
# From llm_chatbot.py (lines 903-950)

is_instant_chat_button = (
    message_text.lower() == "1" or
    message_text.lower() == "option 1" or
    "📞" in message_text or  # Emoji match
    "instant chat" in message_text.lower() or
    payload == "option_1"  # From quick-reply button
)

if is_instant_chat_button:
    logger.info(f"[Action] ✅ BUTTON CLICKED: Instant Chat (Option 1)")
    logger.info(f"[Action] 🔄 CHAT TRANSFER INITIATED")
    
    # Call SalesIQ API
    result = zoho_api.create_chat_session(session_id, conversation_history)
    
    if result['success']:
        logger.info(f"[Action] ✓ TRANSFER CONFIRMATION SENT")
        # Conversation now in SalesIQ, waiting for operator
```

**Speed:** Instant (no API call yet)  
**Reliability:** 100% (explicit user action)

---

## 4. COMPLETE FLOW EXAMPLE

### Real Log from Your Chat:

```
06:20:57 User: "can you help me with password"
         → Router classifies as: "login" (keyword match)
         → State: greeting → issue_gathering
         → LLM confidence: 70% bot can handle

06:21:07 User: "can you connect me to agent"
         → Layer 1 (Keyword): DETECTED! ("connect me to agent")
         → State: issue_gathering → escalation_options
         → Response: "Let me connect you. Choose option:"
         → Shows 2 buttons: [📞 Instant Chat] [📅 Schedule Callback]

06:26:59 User: "📞 Instant Chat"  (clicked button)
         → Layer 3 (Button): DETECTED! (emoji match)
         → State: escalation_options → escalated
         → Action: Call SalesIQ Visitor API
         → Token refresh: [FAILED] → [AUTO-REFRESH] → [SUCCESS]
         → API Response Status: 200 ✅
         → Conversation created in SalesIQ
         → conversation_id: 2782000013454019
         → Status: WAITING for operator

06:36:02 Bot: Receives message from SalesIQ (new conversation in SalesIQ)
         → This is a NEW session (different session_id)
         → Different state machine instance
         → Operator can now see full history of previous conversation
```

---

## 5. CRITICAL INSIGHT: Why It's Not Just Keyword-Based

### Bad Approach (Keyword Only):
```python
if "agent" in message:
    escalate()
```
**Problem:** Would trigger on "I don't need an agent, I can fix it myself"

### Smart Approach (Layered):
```python
# Layer 1: Keywords
if "connect me to agent" in message:
    escalate()

# Layer 2: LLM + Context
elif llm_analysis.escalation_confidence > 70 AND \
     llm_analysis.resolution_confidence < 50:  # They've tried enough
    escalate()

# Layer 3: State Check
elif state == TROUBLESHOOTING AND \
     troubleshooting_attempts > 3:  # Tried 3 times
    suggest_escalation()
```

---

## 6. MEMORY PERSISTENCE (Important!)

### Where Memory Stays:
```
Session Lifetime: Current conversation only
Memory Location: Python RAM (conversations[session_id])
Persistence: Until bot session ends or service restarts
```

### Example Timeline:
```
Time    | Message                      | State              | Memory
--------|------------------------------|-------------------|---------------------------
06:20   | "help with password"        | greeting           | [msg 1]
06:21   | "can you help?"             | issue_gathering    | [msg 1, msg 2]
06:25   | "it still doesn't work"     | troubleshooting    | [msg 1, msg 2, msg 3, msg 4]
06:26   | "connect me to agent"       | escalation_options | [msgs 1-5] ← FULL HISTORY
06:27   | "📞 Instant Chat"           | escalated          | [msgs 1-6] ← SENT TO SALESIQ
```

**When creating conversation in SalesIQ:**
```python
def create_chat_session(visitor_id, conversation_history):
    # conversation_history contains ALL messages:
    question = """User: can you help me with password
Bot: I can help! Are you registered on the SelfCare portal?
User: yes
Bot: Great! Try this...
User: it still doesn't work
Bot: Let me connect you with our team
User: 📞 Instant Chat"""
    
    payload = {
        "question": question,  # ← FULL HISTORY
        "visitor_id": visitor_id,
        "department_id": "2782000000002013"
    }
```

---

## 7. WHAT HAPPENS WHEN SERVICE RESTARTS?

**Critical Detail:**
```python
conversations = {}  # ← This is reset!
state_manager = StateManager()  # ← This is reset!
```

**Result:**
- All RAM-based sessions are lost
- New service = new memory
- Operator handoff must happen BEFORE restart
- In production, need persistent session storage (database)

---

## 8. BUTTON MATCHING LOGIC (Why It Worked)

```python
# Exact matching to prevent false positives:

is_instant_chat_button = (
    message_text.lower() == "1" or              # Just "1"
    message_text.lower() == "option 1" or      # "option 1"
    "📞" in message_text or                     # Contains emoji
    "instant chat" in message_text.lower() or  # Contains phrase
    payload == "option_1"                      # From button JSON
)

# Combined with state check:
if state == ESCALATION_OPTIONS and is_instant_chat_button:
    # Process button
```

**Why state check matters:**
```
If user says "instant chat" in random message → Ignored (not in escalation state)
If buttons shown AND user clicks button → Processed (correct state)
```

---

## 9. FULL CALL STACK

When user clicks button, here's what happens:

```
1. SalesIQ Widget → Send message "📞 Instant Chat"
                    ↓
2. llm_chatbot.py webhook_handler()
   └── Extract visitor_id, message
       ↓
3. State check: Is session in ESCALATION_OPTIONS state? ✅
   ↓
4. Button matching: Does message match "Instant Chat"? ✅
   ↓
5. Build conversation_text from conversations[session_id]
   └── Full history: user messages + bot responses
       ↓
6. Call: zoho_api.create_chat_session(visitor_id, conversation_text)
   ├── Check token: Is it valid? NO → 400 error
   │   ├── Auto-refresh: Call OAuth endpoint
   │   ├── Get new token: 1005.89c06eee...
   │   ├── Retry: Call Visitor API with new token
   │   └── Status: 200 ✅
   │
   └── API Response:
       ├── conversation_id: 2782000013454019
       ├── status: WAITING
       ├── operator_assigned: False (pending)
       └── chat_history: SENT to SalesIQ
           ↓
7. Return response to SalesIQ widget
   └── Show confirmation: "I'm connecting you..."
       ↓
8. SalesIQ receives:
   └── Creates NEW session with conversation_id
   └── Notifies operators
   └── Waits for operator to accept
       ↓
9. NEW webhook from SalesIQ:
   └── Same chat_history sent back
   └── Creates new state machine instance
   └── But operators can see full history
```

---

## 10. SUMMARY TABLE

| Aspect | How It Works | Memory? | Speed |
|--------|-------------|---------|-------|
| **Keyword Detect** | String matching agent phrases | RAM dict | <10ms |
| **LLM Classify** | Gemini analyzes full context | RAM dict | 500-2000ms |
| **Button Click** | Exact emoji/text match | State machine | <10ms |
| **State Machine** | Tracks conversation flow | RAM dataclass | <10ms |
| **Session Tracking** | Stores all messages | conversations[] dict | <10ms |
| **Token Refresh** | OAuth auto-refresh on 400 | Inline | ~750ms |
| **Chat Transfer** | POST to SalesIQ API | Full history sent | ~1-2s |

---

## 11. NEXT STEPS FOR SERVER

To replicate this on your server:

1. **Keep conversation history in memory** (or database)
   ```python
   conversations[session_id] = [...]  # Full message history
   ```

2. **Use state machine** for tracking state
   ```python
   state_manager.transition(session_id, trigger)
   ```

3. **Implement OAuth token refresh**
   ```python
   if response.status_code == 400:
       refresh_token()
       retry_request()
   ```

4. **Send full history on escalation**
   ```python
   conversation_text = "\n".join([msg["content"] for msg in conversations[session_id]])
   zoho_api.create_chat_session(visitor_id, conversation_text)
   ```

5. **Use persistent storage** (not RAM) for sessions:
   ```python
   # Option 1: Redis
   redis.set(f"session:{session_id}", session_data)
   
   # Option 2: Database
   db.sessions.insert({session_id, state, messages})
   
   # Option 3: File system
   # Save JSON files per session
   ```

