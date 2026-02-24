"""
Simplified LLM-First Chatbot - Direct to LLM approach
No classification layer, no routing complexity
Just: Expert Prompt → LLM → Response → Escalation Detection → SalesIQ/Desk APIs
"""

import os
import re
import json
import uuid
import asyncio
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI, APITimeoutError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from zoho_live_integration import create_desk_ticket, send_salesiq_message

# Setup structured JSON logging
from pythonjsonlogger import json as jsonlogger

log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
log_handler.setFormatter(formatter)
logging.root.handlers = [log_handler]
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy third-party loggers
logging.getLogger("uvicorn.access").handlers = []
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize FastAPI with lifespan for background tasks
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(application):
    """Start background session cleanup on startup, cancel on shutdown."""
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            conversations.cleanup_expired()
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()

app = FastAPI(title="ACE Cloud Chatbot - Simplified v2.0", lifespan=lifespan)

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN", "")
ZOHO_ORG_ID = os.getenv("ZOHO_ORG_ID", "")
ZOHO_DEPT_ID = os.getenv("ZOHO_DEPT_ID", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


async def verify_webhook_secret(request: Request):
    """Validate webhook requests using a shared secret header.
    If WEBHOOK_SECRET is not configured, auth is skipped (local dev mode).
    """
    if not WEBHOOK_SECRET:
        return  # No secret configured → skip auth
    incoming = request.headers.get("X-Webhook-Secret", "")
    if incoming != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


# LLM Client (async for non-blocking event loop)
client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Session configuration
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "1000"))
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "30"))
MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "20"))


class SessionStore:
    """Bounded, TTL-based conversation store.

    - Evicts sessions idle for longer than `ttl_minutes`.
    - Caps total sessions at `max_sessions` (LRU eviction).
    - Caps messages per session at `max_messages`.
    """

    def __init__(self, max_sessions: int = 1000, ttl_minutes: int = 30, max_messages: int = 50):
        self._store: OrderedDict[str, List[Dict]] = OrderedDict()
        self._last_active: Dict[str, datetime] = {}
        self.max_sessions = max_sessions
        self.ttl_minutes = ttl_minutes
        self.max_messages = max_messages

    def get_or_create(self, session_id: str) -> List[Dict]:
        """Return message history for session, creating if needed."""
        if session_id in self._store:
            self._store.move_to_end(session_id)
        else:
            # Evict LRU session if at capacity
            if len(self._store) >= self.max_sessions:
                oldest_key, _ = self._store.popitem(last=False)
                self._last_active.pop(oldest_key, None)
                logger.info("Session evicted (LRU): %s", oldest_key)
            self._store[session_id] = []
        self._last_active[session_id] = datetime.now()
        return self._store[session_id]

    def reset(self, session_id: str):
        """Clear history for a session."""
        self._store.pop(session_id, None)

    def add_message(self, session_id: str, message: Dict):
        """Append a message, dropping oldest if over max_messages."""
        history = self.get_or_create(session_id)
        history.append(message)
        if len(history) > self.max_messages:
            del history[: len(history) - self.max_messages]

    def cleanup_expired(self) -> int:
        """Remove sessions idle longer than TTL. Returns count removed."""
        now = datetime.now()
        expired = [
            sid
            for sid, last in self._last_active.items()
            if (now - last).total_seconds() > self.ttl_minutes * 60
        ]
        for sid in expired:
            self._store.pop(sid, None)
            self._last_active.pop(sid, None)
        if expired:
            logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, session_id: str) -> bool:
        return session_id in self._store


conversations = SessionStore(
    max_sessions=MAX_SESSIONS,
    ttl_minutes=SESSION_TTL_MINUTES,
    max_messages=MAX_MESSAGES_PER_SESSION,
)

# Default fallback prompt if expert prompt file is missing
_FALLBACK_PROMPT = (
    "You are AceBuddy, an IT support assistant for ACE Cloud Hosting. "
    "Help users with basic troubleshooting. If unsure, escalate to a human agent."
)


# Load expert prompt
def load_expert_prompt() -> str:
    """Load the expert system prompt with fallback."""
    prompt_path = os.path.join(os.path.dirname(__file__), "config", "prompts", "expert_system_prompt_production.txt")

    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info("Loaded expert prompt: %d characters from %s", len(content), prompt_path)
            return content
    except FileNotFoundError:
        logger.error("Prompt file not found at %s — using fallback prompt", prompt_path)
        return _FALLBACK_PROMPT


EXPERT_PROMPT = load_expert_prompt()

# Structured startup log (replaces print() banner for clean JSON logs)
logger.info(
    "Chatbot started",
    extra={
        "version": "2.0",
        "architecture": "direct_llm",
        "prompt_chars": len(EXPERT_PROMPT),
        "salesiq": True,
        "desk_api": True,
    },
)

# Escalation keywords — only explicit agent requests (broad frustration
# phrases like "not working" removed to avoid false-positive escalations;
# the LLM system prompt handles nuanced escalation detection).
ESCALATION_KEYWORDS = [
    # Explicit agent requests
    "talk to someone", "speak to agent", "connect me to", "transfer me",
    "human agent", "real person", "customer service", "technical support",
    "call me", "schedule callback", "contact support",
    # Explicit escalation
    "escalate", "supervisor", "manager", "complaint",
]

BOT_ESCALATION_PHRASES = [
    # Bot self-generated escalation signals
    "i'll connect you", "connecting you", "transfer you",
    "let me connect", "i'll transfer", "escalate this",
    "contact support", "reach out to support", "technical support team",
    # LLM-generated escalation patterns
    "i'd like to connect you", "let me connect you",
    "connect you with our", "connect you with the",
    "would you like me to connect you", "let me get our team",
    "immediate attention", "connect you with our technical team",
]


