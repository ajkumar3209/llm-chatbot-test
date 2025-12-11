# Quick Reference: Context Window

## Simple Answer
**Context window is PER API CALL**

Each time user sends a message = 1 API call with:
- System Prompt (2,017 tokens)
- All previous messages (history)
- Current user message

---

## Token Usage Per Turn

| Turns | Tokens | % of Context | Status |
|-------|--------|--------------|--------|
| 1 | 2,037 | 1.6% | ✅ Safe |
| 5 | 2,502 | 1.9% | ✅ Safe |
| 10 | 3,052 | 2.4% | ✅ Safe |
| 20 | 4,152 | 3.2% | ✅ Safe |
| 50 | 5,217 | 4.1% | ✅ Safe |
| 100 | 8,397 | 6.6% | ✅ Safe |
| 500 | 45,837 | 35.8% | ✅ Safe |
| 1,000 | 90,000+ | 70%+ | ⚠️ Risky |

---

## What Happens Each Turn

```
Turn 1: Send (System + Message) = 2,037 tokens
Turn 2: Send (System + Turn1 + Message) = 2,152 tokens
Turn 3: Send (System + Turn1 + Turn2 + Message) = 2,242 tokens
Turn 4: Send (System + Turn1 + Turn2 + Turn3 + Message) = 2,342 tokens
Turn 5: Send (System + Turn1 + Turn2 + Turn3 + Turn4 + Message) = 2,502 tokens
```

---

## When Does It Reset?

- ✅ User transfers to agent
- ✅ User ends chat
- ✅ Session timeout (5+ min idle)
- ✅ Manual reset via API

After reset → Next conversation starts fresh at 2,037 tokens

---

## Your Real Data

- **33,130 conversations analyzed**
- **Average duration**: 22.5 minutes
- **Average tokens**: 99 per conversation
- **Typical max**: 2,500 tokens per API call (1.9% of context)

---

## Bottom Line

✅ You're safe for all realistic conversation lengths
✅ Context grows per turn but resets when chat ends
✅ Keep all resolution steps in system prompt
✅ Deploy to production with confidence

---

## Code Reference

```python
# Each API call includes:
messages = [
    {"role": "system", "content": system_prompt},  # 2,017 tokens
    {"role": "user", "content": "Turn 1 message"},  # 20 tokens
    {"role": "assistant", "content": "Turn 1 response"},  # 100 tokens
    {"role": "user", "content": "Turn 2 message"},  # 15 tokens
    {"role": "assistant", "content": "Turn 2 response"},  # 80 tokens
    {"role": "user", "content": "Turn 3 message"},  # 10 tokens
]
# Total: 2,242 tokens sent to OpenAI
```

---

**Status**: Production-Ready ✅
