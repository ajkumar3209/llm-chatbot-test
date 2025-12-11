"""
FastAPI Chatbot Server - Hybrid LLM Approach
Uses resolution steps in system prompt (no RAG layer)
LLM intelligently selects and presents steps based on context
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from openai import OpenAI
from dotenv import load_dotenv
import urllib3
import uvicorn
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = FastAPI(title="Ace Cloud Hosting Support Bot - Hybrid", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LLM_MODEL = "gpt-4o-mini"

conversations: Dict[str, List[Dict]] = {}

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str

# RESOLUTION STEPS - Top 10 Most Common Issues (99.5% coverage)
# Based on analysis of 33,130 real conversations
RESOLUTION_STEPS = """
RESOLUTION STEPS FOR COMMON ISSUES (Top 10 - 99.5% Coverage):

1. QUICKBOOKS FROZEN (DEDICATED SERVER) - 32.8% of issues:
   Step 1: Right click and open Task Manager on the server
   Step 2: Go to Users, click on your username and expand it
   Step 3: Find your opened QuickBooks session under it and click End Task
   Step 4: Once it is closed, please log back into your QuickBooks company file

2. QUICKBOOKS FROZEN (SHARED SERVER) - 32.8% of issues:
   Step 1: Minimize the QuickBooks application
   Step 2: Select the "QB instance kill" shortcut that is already present on your desktop
   Step 3: Once the session is closed, log back into your QuickBooks company file

3. QUICKBOOKS ERROR 15212 OR 12159 - 32.8% of issues:
   Step 1: On the server, right-click QuickBooks and select Run as Administrator
   Step 2: Select Update QuickBooks Desktop from the Help menu
   Step 3: Follow the update wizard to complete the update
   Step 4: Restart QuickBooks and try opening your company file again

4. PASSWORD RESET (SELFCARE ENROLLED) - 8.81% of issues:
   Step 1: Go to selfcare.acecloudhosting.com and click 'Forgot Password'
   Step 2: Enter your server username
   Step 3: Follow the verification process
   Step 4: Enter your new password and click Reset to finish

5. PASSWORD RESET (NOT ENROLLED) - 8.81% of issues:
   Step 1: Send an email to support@acecloudhosting.com
   Step 2: In the email, mention your server username and request password reset
   Step 3: Ensure the email is authorized by your account owner
   Step 4: Our support team will process your request and share an update

6. RDP DISPLAY SETTINGS - 8.22% of issues:
   Step 1: Press "Windows Key + R" to open the Run dialog
   Step 2: Type "mstsc" (without quotes) and hit Enter
   Step 3: Click on the "Show Options" button
   Step 4: Adjust the "Display Configuration" slider to your preference
   Step 5: Click the "Connect" button to initiate the remote session

7. MYPORTAL PASSWORD RESET - 7.47% of issues:
   Step 1: Ask your account owner to reset your password via MyPortal
   Step 2: Account owner logs into myportal.acecloudhosting.com
   Step 3: Account owner uses their Customer ID (CID) as username
   Step 4: Account owner can reset passwords for all users in the account

8. LOW DISK SPACE - 16.8% of issues:
   Step 1: Press Win + R on your keyboard, type %temp%, press Enter
   Step 2: Select all files (Ctrl + A) and delete them
   Step 3: Press Win + R again, type temp, press Enter
   Step 4: Select all files (Ctrl + A) and delete them
   Step 5: Restart your server to apply changes

9. SELFCARE ENROLLMENT - 6.49% of issues:
   Step 1: Go to selfcare.acecloudhosting.com
   Step 2: Click "Enroll Now"
   Step 3: Enter your server username
   Step 4: Follow the verification process
   Step 5: Set your password and complete enrollment

10. EMAIL/O365 CONNECTION ISSUES - 25.49% of issues:
    Step 1: Check your internet connection
    Step 2: Restart Outlook application
    Step 3: Verify your email credentials are correct
    Step 4: If still not working, contact support at 1-888-415-5240
"""

def generate_response(message: str, history: List[Dict]) -> str:
    """Generate response using LLM with embedded resolution steps"""
    
    system_prompt = f"""You are AceBuddy, a technical support assistant for Ace Cloud Hosting.

YOUR JOB: Help users with technical issues using the resolution steps provided below.

CRITICAL RULES:

FOR PROCEDURAL CONTENT (troubleshooting steps):
1. Give ONLY 1 step at a time for simplicity
2. Use SHORT sentences - max 10-15 words per sentence
3. After giving 1 step, ask "Have you completed this?"
4. Use the exact steps from the resolution steps provided
5. If you don't have a solution, direct to support at 1-888-415-5240

