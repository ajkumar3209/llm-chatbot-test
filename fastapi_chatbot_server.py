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
# Store context for each session
session_contexts: Dict[str, str] = {}

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
    """
    Retrieve relevant KB articles from Pinecone.
    Now using KB articles only for cleaner, more predictable responses.
    """
    # Expand short queries for better retrieval
    expanded_query = query
    query_lower = query.lower()
    
    # Fix common typos and incomplete words
    if ('porta' in query_lower or 'my portal' in query_lower) and 'myportal' not in query_lower:
        expanded_query = query_lower.replace('porta', 'myportal').replace('my portal', 'myportal')
        expanded_query = f"password reset using myportal"
    
    # Only expand if it's a QuickBooks-specific query
    if len(query.split()) <= 4:
        # Check if query is about QuickBooks
        qb_keywords = ['quickbooks', 'qb', 'company file', 'lacerte', 'drake', 'proseries']
        if any(keyword in query_lower for keyword in qb_keywords):
            expanded_query = f"How to {query} in QuickBooks"
        else:
            # For non-QB queries, just add "How to"
            expanded_query = f"How to {query}"
    
    # Generate query embedding
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=expanded_query
    )
    query_embedding = response.data[0].embedding
    
    # Query Pinecone for KB articles only
    url = f"https://{INDEX_HOST}/query"
    payload = {
        "vector": query_embedding,
        "topK": top_k,
        "includeMetadata": True,
        "filter": {"source": {"$eq": "kb_article"}}
    }
    
    response = requests.post(
        url,
        headers=PINECONE_HEADERS,
        json=payload,
        verify=False
    )
    response.raise_for_status()
    results = response.json().get('matches', [])
    
    # Filter for good matches (>0.4 similarity)
    good_results = [m for m in results if m['score'] > 0.4]
    
    if good_results:
        print(f"[Context] Found {len(good_results)} relevant KB articles")
    else:
        print(f"[Context] No relevant KB articles found (threshold: 0.4)")
    
    return good_results

def is_new_issue(message: str, history: List[Dict]) -> bool:
    """Determine if this is a new issue or continuation."""
    if len(history) == 0:
        return True
    
    message_lower = message.lower()
    
    # Resolution keywords - user is done
    resolution_keywords = ["resolved", "fixed", "working now", "solved", "all set", "that's it", "thank you", "thanks"]
    
    # If user says issue is resolved, treat as NEW (to end conversation)
    if any(keyword in message_lower for keyword in resolution_keywords):
        return True
    
    # IMPORTANT: Check technical keywords FIRST before continuation keywords
    # This ensures "quickbooks frozen" is detected as NEW, not continuation
    # BUT: Exclude simple answers like "shared server", "dedicated", "yes", "no"
    technical_keywords = [
        "quickbooks", "frozen", "error", "issue", "problem", "not working",
        "disk space", "password", "reset", "lacerte", "drake",
        "outlook", "email", "printer", "install", "setup", "configure"
    ]
    
    # Check if message is a simple answer to a question or correction
    # Examples: "shared server", "dedicated", "yes enrolled", "not enrolled"
    # Also: "but i am on a shared server", "actually it's dedicated"
    correction_patterns = [
        "shared server", "dedicated server", "shared", "dedicated",
        "i am on", "i'm on", "actually", "but i", "no i"
    ]
    
    # If message contains correction patterns and server type, treat as continuation
    if any(pattern in message_lower for pattern in correction_patterns):
        if "shared" in message_lower or "dedicated" in message_lower:
            return False
    
    # Check if message is a simple answer (1-3 words)
    if len(message.split()) <= 3:
        # These are likely answers to clarifying questions, treat as continuation
        simple_answers = ["yes", "no", "enrolled", "not enrolled"]
        if any(answer in message_lower for answer in simple_answers):
            return False
    
    if any(keyword in message_lower for keyword in technical_keywords):
        return True
    
    # Simple continuation keywords (1-3 words)
    continuation_keywords = ["yes", "done", "completed", "next", "ok", "okay", "continue"]
    
    # If message is ONLY a continuation keyword, it's a continuation
    if message_lower.strip() in continuation_keywords:
        return False
    
    # If message is very short (1-3 words) and contains continuation keywords
    if len(message.split()) <= 3:
        if any(keyword in message_lower for keyword in continuation_keywords):
            return False
    
    # Long messages (>5 words) are usually new issues
    if len(message.split()) > 5:
        return True
    
    return False

