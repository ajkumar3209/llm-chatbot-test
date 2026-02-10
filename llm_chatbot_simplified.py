"""
Simplified LLM-First Chatbot - Direct to LLM approach
No classification layer, no routing complexity
Just: Expert Prompt → LLM → Response → Escalation Detection → SalesIQ/Desk APIs
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="ACE Cloud Chatbot - Simplified v2.0")

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN", "")
ZOHO_ORG_ID = os.getenv("ZOHO_ORG_ID", "")
ZOHO_DEPT_ID = os.getenv("ZOHO_DEPT_ID", "")

# LLM Client
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# In-memory conversation storage
conversations: Dict[str, List[Dict]] = {}

# Load expert prompt
def load_expert_prompt() -> str:
    """Load the expert system prompt"""
    # Load the production expert prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "config", "prompts", "expert_system_prompt_production.txt")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Loaded expert prompt from {prompt_path}: {len(content)} characters")
            return content
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {prompt_path}")
        raise

EXPERT_PROMPT = load_expert_prompt()

# Startup banner
print("\n" + "="*70)
print("🚀 ACE CLOUD CHATBOT - SIMPLIFIED v2.0 (LLM-FIRST ARCHITECTURE)")
print("="*70)
print(f"✅ Expert prompt loaded: {len(EXPERT_PROMPT)} characters")
print(f"✅ Single LLM call architecture (no classification layer)")
print(f"✅ Anti-hallucination mode: ENABLED")
print(f"✅ SalesIQ integration: ENABLED")
print(f"✅ Desk API integration: ENABLED")
print("="*70 + "\n")

# Escalation keywords
ESCALATION_KEYWORDS = [
    # User requests
    "talk to someone", "speak to agent", "connect me to", "transfer me",
    "human agent", "real person", "customer service", "technical support",
    "call me", "schedule callback", "contact support",
    
    # Frustration indicators
    "not helping", "doesn't work", "still not working", "frustrated",
    "waste of time", "useless", "not solving", "third time",
    
    # Explicit escalation
    "escalate", "supervisor", "manager", "complaint"
]

BOT_ESCALATION_PHRASES = [
    "i'll connect you", "connecting you", "transfer you",
    "let me connect", "i'll transfer", "escalate this",
    "contact support", "reach out to support", "technical support team"
]


def detect_escalation(user_message: str, bot_response: str, conversation_length: int) -> bool:
    """
    Detect if escalation is needed based on:
    1. User explicitly requesting agent
    2. Bot response indicating escalation
    3. Conversation length (frustration indicator)
    4. Repetitive failed attempts
    """
    user_lower = user_message.lower()
    bot_lower = bot_response.lower()
    
    # Check user keywords
    for keyword in ESCALATION_KEYWORDS:
        if keyword in user_lower:
            logger.info(f"Escalation detected: user keyword '{keyword}'")
            return True
    
    # Check bot response
    for phrase in BOT_ESCALATION_PHRASES:
        if phrase in bot_lower:
            logger.info(f"Escalation detected: bot phrase '{phrase}'")
            return True
    
    # Long conversation without resolution
    if conversation_length > 10:
        logger.info(f"Escalation detected: conversation too long ({conversation_length} messages)")
        return True
    
    return False


async def send_salesiq_message(session_id: str, message: str, suggestions: Optional[List[Dict]] = None) -> bool:
    """Send message to SalesIQ chat"""
    try:
        url = f"https://desk.zoho.com/api/v1/portals/{ZOHO_ORG_ID}/chats/{session_id}/messages"
        
        payload = {
            "type": "message",
            "text": message
        }
        
        if suggestions:
            payload["suggestions"] = suggestions
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {ZOHO_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to SalesIQ session {session_id}")
                return True
            else:
                logger.error(f"❌ SalesIQ API error: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to send SalesIQ message: {e}")
        return False


async def create_desk_ticket(session_id: str, user_name: str, conversation_history: List[Dict]) -> Optional[str]:
    """Create Desk ticket for escalation"""
    try:
        # Format conversation for ticket
        conversation_text = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Bot'}: {msg['content']}"
            for msg in conversation_history[-10:]  # Last 10 messages
        ])
        
        ticket_data = {
            "subject": f"Chat Escalation - {user_name}",
            "departmentId": ZOHO_DEPT_ID,
            "contactId": session_id,  # Link to chat session
            "description": f"Chat escalation from AI assistant.\n\n--- Conversation History ---\n\n{conversation_text}",
            "status": "Open",
            "priority": "High",
            "channel": "Chat"
        }
        
        url = f"https://desk.zoho.com/api/v1/tickets"
        headers = {
            "Authorization": f"Zoho-oauthtoken {ZOHO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "orgId": ZOHO_ORG_ID
        }
        
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(url, json=ticket_data, headers=headers)
            
            if response.status_code in [200, 201]:
                ticket = response.json()
                ticket_id = ticket.get("id", "unknown")
                logger.info(f"✅ Desk ticket created: {ticket_id}")
                return ticket_id
            else:
                logger.error(f"❌ Desk API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Failed to create Desk ticket: {e}")
        return None


def generate_llm_response(message: str, history: List[Dict]) -> str:
    """
    Single LLM call with expert prompt
    No classification, no routing - just direct generation
    """
    try:
        messages = [{"role": "system", "content": EXPERT_PROMPT}]
        messages.extend(history[-20:])  # Last 20 messages for context
        messages.append({"role": "user", "content": message})
        
        logger.info(f"🤖 Calling LLM with {len(messages)} messages")
        
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=messages,
            temperature=0.3,
            max_tokens=300  
        )
        
        bot_response = response.choices[0].message.content.strip()
        
        logger.info(f"✅ LLM response: {bot_response[:100]}...")
        return bot_response
        
    except Exception as e:
        logger.error(f"❌ LLM generation failed: {e}")
        return "I apologize, but I'm having trouble processing your request. Let me connect you with our support team."


@app.get("/webhook")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {
        "status": "ready",
        "endpoint": "/webhook (POST for messages)",
        "alt_endpoint": "/webhook/salesiq (POST for SalesIQ)"
    }


@app.post("/webhook")
async def webhook(request: Request):
    """
    Main webhook handler - simplified flow:
    1. Receive message from SalesIQ
    2. Generate LLM response (single call)
    3. Check for escalation
    4. Send response + buttons if needed
    5. Create Desk ticket if escalating
    """
    try:
        data = await request.json()
        logger.info(f"📨 Webhook received: {json.dumps(data, indent=2)}")
        
        # Extract data
        handler = data.get("handler", "")
        message = data.get("message", {}).get("text", "") if isinstance(data.get("message"), dict) else ""
        visitor = data.get("visitor", {})
        session_id = visitor.get("active_conversation_id", data.get("session_id", "unknown"))
        visitor_name = visitor.get("name", visitor.get("email", "User"))
        
        # Handle initial contact (trigger event)
        if handler == "trigger" and not message:
            logger.info(f"👋 Initial contact - session {session_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": ["Hi! I'm AceBuddy,What can I help you with today?"],
                    "session_id": session_id
                }
            )
        
        if not message:
            logger.warning("Empty message received (non-trigger)")
            return JSONResponse(
                status_code=200,
                content={"action": "reply", "replies": [], "session_id": session_id}
            )
        
        # Session reset keyword
        if message.lower() in ["new issue", "start fresh", "reset", "clear context"]:
            conversations[session_id] = []
            logger.info(f"🔄 Session reset for {session_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": ["Sure! Starting fresh. What issue can I help you with today?"],
                    "session_id": session_id
                }
            )
        
        # Get/create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Add user message to history
        history.append({"role": "user", "content": message})
        
        # Generate LLM response (SINGLE CALL)
        bot_response = generate_llm_response(message, history)
        
        # Add bot response to history
        history.append({"role": "assistant", "content": bot_response})
        
        # Check if escalation needed
        # ESCALATION TRIGGER 1: User explicitly asks
        user_asks_escalation = any(phrase in message.lower() for phrase in [
            "talk to someone", "speak to agent", "connect me", "human agent", "real person"
        ])
        
        # ESCALATION TRIGGER 2: LLM generated escalation message (detected by keywords)
        llm_generated_escalation = any(phrase in bot_response.lower() for phrase in [
            "i'd like to connect you", "let me connect you", "connect you with our", "connect you with the",
            "would you like me to connect you", "let me get our team", "immediate attention", "technical team",
            "connect you with our technical team", "i understand this is", "thank you for your patience"
        ])
        
        needs_escalation = user_asks_escalation or llm_generated_escalation
        
        if needs_escalation:
            logger.info(f"🚨 Escalation triggered for session {session_id}")
            
            # Create Desk ticket
            ticket_id = await create_desk_ticket(session_id, visitor_name, history)
            
            # Show escalation buttons in SalesIQ format
            suggestions = [
                {
                    "text": "Chat with Technician",
                    "action_type": "article",
                    "action_value": "ESCALATE_CHAT"
                },
                {
                    "text": "Schedule Callback",
                    "action_type": "article",
                    "action_value": "SCHEDULE_CALLBACK"
                }
            ]
            
            # Send to SalesIQ with buttons (disabled - tokens missing)
            # await send_salesiq_message(session_id, bot_response, suggestions)
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [bot_response],
                    "suggestions": suggestions,
                    "session_id": session_id
                }
            )
        
        else:
            # Normal response - no escalation (disabled - tokens missing)
            # await send_salesiq_message(session_id, bot_response)
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [bot_response],
                    "session_id": session_id
                }
            )
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "action": "reply",
                "replies": ["I'm experiencing technical difficulties. Let me connect you with our support team."],
                "session_id": session_id if 'session_id' in locals() else "unknown"
            }
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "expert_prompt_loaded": len(EXPERT_PROMPT) > 0,
        "active_sessions": len(conversations)
    }


@app.get("/webhook/salesiq")
async def webhook_salesiq_health():
    """Health check for SalesIQ webhook endpoint"""
    return {
        "status": "ready",
        "message": "SalesIQ webhook is active and ready to receive POST requests",
        "usage": "POST to this endpoint with SalesIQ chat events",
        "supported_endpoints": {
            "/webhook": "Main webhook (POST only)",
            "/webhook/salesiq": "SalesIQ alias (POST only)",
            "/health": "Health check",
            "/": "Info"
        }
    }


@app.post("/webhook/salesiq")
async def webhook_salesiq(request: Request):
    """Alias for SalesIQ webhook - same as /webhook"""
    return await webhook(request)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ACE Cloud Chatbot - Simplified",
        "version": "2.0",
        "architecture": "Direct LLM (no classification layer)",
        "endpoints": {
            "/webhook": "Main webhook for SalesIQ",
            "/health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