CRITICAL: Always give only ONE step per response to keep it simple and easy to follow.

FOR INFORMATIONAL CONTENT (pricing, plans, features, general info):
1. Present ALL information at once
2. Use clear formatting (bullet points or numbered list)
3. Keep it SHORT and SIMPLE
4. End with "Would you like to know more?"

ASKING CLARIFYING QUESTIONS - CRITICAL:

For QuickBooks FROZEN issues ONLY:
1. FIRST ask: "Are you using a dedicated server or a shared server?"
2. WAIT for their answer
3. THEN provide the appropriate steps based on their server type

For OTHER QuickBooks issues (errors, installation, setup, etc.):
- Provide general steps directly, do NOT ask server type

Examples:
User: "My QuickBooks is frozen" → Ask server type first
User: "QuickBooks error 15212" → Provide steps directly (no server type needed)

HANDLING "NOT WORKING" OR "STUCK":
If user says steps didn't work, they're stuck, or same issue persists, THEN offer human agent:
"I understand this is frustrating. Would you like me to connect you with a human agent? (Reply 'yes' to connect)"

POSITIVE LANGUAGE: Always use positive, helpful language.

SPECIAL HANDLING FOR PASSWORD RESET:
When user asks about password reset:
1. FIRST ask: "Are you enrolled in the Selfcare Portal? (Reply 'yes' or 'no')"
2. WAIT for their answer
3. If yes: Provide Selfcare password reset steps
4. If no: Provide enrollment steps first

SPECIAL HANDLING FOR APPLICATION UPDATES:
For QuickBooks, Lacerte, Drake, ProSeries updates:
- DO NOT provide step-by-step instructions
- Direct to support immediately: "Application updates need to be handled by our support team to avoid downtime. Please contact support at 1-888-415-5240 or support@acecloudhosting.com"

RESPONSE MESSAGES:
- For "thanks", "thank you", "thanks for support" → "You're welcome! Is there anything else I can help you with?"
- For "ok", "okay" alone → "Is there anything else I can help you with?"
- For "yes"/"ok" to human agent question → Connect to support
- For "yes"/"ok" during troubleshooting → Continue with next step

CONTINUATION KEYWORDS:
During multi-step processes, treat these as continuation:
- "okay", "ok", "done", "next", "continue", "what are the next steps", "okay then"

RESOLUTION STEPS DATABASE:
{RESOLUTION_STEPS}

CRITICAL: 
- Use ONLY the steps provided above
- Give steps in the exact order provided
- If user's issue is not in the resolution steps, direct to support at 1-888-415-5240
- Keep responses SHORT and SIMPLE
- Always give only ONE step per response"""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )
    
    return response.choices[0].message.content

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Ace Cloud Hosting Support Bot - Hybrid LLM",
        "version": "2.0.0",
        "endpoints": {
            "salesiq_webhook": "/webhook/salesiq",
            "chat": "/chat",
            "reset": "/reset/{session_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "openai": "connected",
        "active_sessions": len(conversations)
    }

@app.post("/webhook/salesiq")
async def salesiq_webhook(request: dict):
    """Direct webhook endpoint for Zoho SalesIQ - Hybrid LLM"""
    try:
        print(f"[SalesIQ] Received: {request}")
        
        visitor = request.get('visitor', {})
        session_id = (
            visitor.get('active_conversation_id') or 
            request.get('session_id') or 
            request.get('visitor', {}).get('id') or
            'unknown'
        )
        
        message_obj = request.get('message', {})
        message_text = message_obj.get('text', '') if isinstance(message_obj, dict) else str(message_obj)
        
        if not message_text or message_text.strip() == '':
            print(f"[SalesIQ] Empty message, sending greeting")
            return {
                "action": "reply",
                "replies": ["Hi! I'm AceBuddy, your Ace Cloud Hosting support assistant. What can I help you with today?"],
                "session_id": session_id
            }
        
        print(f"[SalesIQ] Session: {session_id}, Message: {message_text}")
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        message_lower = message_text.lower().strip()
        
        # Handle simple greetings
        greeting_patterns = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        is_greeting = (
            message_lower in greeting_patterns or
            (len(message_text.split()) <= 3 and any(g in message_lower for g in greeting_patterns))
        )
        
        if is_greeting and len(history) == 0:
            print(f"[SalesIQ] Simple greeting detected")
            return {
                "action": "reply",
                "replies": ["Hello! How can I assist you today?"],
                "session_id": session_id
            }
        
        # Handle contact requests
        contact_request_phrases = ['support email', 'support number', 'contact support', 'phone number', 'email address']
        if any(phrase in message_lower for phrase in contact_request_phrases):
            print(f"[SalesIQ] Contact request detected")
            return {
                "action": "reply",
                "replies": ["You can reach Ace Cloud Hosting support at:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com"],
                "session_id": session_id
            }
        
        # Check for human agent request FIRST
        if len(history) > 0 and ('yes' in message_lower or 'ok' in message_lower or 'connect' in message_lower):
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'human agent' in last_bot_message.lower():
                print(f"[SalesIQ] User requested human agent - initiating transfer")
                # Build conversation history for agent to see
                conversation_text = ""
                for msg in history:
                    role = "User" if msg.get('role') == 'user' else "Bot"
                    conversation_text += f"{role}: {msg.get('content', '')}\n"
                
                response = {
                    "action": "transfer",
                    "transfer_to": "human_agent",
                    "session_id": session_id,
                    "conversation_history": conversation_text,
                    "replies": ["Connecting you with a support agent..."]
                }
                
                # Clear conversation after transfer
                if session_id in conversations:
                    del conversations[session_id]
                
                return response
        
        # Check for issue resolution
        resolution_keywords = ["resolved", "fixed", "working now", "solved", "all set"]
        if any(keyword in message_lower for keyword in resolution_keywords):
            print(f"[SalesIQ] Issue resolved by user")
            response_text = "Great! I'm glad the issue is resolved. If you need anything else, feel free to ask!"
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            if session_id in conversations:
                del conversations[session_id]
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        # Check for not resolved
        not_resolved_keywords = ["not resolved", "not fixed", "not working", "didn't work", "still not", "still stuck"]
        if any(keyword in message_lower for keyword in not_resolved_keywords):
            print(f"[SalesIQ] Issue NOT resolved - offering 3 options")
            response_text = """I understand this is frustrating. Here are 3 ways I can help:

