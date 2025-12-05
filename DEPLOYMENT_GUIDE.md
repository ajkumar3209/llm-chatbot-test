# 🚀 Deployment Guide: Zoho SalesIQ + n8n + RAG Chatbot

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER VISITS YOUR WEBSITE                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Zoho SalesIQ Chat Widget (Embedded)                │
│  User types: "How do I fix QuickBooks error -6189?"            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (Webhook)
┌─────────────────────────────────────────────────────────────────┐
│                      n8n Workflow Engine                        │
│  1. Receives webhook from SalesIQ                               │
│  2. Extracts: session_id, message, visitor_info                 │
│  3. Calls FastAPI chatbot server                                │
│  4. Formats response                                            │
│  5. Sends back to SalesIQ                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (HTTP Request)
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Chatbot Server (Your RAG Bot)              │
│  1. Receives: session_id + message                              │
│  2. Checks if new issue or continuation                         │
│  3. If new: Retrieves from Pinecone                             │
│  4. Generates response with GPT-4o-mini                         │
│  5. Returns: response + metadata                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Pinecone + OpenAI APIs                         │
│  - Pinecone: Vector search (5,487 documents)                    │
│  - OpenAI: Embeddings + GPT-4o-mini generation                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Response to User                             │
│  "Let's fix this together. First:                               │
│   1. Close QuickBooks completely                                │
│   2. Open QuickBooks Tool Hub                                   │
│   Have you completed these steps?"                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

### 1. Zoho SalesIQ Account
- Active SalesIQ subscription
- Chat widget installed on your website
- Webhook configuration access

### 2. n8n Instance
- Self-hosted or cloud n8n
- Public URL accessible by Zoho SalesIQ
- Example: `https://your-n8n.com`

### 3. Server for FastAPI
- VPS or cloud server (AWS, DigitalOcean, etc.)
- Python 3.8+
- Public IP or domain
- Example: `https://your-chatbot-server.com`

### 4. API Keys (Already Have)
- ✅ OpenAI API key
- ✅ Pinecone API key

---

## 🔧 Step-by-Step Setup

### STEP 1: Deploy FastAPI Chatbot Server

#### Option A: Local Testing (Development)
```bash
# Install dependencies
pip install fastapi uvicorn python-dotenv openai requests

# Run server
python fastapi_chatbot_server.py
```
Server will run at: `http://localhost:8000`

#### Option B: Production Deployment (Recommended)

**Using Docker:**
```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

COPY requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt
RUN pip install fastapi uvicorn

COPY . .

EXPOSE 8000

CMD ["python", "fastapi_chatbot_server.py"]
EOF

# Build and run
docker build -t rag-chatbot .
docker run -d -p 8000:8000 --env-file .env rag-chatbot
```

**Using systemd (Linux server):**
```bash
# Create service file
sudo nano /etc/systemd/system/rag-chatbot.service

# Add this content:
[Unit]
Description=RAG Chatbot Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Ragv1
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python fastapi_chatbot_server.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot
sudo systemctl status rag-chatbot
```

**Test the server:**
```bash
curl http://your-server:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "pinecone": "connected",
  "openai": "connected",
  "active_sessions": 0
}
```

---

### STEP 2: Set Up n8n Workflow

#### 1. Import Workflow
1. Open your n8n dashboard
2. Click "Add Workflow" → "Import from File"
3. Upload `n8n_workflow.json`

#### 2. Configure Webhook Node
1. Click on "Webhook - Zoho SalesIQ" node
2. Set path: `salesiq-webhook`
3. Copy the webhook URL (e.g., `https://your-n8n.com/webhook/salesiq-webhook`)

#### 3. Configure HTTP Request Node
1. Click on "Call RAG Chatbot" node
2. Update URL to your FastAPI server:
   ```
   http://your-chatbot-server.com:8000/chat
   ```
3. Ensure method is POST
4. Body parameters:
   - `session_id`: `={{$json.session_id}}`
   - `message`: `={{$json.message}}`

#### 4. Activate Workflow
1. Click "Active" toggle in top-right
2. Workflow is now listening for webhooks

---

### STEP 3: Configure Zoho SalesIQ Webhook

#### 1. Access SalesIQ Settings
1. Log in to Zoho SalesIQ
2. Go to Settings → Developers → Webhooks

#### 2. Create New Webhook
1. Click "Add Webhook"
2. Name: `RAG Chatbot Integration`
3. Webhook URL: `https://your-n8n.com/webhook/salesiq-webhook`
4. Trigger: `On Message Received`
5. Method: `POST`

