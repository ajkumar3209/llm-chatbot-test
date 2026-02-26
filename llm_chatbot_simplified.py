"""
Simplified LLM-First Chatbot - Direct to LLM approach
No classification layer, no routing complexity
Just: Expert Prompt → LLM → Response → Escalation Detection → SalesIQ/Desk APIs
"""

import os
import re
import uuid
import asyncio
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI, APITimeoutError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from zoho_live_integration import create_callback_activity, close_chat

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
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
SALESIQ_DEPARTMENT_ID = os.getenv("SALESIQ_DEPARTMENT_ID", "2782000000002013")


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

# ── Button click triggers (strict matching) ──
# SalesIQ sends action_value or button text as the message when clicked
CHAT_TRANSFER_TRIGGERS = {
    "ESCALATE_CHAT",
    "💬 Chat with Technician", "Chat with Technician", "chat with technician",
    "option 1", "1",
}
CALLBACK_TRIGGERS = {
    "SCHEDULE_CALLBACK",
    "📅 Schedule Callback", "Schedule Callback", "schedule callback",
    "callback", "option 2", "2",
}

# ── Resolution detection ──
USER_RESOLUTION_PHRASES = [
    "yes", "yeah", "yep", "yup", "ya", "han", "haan",
    "working now", "it's working", "its working", "it works",
    "fixed", "resolved", "solved", "issue resolved", "problem solved",
    "that worked", "that fixed it", "that helped",
    "all good", "good now", "fine now", "okay now",
    "no more issues", "no issues", "no problem",
]

BOT_RESOLUTION_ASK_PHRASES = [
    "is your issue resolved", "is the issue resolved", "is it resolved",
    "is it working now", "is that working", "did that help", "did that fix",
    "does that resolve", "has your issue been resolved",
    "is there anything else", "anything else i can help",
    "anything else i can assist", "can i help you with anything else",
    "glad i could help", "glad to help", "happy to help",
    "glad that helped", "great to hear",
]

# ── State markers (stored in session history to track multi-step flows) ──
CALLBACK_WAITING_MARKER = "WAITING_FOR_CALLBACK_DETAILS"


def detect_resolution(user_message: str, history: List[Dict]) -> bool:
    """Detect if the user is confirming their issue is resolved.
    
    Relaxed logic: simply check if the user is explicitly stating the issue is resolved.
    """
    user_lower = user_message.lower().strip()

    # If the user explicitly says they want to close the chat, or it's resolved
    explicit_close_phrases = ["close this chat", "close chat", "end chat"]
    if any(phrase in user_lower for phrase in explicit_close_phrases):
        return True

    if len(user_lower) < 60:
        for phrase in USER_RESOLUTION_PHRASES:
            if phrase in user_lower:
                logger.info("Resolution detected: user said '%s'", user_lower)
                return True

    return False


def detect_escalation(user_message: str, bot_response: str, history: List[Dict]) -> bool:
    """Detect if escalation is needed.
    Only triggers ONCE per session to prevent button spam, unless the user explicitly asks for it again.
    """
    user_lower = user_message.lower()
    bot_lower = bot_response.lower()

    # Check if we already showed buttons recently
    already_escalated = any(msg.get("escalated", False) for msg in history[-5:])

    for keyword in ESCALATION_KEYWORDS:
        if keyword in user_lower:
            logger.info("Escalation detected: user keyword '%s'", keyword)
            return True

    # If we already offered escalation, don't keep offering it automatically based on bot phrases/length
    if already_escalated:
        return False

    for phrase in BOT_ESCALATION_PHRASES:
        if phrase in bot_lower:
            logger.info("Escalation detected: bot phrase '%s'", phrase)
            return True

    # Check conversation length (count only user/assistant messages)
    msg_count = sum(1 for m in history if m.get("role") in ("user", "assistant"))
    if msg_count > 10:
        logger.info("Escalation detected: conversation too long (%d messages)", msg_count)
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


def _build_conversation_summary(history: List[Dict]) -> str:
    """Build a short text summary from the last 10 user/assistant messages."""
    return "\n".join(
        f"{'User' if m['role'] == 'user' else 'Bot'}: {m['content']}"
        for m in history[-10:]
        if m.get("role") in ("user", "assistant")  # skip system markers
    )


def _is_waiting_for_callback(history: List[Dict]) -> bool:
    """Check if session is waiting for callback details (phone + time)."""
    return (
        len(history) > 0
        and history[-1].get("role") == "system"
        and history[-1].get("content") == CALLBACK_WAITING_MARKER
    )


