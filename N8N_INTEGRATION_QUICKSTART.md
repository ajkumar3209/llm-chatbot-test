# 🚀 Quick Start: n8n Integration with Zoho SalesIQ

## Overview
This guide helps you integrate your RAG chatbot with Zoho SalesIQ using n8n as the middleware.

---

## ⚡ Quick Setup (15 minutes)

### Step 1: Start FastAPI Server (2 min)

```bash
# Install dependencies
pip install -r requirements_production.txt

# Start server
python fastapi_chatbot_server.py
```

Server will start at: `http://localhost:8000`

**Verify it's working:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "pinecone": "connected",
  "openai": "connected"
}
```

---

### Step 2: Test Server Locally (3 min)

```bash
python test_fastapi_server.py
```

This will run 5 tests:
1. ✅ Health check
2. ✅ New issue handling
3. ✅ Conversation continuation
4. ✅ Full conversation flow
5. ✅ Session management

All tests should pass!

---

### Step 3: Import n8n Workflow (5 min)

1. **Open n8n dashboard**
   - Go to your n8n instance (e.g., `https://your-n8n.com`)

2. **Import workflow**
   - Click "Add Workflow"
   - Click "Import from File"
   - Select `n8n_workflow.json`

3. **Configure HTTP Request node**
   - Click on "Call RAG Chatbot" node
   - Update URL to your server:
     ```
     http://your-server-ip:8000/chat
     ```
   - If testing locally, use:
     ```
     http://localhost:8000/chat
     ```

4. **Activate workflow**
   - Click "Active" toggle in top-right
   - Copy the webhook URL (e.g., `https://your-n8n.com/webhook/salesiq-webhook`)

---

### Step 4: Configure Zoho SalesIQ (5 min)

1. **Go to SalesIQ Settings**
   - Log in to Zoho SalesIQ
   - Settings → Developers → Webhooks

2. **Create webhook**
   - Click "Add Webhook"
   - Name: `RAG Chatbot`
   - URL: `https://your-n8n.com/webhook/salesiq-webhook`
   - Trigger: `On Message Received`
   - Method: `POST`

3. **Select payload fields:**
   - ✅ `visitor_id`
   - ✅ `chat_id`
   - ✅ `message`
   - ✅ `visitor_name` (optional)
   - ✅ `visitor_email` (optional)

4. **Test webhook**
   - Click "Test Webhook"
   - Check n8n execution log
   - Should see successful execution

---

## 🧪 Testing the Integration

### Test 1: Manual Test via n8n

1. Go to n8n workflow
2. Click "Execute Workflow" (play button)
3. Click on "Webhook" node
4. Click "Listen for Test Event"
5. Send test request:

```bash
curl -X POST https://your-n8n.com/webhook/salesiq-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "visitor_id": "test123",
    "chat_id": "chat456",
    "message": "How do I fix QuickBooks error -6189?"
  }'
```

6. Check n8n execution log
7. Should see response from chatbot

### Test 2: Live Test via SalesIQ

1. Open your website with SalesIQ widget
2. Start a chat
3. Type: "How do I fix QuickBooks error -6189?"
4. Bot should respond with first 1-2 steps
5. Reply: "Yes, done"
6. Bot should provide next steps

---

## 📊 Monitoring

### Check Server Status
```bash
curl http://your-server:8000/health
```

### Check Active Sessions
```bash
curl http://your-server:8000/sessions
```

### View n8n Executions
1. Go to n8n dashboard
2. Click "Executions" in sidebar
3. View recent webhook calls

### Monitor API Usage
- **OpenAI**: https://platform.openai.com/usage
- **Pinecone**: https://app.pinecone.io/

---

## 🔧 Configuration Options

### Adjust Response Length

Edit `fastapi_chatbot_server.py`:
```python
# Line ~180
max_tokens=300  # Change to 200 for shorter, 500 for longer
```

### Change Retrieval Count

