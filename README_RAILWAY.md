# 🚂 RAG Chatbot - Railway Deployment

## 🎯 Quick Deploy to Railway

Your intelligent support chatbot is ready to deploy to Railway for testing!

---

## ⚡ 5-Minute Deployment

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "RAG Chatbot"
git push
```

### 2. Deploy on Railway
1. Go to https://railway.app/new
2. Select your GitHub repo
3. Click "Deploy Now"

### 3. Add API Keys
```
OPENAI_API_KEY=your-key
PINECONE_API_KEY=your-key
```

### 4. Get Your URL
```
https://your-app.up.railway.app
```

### 5. Test It
```bash
curl https://your-app.up.railway.app/health
```

---

## 📚 Documentation

- **Quick Start**: `RAILWAY_QUICKSTART.md` (5 min)
- **Full Guide**: `RAILWAY_DEPLOYMENT.md` (detailed)
- **Integration**: `N8N_INTEGRATION_QUICKSTART.md`
- **Summary**: `DEPLOYMENT_SUMMARY.md`

---

## 🧪 Testing

```bash
# Test Railway deployment
python test_railway_deployment.py https://your-app.up.railway.app

# Test locally first
python test_fastapi_server.py
```

---

## 🏗️ Architecture

```
User → Zoho SalesIQ → n8n → Railway (Your Chatbot) → Pinecone + OpenAI
```

---

## 💰 Cost

- **Railway**: $0-5/month (free tier)
- **OpenAI**: $6-10/month
- **Pinecone**: $0 (free tier)
- **Total**: $6-15/month

---

## ✅ What's Included

- ✅ 5,487 documents in Pinecone
- ✅ Interactive step-by-step guidance
- ✅ Conversation memory
- ✅ FastAPI webhook server
- ✅ n8n workflow template
- ✅ Complete documentation

---

## 🚀 Next Steps

1. Deploy to Railway (5 min)
2. Connect to n8n (5 min)
3. Configure Zoho SalesIQ (10 min)
4. Test end-to-end
5. Go live!

---

## 📞 Support

- Railway: https://railway.app/dashboard
- OpenAI: https://platform.openai.com
- Pinecone: https://app.pinecone.io

---

**Start here**: `RAILWAY_QUICKSTART.md` 🚂