def _parse_callback_details(message: str) -> Dict[str, Optional[str]]:
    """裁Best-effort parse phone number and preferred time from user's message."""
    # Handle the exact format: "time : 11pm today\nphone:343433333"
    preferred_time = None
    phone = None
    
    # Try parsing line by line first (handles the user's specific input style well)
    for line in message.split('\n'):
        line_lower = line.lower().strip()
        if line_lower.startswith('time') and ':' in line_lower:
            preferred_time = line.split(':', 1)[1].strip()
        elif line_lower.startswith('phone') and ':' in line_lower:
            phone_raw = line.split(':', 1)[1].strip()
            phone = re.sub(r"[^\d+]", "", phone_raw)

    if not preferred_time:
        # Try structured format: "time: ...\nphone: ..."
        time_match = re.search(
            r"(?i)\btime\b\s*[:=\-]\s*([^\n]+?)(?=\s*phone\b|\s*$)",
            message, re.DOTALL,
        )
        preferred_time = time_match.group(1).strip() if time_match else None

    if not phone:
        # Extract phone number
        phone_match = re.search(r"(?i)\bphone\b\s*[:=\-]\s*([\d\s+\-]+)", message)
        if phone_match:
            phone = re.sub(r"[^\d+]", "", phone_match.group(1))
        else:
            # Fallback: find any number sequence that looks like a phone number
            phone_match = re.search(r"\b(?:\+?\d[\d\s\-]{8,}\d)\b", message)
            phone = phone_match.group(0).strip() if phone_match else None

    # If no structured time found, try to extract from message
    if not preferred_time:
        time_keywords = re.search(
            r"(?i)(tomorrow|today|monday|tuesday|wednesday|thursday|friday|"
            r"saturday|sunday|morning|afternoon|evening|night|"
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))",
            message,
        )
        preferred_time = time_keywords.group(0).strip() if time_keywords else None

    return {"phone": phone, "preferred_time": preferred_time}


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
    # Only include user/assistant messages (skip system markers)
    messages.extend(
        m for m in history[-20:]
        if m.get("role") in ("user", "assistant")
    )

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
        return "I apologize, but I'm having trouble processing your request. Please try again in a moment."
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        return "I apologize, but I'm having trouble processing your request. Please try again in a moment."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUTTON HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_chat_transfer(session_id: str) -> JSONResponse:
    """Handle 'Chat with Technician' button click.

    Uses SalesIQ's official "forward" action — this tells SalesIQ to
    hand off the chat to a human operator in the specified department.
    No custom API call needed; SalesIQ handles the routing natively.
    """
    logger.info("Chat transfer requested — using SalesIQ forward action for session %s", session_id)
    return JSONResponse(
        status_code=200,
        content={
            "action": "forward",
            "department": SALESIQ_DEPARTMENT_ID,
            "replies": [
                "I'm connecting you with our support team. "
                "An operator will assist you shortly."
            ],
        },
    )


async def handle_callback_step1(session_id: str, history: List[Dict]) -> JSONResponse:
    """Handle 'Schedule Callback' button click — Step 1: Ask for details.

    Sets a WAITING_FOR_CALLBACK_DETAILS marker in session history so the
    next message from the user is routed to Step 2 for parsing.
    """
    logger.info("Callback requested — asking for details, session %s", session_id)

    response_text = (
        "Perfect! I'm setting up a callback request for you.\n\n"
        "Please provide:\n"
        "1. Your preferred time (e.g., 'tomorrow at 2 PM' or 'Monday morning')\n"
        "2. Your phone number\n\n"
        "Our support team will call you back at that time."
    )

    # Store the interaction and set the waiting marker
    history.append({"role": "user", "content": "Schedule Callback"})
    history.append({"role": "assistant", "content": response_text})
    history.append({"role": "system", "content": CALLBACK_WAITING_MARKER})

    return build_reply([response_text], session_id)


