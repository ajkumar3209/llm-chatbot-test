# 🚂 Railway Quick Start (5 Minutes)

## ⚡ Super Fast Deployment

### Step 1: Push to GitHub (2 min)

```bash
# If not already initialized
git init
git add .
git commit -m "RAG Chatbot for Railway"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy on Railway (2 min)

1. **Go to Railway**: https://railway.app/new
2. **Click**: "Deploy from GitHub repo"
3. **Select**: Your `rag-chatbot` repository
4. **Click**: "Deploy Now"

Railway will automatically:
- ✅ Detect Python
- ✅ Install dependencies
- ✅ Start your server

---

### Step 3: Add Environment Variables (1 min)

1. **Click** on your deployed service
2. **Go to** "Variables" tab
3. **Add** these variables:

```
OPENAI_API_KEY=sk-proj-your-key-here
PINECONE_API_KEY=pcsk_your-key-here
```

4. **Save** - Railway will auto-redeploy

---

### Step 4: Get Your URL (30 sec)

1. **Go to** "Settings" tab
2. **Scroll to** "Networking"
3. **Click** "Generate Domain"
4. **Copy** your URL: `https://your-app.up.railway.app`

---

### Step 5: Test It! (30 sec)

```bash
# Replace with your Railway URL
curl https://your-app.up.railway.app/health
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

## ✅ You're Done!

Your chatbot is now live at: `https://your-app.up.railway.app`

### Use this URL in n8n:
```
https://your-app.up.railway.app/chat
```

---

## 🧪 Full Test

```bash
python test_railway_deployment.py https://your-app.up.railway.app
```

This will test:
- ✅ Health check
- ✅ Chat endpoint
- ✅ Conversation memory
- ✅ Session management

---

## 🐛 Troubleshooting

### App not starting?
**Check logs:**
1. Railway dashboard → Your service
2. "Deployments" tab → Latest deployment
3. View logs

**Common issues:**
- Missing environment variables
- Wrong Python version
- API connection failures

### Environment variables not working?
1. Go to "Variables" tab
2. Ensure no extra spaces
3. Click "Redeploy"

### Slow first request?
- Normal! Cold start takes 5-10 seconds
- Subsequent requests are fast

---

## 💰 Cost

**Free tier**: $5 credits/month
**Your usage**: ~$3-5/month
**Perfect for testing!**

---

## 🔗 Next: Connect to n8n

1. Open your n8n workflow
2. Update "Call RAG Chatbot" node URL to:
   ```
   https://your-app.up.railway.app/chat
   ```
3. Test the integration
4. Connect to Zoho SalesIQ

---

## 📚 Full Guide

For detailed instructions, see: `RAILWAY_DEPLOYMENT.md`

---

**That's it! Your RAG chatbot is live on Railway! 🎉**