Edit `fastapi_chatbot_server.py`:
```python
# Line ~150
context_docs = retrieve_context(message, top_k=3)  # Change to 2 or 5
```

### Modify System Prompt

Edit `fastapi_chatbot_server.py`:
```python
# Line ~160
system_prompt = """You are a helpful technical support assistant...
# Customize instructions here
"""
```

---

## 🐛 Troubleshooting

### Issue: Server won't start
**Solution:**
```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# Use different port
# Edit fastapi_chatbot_server.py, line ~280
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Issue: n8n can't reach server
**Solution:**
- If server is on localhost, n8n can't reach it
- Deploy server to public IP or use ngrok:
```bash
ngrok http 8000
# Use ngrok URL in n8n workflow
```

### Issue: Webhook not triggering
**Solution:**
- Check n8n workflow is active
- Verify webhook URL in SalesIQ
- Check firewall allows incoming connections

### Issue: Slow responses
**Solution:**
- Reduce `max_tokens` (300 → 200)
- Reduce `top_k` (3 → 2)
- Add caching for common queries

---

## 💰 Cost Estimate

### For 1,000 conversations/month (avg 6 turns each)

| Component | Usage | Cost |
|-----------|-------|------|
| OpenAI Embeddings | 6,000 calls | $0.06 |
| OpenAI GPT-4o-mini | 6,000 calls | $6.00 |
| Pinecone | 6,000 queries | $0.00 (free tier) |
| n8n (self-hosted) | Unlimited | $0.00 |
| Server (VPS) | 1 month | $5-20 |
| **TOTAL** | | **$11-26/month** |

**Per conversation: $0.011 (1.1 cents)**

---

## 🚀 Production Deployment

### Option 1: Docker (Recommended)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.10-slim
WORKDIR /app
COPY requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt
COPY . .
EXPOSE 8000
CMD ["python", "fastapi_chatbot_server.py"]
EOF

# Build and run
docker build -t rag-chatbot .
docker run -d -p 8000:8000 --env-file .env --name rag-chatbot rag-chatbot

# Check logs
docker logs -f rag-chatbot
```

### Option 2: systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/rag-chatbot.service

# Add content (see DEPLOYMENT_GUIDE.md)

# Start service
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot
sudo systemctl status rag-chatbot
```

### Option 3: Cloud Platforms

**AWS EC2:**
1. Launch t2.micro instance
2. Install Python and dependencies
3. Run server with systemd
4. Configure security group (port 8000)

**DigitalOcean:**
1. Create $5/month droplet
2. Follow systemd setup
3. Configure firewall

**Heroku:**
```bash
# Create Procfile
echo "web: python fastapi_chatbot_server.py" > Procfile

# Deploy
heroku create your-rag-chatbot
git push heroku main
```

---

## ✅ Deployment Checklist

Before going live:

- [ ] FastAPI server running and healthy
- [ ] Test endpoint responding correctly
- [ ] n8n workflow imported and active
- [ ] Webhook configured in SalesIQ
- [ ] End-to-end test successful
- [ ] Monitoring set up
- [ ] API keys secured
- [ ] Backup plan in place
- [ ] Team trained
- [ ] Documentation complete

---

## 📞 Next Steps

1. **Test thoroughly** with internal team
2. **Soft launch** with 10% of traffic
3. **Monitor** performance and costs
4. **Optimize** based on real usage
5. **Scale** as needed

---

## 🎉 You're Ready!

Your RAG chatbot is now integrated with Zoho SalesIQ via n8n!

**What happens now:**
1. User asks question in SalesIQ widget
2. Webhook sends to n8n
3. n8n calls your FastAPI server
4. Server retrieves from Pinecone
5. GPT-4o-mini generates response
6. Response sent back to user
7. Conversation continues step-by-step

**Result:** Intelligent, conversational support that guides users to resolution!

For detailed deployment instructions, see `DEPLOYMENT_GUIDE.md`
