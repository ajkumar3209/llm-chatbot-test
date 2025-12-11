# Context Window Explained - Clear Breakdown

## What is Context Window?

The **context window is PER API CALL**, not per conversation or per user.

Every time you send a message to OpenAI, you send:
1. System prompt
2. Conversation history (all previous messages)
3. Current user message

And OpenAI returns a response.

---

## Visual Breakdown

### Single API Call Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    ONE API CALL (128,000 tokens)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SYSTEM PROMPT (2,017 tokens)                               │
│  ├─ Instructions                                            │
│  ├─ 10 Resolution Steps                                     │
│  └─ Behavior Rules                                          │
│                                                              │
│  CONVERSATION HISTORY (variable)                            │
│  ├─ User Message 1 (50 tokens)                              │
│  ├─ Bot Response 1 (100 tokens)                             │
│  ├─ User Message 2 (40 tokens)                              │
│  ├─ Bot Response 2 (80 tokens)                              │
│  ├─ User Message 3 (60 tokens)                              │
│  └─ Bot Response 3 (90 tokens)                              │
│                                                              │
│  CURRENT USER MESSAGE (variable)                            │
│  └─ "My QuickBooks is frozen" (20 tokens)                   │
│                                                              │
│  AVAILABLE FOR RESPONSE (remaining tokens)                  │
│  └─ Bot generates response here                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Real Example: 5-Turn Conversation

### Turn 1: User sends first message

```
API Call #1:
├─ System Prompt: 2,017 tokens
├─ Conversation History: (empty)
├─ User Message: "Hi, my QuickBooks is frozen" (20 tokens)
└─ Total Sent: 2,037 tokens
   Response: Bot generates 100 tokens
```

### Turn 2: User sends second message

```
API Call #2:
├─ System Prompt: 2,017 tokens
├─ Conversation History:
│  ├─ User Message 1: 20 tokens
│  └─ Bot Response 1: 100 tokens
├─ User Message 2: "It's a dedicated server" (15 tokens)
└─ Total Sent: 2,152 tokens
   Response: Bot generates 80 tokens
```

### Turn 3: User sends third message

```
API Call #3:
├─ System Prompt: 2,017 tokens
├─ Conversation History:
│  ├─ User Message 1: 20 tokens
│  ├─ Bot Response 1: 100 tokens
│  ├─ User Message 2: 15 tokens
│  └─ Bot Response 2: 80 tokens
├─ User Message 3: "Done, what's next?" (10 tokens)
└─ Total Sent: 2,242 tokens
   Response: Bot generates 90 tokens
```

### Turn 4: User sends fourth message

```
API Call #4:
├─ System Prompt: 2,017 tokens
├─ Conversation History:
│  ├─ User Message 1: 20 tokens
│  ├─ Bot Response 1: 100 tokens
│  ├─ User Message 2: 15 tokens
│  ├─ Bot Response 2: 80 tokens
│  ├─ User Message 3: 10 tokens
│  └─ Bot Response 3: 90 tokens
├─ User Message 4: "Still frozen" (10 tokens)
└─ Total Sent: 2,342 tokens
   Response: Bot generates 150 tokens (escalation message)
```

### Turn 5: User selects "Instant Chat"

```
API Call #5:
├─ System Prompt: 2,017 tokens
├─ Conversation History:
│  ├─ User Message 1: 20 tokens
│  ├─ Bot Response 1: 100 tokens
│  ├─ User Message 2: 15 tokens
│  ├─ Bot Response 2: 80 tokens
│  ├─ User Message 3: 10 tokens
│  ├─ Bot Response 3: 90 tokens
│  ├─ User Message 4: 10 tokens
│  └─ Bot Response 4: 150 tokens
├─ User Message 5: "Yes, connect me" (10 tokens)
└─ Total Sent: 2,502 tokens
   Response: Bot generates transfer response (50 tokens)
   THEN: Transfer to human agent (conversation ends)
```

---

## Key Points

### 1. Context Window is PER API CALL
- **NOT** per conversation
- **NOT** per user
- **NOT** per message
- **YES** per OpenAI API request

### 2. What Gets Sent Each Time

Every API call includes:
```
Total Tokens Sent = System Prompt + All Previous Messages + Current Message
```

### 3. Conversation History Grows

```
Turn 1: 2,037 tokens sent
Turn 2: 2,152 tokens sent (115 more)
Turn 3: 2,242 tokens sent (90 more)
Turn 4: 2,342 tokens sent (100 more)
Turn 5: 2,502 tokens sent (160 more)
```

Each turn adds the previous bot response + current user message.

### 4. When Does It Reset?

The conversation history resets when:
- ✅ User transfers to human agent (conversation ends)
- ✅ User ends chat
- ✅ Session timeout (5+ minutes idle)
- ✅ You manually reset with `/reset/{session_id}`

After reset, next conversation starts fresh:
```
New Conversation:
├─ System Prompt: 2,017 tokens
├─ Conversation History: (empty)
└─ First User Message: ~20 tokens
```

---

## Real-World Scenario

### Typical Support Chat (5 turns, then escalation)

```
Turn 1: 2,037 tokens
Turn 2: 2,152 tokens
Turn 3: 2,242 tokens
Turn 4: 2,342 tokens
Turn 5: 2,502 tokens (transfer to agent)

Total Tokens Sent Across All Calls: 12,275 tokens
Average Per Call: 2,455 tokens
Context Window Used: 2,455 / 128,000 = 1.9%
```

### Long Support Chat (20 turns, then escalation)