#### 3. Configure Payload
Select these fields to send:
- `visitor_id` (session identifier)
- `chat_id` (conversation ID)
- `message` (user's message)
- `visitor_name` (optional)
- `visitor_email` (optional)

#### 4. Test Webhook
1. Click "Test Webhook"
2. Check n8n execution log
3. Verify response received

---

### STEP 4: Configure SalesIQ Bot

#### 1. Create Bot in SalesIQ
1. Go to Settings → Bots
2. Click "Add Bot"
3. Name: `Ace Support Assistant`
4. Type: `Webhook Bot`

#### 2. Configure Bot Behavior
1. **Greeting Message:**
   ```
   Hi! I'm your Ace Cloud Hosting support assistant. 
   I can help you with QuickBooks, server issues, and more.
   What can I help you with today?
   ```

2. **Webhook Configuration:**
   - Enable "Use webhook for responses"
   - Webhook URL: `https://your-n8n.com/webhook/salesiq-webhook`

3. **Fallback Message:**
   ```
   I'm having trouble connecting. Let me transfer you to a human agent.
   ```

#### 3. Set Bot Rules
1. **When to trigger:**
   - On new chat
   - When visitor asks a question
   - During business hours (optional)

2. **When to escalate:**
   - If user types "agent" or "human"
   - If issue not resolved after 10 messages
   - If user expresses frustration

---

## 🧪 Testing the Integration

### Test 1: End-to-End Flow
1. Open your website with SalesIQ widget
2. Start a chat
3. Type: "How do I fix QuickBooks error -6189?"
4. Verify bot responds with first 1-2 steps
5. Reply: "Yes, done"
6. Verify bot provides next steps
7. Continue until issue resolved

### Test 2: Check n8n Logs
1. Open n8n dashboard
2. Go to "Executions"
3. Check recent executions
4. Verify:
   - Webhook received
   - HTTP request sent to chatbot
   - Response returned to SalesIQ

### Test 3: Check FastAPI Logs
```bash
# View server logs
tail -f /var/log/rag-chatbot.log

# Or if using systemd
sudo journalctl -u rag-chatbot -f
```

### Test 4: Monitor API Usage
- **OpenAI Dashboard:** https://platform.openai.com/usage
- **Pinecone Dashboard:** https://app.pinecone.io/

---

## 📊 Monitoring & Analytics

### 1. n8n Monitoring
- Track execution success rate
- Monitor response times
- Set up error alerts

### 2. FastAPI Monitoring
Add logging to `fastapi_chatbot_server.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
```

### 3. SalesIQ Analytics
- Track bot engagement rate
- Monitor resolution rate
- Analyze common queries

---

## 💰 Cost Optimization

### Current Setup Costs (1,000 chats/month)
| Component | Cost |
|-----------|------|
| OpenAI (embeddings + generation) | $6-10/month |
| Pinecone (vector search) | $0 (free tier) |
| n8n (self-hosted) | $0 (or $20/month cloud) |
| Server (VPS) | $5-20/month |
| **TOTAL** | **$11-50/month** |

### Optimization Tips
1. **Cache common queries** (reduce OpenAI calls)
2. **Use Redis** for conversation storage (faster than in-memory)
3. **Implement rate limiting** (prevent abuse)
4. **Monitor usage** (set budget alerts)

---

## 🔒 Security Best Practices

### 1. API Key Security
```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use environment variables
export OPENAI_API_KEY="your-key"
export PINECONE_API_KEY="your-key"
```

### 2. Webhook Authentication
Add authentication to n8n webhook:
```javascript
// In n8n function node
const authHeader = $input.item.headers.authorization;
const expectedToken = "your-secret-token";

if (authHeader !== `Bearer ${expectedToken}`) {
  throw new Error("Unauthorized");
}
```

### 3. Rate Limiting
Add to FastAPI:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    # ... existing code
```

---

## 🐛 Troubleshooting

### Issue 1: Webhook Not Receiving Data
**Check:**
- n8n workflow is active
- Webhook URL is correct in SalesIQ
- Firewall allows incoming connections

**Test:**
```bash
curl -X POST https://your-n8n.com/webhook/salesiq-webhook \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test123","message":"test"}'
```

### Issue 2: Chatbot Not Responding
**Check:**
- FastAPI server is running: `curl http://your-server:8000/health`
- API keys are valid
- Pinecone index exists

**Test:**
```bash
curl -X POST http://your-server:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"How do I fix QuickBooks error?"}'
```

### Issue 3: Slow Response Times
**Solutions:**
- Increase server resources
- Reduce `top_k` in retrieval (3 → 2)
- Reduce `max_tokens` in generation (300 → 200)
- Add caching for common queries

---

## 🚀 Next Steps

### Phase 1: Testing (Week 1)
- [ ] Deploy FastAPI server
- [ ] Set up n8n workflow
- [ ] Configure SalesIQ webhook
- [ ] Test with internal team

### Phase 2: Soft Launch (Week 2)
- [ ] Enable for 10% of visitors
- [ ] Monitor performance
- [ ] Collect feedback
- [ ] Fix issues

### Phase 3: Full Rollout (Week 3)
- [ ] Enable for all visitors
- [ ] Set up monitoring alerts
- [ ] Train support team
- [ ] Document common issues

### Phase 4: Optimization (Ongoing)
- [ ] Add conversation analytics
- [ ] Implement caching
- [ ] Fine-tune prompts
- [ ] Add new KB articles

---

## 📞 Support

If you encounter issues:
1. Check server logs
2. Review n8n execution logs
3. Test each component individually
4. Verify API keys and connections

---

## ✅ Deployment Checklist

- [ ] FastAPI server deployed and running
- [ ] Health endpoint responding
- [ ] n8n workflow imported and active
- [ ] Webhook URL configured in SalesIQ
- [ ] Bot created in SalesIQ
- [ ] End-to-end test successful
- [ ] Monitoring set up
- [ ] Error alerts configured
- [ ] Team trained on system
- [ ] Documentation complete

---

**🎉 Your RAG chatbot is ready to replace Zoho Zobot!**

The system will now:
- Receive messages from SalesIQ
- Process through n8n
- Generate intelligent responses
- Guide users step-by-step
- Resolve issues efficiently