def detect_escalation(user_message: str, bot_response: str, conversation_length: int) -> bool:
    """Detect if escalation is needed based on:
    1. User explicitly requesting agent
    2. Bot response indicating escalation
    3. Conversation length (frustration indicator)
    """
    user_lower = user_message.lower()
    bot_lower = bot_response.lower()

    for keyword in ESCALATION_KEYWORDS:
        if keyword in user_lower:
            logger.info("Escalation detected: user keyword '%s'", keyword)
            return True

    for phrase in BOT_ESCALATION_PHRASES:
        if phrase in bot_lower:
            logger.info("Escalation detected: bot phrase '%s'", phrase)
            return True

    if conversation_length > 10:
        logger.info("Escalation detected: conversation too long (%d messages)", conversation_length)
        return True

    return False


def build_reply(replies: List[str], session_id: str, suggestions: Optional[List[Dict]] = None) -> JSONResponse:
    """Build a SalesIQ-compatible webhook response."""
    content: Dict = {
        "action": "reply",
        "replies": replies,
        "session_id": session_id,
    }
    if suggestions:
        content["suggestions"] = suggestions
    return JSONResponse(status_code=200, content=content)


async def generate_llm_response(message: str, history: List[Dict]) -> str:
    """Single async LLM call with expert prompt, retry, and input sanitization.

    NOTE: The caller must have already appended the user message to `history`
    before calling this function. This function builds the LLM messages list
    from the system prompt + the last 20 messages in history.
    """
    # Input sanitization: strip control chars, cap length
    message = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', message)
    message = message[:2000]

    messages = [{"role": "system", "content": EXPERT_PROMPT}]
    messages.extend(history[-20:])
    # Do NOT re-append user message here — it's already in history

    logger.info("Calling LLM with %d messages", len(messages))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIConnectionError)),
        reraise=True,
    )
    async def _call_llm():
        return await client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=messages,
            temperature=0.3,
            max_tokens=300,
        )

    try:
        response = await _call_llm()
        bot_response = response.choices[0].message.content.strip()
        logger.info("LLM response length: %d chars", len(bot_response))
        return bot_response

    except (APITimeoutError, RateLimitError, APIConnectionError) as e:
        logger.error("LLM transient failure after retries: %s", e)
        return "I apologize, but I'm having trouble processing your request. Let me connect you with our support team."
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
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
async def webhook(request: Request, _auth=Depends(verify_webhook_secret)):
    """
    Main webhook handler - simplified flow:
    1. Receive message from SalesIQ
    2. Generate LLM response (single call)
    3. Check for escalation via detect_escalation()
    4. Create Desk ticket if escalating
    5. Return response + buttons if needed
    """
    # Parse payload early so session_id is always available for error handler
    session_id = "unknown"
    request_id = str(uuid.uuid4())[:8]  # Short unique ID for log correlation
    try:
        data = await request.json()

        # Extract data
        handler = data.get("handler", "")
        message = data.get("message", {}).get("text", "") if isinstance(data.get("message"), dict) else ""
        visitor = data.get("visitor", {})
        session_id = visitor.get("active_conversation_id", data.get("session_id", "unknown"))
        visitor_name = visitor.get("name", visitor.get("email", "User"))

        logger.info("Webhook received", extra={"request_id": request_id, "handler": handler, "session_id": session_id, "msg_len": len(message)})

        # Handle initial contact (trigger event)
        if handler == "trigger" and not message:
            logger.info("Initial contact - session %s", session_id)
            return build_reply(["Hi! I'm AceBuddy, What can I help you with today?"], session_id)

        if not message:
            return build_reply([], session_id)

        # Session reset keyword
        if message.lower() in ["new issue", "start fresh", "reset", "clear context"]:
            conversations.reset(session_id)
            logger.info("Session reset for %s", session_id)
            return build_reply(["Sure! Starting fresh. What issue can I help you with today?"], session_id)

        # Get/create conversation history (bounded + TTL-tracked)
        history = conversations.get_or_create(session_id)

        # Add user message to history
        conversations.add_message(session_id, {"role": "user", "content": message})

        # Generate LLM response (SINGLE CALL)
        bot_response = await generate_llm_response(message, history)

        # Add bot response to history
        conversations.add_message(session_id, {"role": "assistant", "content": bot_response})

        # Check if escalation needed (consolidated detection)
        needs_escalation = detect_escalation(message, bot_response, len(history))

        if needs_escalation:
            logger.info("Escalation triggered for session %s", session_id)

            # Create Desk ticket
            ticket_id = await create_desk_ticket(
                session_id=session_id,
                user_name=visitor_name,
                conversation_history=history,
                access_token=ZOHO_ACCESS_TOKEN,
                org_id=ZOHO_ORG_ID,
                dept_id=ZOHO_DEPT_ID,
            )

            # Show escalation buttons in SalesIQ format
            suggestions = [
                {"text": "Chat with Technician", "action_type": "article", "action_value": "ESCALATE_CHAT"},
                {"text": "Schedule Callback", "action_type": "article", "action_value": "SCHEDULE_CALLBACK"},
            ]

            return build_reply([bot_response], session_id, suggestions=suggestions)

        return build_reply([bot_response], session_id)

    except Exception as e:
        logger.error("Webhook error: %s", e, exc_info=True)
        return build_reply(
            ["I'm experiencing technical difficulties. Let me connect you with our support team."],
            session_id,
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
async def webhook_salesiq(request: Request, _auth=Depends(verify_webhook_secret)):
    """Alias for SalesIQ webhook - same as /webhook"""
    return await webhook(request, _auth=_auth)


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