async def handle_callback_step2(
    session_id: str,
    message: str,
    visitor: Dict,
    history: List[Dict],
) -> JSONResponse:
    """Handle callback Step 2: Parse details, create activity, close chat.

    1. Remove the WAITING marker
    2. Parse phone + preferred time from user's message
    3. Create callback activity on Desk
    4. On success → close chat via SalesIQ API + clear session
    """
    # Remove the system marker
    if history and history[-1].get("content") == CALLBACK_WAITING_MARKER:
        history.pop()

    # Add user's details to history
    history.append({"role": "user", "content": message})

    # Parse details
    details = _parse_callback_details(message)
    logger.info("Callback details parsed: time=%s, phone=%s", details["preferred_time"], details["phone"])

    # Extract visitor info
    visitor_email = visitor.get("email", "support@acecloudhosting.com")
    visitor_name = visitor.get("name", visitor_email.split("@")[0] if visitor_email else "Chat User")

    # Build full description including user-provided details
    summary = _build_conversation_summary(history)
    full_description = f"{summary}\n\nUSER PROVIDED DETAILS:\n{message}"

    # Create callback activity on Desk
    try:
        result = await create_callback_activity(
            session_id=session_id,
            user_name=visitor_name,
            user_email=visitor_email,
            user_phone=details["phone"] or "",
            preferred_time=details["preferred_time"] or "",
            conversation_summary=full_description,
        )
        logger.info("Callback activity result: %s", result.get("success"))
    except Exception as exc:
        logger.error("Callback activity exception: %s", exc, exc_info=True)
        result = {"success": False, "error": "exception", "details": str(exc)}

    if result.get("success"):
        logger.info("Callback created successfully for session %s", session_id)

        response_text = (
            "Your callback has been created successfully.\n"
            "You will receive a call from our support team at your requested time. "
            "Thank you for contacting Ace Cloud Hosting!"
        )

        # Close the SalesIQ chat session
        try:
            close_result = await close_chat(session_id)
            logger.info("Chat closure result: %s", close_result.get("success"))
        except Exception as exc:
            logger.error("Chat closure error: %s", exc)

        # Clear conversation memory
        conversations.reset(session_id)

        return build_reply([response_text], session_id)
    else:
        logger.warning("Callback creation failed for session %s: %s", session_id, result.get("error"))
        response_text = (
            "I got your details, but I couldn't create the callback in our system right now. "
            "Please call our support team at 1-888-415-5240 for immediate help."
        )
        return build_reply([response_text], session_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    Main webhook handler:
    1. Receive message from SalesIQ
    2. Check for button clicks (Chat Transfer / Schedule Callback)
    3. Handle callback detail collection (two-step flow)
    4. Generate LLM response (single call)
    5. Check for escalation → show buttons
    6. Check for resolution → close chat
    7. Return response
    """
    session_id = "unknown"
    request_id = str(uuid.uuid4())[:8]
    try:
        data = await request.json()

        # Extract data
        handler = data.get("handler", "")
        message = data.get("message", {}).get("text", "") if isinstance(data.get("message"), dict) else ""
        visitor = data.get("visitor", {})
        session_id = visitor.get("active_conversation_id", data.get("session_id", "unknown"))

        logger.info("Webhook received", extra={
            "request_id": request_id, "handler": handler,
            "session_id": session_id, "msg_len": len(message),
        })

        # Handle initial contact (trigger event)
        if handler == "trigger" and not message:
            logger.info("Initial contact — session %s", session_id)
            return build_reply(["Hi! I'm AceBuddy, What can I help you with today?"], session_id)

        if not message:
            return build_reply([], session_id)

        message_stripped = message.strip()
        message_lower = message_stripped.lower()

        # ── Button click: Chat with Technician ──
        # Uses SalesIQ native "forward" action — no API call needed
        if message_stripped in CHAT_TRANSFER_TRIGGERS or message_lower in CHAT_TRANSFER_TRIGGERS:
            return handle_chat_transfer(session_id)

        # ── Button click: Schedule Callback (Step 1 — ask for details) ──
        if message_stripped in CALLBACK_TRIGGERS or message_lower in CALLBACK_TRIGGERS:
            history = conversations.get_or_create(session_id)
            # Only start step 1 if not already waiting
            if not _is_waiting_for_callback(history):
                return await handle_callback_step1(session_id, history)

        # ── Callback Step 2: User is providing phone + time details ──
        history = conversations.get_or_create(session_id)
        if _is_waiting_for_callback(history):
            return await handle_callback_step2(session_id, message, visitor, history)

        # ── Session reset keyword ──
        if message_lower in ("new issue", "start fresh", "reset", "clear context"):
            conversations.reset(session_id)
            logger.info("Session reset for %s", session_id)
            return build_reply(["Sure! Starting fresh. What issue can I help you with today?"], session_id)

        # ── Check for resolution BEFORE generating a new LLM response ──
        if len(history) >= 2 and detect_resolution(message, history):
            logger.info("Resolution confirmed for session %s — closing chat", session_id)

            # Close the SalesIQ chat session via API
            close_result = await close_chat(session_id)
            if close_result.get("success"):
                logger.info("Chat closed successfully for session %s", session_id)
            else:
                logger.warning("Chat close API failed for %s: %s", session_id, close_result.get("error"))

            # Clear session memory
            conversations.reset(session_id)

            return build_reply(
                [
                    "Great to hear your issue is resolved! "
                    "If you ever need help again, feel free to start a new chat. Have a great day!"
                ],
                session_id,
            )

        # ── Normal message flow ──
        # Add user message to history
        conversations.add_message(session_id, {"role": "user", "content": message})

        # Generate LLM response (SINGLE CALL)
        bot_response = await generate_llm_response(message, history)

        # Check if escalation needed (consolidated detection)
        needs_escalation = detect_escalation(message, bot_response, history)

        # Add bot response to history (and mark if we escalated so we don't spam it)
        conversations.add_message(session_id, {"role": "assistant", "content": bot_response, "escalated": needs_escalation})

        if needs_escalation:
            logger.info("Escalation triggered for session %s", session_id)

            # Show escalation buttons — actual API calls happen when user clicks
            suggestions = [
                {"text": "💬 Chat with Technician", "action_type": "article", "action_value": "ESCALATE_CHAT"},
                {"text": "📅 Schedule Callback", "action_type": "article", "action_value": "SCHEDULE_CALLBACK"},
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