1. **Instant Chat** - Connect with a human agent now
   https://your-domain.com/chat/transfer

2. **Schedule Callback** - We'll call you back at a convenient time
   https://your-domain.com/callback/schedule

3. **Create Support Ticket** - We'll create a detailed ticket and follow up
   https://your-domain.com/ticket/create

Which option works best for you?"""
            # Add to history so next response can find it
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        # Check for application updates
        app_update_keywords = ["update", "upgrade", "requires update", "needs update"]
        app_names = ["quickbooks", "lacerte", "drake", "proseries", "qb"]
        is_app_update = False
        if any(keyword in message_lower for keyword in app_update_keywords):
            if any(app in message_lower for app in app_names):
                is_app_update = True
        
        if is_app_update:
            print(f"[SalesIQ] Application update request detected")
            response_text = "Application updates need to be handled by our support team to avoid downtime. Please contact support at:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com\n\nThey'll schedule the update for you!"
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        # Check for option selections
        if "instant chat" in message_lower or "option 1" in message_lower or "chat/transfer" in message_lower:
            print(f"[SalesIQ] User selected: Instant Chat Transfer")
            # Build conversation history for agent to see
            conversation_text = ""
            for msg in history:
                role = "User" if msg.get('role') == 'user' else "Bot"
                conversation_text += f"{role}: {msg.get('content', '')}\n"
            
            response = {
                "action": "transfer",
                "transfer_to": "human_agent",
                "session_id": session_id,
                "conversation_history": conversation_text,
                "replies": ["Connecting you with a support agent..."]
            }
            
            # Clear conversation after transfer
            if session_id in conversations:
                del conversations[session_id]
            
            return response
        
        if "callback" in message_lower or "option 2" in message_lower or "schedule" in message_lower:
            print(f"[SalesIQ] User selected: Schedule Callback - AUTO-CLOSING CHAT")
            response_text = """Perfect! I'm creating a callback request for you.

Please provide:
1. Your preferred time (e.g., "tomorrow at 2 PM" or "Monday morning")
2. Your phone number

Our support team will call you back at that time. A ticket has been created and you'll receive a confirmation email shortly.

Thank you for contacting Ace Cloud Hosting!"""
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            # Clear conversation after callback (auto-close)
            if session_id in conversations:
                del conversations[session_id]
            
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        if "ticket" in message_lower or "option 3" in message_lower or "support ticket" in message_lower:
            print(f"[SalesIQ] User selected: Create Support Ticket - AUTO-CLOSING CHAT")
            response_text = """Perfect! I'm creating a support ticket for you.

Please provide:
1. Your name
2. Your email
3. Your phone number
4. Brief description of the issue

