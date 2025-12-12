# Railway Indentation Error - FIXED

## Problem

Railway was crashing with:
```
IndentationError: unexpected indent
File "/app/fastapi_chatbot_hybrid.py", line 677
messages = [{"role": "system", "content": system_prompt}]
```

## Root Cause

The `generate_response()` function definition was missing. The code had:
- ❌ System prompt string (closed with `"""`)
- ❌ Orphaned code with indentation (messages = [...])
- ❌ No function definition

## Solution Applied ✅

Added the missing function definition:

```python
def generate_response(message: str, history: List[Dict]) -> str:
    """Generate response using LLM with embedded resolution steps"""
    
    system_prompt = EXPERT_PROMPT
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )
    
    return response.choices[0].message.content
```

## What Changed

**Before**:
```python
"""
[System prompt content]
"""
    
    messages = [...]  # ❌ Orphaned, no function
```

**After**:
```python
"""
[System prompt content]
"""

def generate_response(message: str, history: List[Dict]) -> str:
    """Generate response using LLM with embedded resolution steps"""
    
    system_prompt = EXPERT_PROMPT
    
    messages = [...]  # ✅ Inside function
```

## Deploy Now

```bash
# 1. Commit fix
git add fastapi_chatbot_hybrid.py
git commit -m "Fix: Add missing generate_response function definition"

# 2. Push to Railway
git push railway main

# 3. Monitor deployment
railway logs --follow
```

## Expected Output

After deployment, you should see:
```
======================================================================
ACE CLOUD HOSTING - SUPPORT BOT (HYBRID LLM)
======================================================================

🚀 Starting FastAPI server on port 8000...
✅ Ready to receive webhooks from n8n!
======================================================================
```

## Verification

### Test 1: Health Check
```bash
curl https://your-railway-url.railway.app/health
```

Expected:
```json
{
  "status": "healthy",
  "openai": "connected",
  "active_sessions": 0
}
```

### Test 2: Webhook
```bash
curl -X POST https://your-railway-url.railway.app/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": {"text": "hello"}, "visitor": {"id": "user"}}'
```

Expected:
```json
{
  "action": "reply",
  "replies": ["Hello! I'm AceBuddy. How can I assist you today?"],
  "session_id": "test"
}
```

### Test 3: Logs
```bash
railway logs --follow
```

Should show:
```
[SalesIQ] Webhook received
[SalesIQ] Session ID: test
[SalesIQ] Message: hello
[SalesIQ] Response generated: Hello! I'm AceBuddy...
```

## Status

✅ **FIXED** - Ready to deploy

