"""
FastAPI Chatbot Server for Zoho SalesIQ Integration via n8n
Provides webhook endpoint for interactive step-by-step support.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import urllib3
import uvicorn
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Ace Cloud Hosting Support Bot", version="1.0.0")

# CORS middleware for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "support-chatbot"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Get Pinecone index host
def get_index_host():
    headers = {
        "Api-Key": PINECONE_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.pinecone.io/indexes",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    
    indexes = response.json()
    for idx in indexes.get('indexes', []):
        if idx['name'] == INDEX_NAME:
            return idx['host']
    
    raise Exception(f"Index '{INDEX_NAME}' not found")

INDEX_HOST = get_index_host()
PINECONE_HEADERS = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json"
}

# In-memory conversation storage (use Redis in production)
conversations: Dict[str, List[Dict]] = {}

# Request/Response Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str  # Unique ID from Zoho SalesIQ
    message: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    session_id: str
    response: str
    is_new_issue: bool
    retrieved_articles: Optional[List[str]] = []
    timestamp: str

def retrieve_context(query: str, top_k: int = 3):
    """Retrieve relevant documents from Pinecone."""
    # Generate query embedding
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Search Pinecone
    url = f"https://{INDEX_HOST}/query"
    payload = {
        "vector": query_embedding,
        "topK": top_k,
        "includeMetadata": True
    }
    
    response = requests.post(
        url,
        headers=PINECONE_HEADERS,
        json=payload,
        verify=False
    )
    response.raise_for_status()
    results = response.json()
    
    return results.get('matches', [])

def is_new_issue(message: str, history: List[Dict]) -> bool:
    """Determine if this is a new issue or continuation."""
    if len(history) == 0:
        return True
    
    continuation_keywords = [
        "yes", "done", "completed", "next", "continue", "ok", "okay",
        "no", "didn't work", "error", "failed", "stuck", "help"
    ]
    
    message_lower = message.lower()
    
    # Short responses are usually continuations
    if len(message.split()) <= 5:
        for keyword in continuation_keywords:
            if keyword in message_lower:
                return False
    
    # Long questions about different topics are new issues
    if any(word in message_lower for word in ["how", "what", "why", "can", "fix", "error", "issue"]):
        if len(message.split()) > 5:
            return True
    
    return False

def build_context(context_docs: List[Dict]) -> str:
    """Build context string from retrieved documents."""
    context_parts = []
    
    for doc in context_docs:
        source = doc['metadata']['source']
        
        if source == 'kb_article':
            title = doc['metadata'].get('title', 'KB Article')
            context_parts.append(f"[KB Article] {title}\n{doc['metadata']['text']}")
        else:
            context_parts.append(f"[Support Chat]\n{doc['metadata']['text']}")
    
    return "\n\n---\n\n".join(context_parts)

def generate_response(message: str, history: List[Dict], context: Optional[str] = None) -> str:
    """Generate response using GPT-4o-mini."""
    
    system_prompt = """You are a helpful technical support assistant for Ace Cloud Hosting.

CRITICAL INSTRUCTIONS FOR STEP-BY-STEP GUIDANCE:
1. When user asks about a technical issue, provide ONLY the first 1-2 steps
2. After each step, ask "Have you completed this?" or "Did this work?"
3. Wait for user confirmation before providing next steps
4. If user says "yes" or "done", provide the NEXT 1-2 steps
5. If user says "no" or reports an error, troubleshoot that specific step
6. Keep responses SHORT and FOCUSED (3-5 sentences max)
7. Be conversational, friendly, and encouraging
8. Track progress through the resolution process
9. When issue is resolved, congratulate and ask if they need anything else

EXAMPLE GOOD RESPONSE:
"Let's fix this together. First:
1. Close QuickBooks completely
2. Open QuickBooks Tool Hub

Have you completed these steps?"

EXAMPLE BAD RESPONSE (DON'T DO THIS):
"Here are all 15 steps: Step 1... Step 2... Step 3... [dumps everything]"

Remember: Guide step-by-step, not all at once!"""
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add context if available (only for new issues)
    if context and len(history) == 0:
        context_message = f"""Here is relevant information from our knowledge base:

{context}

Use this to guide the user step-by-step. Remember: Show only 1-2 steps at a time!"""
        messages.append({"role": "system", "content": context_message})
    
    # Add conversation history
    messages.extend(history)
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Generate response
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )
    
    return response.choices[0].message.content

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Ace Cloud Hosting Support Bot",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "reset": "/reset/{session_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {
        "status": "healthy",
        "pinecone": "connected",
        "openai": "connected",
        "active_sessions": len(conversations)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for n8n webhook.
    
    Receives message from Zoho SalesIQ via n8n, processes it, and returns response.
    """
    try:
        session_id = request.session_id
        message = request.message
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Determine if new issue
        new_issue = is_new_issue(message, history)
        
        context = None
        retrieved_articles = []
        
        # If new issue, retrieve context from Pinecone
        if new_issue:
            context_docs = retrieve_context(message, top_k=3)
            
            if context_docs:
                context = build_context(context_docs)
                retrieved_articles = [
                    doc['metadata'].get('title', 'KB Article')
                    for doc in context_docs
                    if doc['metadata']['source'] == 'kb_article'
                ]
        
        # Generate response
        response_text = generate_response(message, history, context)
        
        # Update conversation history
        conversations[session_id].append({"role": "user", "content": message})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        # Return response
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            is_new_issue=new_issue,
            retrieved_articles=retrieved_articles if retrieved_articles else None,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset/{session_id}")
async def reset_conversation(session_id: str):
    """Reset conversation for a session."""
    if session_id in conversations:
        del conversations[session_id]
        return {"status": "success", "message": f"Conversation {session_id} reset"}
    return {"status": "not_found", "message": f"Session {session_id} not found"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions (for debugging)."""
    return {
        "active_sessions": len(conversations),
        "sessions": list(conversations.keys())
    }

if __name__ == "__main__":
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    
    print("="*70)
    print("ACE CLOUD HOSTING - SUPPORT BOT SERVER")
    print("="*70)
    print(f"\n🚀 Starting FastAPI server on port {port}...")
    print(f"📍 Endpoint: http://0.0.0.0:{port}")
    print(f"📖 Docs: http://0.0.0.0:{port}/docs")
    print("\n✅ Ready to receive webhooks from n8n!")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
