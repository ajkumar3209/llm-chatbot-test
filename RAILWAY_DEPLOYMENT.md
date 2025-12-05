# 🚂 Railway Deployment Guide

## Quick Deploy to Railway (5 minutes)

Railway is perfect for testing before moving to n8n. It's free for hobby projects and super easy to deploy!

---

## 📋 Prerequisites

1. **GitHub Account** (to connect Railway)
2. **Railway Account** (sign up at https://railway.app)
3. **API Keys** (you already have these):
   - OpenAI API key
   - Pinecone API key

---

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository (2 min)

#### Option A: Push to GitHub (Recommended)

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "RAG Chatbot ready for Railway deployment"

# Create GitHub repo and push
# Go to github.com → New Repository → "rag-chatbot"
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git
git branch -M main
git push -u origin main
```

#### Option B: Use Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init
```

---

### Step 2: Deploy to Railway (3 min)

#### Using GitHub (Recommended):

1. **Go to Railway Dashboard**
   - Visit https://railway.app/dashboard
   - Click "New Project"

2. **Deploy from GitHub**
   - Click "Deploy from GitHub repo"
   - Select your repository: `rag-chatbot`
   - Click "Deploy Now"

3. **Railway will automatically:**
   - Detect Python project
   - Install dependencies from `requirements_production.txt`
   - Run `python fastapi_chatbot_server.py`

#### Using Railway CLI:

```bash
# In your project directory
railway up

# Railway will deploy automatically
```

---

### Step 3: Configure Environment Variables (1 min)

1. **Go to your Railway project**
   - Click on your deployed service

2. **Add Variables**
   - Click "Variables" tab
   - Click "New Variable"
   - Add these:

```
OPENAI_API_KEY=sk-proj-your-openai-key-here
PINECONE_API_KEY=pcsk_your-pinecone-key-here
PORT=8000
```

3. **Save**
   - Railway will automatically redeploy with new variables

---

### Step 4: Get Your Public URL (30 seconds)

1. **Generate Domain**
   - Go to "Settings" tab
   - Scroll to "Networking"
   - Click "Generate Domain"
   - You'll get a URL like: `https://your-app.up.railway.app`

2. **Copy this URL** - you'll use it in n8n!

---

### Step 5: Test Your Deployment (1 min)

```bash
# Test health endpoint
curl https://your-app.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "pinecone": "connected",
  "openai": "connected",
  "active_sessions": 0
}
```

```bash
# Test chat endpoint
curl -X POST https://your-app.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "message": "How do I fix QuickBooks error -6189?"
  }'

# Should return bot response!
```

---

## 📊 Railway Dashboard Features

### View Logs
1. Go to your service
2. Click "Deployments" tab
3. Click on latest deployment
4. View real-time logs

### Monitor Usage
1. Go to "Metrics" tab
2. See:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Check Deployments
1. Go to "Deployments" tab
2. See deployment history
3. Rollback if needed

---

## 💰 Railway Pricing

### Free Tier (Hobby Plan)
- **$5 free credits/month**
- **500 hours execution time**
- **Perfect for testing!**

### Estimated Usage
- Your chatbot: ~$3-5/month on Railway
- OpenAI + Pinecone: ~$6-10/month
- **Total: ~$9-15/month**

### If you exceed free tier:
- Upgrade to Developer plan: $5/month
- Pay-as-you-go for usage

---

## 🔧 Configuration Files Created

### `railway.json`
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python fastapi_chatbot_server.py",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### `Procfile`
```
web: python fastapi_chatbot_server.py
```

### `runtime.txt`
```
python-3.10.12
```

### `.railwayignore`
Excludes unnecessary files from deployment (test files, docs, etc.)

---

## 🧪 Testing Your Railway Deployment

### Test 1: Health Check
```bash
curl https://your-app.up.railway.app/health
```

### Test 2: Chat Endpoint
```bash
curl -X POST https://your-app.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "railway_test",
    "message": "How do I backup Lacerte data?"
  }'
```

### Test 3: API Documentation
Visit: `https://your-app.up.railway.app/docs`

You'll see interactive API documentation (Swagger UI)!

---

## 🔗 Connect to n8n

Once deployed on Railway, update your n8n workflow:

1. **Open n8n workflow**
2. **Click "Call RAG Chatbot" node**
3. **Update URL to:**
   ```
   https://your-app.up.railway.app/chat
   ```
4. **Save and activate workflow**

---

## 🐛 Troubleshooting

### Issue: Deployment Failed

**Check build logs:**
1. Go to "Deployments" tab
2. Click failed deployment
3. Check logs for errors

**Common fixes:**
- Ensure `requirements_production.txt` is correct
- Check Python version in `runtime.txt`
- Verify all imports are available

### Issue: App Crashes on Start

**Check runtime logs:**
1. Go to "Deployments" tab
2. Click on deployment
3. View logs

**Common causes:**
- Missing environment variables (OPENAI_API_KEY, PINECONE_API_KEY)
- Port binding issue (Railway sets PORT automatically)
- API connection failures

### Issue: Slow Response Times

**Solutions:**
1. Upgrade Railway plan (more resources)
2. Reduce `max_tokens` in chatbot (300 → 200)
3. Reduce `top_k` in retrieval (3 → 2)
4. Add caching

### Issue: Environment Variables Not Working

**Fix:**
1. Go to "Variables" tab
2. Ensure no extra spaces in keys/values
3. Click "Redeploy" after adding variables
4. Check logs to verify variables loaded

---

## 📈 Monitoring & Maintenance

### View Logs in Real-Time
```bash
# Using Railway CLI
railway logs
```

### Check Service Status
```bash
# Health check
curl https://your-app.up.railway.app/health

# Active sessions
curl https://your-app.up.railway.app/sessions
```

### Monitor API Usage
- **OpenAI**: https://platform.openai.com/usage
- **Pinecone**: https://app.pinecone.io/
- **Railway**: Dashboard → Metrics

---

## 🔄 Updating Your Deployment

### Method 1: Git Push (Automatic)
```bash
# Make changes to code
git add .
git commit -m "Update chatbot"
git push

# Railway automatically redeploys!
```

### Method 2: Railway CLI
```bash
# Deploy latest changes
railway up
```

### Method 3: Manual Redeploy
1. Go to Railway dashboard
2. Click "Deployments" tab
3. Click "Redeploy" on latest deployment

---

## 🎯 Next Steps After Railway Deployment

### 1. Test Thoroughly
- [ ] Health endpoint working
- [ ] Chat endpoint responding
- [ ] Conversation memory working
- [ ] API keys configured correctly

### 2. Connect to n8n
- [ ] Update n8n workflow with Railway URL
- [ ] Test n8n → Railway connection
- [ ] Verify end-to-end flow

### 3. Connect to Zoho SalesIQ
- [ ] Configure SalesIQ webhook to n8n
- [ ] Test full integration
- [ ] Monitor first conversations

### 4. Monitor & Optimize
- [ ] Check Railway metrics
- [ ] Monitor API costs
- [ ] Optimize based on usage
- [ ] Collect user feedback

---

## 💡 Railway vs Other Platforms

| Feature | Railway | Heroku | AWS EC2 | DigitalOcean |
|---------|---------|--------|---------|--------------|
| **Setup Time** | 5 min | 10 min | 30 min | 20 min |
| **Free Tier** | $5 credits | Limited | No | No |
| **Auto Deploy** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Easy Logs** | ✅ Yes | ✅ Yes | ⚠️ Manual | ⚠️ Manual |
| **Custom Domain** | ✅ Free | ✅ Free | ✅ Yes | ✅ Yes |
| **Scaling** | ✅ Easy | ✅ Easy | ⚠️ Manual | ⚠️ Manual |
| **Best For** | Testing | Production | Enterprise | Production |

**Railway is perfect for your use case: Quick testing before full production!**

---

## ✅ Deployment Checklist

Before deploying:
- [x] `railway.json` created
- [x] `Procfile` created
- [x] `runtime.txt` created
- [x] `.railwayignore` created
- [x] `requirements_production.txt` updated
- [x] FastAPI server uses PORT env variable
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables added
- [ ] Domain generated
- [ ] Health check passing
- [ ] Chat endpoint tested

---

## 🎉 You're Ready!

Your chatbot will be deployed to Railway in minutes!

**What you'll get:**
- ✅ Public HTTPS URL (e.g., `https://your-app.up.railway.app`)
- ✅ Automatic SSL certificate
- ✅ Auto-deploy on git push
- ✅ Real-time logs
- ✅ Easy environment variable management
- ✅ Free tier for testing

**Railway URL Format:**
```
https://your-app-name-production.up.railway.app
```

Use this URL in your n8n workflow!

---

## 📞 Quick Commands Reference

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Open in browser
railway open

# Check status
railway status

# Add environment variable
railway variables set OPENAI_API_KEY=your-key

# Link to existing project
railway link
```

---

## 🚀 Deploy Now!

1. Push code to GitHub
2. Go to https://railway.app/new
3. Select your repo
4. Add environment variables
5. Generate domain
6. Test with curl
7. Connect to n8n

**Total time: 5-10 minutes!**

Good luck with your deployment! 🎊