def build_context(context_docs: List[Dict]) -> str:
    """Build context string from retrieved KB articles."""
    context_parts = []
    
    for doc in context_docs:
        title = doc['metadata'].get('title', 'KB Article')
        text = doc['metadata'].get('text', '')
        context_parts.append(f"[KB Article] {title}\n{text}")
    
    return "\n\n---\n\n".join(context_parts)

def generate_response(message: str, history: List[Dict], context: Optional[str] = None) -> str:
    """Generate response using GPT-4o-mini."""
    
    system_prompt = """You are AceBuddy, a technical support assistant for Ace Cloud Hosting.

YOUR JOB: Help users with technical issues and provide information in a SIMPLE, CONCISE way.

CRITICAL RULES:

FOR PROCEDURAL CONTENT (troubleshooting steps):
1. ONLY use steps that are EXPLICITLY in the knowledge base
2. Give steps in sequential order: 1-2, then 3-4, then 5, etc.
3. SIMPLIFY the steps - remove unnecessary details, keep only essential actions
4. Use SHORT sentences - max 10-15 words per sentence
5. After giving 1-2 steps, ask "Have you completed this?"
6. If the KB content doesn't match the user's question, say "Our support team can assist you better with this. Please contact them at 1-888-415-5240."

FOR INFORMATIONAL CONTENT (pricing, plans, features, general info):
1. Present ALL information at once (don't break into steps)
2. Use clear formatting (bullet points or numbered list)
3. Keep it SHORT and SIMPLE
4. End with "Would you like to know more?"

ASKING CLARIFYING QUESTIONS - CRITICAL:

For QuickBooks/Lacerte/Drake/ProSeries FROZEN issues ONLY:
1. FIRST ask: "Are you using a dedicated server or a shared server?"
2. WAIT for their answer
3. THEN provide the appropriate steps based on their server type

For OTHER QuickBooks issues (errors, installation, setup, etc.):
- Provide general steps directly, do NOT ask server type

DO NOT provide any troubleshooting steps for FROZEN issues until you know the server type.
DO NOT offer to connect with human agent first - always ask server type and provide steps.

Examples:
User: "My QuickBooks is frozen" → Ask server type first
User: "QuickBooks error 15212" → Provide steps directly (no server type needed)
User: "How to install QuickBooks" → Provide steps directly (no server type needed)

HANDLING "NOT WORKING" OR "STUCK":
If user says steps didn't work, they're stuck, or same issue persists, THEN offer human agent:
"I understand this is frustrating. Would you like me to connect you with a human agent? (Reply 'yes' to connect)"

POSITIVE LANGUAGE: Always use positive, helpful language. Instead of "I don't have" say "Our support team can assist you better".

SIMPLIFICATION EXAMPLES:

BAD (too verbose):
"Step 1: Contact your account owner to reset your password. The account owner has access to MyPortal (myportal.acecloudhosting.com) and can reset passwords for all users."

GOOD (simple and concise):
"Step 1: Ask your account owner to reset your password via MyPortal."

BAD (too detailed):
"Step 1: Visit Selfcare Portal https://selfcare.acecloudhosting.com Click 'Forgot your password'. Step 2: Enter your Server Username."

GOOD (simplified):
"Step 1: Go to selfcare.acecloudhosting.com and click 'Forgot Password'.
Step 2: Enter your server username."

CRITICAL: Keep responses SHORT and SIMPLE. Users want quick, easy-to-follow instructions.

SPECIAL HANDLING FOR PASSWORD RESET - CRITICAL:
When user asks about password reset:
1. FIRST ask: "Are you enrolled in the Selfcare Portal? (Reply 'yes' or 'no')"
2. WAIT for their answer
3. If yes: Provide Selfcare password reset steps (step-by-step)
4. If no: Provide Selfcare ENROLLMENT steps first (step-by-step)

DO NOT provide any password reset steps until you know enrollment status.
If user is not enrolled, help them enroll first so they can reset passwords themselves.

Example:
User: "Can you help me with password reset"
Bot: "Are you enrolled in the Selfcare Portal? (Reply 'yes' or 'no')"
User: "No"
Bot: "Let me help you enroll first. Step 1: Go to selfcare.acecloudhosting.com. Have you completed this?"

CRITICAL: Always break enrollment into small steps (1-2 at a time) and ask "Have you completed this?" after each set.

CONTINUATION KEYWORDS:
During multi-step processes (enrollment, troubleshooting), treat these as continuation:
- "okay", "ok", "done", "next", "continue", "what are the next steps", "okay then"
Only treat them as acknowledgment if conversation is complete.

HANDLING VAGUE QUERIES:
For other vague questions with relevant KB article, ask a clarifying question.

If no relevant KB article is found, offer to connect them with support at 1-888-415-5240."""
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add context if available (for both new issues AND continuations)
    if context and context.strip():
        context_message = f"""KNOWLEDGE BASE CONTENT:

{context}

IMPORTANT: 
- If this is PROCEDURAL (troubleshooting steps), give steps 1-2 first, then wait for confirmation
- If this is INFORMATIONAL (pricing, plans, features), present ALL information at once
- For procedural: Ask "Have you completed this?" after each set of steps
- For informational: Ask "Would you like to know more?" at the end
- Copy the exact text, do not paraphrase"""
        messages.append({"role": "system", "content": context_message})
    elif not context or not context.strip():
        # No good context found
        return "Our support team can assist you better with this. Please contact them at:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com"
    
    # Add a safety instruction to prevent hallucination
    messages.append({"role": "system", "content": "CRITICAL: Use the knowledge base content if it's RELATED to the user's question, even if not an exact match. For example, 'RDP display settings' articles can help with 'dual display setup'. Only say 'Our support team can assist you better with this. Please contact them at 1-888-415-5240.' if the content is completely unrelated. DO NOT make up steps that aren't in the knowledge base. Always use positive, helpful language."})
    
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
            "salesiq_webhook": "/webhook/salesiq (Use this for SalesIQ)",
            "chat": "/chat (For n8n integration)",
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

