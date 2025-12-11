# Ace Cloud Hosting Support Bot - Hybrid LLM

Production-ready support chatbot using GPT-4o-mini with embedded resolution steps. No RAG layer, no vector database, no Pinecone dependency.

## 🎯 Architecture

**LLM-Based Approach**: Resolution steps embedded directly in system prompt. GPT-4o-mini intelligently selects and presents steps based on user context.

```
User → Zoho SalesIQ Widget → FastAPI Server → OpenAI GPT-4o-mini
```

## ✨ Key Features

- **10 Common Issues**: Disk space, QuickBooks frozen, password reset, RDP display, etc.
- **Smart Escalation**: 3 options when issue not resolved
  - Instant Chat (transfer to human agent)
  - Schedule Callback (collect time + phone)
  - Create Support Ticket (collect details)
- **Conversation Memory**: Full chat history maintained per session
- **One-Step-at-a-Time**: Guides users through troubleshooting step by step
- **SalesIQ Integration**: Native JSON response format for Zoho SalesIQ webhook
- **Railway Ready**: Deploy in 5 minutes

## 🚀 Quick Start

### 1. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-proj-your-key-here

# Run locally
python fastapi_chatbot_hybrid.py
```

Server runs on `http://localhost:8000`

### 2. Deploy to Railway

1. Push to GitHub
2. Go to https://railway.app/new
3. Select this repository
4. Add environment variable: `OPENAI_API_KEY=sk-proj-your-key-here`
5. Railway auto-deploys and generates domain

### 3. Connect to Zoho SalesIQ

In SalesIQ Bot Settings:
- Webhook URL: `https://your-app.up.railway.app/webhook/salesiq`
- Method: POST
- Test webhook

## 📋 Resolution Steps Included

1. **QuickBooks Frozen (Dedicated Server)**
2. **QuickBooks Frozen (Shared Server)**
3. **QuickBooks Error 15212/12159**
4. **Low Disk Space**
5. **Password Reset (Selfcare Enrolled)**
6. **Password Reset (Not Enrolled)**
7. **RDP Display Settings**
8. **MyPortal Password Reset**
9. **Lacerte/Drake/ProSeries Frozen**

## 🔌 API Endpoints

- `GET /` - Health check + endpoints info
- `GET /health` - Service health
- `POST /webhook/salesiq` - Zoho SalesIQ webhook
- `POST /chat` - Direct chat endpoint
- `GET /sessions` - List active sessions
- `POST /reset/{session_id}` - Reset conversation

## 📊 Response Format (SalesIQ JSON)

```json
{
  "action": "reply",
  "replies": ["Your response here"],
  "session_id": "session-123"
}
```

For agent transfer:
```json
{
  "action": "transfer",
  "transfer_to": "human_agent",
  "session_id": "session-123",
  "conversation_history": "Full chat history...",
  "replies": ["Connecting you with a support agent..."]
}
```

## 🧪 Testing

Test locally:
```bash
curl -X POST http://localhost:8000/webhook/salesiq \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": {"text": "My QuickBooks is frozen"},
    "visitor": {"id": "user-123"}
  }'
```

## 📁 Project Structure

```
.
├── fastapi_chatbot_hybrid.py  # Main bot server
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (local)
├── .env.example               # Example env file
├── Procfile                   # Railway deployment config
├── railway.json               # Railway settings
└── README.md                  # This file
```

## 🔐 Environment Variables

```
OPENAI_API_KEY=sk-proj-your-key-here
PORT=8000  # Optional, defaults to 8000
```

## 💡 How It Works

1. **User sends message** via SalesIQ widget
2. **Webhook received** at `/webhook/salesiq`
3. **LLM processes** with embedded resolution steps
4. **Response generated** with one step at a time
5. **Conversation stored** in memory per session
6. **If not resolved** → Show 3 escalation options
7. **If agent selected** → Transfer with full history

## 🎯 Conversation Flow

```
User: "My QuickBooks is frozen"
Bot: "Are you using a dedicated server or a shared server?"
User: "Dedicated"
Bot: "Step 1: Right click and open Task Manager on the server. Have you completed this?"
User: "Yes"
Bot: "Step 2: Go to Users, click on your username and expand it. Have you completed this?"
...
User: "Still not working"
Bot: [Shows 3 options: Instant Chat, Schedule Callback, Create Ticket]
```

## 🚀 Production Checklist

- [ ] Test all 10 resolution steps locally
- [ ] Verify SalesIQ webhook integration
- [ ] Test 3 escalation options
- [ ] Deploy to Railway
- [ ] Monitor `/health` endpoint
- [ ] Set up error logging
- [ ] Test file sharing in SalesIQ (if enabled)

## 📞 Support

For issues:
1. Check `/health` endpoint
2. Review server logs
3. Verify `OPENAI_API_KEY` is set
4. Test webhook with curl

## 📝 Notes

- No Pinecone or vector database needed
- No n8n workflow required (direct Railway deployment)
- Conversation history stored in memory (resets on server restart)
- For persistent storage, add database layer
- File sharing via SalesIQ native file attachment (enable in bot settings)

---

**Status**: Production-ready for testing on Railway
