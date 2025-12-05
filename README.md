# 🤖 RAG Chatbot - Intelligent Support Assistant

AI-powered support chatbot with step-by-step guidance for Zoho SalesIQ integration.

## 🎯 Features

- ✅ **5,487 documents** in Pinecone vector database
- ✅ **Interactive step-by-step guidance** (not overwhelming)
- ✅ **Conversation memory** across multiple turns
- ✅ **Smart retrieval** from KB articles and chat history
- ✅ **Natural responses** powered by GPT-4o-mini
- ✅ **Webhook endpoint** for n8n integration
- ✅ **Railway-ready** deployment

## 🚀 Quick Deploy to Railway

### 1. Deploy on Railway
1. Go to https://railway.app/new
2. Select this GitHub repository
3. Click "Deploy Now"

### 2. Add Environment Variables
In Railway dashboard, add:
```
OPENAI_API_KEY=sk-proj-your-key-here
PINECONE_API_KEY=pcsk_your-key-here
```

### 3. Generate Domain
- Go to Settings → Networking
- Click "Generate Domain"
- Copy your URL: `https://your-app.up.railway.app`

### 4. Test It
```bash
curl https://your-app.up.railway.app/health
```

## 📊 Architecture

```
User → Zoho SalesIQ → n8n → Railway (Chatbot) → Pinecone + OpenAI
```

## 💰 Cost

- **Railway**: $0-5/month (free tier)
- **OpenAI**: $6-10/month
- **Pinecone**: $0 (free tier)
- **Total**: $6-15/month for 1,000 conversations

## 📚 Documentation

- **Quick Start**: `RAILWAY_QUICKSTART.md`
- **Full Deployment**: `RAILWAY_DEPLOYMENT.md`
- **n8n Integration**: `N8N_INTEGRATION_QUICKSTART.md`
- **Complete Guide**: `DEPLOYMENT_SUMMARY.md`

## 🧪 Testing

After deployment, test with:
```bash
python test_railway_deployment.py https://your-app.up.railway.app
```

## 🔗 Integration

1. Deploy to Railway (5 min)
2. Import `n8n_workflow.json` into n8n
3. Configure Zoho SalesIQ webhook
4. Test end-to-end

## 📞 API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat endpoint (webhook)
- `GET /sessions` - Active sessions
- `GET /docs` - API documentation

## ✅ What's Included

- FastAPI webhook server
- Conversation memory management
- Step-by-step guidance system
- n8n workflow template
- Complete documentation

## 🎉 Ready to Deploy!

Follow `RAILWAY_QUICKSTART.md` to get started in 5 minutes!
