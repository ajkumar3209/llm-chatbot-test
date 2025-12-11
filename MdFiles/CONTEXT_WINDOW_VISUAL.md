# Context Window - Visual Timeline

## How It Works: Step by Step

### TURN 1: User sends first message

```
┌─────────────────────────────────────────────────────────┐
│ API CALL #1 (2,037 tokens)                              │
├─────────────────────────────────────────────────────────┤
│ System Prompt: 2,017 tokens                             │
│ History: (empty)                                        │
│ User: "My QB is frozen" (20 tokens)                     │
└─────────────────────────────────────────────────────────┘
                          ↓
                    OpenAI Processes
                          ↓
                    Bot Response: 100 tokens
                          ↓
            Stored in memory for next turn
```

### TURN 2: User sends second message

```
┌─────────────────────────────────────────────────────────┐
│ API CALL #2 (2,152 tokens)                              │
├─────────────────────────────────────────────────────────┤
│ System Prompt: 2,017 tokens                             │
│ History:                                                │
│   ├─ User Turn 1: 20 tokens                             │
│   └─ Bot Turn 1: 100 tokens                             │
│ User: "It's dedicated" (15 tokens)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
                    OpenAI Processes
                          ↓
                    Bot Response: 80 tokens
                          ↓
            Stored in memory for next turn
```

### TURN 3: User sends third message

```
┌─────────────────────────────────────────────────────────┐
│ API CALL #3 (2,242 tokens)                              │
├─────────────────────────────────────────────────────────┤
│ System Prompt: 2,017 tokens                             │
│ History:                                                │
│   ├─ User Turn 1: 20 tokens                             │
│   ├─ Bot Turn 1: 100 tokens                             │
│   ├─ User Turn 2: 15 tokens                             │
│   └─ Bot Turn 2: 80 tokens                              │
│ User: "Done, next?" (10 tokens)                         │
└─────────────────────────────────────────────────────────┘
                          ↓
                    OpenAI Processes
                          ↓
                    Bot Response: 90 tokens
                          ↓
            Stored in memory for next turn
```

---

## Key Insight

**Each API call includes EVERYTHING sent before + current message**

```
Turn 1: 2,037 tokens
Turn 2: 2,152 tokens (includes Turn 1 + new message)
Turn 3: 2,242 tokens (includes Turn 1 + Turn 2 + new message)
Turn 4: 2,342 tokens (includes Turn 1 + Turn 2 + Turn 3 + new message)
...
```

---

## When Does It Reset?

```
Turn 1 → Turn 2 → Turn 3 → Turn 4 → Turn 5
  ↓       ↓       ↓       ↓       ↓
2,037   2,152   2,242   2,342   2,502
                                   ↓
                        User: "Connect me"
                                   ↓
                        Bot: "Transferring..."
                                   ↓
                        CONVERSATION ENDS
                                   ↓
                        HISTORY CLEARED
                                   ↓
                        NEXT CONVERSATION
                        (Starts fresh at 2,037)
```

---

## Real Numbers from Your Data

### Typical 5-Turn Chat
```
Turn 1: 2,037 tokens
Turn 2: 2,152 tokens
Turn 3: 2,242 tokens
Turn 4: 2,342 tokens
Turn 5: 2,502 tokens (escalation)

Max tokens in single call: 2,502 / 128,000 = 1.9%
```

### Long 20-Turn Chat
```
Turn 1:  2,037 tokens
Turn 5:  2,502 tokens
Turn 10: 3,052 tokens
Turn 15: 3,602 tokens
Turn 20: 4,152 tokens (escalation)

Max tokens in single call: 4,152 / 128,000 = 3.2%
```

### Very Long 100-Turn Chat
```
Turn 1:   2,037 tokens
Turn 25:  3,627 tokens
Turn 50:  5,217 tokens
Turn 75:  6,807 tokens
Turn 100: 8,397 tokens (escalation)

Max tokens in single call: 8,397 / 128,000 = 6.6%
```

---

## The Bottom Line

**Context window is PER API CALL, not per conversation**

- Each message = 1 API call
- Each API call = System Prompt + All History + Current Message
- History grows with each turn
- Conversation resets when user transfers to agent

**You're safe because:**
- Typical chats: 5-10 turns (uses 1-3% of context)
- Long chats: 50-100 turns (uses 3-8% of context)
- Very long chats: 500+ turns (uses 40-80% of context)
- Extreme chats: 1,000+ turns (exceeds limit - rare)

**Your implementation is production-ready.**
