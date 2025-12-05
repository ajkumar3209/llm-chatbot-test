# 🚀 RAG Chatbot - Quick Reference

## ✅ Current Status
- **Pinecone Index**: `support-chatbot` (5,487 vectors loaded)
- **Status**: ✅ Ready for production use
- **Last Updated**: December 5, 2025

---

## 🎯 Quick Commands

### Test the Chatbot
```bash
python test_chatbot.py
```
Runs 3 automated test queries to verify everything works.

### Interactive Chat
```bash
python rag_chatbot.py
```
Start chatting! Type your questions, get AI responses. Type 'quit' to exit.

### Check Pinecone Stats
```bash
python check_pinecone_stats.py
```
View index statistics and vector count.

---

## 📊 What's in the Database

| Source | Count | Priority | Purpose |
|--------|-------|----------|---------|
| KB/SOP Articles | 216 | HIGH | Authoritative step-by-step solutions |
| Chat Transcripts | 5,271 | MEDIUM | Natural language query matching |
| **TOTAL** | **5,487** | - | Complete knowledge base |

---

## 💡 Example Queries

Try asking:
- "How do I fix QuickBooks error -6189?"
- "My server keeps disconnecting"
- "How to backup Lacerte data?"
- "Reset password for Office 365"
- "QuickBooks multi-user access error"
- "Server reconnecting issue"

---

## 🔑 API Keys Location

File: `.env`
```
OPENAI_API_KEY=sk-proj-...
PINECONE_API_KEY=pcsk_...
```

---

## 💰 Cost Tracking

### Monitor Usage
- **OpenAI**: https://platform.openai.com/usage
- **Pinecone**: https://app.pinecone.io/

### Expected Monthly Cost (1,000 queries)
- Embeddings: ~$0.01
- Pinecone: ~$10-15
- GPT-4o-mini: ~$20-30
- **Total**: ~$30-50/month

---

## 🔧 Configuration

### Change LLM Model
Edit `rag_chatbot.py`:
```python
LLM_MODEL = "gpt-4o-mini"  # Change to gpt-4o, gpt-4-turbo, etc.
```

### Adjust Retrieval Count
Edit `rag_chatbot.py`:
```python
context_docs = retrieve_context(query, top_k=5)  # Change 5 to 3, 10, etc.
```

### Modify Response Style
Edit the system prompt in `generate_response()` function in `rag_chatbot.py`.

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `rag_chatbot.py` | Main interactive chatbot |
| `test_chatbot.py` | Automated testing |
| `ingest_to_pinecone_v2.py` | Data ingestion (re-run to update data) |
| `check_pinecone_stats.py` | View index statistics |
| `processed_data/FINAL_QUALITY_FILTERED.jsonl` | Source data |
| `.env` | API keys |
| `SUCCESS_SUMMARY.md` | Complete project summary |

---

## 🆘 Troubleshooting

### "SSL Certificate Error"
✅ Already fixed! We use REST API with `verify=False`.

### "Index not found"
Check index name in Pinecone dashboard. Should be `support-chatbot`.

### "API key invalid"
Verify keys in `.env` file. No quotes, no spaces.

### "No results returned"
Check if data was ingested: `python check_pinecone_stats.py`

### "Response quality poor"
Try adjusting:
- `top_k` (retrieve more documents)
- `temperature` (lower = more focused)
- System prompt (add more instructions)

---

## 🔄 Update Data

To add new KB articles or chat transcripts:

1. Add new files to respective folders
2. Re-run processing scripts
3. Re-run ingestion:
   ```bash
   python ingest_to_pinecone_v2.py
   ```

---

## 📈 Next Steps

### Immediate
- [x] Test with real support queries
- [ ] Share with support team for feedback
- [ ] Monitor response quality

### Short-term (1-2 weeks)
- [ ] Deploy as web service (FastAPI)
- [ ] Add authentication
- [ ] Create simple web UI

### Long-term (1-3 months)
- [ ] Integrate with existing support portal
- [ ] Add conversation memory
- [ ] Implement automatic ticket creation
- [ ] Multi-language support

---

## 📞 Need Help?

All scripts include error handling and detailed output. If something fails:
1. Check the error message
2. Verify API keys in `.env`
3. Run `python check_pinecone_stats.py` to verify index
4. Check OpenAI/Pinecone dashboards for usage/errors

---

**🎉 Your RAG chatbot is ready to replace Zoho Zobot!**

Start with `python test_chatbot.py` to see it in action.