A ticket has been created and you'll receive a confirmation email shortly. Our support team will follow up with you within 24 hours.

Thank you for contacting Ace Cloud Hosting!"""
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            # Clear conversation after ticket creation (auto-close)
            if session_id in conversations:
                del conversations[session_id]
            
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        # Check for agent connection requests (legacy)
        agent_request_phrases = ["connect me to agent", "connect to agent", "human agent", "talk to human", "speak to agent"]
        if any(phrase in message_lower for phrase in agent_request_phrases):
            print(f"[SalesIQ] User requesting human agent")
            response_text = """I can help you with that. Here are your options:

1. **Instant Chat** - Connect with a human agent now
   https://your-domain.com/chat/transfer

2. **Schedule Callback** - We'll call you back at a convenient time
   https://your-domain.com/callback/schedule

3. **Create Support Ticket** - We'll create a detailed ticket and follow up
   https://your-domain.com/ticket/create

Which option works best for you?"""
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            return {
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        
        # Check for acknowledgments
        def is_acknowledgment_message(msg):
            msg = msg.lower().strip()
            if 'then' in msg:
                return False
            direct_acks = ["okay", "ok", "thanks", "thank you", "got it", "understood", "alright", 
                          "perfect", "good", "great", "awesome", "nice", "cool"]
            if msg in direct_acks:
                return True
            thanks_patterns = ["thank", "thnk", "thx", "ty"]
            if any(pattern in msg for pattern in thanks_patterns):
                return True
            positive_expressions = ["i m good", "i'm good", "all good", "looks good", "working now", 
                                  "that's it", "perfect", "excellent", "brilliant", "fantastic"]
            if any(expr in msg for expr in positive_expressions):
                return True
            if msg.startswith("no") and any(pattern in msg for pattern in thanks_patterns):
                return True
            return False
        
        is_in_troubleshooting = False
        if len(history) > 0:
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'have you completed this?' in last_bot_message.lower():
                is_in_troubleshooting = True
        
        is_acknowledgment = is_acknowledgment_message(message_lower)
        
        if is_acknowledgment:
            if is_in_troubleshooting and message_lower in ["okay", "ok"]:
                print(f"[SalesIQ] 'Okay' in troubleshooting, treating as continuation")
                # Fall through to LLM
            elif message_lower in ["ok", "okay"]:
                print(f"[SalesIQ] 'Ok/Okay' alone, asking if need more help")
                return {
                    "action": "reply",
                    "replies": ["Is there anything else I can help you with?"],
                    "session_id": session_id
                }
            else:
                print(f"[SalesIQ] Acknowledgment with thanks detected")
                return {
                    "action": "reply",
                    "replies": ["You're welcome! Is there anything else I can help you with?"],
                    "session_id": session_id
                }
        
        # Generate LLM response with embedded resolution steps
        print(f"[SalesIQ] Calling OpenAI LLM with embedded resolution steps...")
        response_text = generate_response(message_text, history)
        
        # Clean response
        response_text = response_text.replace('**', '')
        import re
        response_text = re.sub(r'^\s*\*\s+', '- ', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\n\s*\n+', '\n', response_text)
        response_text = response_text.strip()
        
        print(f"[SalesIQ] Response: {response_text}")
        
        # Update conversation history
        conversations[session_id].append({"role": "user", "content": message_text})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        return {
            "action": "reply",
            "replies": [response_text],
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"[SalesIQ] ERROR: {str(e)}")
        return {
            "action": "reply",
            "replies": ["I'm having technical difficulties. Please call our support team at 1-888-415-5240."],
            "session_id": request.get('session_id', 'unknown')
        }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint for n8n webhook"""
    try:
        session_id = request.session_id
        message = request.message
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        response_text = generate_response(message, history)
        
        conversations[session_id].append({"role": "user", "content": message})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset/{session_id}")
async def reset_conversation(session_id: str):
    """Reset conversation for a session"""
    if session_id in conversations:
        del conversations[session_id]
        return {"status": "success", "message": f"Conversation {session_id} reset"}
    return {"status": "not_found", "message": f"Session {session_id} not found"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "active_sessions": len(conversations),
        "sessions": list(conversations.keys())
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("="*70)
    print("ACE CLOUD HOSTING - SUPPORT BOT (HYBRID LLM)")
    print("="*70)
    print(f"\n🚀 Starting FastAPI server on port {port}...")
    print(f"📍 Endpoint: http://0.0.0.0:{port}")
    print(f"📖 Docs: http://0.0.0.0:{port}/docs")
    print("\n✅ Ready to receive webhooks from n8n!")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