@app.post("/webhook/salesiq")
async def salesiq_webhook(request: dict):
    """
    Direct webhook endpoint for Zoho SalesIQ.
    Handles SalesIQ webhook format and returns response in the exact format SalesIQ expects.
    
    Expected Input:
    {
        "session_id": "abc123",
        "message": {"text": "user message"}
    }
    
    Required Output:
    {
        "action": "reply",
        "replies": ["bot response"],
        "session_id": "abc123"
    }
    """
    try:
        # Log incoming request for debugging
        print(f"[SalesIQ] Received: {request}")
        
        # Extract session_id from SalesIQ's nested structure
        visitor = request.get('visitor', {})
        session_id = (
            visitor.get('active_conversation_id') or 
            request.get('session_id') or 
            request.get('visitor', {}).get('id') or
            'unknown'
        )
        
        # Extract message text from nested structure
        message_obj = request.get('message', {})
        message_text = message_obj.get('text', '') if isinstance(message_obj, dict) else str(message_obj)
        
        # Handle empty messages (greeting)
        if not message_text or message_text.strip() == '':
            print(f"[SalesIQ] Empty message, sending greeting")
            return {
                "action": "reply",
                "replies": ["Hi! I'm AceBuddy, your Ace Cloud Hosting support assistant. What can I help you with today?"],
                "session_id": session_id
            }
        
        print(f"[SalesIQ] Session: {session_id}, Message: {message_text}")
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Handle simple greetings without RAG
        message_lower = message_text.lower().strip()
        greeting_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'hi there', 'hello there', 'hey there', 'greetings', 'howdy'
        ]
        
        # Check if message is ONLY a greeting (no technical question)
        is_greeting = (
            message_lower in greeting_patterns or
            (len(message_text.split()) <= 3 and any(g in message_lower for g in ['hello', 'hi', 'hey', 'morning', 'afternoon', 'evening']))
        )
        
        if is_greeting and len(history) == 0:
            print(f"[SalesIQ] Simple greeting detected")
            return {
                "action": "reply",
                "replies": ["Hello! How can I assist you today?"],
                "session_id": session_id
            }
        
        # Handle contact/support requests directly (but not technical issues mentioning email/phone)
        contact_request_phrases = ['support email', 'support number', 'contact support', 'phone number', 'email address', 'how to contact', 'reach support']
        if any(phrase in message_lower for phrase in contact_request_phrases):
            print(f"[SalesIQ] Contact request detected")
            return {
                "action": "reply",
                "replies": ["You can reach Ace Cloud Hosting support at:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com\n\nHow else can I help you?"],
                "session_id": session_id
            }
        
        # Handle simple acknowledgments (okay, thanks, etc.) - don't trigger new retrieval
        # CRITICAL: Check if we're in the middle of multi-step troubleshooting FIRST
        # If last bot message asked "Have you completed this?", then "okay" means continuation
        is_in_troubleshooting = False
        if len(history) > 0:
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'have you completed this?' in last_bot_message.lower() or 'completed this?' in last_bot_message.lower():
                is_in_troubleshooting = True
                print(f"[SalesIQ] In multi-step troubleshooting")
        
        # Handle acknowledgments
        acknowledgment_keywords = ["okay", "ok", "thanks", "thank you", "got it", "understood", "alright"]
        is_acknowledgment = (
            message_lower in acknowledgment_keywords or 
            (message_lower in ["okay thanks", "ok thanks", "thank you very much", "thanks a lot"])
        )
        # Exclude "okay then", "ok then" which are continuations
        if 'then' in message_lower:
            is_acknowledgment = False
        
        if is_acknowledgment:
            # If in troubleshooting and user says just "okay" or "ok" → continuation
            if is_in_troubleshooting and message_lower in ["okay", "ok"]:
                print(f"[SalesIQ] 'Okay' in troubleshooting, treating as continuation")
                # Let it fall through to generate_response for next steps
            # If user says "thanks" or "okay thanks" → acknowledge
            else:
                print(f"[SalesIQ] Acknowledgment detected")
                # If there's no history, just say you're welcome
                if len(history) == 0:
                    return {
                        "action": "reply",
                        "replies": ["You're welcome! Let me know if you need anything else."],
                        "session_id": session_id
                    }
                # If there's history, acknowledge and offer help
                return {
                    "action": "reply",
                    "replies": ["You're welcome! Is there anything else I can help you with?"],
                    "session_id": session_id
                }
        
        # Handle conversational phrases - user saying they'll try/check/test
        # These should be acknowledged naturally, not trigger KB retrieval
        
        # Check for "will try/check" phrases FIRST (more specific)
        will_try_phrases = [
            "let me check", "i will check", "i'll check", "let me try", "i will try", "i'll try",
            "let me test", "i will test", "i'll test", "let me see", "i will see", "i'll see",
            "will inform you", "will let you know", "get back to you", "inform you later",
            "check and inform", "try and inform", "test and inform", "check your process",
            "try your steps", "follow your steps", "will do", "will follow"
        ]
        if any(phrase in message_lower for phrase in will_try_phrases):
            print(f"[SalesIQ] User will try steps")
            return {
                "action": "reply",
                "replies": ["Sure! Take your time and let me know if you need any help or have questions."],
                "session_id": session_id
            }
        
        # Check for clarification phrases (less specific, check after)
        clarification_phrases = ["i did not say", "didn't say anything", "i am saying", "just saying"]
        if any(phrase in message_lower for phrase in clarification_phrases):
            print(f"[SalesIQ] User clarifying")
            return {
                "action": "reply",
                "replies": ["I understand. How can I help you?"],
                "session_id": session_id
            }
        
        # Check if user says issue is NOT resolved (check NEGATIVE first!)
        not_resolved_keywords = ["not resolved", "not fixed", "not working", "didn't work", "doesn't work", "still not", "still frozen", "still stuck", "not solved"]
        if any(keyword in message_lower for keyword in not_resolved_keywords):
            print(f"[SalesIQ] Issue NOT resolved - user needs more help")
            # Offer human agent
            return {
                "action": "reply",
                "replies": ["I understand this is frustrating. Would you like me to connect you with a human agent who can provide personalized assistance? (Reply 'yes' to connect)"],
                "session_id": session_id
            }
        
        # Check if user says issue IS resolved (only if NOT negative)
        resolution_keywords = ["resolved", "fixed", "working now", "solved", "all set", "that's it"]
        if any(keyword in message_lower for keyword in resolution_keywords):
            print(f"[SalesIQ] Issue resolved by user")
            # Clear context
            if session_id in session_contexts:
                del session_contexts[session_id]
            if session_id in conversations:
                del conversations[session_id]
            return {
                "action": "reply",
                "replies": ["Great! I'm glad the issue is resolved. If you need anything else, feel free to ask!"],
                "session_id": session_id
            }
        
        # Handle upgrade requests - these require contacting support
        upgrade_keywords = ["upgrade", "increase disk", "add storage", "more space", "expand disk"]
        if any(keyword in message_lower for keyword in upgrade_keywords):
            # Check if they're asking HOW to upgrade (not just asking about options)
            if any(word in message_lower for word in ["how", "process", "steps", "procedure"]):
                print(f"[SalesIQ] Upgrade request detected")
                return {
                    "action": "reply",
                    "replies": ["To upgrade your disk space, please contact our support team:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com\n\nThey'll help you upgrade to the plan that fits your needs!"],
                    "session_id": session_id
                }
        
        # Handle out-of-scope topics (Windows updates, OS issues, etc.)
        out_of_scope = ["windows update", "windows 11", "operating system", "os update", "system update"]
        if any(keyword in message_lower for keyword in out_of_scope):
            print(f"[SalesIQ] Out-of-scope topic detected")
            return {
                "action": "reply",
                "replies": ["For Windows and operating system issues, please contact our support team directly:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com\n\nThey can help with OS-level troubleshooting!"],
                "session_id": session_id
            }
        
        # Check if user wants human agent (after trying steps)
        if len(history) > 0 and ('yes' in message_lower or 'connect' in message_lower):
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'connect you with a human agent' in last_bot_message:
                print(f"[SalesIQ] User requested human agent after trying steps")
                # Clear context and direct to support
                if session_id in session_contexts:
                    del session_contexts[session_id]
                if session_id in conversations:
                    del conversations[session_id]
                return {
                    "action": "reply",
                    "replies": ["I'll connect you with a human agent now.\n\nYou can also reach our support team directly:\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com"],
                    "session_id": session_id
                }
        
        # Detect if user is stuck or steps didn't work
        # IMPORTANT: Only detect "stuck" when user says steps DIDN'T WORK
        # Don't include "frozen" here - it's a valid issue description, not a stuck indicator
        stuck_keywords = ["not working", "didn't work", "still not", "still stuck", "doesn't work", "not fixed", "same issue", "same problem"]
        if any(keyword in message_lower for keyword in stuck_keywords):
            print(f"[SalesIQ] User is stuck, will offer human agent")
            # Don't clear context yet, let LLM offer human agent option
        
        # Special handling for password reset flow
        # If user says "no" after being asked about enrollment, get enrollment steps
        if len(history) > 0 and message_lower in ["no", "not enrolled"]:
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'enrolled in the selfcare portal' in last_bot_message.lower():
                print(f"[SalesIQ] User not enrolled, retrieving enrollment steps")
                try:
                    context_docs = retrieve_context("enroll selfcare portal", top_k=3)
                    if context_docs:
                        context = build_context(context_docs)
                        session_contexts[session_id] = context
                        print(f"[SalesIQ] Retrieved enrollment context")
                except Exception as e:
                    print(f"[SalesIQ] Enrollment retrieval failed: {str(e)}")
                    context = None
            else:
                # Regular "no" continuation
                context = session_contexts.get(session_id)
        else:
            # Determine if new issue
            new_issue = is_new_issue(message_text, history)
            
            # If it's a new issue, clear old context
            if new_issue and session_id in session_contexts:
                print(f"[SalesIQ] New issue detected, clearing old context")
                del session_contexts[session_id]
            
            context = None
            
            # If new issue, retrieve context from Pinecone
            if new_issue:
                print(f"[SalesIQ] New issue detected, retrieving context...")
                try:
                    context_docs = retrieve_context(message_text, top_k=3)
                    if context_docs:
                        context = build_context(context_docs)
                        # Store context for this session
                        session_contexts[session_id] = context
                        print(f"[SalesIQ] Retrieved {len(context_docs)} context documents")
                except Exception as e:
                    print(f"[SalesIQ] Context retrieval failed: {str(e)}")
                    # Continue without context
            else:
                # Continuation - use stored context if available
                context = session_contexts.get(session_id)
                if context:
                    print(f"[SalesIQ] Using stored context for continuation")
        
        # Generate response
        print(f"[SalesIQ] Calling OpenAI...")
        if context:
            print(f"[SalesIQ] Context preview: {context[:300]}...")
        response_text = generate_response(message_text, history, context)
        
        # Clean response - remove markdown but preserve special characters like %temp%
        # Only remove markdown bold (**) and bullet points at start of lines
        response_text = response_text.replace('**', '')
        # Remove bullet point asterisks only at start of lines, not in middle of text
        import re
        response_text = re.sub(r'^\s*\*\s+', '- ', response_text, flags=re.MULTILINE)
        response_text = response_text.strip()
        
        # Remove excessive line breaks (replace double/triple newlines with single)
        import re
        response_text = re.sub(r'\n\s*\n+', '\n', response_text)
        
        # Don't truncate - let full response through
        # SalesIQ can handle longer messages
        
        print(f"[SalesIQ] Response: {response_text}")
        
        # Update conversation history
        conversations[session_id].append({"role": "user", "content": message_text})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        # Return in EXACT SalesIQ expected format
        return {
            "action": "reply",
            "replies": [response_text],
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"[SalesIQ] ERROR: {str(e)}")
        # Return error in SalesIQ format
        return {
            "action": "reply",
            "replies": ["I'm having technical difficulties. Please call our support team at 1-888-415-5240."],
            "session_id": request.get('session_id', 'unknown')
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
    reset_count = 0
    if session_id in conversations:
        del conversations[session_id]
        reset_count += 1
    if session_id in session_contexts:
        del session_contexts[session_id]
        reset_count += 1
    
    if reset_count > 0:
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