```
Turn 1:  2,037 tokens
Turn 2:  2,152 tokens
Turn 3:  2,242 tokens
Turn 4:  2,342 tokens
Turn 5:  2,502 tokens
Turn 6:  2,612 tokens
Turn 7:  2,722 tokens
Turn 8:  2,832 tokens
Turn 9:  2,942 tokens
Turn 10: 3,052 tokens
Turn 11: 3,162 tokens
Turn 12: 3,272 tokens
Turn 13: 3,382 tokens
Turn 14: 3,492 tokens
Turn 15: 3,602 tokens
Turn 16: 3,712 tokens
Turn 17: 3,822 tokens
Turn 18: 3,932 tokens
Turn 19: 4,042 tokens
Turn 20: 4,152 tokens (transfer to agent)

Total Tokens Sent: 62,370 tokens
Average Per Call: 3,118 tokens
Context Window Used Per Call: 3,118 / 128,000 = 2.4%
```

---

## Important: Token Limits

### Per API Call Limit
- **Input tokens**: Up to 128,000 tokens
- **Output tokens**: Up to 4,096 tokens (for gpt-4o-mini)
- **Total**: 128,000 tokens max per call

### What Happens If You Exceed?

If conversation history grows too large:
```
Turn 50: 10,000 tokens sent
Turn 100: 15,000 tokens sent
Turn 200: 25,000 tokens sent
Turn 500: 50,000 tokens sent
Turn 1000: 100,000 tokens sent
Turn 1001: ❌ ERROR - Exceeds 128,000 token limit
```

### Solution: Conversation Reset

After ~1,000 turns (or ~100,000 tokens), reset the conversation:
```python
# Reset conversation in your code
conversations[session_id] = []  # Clear history
# Next message starts fresh with only system prompt
```

---

## Your Current Implementation

### How It Works

```python
def generate_response(message: str, history: List[Dict]) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)  # Add all previous messages
    messages.append({"role": "user", "content": message})
    
    # This entire list is sent to OpenAI as ONE API CALL
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,  # ← All of this is ONE context window
        temperature=0.7,
        max_tokens=300
    )
    
    return response.choices[0].message.content
```

### Token Count Per Call

```
System Prompt:        2,017 tokens
Conversation History: Variable (grows with each turn)
Current Message:      ~20-50 tokens
Total Per Call:       2,037 + (history size)
```

---

## Practical Examples

### Example 1: Short Chat (3 turns)

```
Turn 1:
  System: 2,017 tokens
  History: 0 tokens
  Message: 20 tokens
  Total: 2,037 tokens ✅ Safe

Turn 2:
  System: 2,017 tokens
  History: 120 tokens (prev user + bot response)
  Message: 15 tokens
  Total: 2,152 tokens ✅ Safe

Turn 3:
  System: 2,017 tokens
  History: 225 tokens (2 exchanges)
  Message: 10 tokens
  Total: 2,252 tokens ✅ Safe
```

### Example 2: Long Chat (100 turns)

```
Turn 100:
  System: 2,017 tokens
  History: ~8,000 tokens (99 previous exchanges)
  Message: 30 tokens
  Total: 10,047 tokens ✅ Safe (still only 7.8% of context)
```

### Example 3: Very Long Chat (1000 turns)

```
Turn 1000:
  System: 2,017 tokens
  History: ~100,000 tokens (999 previous exchanges)
  Message: 30 tokens
  Total: 102,047 tokens ✅ Still safe (79.7% of context)

Turn 1001:
  System: 2,017 tokens
  History: ~100,100 tokens
  Message: 30 tokens
  Total: 102,147 tokens ❌ EXCEEDS LIMIT
```

---

## Summary

### Context Window is:
- ✅ Per API call
- ✅ Includes system prompt + all history + current message
- ✅ 128,000 tokens max
- ✅ Resets when conversation ends

### Your Conversation Flow:
```
User Message 1 → API Call 1 (2,037 tokens) → Bot Response 1
User Message 2 → API Call 2 (2,152 tokens) → Bot Response 2
User Message 3 → API Call 3 (2,242 tokens) → Bot Response 3
...
User Message N → API Call N (2,037 + history) → Bot Response N
User: "Connect me" → API Call N+1 → Transfer to Agent
                                    → Conversation Ends
                                    → History Cleared
```

### Practical Limits:
- **Typical chat**: 5-10 turns (2,000-3,000 tokens per call) ✅
- **Long chat**: 50-100 turns (3,000-10,000 tokens per call) ✅
- **Very long chat**: 500-1,000 turns (50,000-100,000 tokens per call) ✅
- **Extreme chat**: 1,000+ turns (exceeds limit) ❌

---

## Bottom Line

**Context window is per API call, not per conversation.**

Each time a user sends a message:
1. You send: System Prompt + All Previous Messages + Current Message
2. OpenAI processes all of it (max 128,000 tokens)
3. OpenAI returns a response
4. You store the response in history
5. Next message repeats the process with larger history

For your use case:
- **Typical 5-turn chat**: Uses ~2,500 tokens per call (1.9% of context)
- **Long 100-turn chat**: Uses ~10,000 tokens per call (7.8% of context)
- **Very long 1,000-turn chat**: Uses ~100,000 tokens per call (78% of context)

You're safe for all realistic conversation lengths.

---

**Key Takeaway**: The context window grows with each turn because you're sending the entire conversation history every time. This is normal and expected. You won't hit the limit unless conversations exceed 1,000+ turns, which is extremely rare.
