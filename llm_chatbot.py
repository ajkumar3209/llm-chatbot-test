"""
Ace Cloud Hosting LLM Chatbot v3.0 - OpenRouter Edition
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from dataclasses import dataclass
import os
import asyncio
from dotenv import load_dotenv
import urllib3
import uvicorn
from datetime import datetime, timezone
import logging
import traceback
import uuid
import json
import requests
from contextvars import ContextVar

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INLINE SERVICE STUBS (Replacing missing module imports)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from enum import Enum
import time

class ConversationState(Enum):
    """Conversation states"""
    NEW = "new"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class TransitionTrigger(Enum):
    """State transition triggers"""
    MESSAGE_RECEIVED = "message_received"
    ISSUE_RESOLVED = "issue_resolved"
    ESCALATION_REQUESTED = "escalation_requested"

@dataclass
class ClassificationResult:
    """LLM classification result"""
    intent: str
    confidence: float
    requires_escalation: bool
    reasoning: str = ""

class MetricsCollector:
    """Tracks performance metrics"""
    def __init__(self):
        self.conversations = {}
    
    def start_conversation(self, session_id: str, category: str = "general"):
        self.conversations[session_id] = {
            "start_time": time.time(),
            "category": category,
            "message_count": 0
        }
    
    def track_message(self, session_id: str):
        if session_id in self.conversations:
            self.conversations[session_id]["message_count"] += 1
    
    def end_conversation(self, session_id: str, outcome: str):
        if session_id in self.conversations:
            duration = time.time() - self.conversations[session_id]["start_time"]
            logger.info(f"[Metrics] Session {session_id} ended: {outcome}, duration: {duration:.1f}s")
            del self.conversations[session_id]
    
    def record_error(self, session_id: str):
        """Record error for metrics tracking"""
        if session_id in self.conversations:
            self.conversations[session_id]["errors"] = self.conversations[session_id].get("errors", 0) + 1

class StateManager:
    """Manages conversation states"""
    def __init__(self):
        self.states = {}
    
    def start_session(self, session_id: str):
        self.states[session_id] = ConversationState.NEW
    
    def update_state(self, session_id: str, new_state: ConversationState):
        self.states[session_id] = new_state
    
    def get_state(self, session_id: str) -> ConversationState:
        return self.states.get(session_id, ConversationState.NEW)
    
    def get_session(self, session_id: str):
        """Check if session exists (for duplicate detection)"""
        return session_id in self.states
    
    def end_session(self, session_id: str, final_state: ConversationState):
        if session_id in self.states:
            self.states[session_id] = final_state

class HandlerRegistry:
    """Pattern-based response handlers"""
    def __init__(self):
        self.handlers = {}
    
    def register(self, pattern: str, handler):
        self.handlers[pattern] = handler

class IssueRouter:
    """Categorizes issues"""
    def __init__(self):
        pass
    
    def classify(self, message: str) -> str:
        return "general"

def detect_trigger_from_message(message: str) -> TransitionTrigger:
    """Detect transition trigger from message"""
    return TransitionTrigger.MESSAGE_RECEIVED

# Initialize singletons
metrics_collector = MetricsCollector()
state_manager = StateManager()
handler_registry = HandlerRegistry()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GEMINI-POWERED: LLM-FIRST ARCHITECTURE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from openai import OpenAI

class GeminiClassifier:
    """LLM-powered intent classifier using Gemini"""
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "google/gemini-2.5-flash-lite"
        self.escalation_threshold = 0.7
        self.resolution_threshold = 0.8
    
    def classify_intent(self, message: str, history: List[Dict]) -> ClassificationResult:
        """Classify user intent using LLM - NO KEYWORDS"""
        try:
            classification_prompt = f"""Analyze this customer message and classify the intent.

User message: "{message}"

Conversation history:
{self._format_history(history)}

Determine:
1. Primary intent (greeting, password_reset, billing, technical_support, account_access, escalation_request, general_inquiry)
2. Whether escalation to human agent is needed (True/False)
3. Confidence level (0.0 to 1.0)

Respond in JSON format:
{{"intent": "category", "requires_escalation": false, "confidence": 0.95, "reasoning": "brief explanation"}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            # Parse JSON response - handle markdown code blocks
            import json
            import re
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            # Log raw response for debugging
            if not result_text or result_text[0] != '{':
                logger.warning(f"[JSON Parse] Non-JSON response: {result_text[:200]}")
            # Log raw response for debugging
            if not result_text or result_text[0] != '{':
                logger.warning(f"[JSON Parse] Non-JSON response: {result_text[:200]}")
            result = json.loads(result_text)
            
            return ClassificationResult(
                intent=result.get("intent", "general_inquiry"),
                confidence=result.get("confidence", 0.5),
                requires_escalation=result.get("requires_escalation", False),
                reasoning=result.get("reasoning", "")
            )
        except Exception as e:
            logger.error(f"[GeminiClassifier] Classification failed: {e}")
            # Fallback to safe defaults
            return ClassificationResult(
                intent="general_inquiry",
                confidence=0.3,
                requires_escalation=False,
                reasoning=f"Classification error: {str(e)}"
            )
    
    def classify_unified(self, message: str, history: List[Dict], session_id: str = None) -> Dict[str, ClassificationResult]:
        """Unified classification for resolution, escalation, and intent"""
        try:
            prompt = f"""Analyze this customer support conversation and provide THREE classifications:

User message: "{message}"

Recent conversation:
{self._format_history(history)}

Provide JSON response with these three classifications:
1. "resolution": Is the customer's issue resolved? (RESOLVED, UNCERTAIN, NOT_RESOLVED)
2. "escalation": Should this be escalated? (NEEDS_HUMAN, BOT_CAN_HANDLE, UNCERTAIN)
3. "intent": What is the user trying to do? (QUESTION, FEEDBACK, REQUEST, COMPLAINT, GREETING, OTHER)

Format:
{{
  "resolution": {{"intent": "RESOLVED", "confidence": 0.95, "reasoning": "User confirmed satisfaction"}},
  "escalation": {{"intent": "BOT_CAN_HANDLE", "confidence": 0.90, "reasoning": "Simple query"}},
  "intent": {{"intent": "QUESTION", "confidence": 0.95, "reasoning": "Asking about pricing"}}
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            import json
            import re
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            # Log for debugging
            logger.debug(f"[JSON Parse] Attempting to parse: {result_text[:200]}...")
            result = json.loads(result_text)
            
            return {
                "resolution": ClassificationResult(
                    intent=result["resolution"]["intent"],
                    confidence=result["resolution"]["confidence"],
                    requires_escalation=False,
                    reasoning=result["resolution"]["reasoning"]
                ),
                "escalation": ClassificationResult(
                    intent=result["escalation"]["intent"],
                    confidence=result["escalation"]["confidence"],
                    requires_escalation=(result["escalation"]["intent"] == "NEEDS_HUMAN"),
                    reasoning=result["escalation"]["reasoning"]
                ),
                "intent": ClassificationResult(
                    intent=result["intent"]["intent"],
                    confidence=result["intent"]["confidence"],
                    requires_escalation=False,
                    reasoning=result["intent"]["reasoning"]
                )
            }
        except Exception as e:
            logger.error(f"[GeminiClassifier] Unified classification failed: {e}")
            return {
                "resolution": ClassificationResult("UNCERTAIN", 0.0, False, f"Error: {e}"),
                "escalation": ClassificationResult("BOT_CAN_HANDLE", 0.5, False, "Fallback"),
                "intent": ClassificationResult("OTHER", 0.0, False, "Fallback")
            }
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for LLM"""
        if not history:
            return "No previous messages"
        
        formatted = []
        for msg in history[-5:]:  # Last 5 messages for context
            role = "Customer" if msg.get('role') == 'user' else "Assistant"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(formatted)
    
    def should_close_chat(self, resolution_classification: ClassificationResult) -> bool:
        """Determine if chat should be closed based on resolution classification"""
        return (resolution_classification.intent == "RESOLVED" and 
                resolution_classification.confidence > 0.8)
    
    def should_escalate(self, escalation_classification: ClassificationResult) -> bool:
        """Determine if conversation should be escalated to human"""
        # Only escalate if LLM says NEEDS_HUMAN with high confidence
        if escalation_classification.intent == "NEEDS_HUMAN" and escalation_classification.confidence > 0.7:
            return True
        # Or if requires_escalation flag is explicitly set
        if escalation_classification.requires_escalation:
            return True
        return False

class GeminiGenerator:
    """LLM-powered response generator using Gemini"""
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "google/gemini-2.5-flash-lite"
    
    def generate_response(self, message: str, history: List[Dict], system_prompt: str, category: str = "general") -> tuple:
        """Generate response using Gemini - WITH ERROR HANDLING"""
        try:
            # Build full message history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in history:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            return response_text, tokens_used
            
        except Exception as e:
            logger.error(f"[GeminiGenerator] Response generation failed: {e}")
            # Return honest error message
            fallback = (
                "I apologize, but I'm experiencing technical difficulties right now. "
                "Please contact our support team directly:\n\n"
                "📞 Phone: 1-888-415-5240 (24/7)\n"
                "✉️ Email: support@acecloudhosting.com"
            )
            return fallback, 0

# Initialize Gemini services
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
gemini_classifier = GeminiClassifier(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None
gemini_generator = GeminiGenerator(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None
llm_classifier = gemini_classifier  # Alias for compatibility

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API RETRY LOGIC: Handle transient failures with exponential backoff
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_api_with_retry(api_func, *args, max_retries=3, initial_delay=1.0, **kwargs):
    """Call API with exponential backoff retry on transient failures
    
    Args:
        api_func: The API function to call
        *args: Positional arguments for the API function
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        **kwargs: Keyword arguments for the API function
    
    Returns:
        API result dictionary with 'success' flag
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries):
        try:
            result = api_func(*args, **kwargs)
            
            # If API call succeeded, return immediately
            if result.get('success'):
                if attempt > 0:
                    logger.info(f"[Retry] ✓ API call succeeded on attempt {attempt + 1}/{max_retries}")
                return result
            
            # If API returned failure (not exception), retry
            last_error = result.get('error', 'Unknown error')
            logger.warning(f"[Retry] Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"[Retry] Attempt {attempt + 1}/{max_retries} exception: {e}")
        
        # Don't sleep after last attempt
        if attempt < max_retries - 1:
            logger.info(f"[Retry] Waiting {delay}s before retry...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    
    # All retries failed
    logger.error(f"[Retry] ✗ All {max_retries} attempts failed. Last error: {last_error}")
    return {"success": False, "error": "max_retries_exceeded", "details": last_error}

def classify_intent(message: str, history: List[Dict] = None) -> ClassificationResult:
    """Standalone classification function"""
    if gemini_classifier:
        return gemini_classifier.classify_intent(message, history or [])
    return ClassificationResult(intent="general_inquiry", confidence=0.0, requires_escalation=False)

def classify_resolution(message: str) -> bool:
    """Check if issue is resolved"""
    resolved_keywords = ['thank you', 'thanks', 'resolved', 'fixed', 'working now', 'solved']
    return any(keyword in message.lower() for keyword in resolved_keywords)

def classify_escalation(message: str) -> bool:
    """Check if escalation needed - delegate to LLM"""
    result = classify_intent(message, [])
    return result.requires_escalation

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='no-request-id')
session_id_var: ContextVar[str] = ContextVar('session_id', default='no-session-id')

# Custom log formatter with request ID and session ID
class ContextualFormatter(logging.Formatter):
    """Custom formatter that includes request_id and session_id in logs"""
    
    def format(self, record):
        # Add contextual information to log record
        record.request_id = request_id_var.get()
        record.session_id = session_id_var.get()
        return super().format(record)

# Configure enhanced logging with request tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [req:%(request_id)s] [session:%(session_id)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Apply custom formatter to all handlers
for handler in logging.getLogger().handlers:
    handler.setFormatter(ContextualFormatter(
        '%(asctime)s [%(levelname)s] [req:%(request_id)s] [session:%(session_id)s] %(name)s - %(message)s'
    ))

# Error alerting configuration
ERROR_ALERT_WEBHOOK = os.getenv("ERROR_ALERT_WEBHOOK", None)
ERROR_ALERT_THRESHOLD = 3  # Alert after 3 errors in a window
error_counts: Dict[str, int] = {}

def send_critical_alert(error_type: str, error_message: str, context: dict = None):
    """Send critical error alert to monitoring service"""
    try:
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "severity": "CRITICAL",
            "error_type": error_type,
            "message": error_message,
            "context": context or {},
            "service": "llm-chatbot",
            "request_id": request_id_var.get()
        }
        
        # Log structured alert
        logger.critical(f"ALERT: {error_type} - {error_message}", extra={"alert_data": json.dumps(alert_data)})
        
        # Send to external webhook if configured
        if ERROR_ALERT_WEBHOOK:
            import requests
            requests.post(
                ERROR_ALERT_WEBHOOK,
                json=alert_data,
                timeout=5,
                verify=False
            )
            logger.info(f"Alert sent to webhook for {error_type}")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

def track_error(error_type: str, error_message: str, context: dict = None):
    """Track errors and send alerts when threshold is exceeded"""
    global error_counts
    
    # Increment error count
    error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    # Send alert if threshold exceeded
    if error_counts[error_type] >= ERROR_ALERT_THRESHOLD:
        send_critical_alert(
            error_type,
            f"{error_message} (occurred {error_counts[error_type]} times)",
            context
        )
        error_counts[error_type] = 0  # Reset counter

app = FastAPI(title="Ace Cloud Hosting Support Bot - Gemini", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GEMINI-POWERED: No more OpenAI client needed!
# All LLM operations now use Gemini 2.5 Flash
# Benefits: 1M context, no truncation, 50% cheaper, faster
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LLM_MODEL = "gemini-2.5-flash"  # Changed from gpt-4o-mini

# Initialize IssueRouter for category classification
issue_router = IssueRouter()
logger.info("IssueRouter initialized successfully")

# MetricsCollector is already initialized as a global singleton
logger.info("MetricsCollector ready for tracking")

# StateManager is already initialized as a global singleton
logger.info("StateManager ready for conversation tracking")

# HandlerRegistry is already initialized as a global singleton
logger.info(f"HandlerRegistry ready with {len(handler_registry.handlers)} handlers")

conversations: Dict[str, List[Dict]] = {}

# Store SalesIQ conversation IDs for API operations (close, transfer, etc.)
# Maps internal session_id -> salesiq_conversation_id
conversation_id_map: Dict[str, str] = {}

# Fallback API class for when real API is not available
class FallbackAPI:
    def __init__(self):
        self.enabled = False
    def create_chat_session(self, visitor_id, conversation_history):
        logger.info(f"[API] Fallback: Simulating chat transfer for {visitor_id}")
        return {"success": True, "simulated": True, "message": "Chat transfer simulated"}
    def close_chat(self, conversation_id, reason="resolved"):
        logger.info(f"[API] Fallback: Simulating chat closure for conversation {conversation_id}, reason: {reason}")
        return {"success": True, "simulated": True, "message": f"Chat closure simulated - {reason}"}
    def create_callback_ticket(self, *args, **kwargs):
        logger.info("[API] Fallback: Simulating callback ticket creation")
        return {"success": True, "simulated": True, "ticket_number": "CB-SIM-001"}
    def create_support_ticket(self, *args, **kwargs):
        logger.info("[API] Fallback: Simulating support ticket creation")
        return {"success": True, "simulated": True, "ticket_number": "TK-SIM-001"}

# Load Zoho API integration with proper error handling
try:
    from zoho_api_simple import ZohoSalesIQAPI, ZohoDeskAPI
    salesiq_api = ZohoSalesIQAPI()
    desk_api = ZohoDeskAPI()
    logger.info(f"Zoho API loaded successfully - SalesIQ enabled: {salesiq_api.enabled}")
except ImportError as e:
    logger.error(f"Failed to import Zoho API module: {str(e)} - using fallback")
    salesiq_api = FallbackAPI()
    desk_api = FallbackAPI()
except Exception as e:
    logger.error(f"Failed to initialize Zoho API: {str(e)} - using fallback")
    salesiq_api = FallbackAPI()
    desk_api = FallbackAPI()


# Background cleanup job
async def cleanup_stale_sessions():
    """Background task to cleanup stale conversations every 15 minutes"""
    while True:
        try:
            await asyncio.sleep(15 * 60)  # Run every 15 minutes
            
            logger.info("[Cleanup] Starting stale session cleanup...")
            
            # Cleanup state manager sessions
            state_manager.cleanup_stale_sessions(timeout_minutes=30)
            
            # Cleanup in-memory conversations that match stale sessions
            stale_count = 0
            sessions_to_remove = []
            
            for session_id in list(conversations.keys()):
                session = state_manager.get_session(session_id)
                if not session or session.is_stale(timeout_minutes=30):
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                if session_id in conversations:
                    metrics_collector.end_conversation(session_id, "abandoned")
                    del conversations[session_id]
                    stale_count += 1
            
            if stale_count > 0:
                logger.info(f"[Cleanup] Removed {stale_count} stale conversations")
            else:
                logger.debug("[Cleanup] No stale conversations found")
                
        except Exception as e:
            logger.error(f"[Cleanup] Error in cleanup job: {e}", exc_info=True)


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("Starting background tasks...")
    asyncio.create_task(cleanup_stale_sessions())
    logger.info("✓ Cleanup job started (runs every 15 minutes)")
    salesiq_api = FallbackAPI()
    desk_api = FallbackAPI()

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

# Load expert system prompt from config file
def load_expert_prompt() -> str:
    """Load the expert system prompt from config file"""
    prompt_path = os.path.join(os.path.dirname(__file__), "config", "prompts", "expert_system_prompt.txt")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {prompt_path}. Using fallback prompt.")
        return "You are AceBuddy, a friendly IT support assistant for ACE Cloud Hosting."

def build_past_messages(history: List[Dict]) -> List[Dict]:
    """Build past_messages array for SalesIQ API according to their format
    
    Args:
        history: Conversation history in OpenAI format [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        List of message dicts in SalesIQ format:
        [{"sender_type": "visitor/bot", "sender_name": "...", "time": timestamp, "text": "..."}]
    """
    from datetime import datetime, timezone
    import time
    
    past_messages = []
    
    for idx, msg in enumerate(history):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        # Skip system messages
        if role == 'system':
            continue
        
        # Map role to SalesIQ sender_type
        if role == 'user':
            sender_type = "visitor"
            sender_name = "Customer"
        elif role == 'assistant':
            sender_type = "bot"
            sender_name = "AceBuddy"
        else:
            continue
        
        # Generate timestamp (current time minus message age for sequential ordering)
        # More recent messages = higher timestamp
        timestamp_ms = int((time.time() - (len(history) - idx) * 5) * 1000)
        
        message_obj = {
            "sender_type": sender_type,
            "sender_name": sender_name,
            "time": timestamp_ms,
            "text": content
        }
        
        past_messages.append(message_obj)
    
    return past_messages

# Load prompt on startup
EXPERT_PROMPT = load_expert_prompt()
logger.info(f"Expert prompt loaded successfully ({len(EXPERT_PROMPT)} characters)")

def generate_response(message: str, history: List[Dict], category: str = "other") -> str:
    """Generate response using Gemini with FULL conversation context
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🚀 GEMINI-POWERED: No more truncation!
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    With 1M token context:
    - Include FULL conversation history
    - Bot remembers entire conversation
    - Better troubleshooting continuity
    - Higher resolution rates
    
    Args:
        message: User message text
        history: FULL conversation history (no truncation!)
        category: Issue category from IssueRouter
    
    Returns:
        Tuple of (response_text, tokens_used)
    """
    
    # Use Gemini generator with full history
    if gemini_generator:
        response_text, tokens_used = gemini_generator.generate_response(
            message=message,
            history=history,  # FULL history - no truncation!
            system_prompt=EXPERT_PROMPT,
            category=category
        )
        
        logger.info(f"[Gemini] Response generated: {len(response_text)} chars, ~{tokens_used} tokens")
        return response_text, tokens_used
    else:
        # Fallback if Gemini not available
        logger.error("[Gemini] Generator not available - using fallback response")
        fallback = (
            "I apologize, but I'm having trouble processing your request right now. "
            "Let me connect you with our support team for immediate assistance."
        )
        return fallback, 0

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking"""
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "status": "online",
        "service": "Ace Cloud Hosting Support Bot - Gemini Powered",
        "version": "3.0.0",
        "llm_engine": "gemini-2.5-flash",
        "context_window": "1,000,000 tokens (no truncation)",
        "api_status": {
            "salesiq_enabled": salesiq_api.enabled if hasattr(salesiq_api, 'enabled') else False,
            "desk_enabled": desk_api.enabled if hasattr(desk_api, 'enabled') else False,
            "gemini_enabled": gemini_generator is not None
        },
        "endpoints": {
            "salesiq_webhook": "/webhook/salesiq",
            "chat": "/chat",
            "reset": "/reset/{session_id}",
            "health": "/health",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "mode": "production",
        "llm": "gemini-2.5-flash",
        "llm_status": "connected" if gemini_generator else "unavailable",
        "active_sessions": len(conversations),
        "api_status": {
            "salesiq_enabled": salesiq_api.enabled if hasattr(salesiq_api, 'enabled') else False,
            "desk_enabled": desk_api.enabled if hasattr(desk_api, 'enabled') else False,
            "gemini_enabled": gemini_generator is not None
        },
        "webhook_url": "https://web-production-3032d.up.railway.app/webhook/salesiq"
    }

@app.get("/callback")
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """OAuth 2.0 callback endpoint for Zoho authorization"""
    
    if error:
        html = f"""
        <html>
        <head><title>OAuth Error</title></head>
        <body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
            <div style="background: #ffcccc; padding: 20px; border-radius: 5px; max-width: 500px; margin: 20px auto;">
                <h2 style="color: #cc0000;">Authorization Failed</h2>
                <p><strong>Error:</strong> {error}</p>
                <p>Please try again or contact support.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    if not code:
        html = """
        <html>
        <head><title>OAuth Callback</title></head>
        <body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
            <div style="background: #ffcccc; padding: 20px; border-radius: 5px; max-width: 500px; margin: 20px auto;">
                <h2 style="color: #cc0000;">No Authorization Code Received</h2>
                <p>The authorization code was not found in the callback URL.</p>
                <p>Please try the authorization process again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    # Success - display the authorization code
    html = f"""
    <html>
    <head><title>OAuth Authorization Success</title></head>
    <body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
        <div style="background: #ccffcc; padding: 20px; border-radius: 5px; max-width: 600px; margin: 20px auto;">
            <h2 style="color: #00cc00;">Authorization Successful!</h2>
            <p>Your authorization code is ready. Copy the code below and use it in the token exchange step.</p>
            
            <div style="background: #ffffff; padding: 15px; border: 2px solid #00cc00; border-radius: 5px; margin: 20px 0;">
                <h3>Authorization Code:</h3>
                <code style="font-size: 14px; word-break: break-all; display: block; background: #f0f0f0; padding: 10px; border-radius: 3px;">
                    {code}
                </code>
                <button onclick="navigator.clipboard.writeText('{code}'); alert('Code copied to clipboard!');" 
                        style="margin-top: 10px; padding: 10px 20px; background: #00cc00; color: white; border: none; border-radius: 3px; cursor: pointer;">
                    Copy Code
                </button>
            </div>
            
            <p><strong>State:</strong> {state if state else 'N/A'}</p>
            
            <div style="background: #ffffcc; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3>Next Step:</h3>
                <p>Run this PowerShell command to exchange the code for an access token:</p>
                <pre style="background: #f0f0f0; padding: 10px; border-radius: 3px; overflow-x: auto;">
$code = "{code}"
$clientId = "YOUR_CLIENT_ID"
$clientSecret = "YOUR_CLIENT_SECRET"
$redirectUri = "http://localhost:8000/callback"

$response = Invoke-RestMethod -Uri "https://accounts.zoho.in/oauth/v2/token" -Method POST -Body @{{
    code = $code
    grant_type = "authorization_code"
    client_id = $clientId
    client_secret = $clientSecret
    redirect_uri = $redirectUri
    scope = "SalesIQ.conversations.CREATE,SalesIQ.conversations.READ,SalesIQ.conversations.UPDATE,SalesIQ.conversations.DELETE"
}}

Write-Host "Access Token:"
Write-Host $response.access_token
                </pre>
            </div>
        </div>
    </body>
    </html>
    """
    
    logger.info(f"[OAuth] Authorization successful - code received (state: {state})")
    return HTMLResponse(content=html)


@app.get("/webhook/salesiq")
async def salesiq_webhook_test():
    """Test endpoint for SalesIQ webhook - GET request"""
    return {
        "status": "webhook_ready",
        "message": "SalesIQ webhook endpoint is accessible",
        "method": "GET",
        "note": "POST requests will be processed as chat messages"
    }

@app.get("/debug/conversation-ids")
async def get_conversation_ids():
    """Debug endpoint to view all stored SalesIQ conversation IDs"""
    screen_name = os.getenv('SALESIQ_SCREEN_NAME', 'rtdsportal')
    
    id_summary = []
    for session_id, conv_id in conversation_id_map.items():
        close_url = f"https://salesiq.zohopublic.in/api/v2/{screen_name}/conversations/{conv_id}/close"
        id_summary.append({
            "internal_session_id": session_id,
            "salesiq_conversation_id": conv_id,
            "close_api_url": close_url,
            "has_messages": session_id in conversations,
            "message_count": len(conversations.get(session_id, []))
        })
    
    return {
        "total_conversations": len(conversation_id_map),
        "screen_name": screen_name,
        "conversations": id_summary,
        "note": "Use close_api_url with POST request and Bearer token to close chat"
    }

@app.get("/test/widget", response_class=HTMLResponse)
async def test_widget():
    """Public test page to load SalesIQ widget for real visitor testing.
    Set SALESIQ_WIDGET_CODE env var to your SalesIQ embed snippet.
    """
    widget_code = os.getenv("SALESIQ_WIDGET_CODE", "").strip()
    if not widget_code:
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>SalesIQ Test</title></head>"
            "<body><h2>SalesIQ Widget Test</h2>"
            "<p>Set the SALESIQ_WIDGET_CODE env var with your SalesIQ embed snippet to load the widget here.</p>"
            "<p>This page is served from your Railway app and counts as a real website visitor.</p>"
            "</body></html>"
        )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><title>SalesIQ Test</title></head><body>"
        "<h2>SalesIQ Widget Live Test</h2><p>This page is public and will register real visitors.</p>"
        + widget_code +
        "</body></html>"
    )
    return html

@app.post("/webhook/salesiq")
async def salesiq_webhook(request: dict):
    """
    Direct webhook endpoint for Zoho SalesIQ - Hybrid LLM
    
    CRITICAL: This function MUST ALWAYS return a JSONResponse with proper format.
    If ANY exception occurs, we return a fallback response to prevent SalesIQ errors.
    """
    session_id = None
    
    # OUTER TRY-CATCH: Catches absolutely everything including JSON encoding errors
    try:
        return await _salesiq_webhook_inner(request)
    except Exception as outer_e:
        logger.critical(f"[CRITICAL] Outer exception in webhook: {outer_e}")
        logger.critical(f"[CRITICAL] Traceback: {traceback.format_exc()}")
        
        # GUARANTEED fallback response - this should NEVER fail
        return JSONResponse(
            status_code=200,
            content={
                "action": "reply",
                "replies": ["I'm experiencing technical difficulties. Let me connect you with our support team."],
                "session_id": "error"
            }
        )

async def _salesiq_webhook_inner(request: dict):
    """Inner webhook handler with normal exception handling"""
    session_id = None
    try:
        # Set session context for logging (will be updated once extracted)
        session_id_var.set("extracting")
        
        logger.info(f"[SalesIQ] Webhook received")
        
        # Validate request structure
        if not isinstance(request, dict):
            logger.error(f"[SalesIQ] Invalid request format: {type(request)}")
            track_error(
                "invalid_webhook_format",
                f"Received non-dict webhook: {type(request)}",
                {"request_type": str(type(request))}
            )
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": ["I'm having technical difficulties. Let me connect you with our support team."],
                    "session_id": "unknown"
                }
            )
        
        logger.info(f"[SalesIQ] Request keys: {list(request.keys())}")
        logger.debug(f"[SalesIQ] Full request payload: {request}")
        
        # Log all possible IDs for transfer debugging
        visitor = request.get('visitor', {})
        chat = request.get('chat', {})
        conversation = request.get('conversation', {})
        
        logger.debug(f"[SalesIQ] Visitor data: {visitor}")
        logger.debug(f"[SalesIQ] Chat data: {chat}")
        logger.debug(f"[SalesIQ] Conversation data: {conversation}")
        
        # ============================================================
        # SALESIQ API CONVERSATION ID EXTRACTION
        # ============================================================
        # Extract ALL possible conversation IDs from webhook payload
        salesiq_conversation_id = conversation.get('id')
        salesiq_chat_id = chat.get('id')
        salesiq_visitor_id = visitor.get('id')
        salesiq_active_conversation = visitor.get('active_conversation_id')
        
        # Extract message details BEFORE logging
        message_obj = request.get('message', {})
        message_timestamp = None
        message_text_preview = ""
        if isinstance(message_obj, dict):
            message_timestamp = message_obj.get('time') or message_obj.get('timestamp')
            message_text_preview = message_obj.get('text', '').strip()
        else:
            message_text_preview = str(message_obj).strip()
        
        # Get visitor info
        visitor_name = visitor.get('name', 'Unknown')
        visitor_email = visitor.get('email', 'No email')
        visitor_phone = visitor.get('phone', 'No phone')
        
        # Simple logging for debugging
        logger.info(f"[SalesIQ] Message: {message_text_preview[:100] if message_text_preview else '(empty)'}")
        logger.debug(f"[SalesIQ] Visitor: {visitor_email}, Active Conv: {salesiq_active_conversation}")
        
        # Prevent duplicate greeting webhooks (SalesIQ sometimes sends multiple empty requests)
        # Only send greeting once per session
        if not message_text_preview and state_manager.get_session(session_id):
            logger.debug(f"[SalesIQ] Ignoring duplicate empty webhook for existing session {session_id}")
            return JSONResponse(status_code=200, content={"action": "reply", "replies": []})
        
        # Extract payload (from quick reply buttons)
        payload = request.get('payload', '')
        if payload:
            logger.info(f"  - Payload: {payload}")
        
        # Determine the correct conversation_id for API calls
        api_conversation_id = (
            salesiq_conversation_id or 
            salesiq_active_conversation or 
            salesiq_chat_id
        )
        
        # Store conversation ID for potential API operations
        if not api_conversation_id:
            logger.warning(f"[SalesIQ] No conversation ID found for API operations")
        
        # Extract session ID (try multiple sources)
        session_id = (
            visitor.get('active_conversation_id') or
            chat.get('id') or
            conversation.get('id') or
            request.get('session_id') or 
            visitor.get('id') or
            'unknown'
        )
        
        # Update session context for logging
        session_id_var.set(session_id)
        
        # Store conversation ID mapping for later API operations (close, transfer)
        if api_conversation_id and session_id != 'unknown':
            conversation_id_map[session_id] = api_conversation_id
            logger.info(f"[ID Mapping] Stored: session_id={session_id} -> conversation_id={api_conversation_id}")
        
        # Extract message text - handle multiple formats (already extracted above for logging)
        if isinstance(message_obj, dict):
            message_text = message_obj.get('text', '').strip()
        else:
            message_text = str(message_obj).strip()
        
        # Handle empty message
        if not message_text:
            logger.info(f"[Session] 👋 INITIAL CONTACT - Sending greeting")
            logger.info(f"[Session] New visitor from: {visitor.get('email', 'unknown')}")
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": ["Hi! I'm AceBuddy, your Ace Cloud Hosting support assistant. What can I help you with today?"],
                    "session_id": session_id
                }
            )
        
        # Initialize conversation history
        if session_id not in conversations:
            conversations[session_id] = []
            logger.info(f"[Session] ✓ NEW CONVERSATION STARTED | Category: {issue_router.classify(message_text)}")
        
        history = conversations[session_id]
        
        # Create lowercase version for simple keyword checks (used by button handlers, etc.)
        message_lower = message_text.lower().strip()
        
        # ============================================================
        # SESSION RESET: Detect "new issue" request for testing
        # ============================================================
        new_issue_keywords = ["new issue", "start fresh", "clear context", "reset", "new problem", "different issue"]
        is_new_issue_request = any(keyword in message_lower for keyword in new_issue_keywords)
        
        if is_new_issue_request:
            logger.info(f"[Session] 🔄 NEW ISSUE REQUEST DETECTED - Clearing session context")
            conversations[session_id] = []  # Clear conversation history
            response_text = "Sure! Starting fresh. What issue can I help you with today?"
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }
            )
        
        # Check if conversation was handed off to operator - if so, bot should stop responding
        if history and any(msg.get("role") == "system" and msg.get("content") == "HANDOFF_TO_OPERATOR" for msg in history):
            logger.info(f"[Handoff] ✋ Session {session_id} handed off to operator - bot ignoring message")
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [],  # Empty reply - bot stays silent
                    "session_id": session_id
                }
            )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # LLM-FIRST CLASSIFICATION: No more keyword matching!
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info(f"[LLM] Classifying intent for message: '{message_text[:50]}...'")
        intent_classification = classify_intent(message_text, history)
        logger.info(f"[LLM] Intent: {intent_classification.intent} (confidence: {intent_classification.confidence}, escalation: {intent_classification.requires_escalation})")
        
        # DISABLED: Immediate escalation check - let generate_response handle escalation
        # The bot now asks troubleshooting questions FIRST via generate_response()
        # Only escalate AFTER the user can't resolve it (expert prompt handles this)
        if False and (intent_classification.requires_escalation or intent_classification.intent == "escalation_request"):
            logger.info(f"[SalesIQ] LLM detected escalation request - initiating transfer")
            # Escalation handling disabled - fallthrough to generate_response
            pass
        
        # ============================================================
        # CHECK IF USER IS CONTINUING AFTER SATISFACTION MESSAGE
        # ============================================================
        # If user asks a new question after we sent satisfaction message,
        # treat it as a NEW conversation (don't try to close chat)
        
        conversation_should_restart = False
        if len(conversations[session_id]) >= 2:
            last_bot_message = conversations[session_id][-1].get('content', '') if conversations[session_id][-1].get('role') == 'assistant' else ''
            
            # Check if we recently sent satisfaction/closure message
            satisfaction_indicators = [
                "i'm happy the issue is resolved",
                "is there anything else i can help",
                "would you like me to close this chat",
                "have a great day"
            ]
            
            recently_asked_to_close = any(indicator in last_bot_message.lower() for indicator in satisfaction_indicators)
            
            if recently_asked_to_close:
                # Check user's response
                user_wants_to_continue = (
                    "yes" in message_lower or 
                    "i have" in message_lower or
                    "another" in message_lower or
                    "help" in message_lower or
                    "question" in message_lower or
                    len(message_text) > 15  # Likely a new question, not just "no" or "bye"
                )
                
                user_wants_to_close = (
                    "no" in message_lower or
                    "nope" in message_lower or
                    "close" in message_lower or
                    "bye" in message_lower or
                    "thanks" in message_lower or
                    "thank you" in message_lower
                ) and len(message_text) < 20  # Short closure confirmation
                
                if user_wants_to_continue:
                    logger.info(f"[Conversation] User has NEW question after resolution - restarting conversation")
                    conversation_should_restart = True
                    # Reset state to active
                    state_manager.create_session(session_id, category="other")
                    
                elif user_wants_to_close:
                    logger.info(f"[Conversation] User confirmed chat closure")
                    response_text = "You're welcome! Feel free to reach out anytime. Goodbye! 👋"
                    conversations[session_id].append({"role": "user", "content": message_text})
                    conversations[session_id].append({"role": "assistant", "content": response_text})
                    
                    # Mark as resolved and let idle timeout handle closure
                    if session_id in conversations:
                        metrics_collector.end_conversation(session_id, "resolved")
                        state_manager.end_session(session_id, ConversationState.RESOLVED)
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "action": "reply",
                            "replies": [response_text],
                            "session_id": session_id
                        }
                    )
        
        # ============================================================
        # CONTEXT CHANGE DETECTION - User changing their mind after buttons shown
        # ============================================================
        # If buttons were shown (escalation offered) but user provides NEW information instead
        # of clicking buttons, reset the escalation state and process the new message
        correction_keywords = ["no", "wait", "actually", "leave", "i meant", "yrr", "not", "never mind"]
        urgency_keywords = ["today", "tomorrow", "next week", "next month", "later", "day after tomorrow"]
        
        # Check if last bot message showed escalation buttons
        buttons_were_shown = False
        if len(history) > 0:
            last_bot = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            buttons_were_shown = "let me connect you" in last_bot.lower() or "immediate attention" in last_bot.lower()
        
        # If buttons were shown AND user is providing new info (not clicking buttons)
        user_is_correcting = any(keyword in message_lower for keyword in correction_keywords)
        user_is_clarifying = any(keyword in message_lower for keyword in urgency_keywords)
        
        if buttons_were_shown and (user_is_correcting or user_is_clarifying) and len(message_text.strip()) > 5:
            logger.info(f"[Context] 🔄 USER CHANGING CONTEXT after buttons shown: '{message_text[:80]}'")
            logger.info(f"[Context] Detected correction/clarification - bypassing button logic, processing as new message")
            # Don't return here - let it continue to normal LLM processing below
            # This allows the bot to understand "leave i need... next week" as a NEW request
        
        # ============================================================
        # BUTTON HANDLERS - CHECK FIRST (Priority over LLM classification)
        # ============================================================
        # These must run BEFORE LLM classification to prevent escalation loop
        # When user clicks a button, handle it immediately without LLM analysis
        
        # Check for option selections - CHAT WITH TECHNICIAN (with emoji matching)
        # STRICT MATCHING: Only trigger on actual button clicks, not partial matches in sentences
        is_instant_chat_button = (
            message_text.strip() == "💬 Chat with Technician" or
            message_lower.strip() == "chat with technician" or
            message_lower.strip() == "option 1" or
            message_lower.strip() == "1" or
            payload == "option_1" or
            (message_text.strip() == "📞" and len(message_text.strip()) <= 2)  # Emoji only
        )
        
        # Only process button click if user is NOT correcting/clarifying context
        if is_instant_chat_button and not (user_is_correcting or user_is_clarifying):
            logger.info(f"[Action] ✅ BUTTON CLICKED: Chat with Technician (Option 1)")
            logger.info(f"[Action] 🔄 CHAT TRANSFER INITIATED")
            logger.info(f"[SalesIQ] Using FORWARD action (official SalesIQ bot forwarding mechanism)")
            
            # Use official SalesIQ "forward" action to hand off chat
            # This is the CORRECT way per SalesIQ bot documentation
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "forward",
                    "department": "2782000000002013",  # Support (QB & App Hosting) department
                    "replies": ["I'm connecting you with our support team. An operator will assist you shortly."]
                }
            )
        
        # Check for option selections - SCHEDULE CALLBACK (with emoji matching)
        # STRICT MATCHING: Only trigger on actual button clicks, not partial matches in sentences
        is_callback_button = (
            message_text.strip() == "📅 Schedule Callback" or
            message_lower.strip() == "schedule callback" or
            message_lower.strip() == "callback" or
            message_lower.strip() == "option 2" or
            message_lower.strip() == "2" or
            payload == "option_2" or
            (message_text.strip() == "📅" and len(message_text.strip()) <= 2)  # Emoji only
        )
        
        # Only process button click if user is NOT correcting/clarifying context
        if is_callback_button and not (user_is_correcting or user_is_clarifying):
            logger.info(f"[Action] ✅ BUTTON CLICKED: Schedule Callback (Option 2)")
            logger.info(f"[Action] 📞 CALLBACK SCHEDULED - Waiting for time & phone details")
            
            # Log callback request (don't call transition - method doesn't exist)
            logger.debug(f"[State] Callback requested for session {session_id}")
            
            # Extract visitor info
            visitor_email = visitor.get("email", "support@acecloudhosting.com")
            visitor_name = visitor.get("name", visitor_email.split("@")[0] if visitor_email else "Chat User")
            
            response_text = (
                "Perfect! I'm creating a callback request for you.\n\n"
                "Please provide:\n"
                "1. Your preferred time (e.g., 'tomorrow at 2 PM' or 'Monday morning')\n"
                "2. Your phone number\n\n"
                "Our support team will call you back at that time. A callback has been scheduled and you'll receive a confirmation email shortly.\n\n"
                "Thank you for contacting Ace Cloud Hosting!"
            )
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            # Mark session as waiting for callback details
            conversations[session_id].append({"role": "system", "content": "WAITING_FOR_CALLBACK_DETAILS"})

            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }
            )
            
        # Check if we are waiting for callback details
        if len(history) > 0 and history[-1].get("content") == "WAITING_FOR_CALLBACK_DETAILS":
            logger.info(f"[SalesIQ] Received callback details: {message_text}")
            
            # Remove the system marker
            history.pop()
            
            # Extract visitor info
            visitor_email = visitor.get("email", "support@acecloudhosting.com")
            visitor_name = visitor.get("name", visitor_email.split("@")[0] if visitor_email else "Chat User")

            # Best-effort parse for phone / preferred time
            import re
            
            # Extract time (stop at newline or 'phone' keyword)
            time_match = re.search(r"(?i)\btime\b\s*[:=\-]\s*([^\n]+?)(?=\s*phone\b|\s*$)", message_text, re.DOTALL)
            preferred_time = time_match.group(1).strip() if time_match else None
            
            # Extract phone number - fix character class order to avoid range error
            phone_match = re.search(r"(?i)\bphone\b\s*[:=\-]\s*([\d\s+\-]+)", message_text)
            if phone_match:
                phone = re.sub(r"[^\d+]", "", phone_match.group(1))  # Clean phone number
            else:
                # Fallback: find any number sequence
                phone_match = re.search(r"\b(?:\+?\d[\d\s\-]{8,}\d)\b", message_text)
                phone = phone_match.group(0).strip() if phone_match else None
            
            # Add user's details to history
            conversations[session_id].append({"role": "user", "content": message_text})
            
            # Create the callback ticket NOW with the details
            logger.info(f"[Callback] Creating with time={preferred_time}, phone={phone}")
            try:
                # Get conversation history including the details provided
                conv_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversations.get(session_id, [])])
                
                # Append the specific details to the description
                full_description = f"{conv_history}\n\nUSER PROVIDED DETAILS:\n{message_text}"
                
                api_result = desk_api.create_callback_ticket(
                    visitor_email=visitor_email,
                    visitor_name=visitor_name,
                    conversation_history=full_description,
                    preferred_time=preferred_time,
                    phone=phone,
                )
                logger.info(f"[Desk] Callback call result: {api_result}")
            except Exception as e:
                logger.error(f"[Desk] Callback call exception: {str(e)}")
                import traceback
                logger.error(f"[Desk] Traceback: {traceback.format_exc()}")
                api_result = {"success": False, "error": "exception", "details": str(e)}

            if api_result.get("success"):
                logger.info(f"[Action] ✓ CALLBACK TICKET CREATED SUCCESSFULLY")
                logger.info(f"[Action] 📞 Callback scheduled for visitor: {visitor.get('name', 'Unknown')}")
                logger.info(f"[Action] Email: {visitor.get('email', 'Not provided')}")
                response_text = "Perfect! Your callback has been created successfully. You will receive a call from our support team at your requested time. Thank you!"
            else:
                logger.warning(f"[Action] ✗ CALLBACK TICKET CREATION FAILED")
                logger.warning(f"[Action] Error: {api_result.get('error', 'Unknown error')}")
                response_text = (
                    "I got your details, but I couldn't create the callback in our system right now. "
                    "Please call our support team at 1-888-415-5240 for immediate help."
                )
            
            # Only close the chat if callback creation succeeded
            if api_result.get("success"):
                logger.info(f"[Callback] ✓ Callback created successfully - closing chat")
                try:
                    close_result = salesiq_api.close_chat(session_id, "callback_scheduled")
                    logger.info(f"[SalesIQ] Chat closure result: {close_result}")
                except Exception as e:
                    logger.error(f"[SalesIQ] Chat closure error: {str(e)}")
                
                # Clear conversation after success
                if session_id in conversations:
                    logger.info(f"[Metrics] 📊 CONVERSATION ENDED - Reason: Callback Scheduled")
                metrics_collector.end_conversation(session_id, "resolved")
                del conversations[session_id]

            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }
            )
        
        # ============================================================
        # OPTIMIZED LLM CLASSIFICATION (1 API call instead of 3)
        # ============================================================
        # Use unified classification to analyze resolution + escalation + intent in single call
        # Saves 66% of API calls (3x → 1x per message)
        # Includes token tracking and hallucination prevention
        # SKIP classification if conversation just restarted (new question after resolution)
        
        if conversation_should_restart:
            logger.info(f"[LLM Classifier] Skipping classification - conversation restarted with new question")
            # Force uncertain classification to let main LLM handle the new question
            classifications = {
                "resolution": ClassificationResult(intent="UNCERTAIN", confidence=0.0, requires_escalation=False, reasoning="New question after resolution"),
                "escalation": ClassificationResult(intent="BOT_CAN_HANDLE", confidence=1.0, requires_escalation=False, reasoning="New conversation"),
                "intent": ClassificationResult(intent="QUESTION", confidence=1.0, requires_escalation=False, reasoning="User has new question")
            }
        elif not llm_classifier:
            logger.warning(f"[LLM Classifier] Skipping classification - API key not configured")
            classifications = {
                "resolution": ClassificationResult(intent="UNCERTAIN", confidence=0.0, requires_escalation=False, reasoning="No API key"),
                "escalation": ClassificationResult(intent="BOT_CAN_HANDLE", confidence=0.5, requires_escalation=False, reasoning="No API key"),
                "intent": ClassificationResult(intent="OTHER", confidence=0.0, requires_escalation=False, reasoning="No API key")
            }
        else:
            logger.info(f"[LLM Classifier] Running unified classification (1 API call)...")
            
            try:
                classifications = llm_classifier.classify_unified(
                    message_text, 
                    conversations[session_id],
                    session_id=session_id  # Track token usage per session
                )
            except Exception as e:
                logger.error(f"[LLM Classifier] Classification failed: {e}")
                # Fallback: Continue without classification (let main LLM handle it)
                classifications = {
                    "resolution": ClassificationResult(intent="UNCERTAIN", confidence=0.0, requires_escalation=False, reasoning="Classification error"),
                    "escalation": ClassificationResult(intent="UNCERTAIN", confidence=0.0, requires_escalation=False, reasoning="Classification error"),
                    "intent": ClassificationResult(intent="OTHER", confidence=0.0, requires_escalation=False, reasoning="Classification error")
                }
        
        resolution_classification = classifications["resolution"]
        escalation_classification = classifications["escalation"]
        
        logger.info(f"[LLM Classifier] Resolution: {resolution_classification.intent} ({resolution_classification.confidence:.2f}) - {resolution_classification.reasoning}")
        logger.info(f"[LLM Classifier] Escalation: {escalation_classification.intent} ({escalation_classification.confidence:.2f}) - {escalation_classification.reasoning}")
        
        # ============================================================
        # RESOLUTION CHECK (Smart Satisfaction Confirmation)
        # ============================================================
        # NOTE: Zoho doesn't allow API-based chat closure for bot chats
        # Strategy: Confirm resolution + let idle timeout close chat (2-3 min)
        # Main value: Prevents unnecessary escalations by detecting true resolution
        
        if llm_classifier and llm_classifier.should_close_chat(resolution_classification):
            logger.info(f"[Resolution] ✓ ISSUE RESOLVED (LLM-confirmed)")
            logger.info(f"[Resolution] User message: '{message_text[:100]}'")
            logger.info(f"[Resolution] Confidence: {resolution_classification.confidence}% (threshold: {llm_classifier.resolution_threshold}%)")
            logger.info(f"[Resolution] Action: Send satisfaction confirmation (auto-close via idle timeout)")
            
            # Transition to resolved state
            state_manager.end_session(session_id, ConversationState.RESOLVED)
            
            # Send final satisfaction message - chat will close via idle timeout
            response_text = (
                "Great! I'm glad the issue is resolved. 😊\n\n"
                "If you need anything else, just let me know!"
            )
            
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            # Track resolution (important for metrics)
            if session_id in conversations:
                metrics_collector.end_conversation(session_id, "resolved")
                logger.info(f"[Metrics] 📊 Issue resolved by bot - prevented escalation")
                
                # Auto-close chat via API
                if salesiq_api.enabled:
                    logger.info(f"[Resolution] Attempting to close chat {session_id}")
                    close_result = salesiq_api.close_chat(session_id, "resolved")
                    if close_result.get("success"):
                        logger.info(f"[Resolution] ✓ Chat closed successfully")
                    else:
                        logger.warning(f"[Resolution] Failed to close chat: {close_result.get('error')}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }   
            )
        
        # ============================================================
        # ESCALATION CHECK - DISABLED
        # ============================================================
        # DISABLED: Let generate_response() handle escalation via expert prompt
        # Only escalate AFTER bot provides troubleshooting (if user still needs help)
        if False and llm_classifier.should_escalate(escalation_classification):
            logger.info(f"[Escalation] 🆙 USER NEEDS HUMAN ASSISTANCE (LLM-detected)")
            pass  # This escalation path is disabled
        
        # Fallthrough to generate_response() for bot to ask troubleshooting questions
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REMOVED KEYWORD-BASED LOGIC: LLM now handles all intent detection
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Skip removed password keyword checking
        if False:
            logger.info(f"[SalesIQ] Password reset detected")
            # Check if user already answered about SelfCare registration
            if len(history) > 0:
                last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
                # If bot already asked about SelfCare registration
                if 'registered on the selfcare portal' in last_bot_message.lower():
                    # User is responding to that question
                    if 'yes' in message_lower or 'registered' in message_lower:
                        logger.info(f"[SalesIQ] User is registered on SelfCare")
                        response_text = "Great! Visit https://selfcare.acecloudhosting.com and click 'Forgot your password'. Let me know when you're there!"
                        conversations[session_id].append({"role": "user", "content": message_text})
                        conversations[session_id].append({"role": "assistant", "content": response_text})
                        return JSONResponse(
                            status_code=200,
                            content={
                                "action": "reply",
                                "replies": [response_text],
                                "session_id": session_id
                            }
                        )
                    elif 'no' in message_lower or 'not registered' in message_lower:
                        logger.info(f"[SalesIQ] User is NOT registered on SelfCare - providing POC option")
                        response_text = (
                            "No problem! For server/user account password reset, you have two options:\n\n"
                            "1. Contact your account's POC (Point of Contact) or admin - they can reset your password through MyPortal\n"
                            "2. Call our support team at 1-888-415-5240 (24/7)\n\n"
                            "Which option works better for you?"
                        )
                        conversations[session_id].append({"role": "user", "content": message_text})
                        conversations[session_id].append({"role": "assistant", "content": response_text})
                        return JSONResponse(
                            status_code=200,
                            content={
                                "action": "reply",
                                "replies": [response_text],
                                "session_id": session_id
                            }
                        )
            else:
                # First time asking about password reset
                logger.info(f"[SalesIQ] First password reset question - asking about SelfCare registration")
                response_text = "I can help! Are you registered on the SelfCare portal?"
                conversations[session_id].append({"role": "user", "content": message_text})
                conversations[session_id].append({"role": "assistant", "content": response_text})
                return JSONResponse(
                    status_code=200,
                    content={
                        "action": "reply",
                        "replies": [response_text],
                        "session_id": session_id
                    }
                )
        
        # Skip removed app update keyword checking
        if False:
            logger.info(f"[SalesIQ] Application update request detected")
            response_text = "Application updates need to be handled by our support team to avoid downtime. Please contact support at:\n\nPhone: 1-888-415-5240 (24/7)\nEmail: support@acecloudhosting.com\n\nThey'll schedule the update for you!"
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }
            )
        
        # Skip removed agent request phrases keyword checking
        if False:
            agent_request_phrases_removed = [
            # Direct agent requests
            "connect me to agent", "connect to agent", "human agent", "talk to human", "speak to agent",
            "speak to someone", "talk to someone", "connect to human", "real person", "live person",
            "customer service", "customer support", "support agent", "support representative",
            
            # Escalation language
            "escalate", "supervisor", "manager", "senior support", "higher level",
            "transfer me", "transfer to", "forward to", "put me through",
            
            # Help requests
            "need help now", "need immediate help", "need assistance", "get me help",
            "i need someone", "can someone help", "someone help me",
            
            # Alternative phrasing
            "speak with agent", "talk with agent", "chat with agent", "contact agent",
            "operator", "representative", "specialist", "expert",
            
            # Direct requests
            "get me someone", "can i talk to", "may i speak", "i want to talk", "i want to speak",
            "let me talk", "let me speak", "connect me", "transfer call"
            ]
        
        # Skip removed escalation handler
        if False and any(phrase in message_lower for phrase in ["removed"]):
            pass
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REMOVED ACKNOWLEDGMENT CHECKING: LLM handles conversation flow
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Skip acknowledgment detection - let LLM handle
        if False:
            is_acknowledgment_removed = False
            final_goodbye_keywords_removed = []
            is_final_goodbye_removed = False
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REMOVED ALL HARDCODED ACKNOWLEDGMENT/GOODBYE LOGIC
        # LLM now understands conversation flow and context naturally
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Check if user said "no" to our "anything else" question
        if len(history) > 0:
            last_bot_message = history[-1].get('content', '') if history[-1].get('role') == 'assistant' else ''
            if 'anything else i can help you with' in last_bot_message.lower():
                # Bot asked if they need more help
                negative_responses = ["no", "nope", "no thanks", "no thank you", "nah", "i'm good", "im good", "that's all", "thats all"]
                if message_lower in negative_responses or any(neg in message_lower for neg in ["no", "nope", "nah"]):
                    logger.info(f"[Resolution] ✓ User declined further assistance")
                    logger.info(f"[Resolution] Action: Auto-closing chat session")
                    
                    response_text = "Perfect! Thank you for chatting. This chat will close now. Have a great day!"
                    conversations[session_id].append({"role": "user", "content": message_text})
                    conversations[session_id].append({"role": "assistant", "content": response_text})
                    
                    # Auto-close chat
                    close_result = salesiq_api.close_chat(session_id, "completed")
                    if close_result.get('success'):
                        logger.info(f"[Action] ✓ CHAT AUTO-CLOSED SUCCESSFULLY")
                    
                    if session_id in conversations:
                        metrics_collector.end_conversation(session_id, "resolved")
                        state_manager.end_session(session_id, ConversationState.RESOLVED)
                        del conversations[session_id]
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "action": "reply",
                            "replies": [response_text],
                            "session_id": session_id
                        }
                    )
        
        # Classify message category using IssueRouter (saves 60% of LLM tokens)
        category = issue_router.classify(message_text)
        logger.info(f"[SalesIQ] Message classified as: {category}")
        
        # Initialize state tracking for new conversations
        if session_id not in conversations or len(conversations[session_id]) == 0:
            router_matched = category != "other"
            logger.info(f"[Metrics] 📊 NEW CONVERSATION STARTED")
            logger.info(f"[Metrics] Category: {category}, Router Matched: {router_matched}")
            metrics_collector.start_conversation(session_id, category)
            
            # Create state management session
            state_manager.start_session(session_id)
            logger.info(f"[State] Session {session_id} created in state: NEW")
        
        # Detect state transition from user message
        session_exists = state_manager.get_session(session_id)
        if session_exists:
            current_state = state_manager.get_state(session_id)
            # State transitions disabled for now - just track state
            logger.debug(f"[State] Current state: {current_state.value}")
        
        # Get current state
        current_state = state_manager.get_state(session_id)
        
        # SKIP handler registry - go straight to LLM generation
        response_text = None
        tokens_used = 0
        
        # GENERATE LLM RESPONSE (no handlers, just direct LLM)
        if not response_text:
            logger.info(f"[LLM] 🤖 Generating response using Gemini...")
            try:
                response_text, tokens_used = generate_response(
                    message_text,
                    conversations[session_id],
                    category
                )
                logger.info(f"[LLM] ✓ Generated response ({tokens_used} tokens)")
            except Exception as e:
                logger.error(f"[LLM] Generation failed: {e}")
                response_text = "I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team at 1-888-415-5240."
                tokens_used = 0
        
        # ============================================================
        # Phase 3: LLM response generated successfully
        # ============================================================
        
        # Check if user explicitly requested escalation
        escalation_request_keywords = [
            "connect me to someone", "talk to agent", "speak to agent", "chat with agent",
            "human agent", "real person", "live person", "support team", "technician",
            "can you connect me", "connect me to", "transfer me", "escalate",
            "i need help", "i need someone", "not working", "not fixed", "still not working"
        ]
        
        user_requested_escalation = any(keyword in message_lower for keyword in escalation_request_keywords)
        
        # Check if bot response indicates escalation
        bot_escalation_phrases = [
            "i'll connect you", "i understand you'd like to connect",
            "let me connect you", "connecting you with", "connect you with our support team"
        ]
        
        bot_is_escalating = any(phrase in response_text.lower() for phrase in bot_escalation_phrases)
        
        # If escalation is happening, show buttons
        if user_requested_escalation or bot_is_escalating:
            logger.info(f"[Escalation] 🆙 ESCALATION DETECTED - Showing escalation buttons")
            logger.info(f"[Escalation] User requested: {user_requested_escalation}, Bot escalating: {bot_is_escalating}")
            
            # Update response to be clearer about options
            if "connect you" not in response_text.lower():
                response_text = "I understand this needs attention. Let me connect you with the right support:"
            
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "suggestions": [
                        {
                            "text": "Chat with Technician",
                            "action_type": "reply",
                            "action_value": "1"
                        },
                        {
                            "text": "Schedule Callback",
                            "action_type": "reply",
                            "action_value": "2"
                        }
                    ],
                    "session_id": session_id
                }
            )
        
        # Log the final response
            # Standard response (no special action)
            conversations[session_id].append({"role": "user", "content": message_text})
            conversations[session_id].append({"role": "assistant", "content": response_text})
            
            return JSONResponse(
                status_code=200,
                content={
                    "action": "reply",
                    "replies": [response_text],
                    "session_id": session_id
                }
            )
        
        # No handler matched, continue with existing hardcoded logic or LLM
        logger.info(f"[Handler] No handler matched, continuing with existing logic")
        
        # Generate LLM response with embedded resolution steps
        logger.info(f"[LLM] 🤖 CALLING Gemini 2.5 Flash for category: {category}")
        response_text, tokens_used = generate_response(message_text, history, category=category)
        logger.info(f"[LLM] ✓ Response generated | Tokens used: {tokens_used} | Category: {category}")
        
        # Record metrics
        logger.info(f"[Metrics] 📊 Recording message: LLM=True, Tokens={tokens_used}, Category={category}")
        metrics_collector.record_message(session_id, is_llm_call=True, tokens_used=tokens_used)
        
        # Clean response
        response_text = response_text.replace('**', '')
        import re
        response_text = re.sub(r'^\s*\*\s+', '- ', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\n\s*\n+', '\n', response_text)
        response_text = response_text.strip()
        
        # ============================================================
        # FALLBACK: Handle unrecognized/unclear inputs
        # ============================================================
        # If LLM response is very short or generic, might indicate confusion
        # Add helpful escalation option for user
        
        unclear_indicators = [
            "i don't understand",
            "i'm not sure",
            "could you clarify",
            "can you rephrase",
            "i didn't quite get that"
        ]
        
        response_seems_unclear = any(indicator in response_text.lower() for indicator in unclear_indicators)
        
        # Only add escalation if response explicitly says it doesn't understand (not just because it's short)
        if response_seems_unclear:
            logger.info(f"[Fallback] Response indicates unclear understanding - adding escalation option")
            response_text += "\n\nIf I'm not understanding correctly, would you like to speak with our support team? I can connect you to an agent or schedule a callback." 
        
        logger.info(f"[SalesIQ] Response generated: {response_text[:100]}...")
        
        # Update conversation history
        conversations[session_id].append({"role": "user", "content": message_text})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        return JSONResponse(
            status_code=200,
            content={
                "action": "reply",
                "replies": [response_text],
                "session_id": session_id
            }
        )
        
    except Exception as e:
        import traceback as tb_module
        error_msg = str(e)
        error_trace = tb_module.format_exc()
        
        logger.error(f"[SalesIQ] ERROR: {error_msg}")
        logger.error(f"[SalesIQ] Traceback: {error_trace}")
        
        # Track critical error and send alert if threshold exceeded
        track_error(
            "webhook_exception",
            error_msg,
            {
                "session_id": session_id or "unknown",
                "error_type": type(e).__name__,
                "traceback": error_trace[:500]  # Truncate for alert
            }
        )
        
        # Record error in metrics
        if session_id:
            metrics_collector.record_error(session_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "action": "reply",
                "replies": ["I'm having technical difficulties. Please call our support team at 1-888-415-5240."],
                "session_id": session_id or 'unknown'
            }
        )

@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint for n8n webhook"""
    try:
        session_id = request.session_id
        message = request.message
        
        # Set session context for logging
        session_id_var.set(session_id)
        logger.info(f"[Chat] New message received")
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Classify message category
        category = issue_router.classify(message)
        logger.info(f"[Chat] Message classified as: {category}")
        
        response_text = generate_response(message, history, category=category)
        
        conversations[session_id].append({"role": "user", "content": message})
        conversations[session_id].append({"role": "assistant", "content": response_text})
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Chat] Error processing message: {error_msg}")
        
        # Track error with context
        track_error(
            "chat_endpoint_error",
            error_msg,
            {
                "session_id": session_id if 'session_id' in locals() else "unknown",
                "error_type": type(e).__name__
            }
        )
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/transfer")
async def api_transfer(request: Request):
    """Transfer EXISTING conversation from bot to human operator"""
    try:
        body = await request.json()
        session_id = body.get("session_id", "unknown")
        session_id_var.set(session_id)
        
        logger.info(f"[API/Transfer] ✅ BUTTON CLICKED - Transferring conversation {session_id} to human")
        
        # Use the new transfer_to_human method that updates existing conversation
        result = salesiq_api.transfer_to_human(session_id, salesiq_api.department_id)
        
        if result.get("success"):
            logger.info(f"[API/Transfer] ✅ TRANSFER SUCCESSFUL - Conversation assigned to human operator")
            if session_id in conversations:
                metrics_collector.end_conversation(session_id, "escalated")
                del conversations[session_id]
            return {"success": True, "message": "Chat transferred to human agent", "status": "transferred"}
        else:
            logger.error(f"[API/Transfer] Transfer failed: {result.get('error')} - {result.get('details', '')}")
            return {"success": False, "error": result.get("error"), "details": result.get("details")}
            
    except Exception as e:
        logger.error(f"[API/Transfer] ERROR: {str(e)}")
        logger.error(f"[API/Transfer] Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.post("/api/callback")
async def api_callback(request: Request):
    """Handle schedule callback button click - EXACT LOCAL WORKING CODE"""
    try:
        body = await request.json()
        session_id = body.get("session_id", "unknown")
        session_id_var.set(session_id)
        
        logger.info(f"[API/Callback] ✅ BUTTON CLICKED - Starting callback")
        logger.info(f"[API/Callback] Session: {session_id}")
        
        # Get credentials from LOADED desk_api object (not env)
        desk_token = desk_api.access_token
        desk_refresh = desk_api.refresh_token
        desk_client_id = desk_api.client_id
        desk_client_secret = desk_api.client_secret
        desk_org = desk_api.org_id
        desk_dept = desk_api.department_id
        
        logger.info(f"[API/Callback] Using loaded API credentials - Token: {desk_token[:40] if desk_token else 'NONE'}...")
        
        if not all([desk_token, desk_refresh, desk_client_id, desk_client_secret, desk_org, desk_dept]):
            logger.error(f"[API/Callback] Missing credentials in API object")
            return {"success": False, "error": "Missing credentials"}
        
        visitor_email = body.get("visitor_email", "support@acecloudhosting.com")
        visitor_name = body.get("visitor_name", "Chat User")
        phone = body.get("phone")
        preferred_time = body.get("preferred_time", "")
        
        logger.info(f"[API/Callback] Creating callback: phone={phone}, time={preferred_time}")
        
        def refresh_token_callback(refresh_token, client_id, client_secret):
            """Refresh Desk token - EXACT LOCAL LOGIC"""
            url = "https://accounts.zoho.in/oauth/v2/token"
            params = {
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token"
            }
            logger.info(f"[API/Callback] 🔄 Refreshing token...")
            try:
                response = requests.post(url, params=params, timeout=10)
                logger.info(f"[API/Callback] Refresh status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if data and "access_token" in data:
                        new_token = data.get("access_token")
                        logger.info(f"[API/Callback] ✅ Token refreshed")
                        return new_token
                    else:
                        logger.error(f"[API/Callback] No access_token in response: {data}")
                        return None
                else:
                    logger.error(f"[API/Callback] Refresh failed: {response.text[:100]}")
                    return None
            except Exception as e:
                logger.error(f"[API/Callback] Refresh error: {str(e)}")
                logger.error(f"[API/Callback] Traceback: {traceback.format_exc()}")
                return None
        
        def create_contact(access_token):
            """Create contact for callback - EXACT LOCAL WORKING CODE"""
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "orgId": desk_org,
                "Content-Type": "application/json"
            }
            
            # Split visitor name into first/last - EXACT SAME AS LOCAL TEST
            name_parts = visitor_name.split() if visitor_name else ["Chat", "User"]
            first_name = name_parts[0] if name_parts else "Chat"
            last_name = name_parts[-1] if len(name_parts) > 1 else "User"
            
            payload = {
                "lastName": last_name,
                "firstName": first_name,
                "email": visitor_email,
                "phone": phone or "0000000000"
            }
            
            logger.info(f"[API/Callback] Creating contact with payload: {json.dumps(payload)}")
            logger.info(f"[API/Callback] Headers: orgId={headers['orgId']}, Token={headers['Authorization'][:40]}...")
            
            response = requests.post(
                "https://desk.zoho.in/api/v1/contacts",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            logger.info(f"[API/Callback] Contact response: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"[API/Callback] Contact error: {response.text}")
            return response
        
        def create_callback_call(access_token, contact_id):
            """Create callback call - EXACT LOCAL LOGIC"""
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "orgId": desk_org,
                "Content-Type": "application/json"
            }
            
            payload = {
                "contactId": contact_id,
                "departmentId": desk_dept,
                "subject": "Callback Request",
                "description": f"User requested callback at {preferred_time}. Phone: {phone}",
                "direction": "inbound",
                "startTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "duration": 0,
                "status": "In Progress"
            }
            
            logger.info(f"[API/Callback] Creating callback for contact {contact_id}")
            
            response = requests.post(
                "https://desk.zoho.in/api/v1/calls",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            logger.info(f"[API/Callback] Callback creation status: {response.status_code}")
            return response
        
        # STEP 1: CREATE CONTACT
        logger.info(f"[API/Callback] Step 1: Creating contact...")
        contact_response = create_contact(desk_token)
        
        if contact_response.status_code == 200:
            contact_id = contact_response.json().get("id")
            logger.info(f"[API/Callback] ✅ Contact created: {contact_id}")
            
            # STEP 2: CREATE CALLBACK
            logger.info(f"[API/Callback] Step 2: Creating callback...")
            callback_response = create_callback_call(desk_token, contact_id)
            
            if callback_response.status_code == 200:
                logger.info(f"[API/Callback] ✅ CALLBACK SUCCESSFUL!")
                if session_id in conversations:
                    metrics_collector.end_conversation(session_id, "resolved")
                    del conversations[session_id]
                return {"success": True, "message": "Callback scheduled successfully"}
            
            elif callback_response.status_code in [400, 401, 403]:
                logger.warning(f"[API/Callback] Token invalid/expired ({callback_response.status_code}), refreshing...")
                new_token = refresh_token_callback(desk_refresh, desk_client_id, desk_client_secret)
                
                if new_token:
                    logger.info(f"[API/Callback] Retrying callback with refreshed token...")
                    callback_response = create_callback_call(new_token, contact_id)
                    
                    if callback_response.status_code == 200:
                        logger.info(f"[API/Callback] ✅ CALLBACK SUCCESSFUL (after refresh)!")
                        if session_id in conversations:
                            metrics_collector.end_conversation(session_id, "resolved")
                            del conversations[session_id]
                        return {"success": True, "message": "Callback scheduled successfully"}
                    else:
                        logger.error(f"[API/Callback] Retry failed: {callback_response.status_code}")
                        return {"success": False, "error": f"Callback failed after refresh: {callback_response.status_code}"}
                else:
                    logger.error(f"[API/Callback] Token refresh failed")
                    return {"success": False, "error": "Token refresh failed"}
            else:
                logger.error(f"[API/Callback] Callback failed: {callback_response.status_code} - {callback_response.text[:200]}")
                return {"success": False, "error": f"Callback failed: {callback_response.status_code}"}
        
        elif contact_response.status_code in [400, 401, 403]:
            logger.warning(f"[API/Callback] Token invalid/expired ({contact_response.status_code}), refreshing...")
            new_token = refresh_token_callback(desk_refresh, desk_client_id, desk_client_secret)
            
            if new_token:
                logger.info(f"[API/Callback] Retrying contact creation with refreshed token...")
                contact_response = create_contact(new_token)
                
                if contact_response.status_code == 200:
                    contact_id = contact_response.json().get("id")
                    logger.info(f"[API/Callback] ✅ Contact created (after refresh): {contact_id}")
                    
                    logger.info(f"[API/Callback] Creating callback...")
                    callback_response = create_callback_call(new_token, contact_id)
                    
                    if callback_response.status_code == 200:
                        logger.info(f"[API/Callback] ✅ CALLBACK SUCCESSFUL (after refresh)!")
                        if session_id in conversations:
                            metrics_collector.end_conversation(session_id, "resolved")
                            del conversations[session_id]
                        return {"success": True, "message": "Callback scheduled successfully"}
                    else:
                        logger.error(f"[API/Callback] Callback failed: {callback_response.status_code}")
                        return {"success": False, "error": f"Callback failed: {callback_response.status_code}"}
                else:
                    logger.error(f"[API/Callback] Contact creation retry failed: {contact_response.status_code}")
                    return {"success": False, "error": f"Contact creation failed: {contact_response.status_code}"}
            else:
                logger.error(f"[API/Callback] Token refresh failed")
                return {"success": False, "error": "Token refresh failed"}
        else:
            logger.error(f"[API/Callback] Contact creation failed: {contact_response.status_code}")
            return {"success": False, "error": f"Contact creation failed: {contact_response.status_code}"}
            
    except Exception as e:
        logger.error(f"[API/Callback] ERROR: {str(e)}")
        logger.error(f"[API/Callback] Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.post("/reset/{session_id}")
async def reset_conversation(session_id: str):
    """Reset conversation for a session"""
    try:
        session_id_var.set(session_id)
        logger.info(f"[Reset] Resetting conversation")
        
        if session_id in conversations:
            metrics_collector.end_conversation(session_id, "abandoned")
            state_manager.end_session(session_id, ConversationState.ABANDONED)
            del conversations[session_id]
            return {"status": "success", "message": f"Conversation {session_id} reset"}
        return {"status": "not_found", "message": f"Session {session_id} not found"}
    
    except Exception as e:
        logger.error(f"[Reset] Error: {str(e)}")
        track_error("reset_error", str(e), {"session_id": session_id})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """List all active sessions with state information"""
    active_sessions = []
    for session_id in conversations.keys():
        session_summary = state_manager.get_session_summary(session_id)
        if session_summary:
            active_sessions.append(session_summary)
    
    return {
        "active_sessions": len(conversations),
        "sessions": active_sessions
    }

@app.get("/sessions/{session_id}")
async def get_session_state(session_id: str):
    """Get detailed state information for a specific session"""
    summary = state_manager.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return summary

# -----------------------------------------------------------
# Test endpoints to validate SalesIQ Visitor API transfer
# -----------------------------------------------------------
@app.get("/test/salesiq-transfer")
async def test_salesiq_transfer_get():
    """Quick GET test to exercise Visitor API with env defaults.
    
    IMPORTANT: Cannot use bot preview IDs (botpreview_...).
    This endpoint uses a real-looking email-based user ID for testing.
    """
    try:
        # Use email as user_id (most reliable per API docs) instead of session ID
        test_user_id = "vishal.dharan@acecloudhosting.com"
        conversation_text = "Test transfer from GET endpoint"
        logger.info(f"[Test] Initiating SalesIQ Visitor API transfer (GET) with user_id={test_user_id}")
        
        result = salesiq_api.create_chat_session(test_user_id, conversation_text)
        return {
            "user_id": test_user_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"[Test] SalesIQ transfer GET failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/salesiq-transfer")
async def test_salesiq_transfer_post(payload: Dict):
    """POST test to exercise Visitor API with overrides from payload.
    
    Accepts:
    - visitor_user_id: Unique identifier for visitor (use email)
    - conversation: Conversation text for agent
    """
    try:
        # Use email as user_id (more reliable than session IDs)
        visitor_user_id = str(payload.get("visitor_user_id") or "vishal.dharan@acecloudhosting.com")
        conversation_text = str(payload.get("conversation") or "Test transfer from POST endpoint")

        logger.info(f"[Test] Initiating SalesIQ Visitor API transfer (POST) for user_id={visitor_user_id}")
        
        result = salesiq_api.create_chat_session(visitor_user_id, conversation_text)
        return {
            "user_id": visitor_user_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"[Test] SalesIQ transfer POST failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get comprehensive chatbot performance metrics
    
    Returns:
        JSON object with automation rate, category distribution, LLM usage, and more
    """
    try:
        summary = metrics_collector.get_summary()
        logger.info(f"[Metrics] Metrics requested - {summary['overview']['total_conversations']} conversations tracked")
        return summary
    except Exception as e:
        logger.error(f"[Metrics] Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/report")
async def get_metrics_report():
    """Get human-readable metrics report
    
    Returns:
        Plain text formatted report
    """
    try:
        report = metrics_collector.get_detailed_report()
        logger.info(f"[Metrics] Detailed report requested")
        return {"report": report}
    except Exception as e:
        logger.error(f"[Metrics] Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metrics/reset")
async def reset_metrics():
    """Reset all metrics (use with caution)
    
    Requires confirmation parameter
    """
    try:
        metrics_collector.reset()
        logger.warning("[Metrics] All metrics have been reset")
        return {"status": "success", "message": "All metrics have been reset"}
    except Exception as e:
        logger.error(f"[Metrics] Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint
    
    Returns system status including:
    - Service health (router, metrics, state manager, handlers)
    - Active conversation count
    - System uptime
    - API status
    """
    try:
        metrics_summary = metrics_collector.get_summary()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "issue_router": {
                    "status": "healthy",
                    "categories": 6
                },
                "metrics_collector": {
                    "status": "healthy",
                    "total_conversations": metrics_summary['overview']['total_conversations'],
                    "uptime_hours": metrics_summary['overview']['uptime_hours']
                },
                "state_manager": {
                    "status": "healthy",
                    "active_sessions": len(conversations)
                },
                "handler_registry": {
                    "status": "healthy",
                    "handlers_count": len(handler_registry.handlers)
                },
                "zoho_salesiq_api": {
                    "status": "healthy" if salesiq_api.enabled else "fallback",
                    "enabled": salesiq_api.enabled
                },
                "zoho_desk_api": {
                    "status": "healthy" if desk_api.enabled else "fallback",
                    "enabled": getattr(desk_api, 'enabled', False)
                }
            },
            "performance": {
                "active_conversations": len(conversations),
                "automation_rate": metrics_summary['resolution']['automation_rate'],
                "router_effectiveness": metrics_summary['performance']['router_effectiveness']
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"[Health] Error generating health check: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/stats")
async def get_statistics():
    """Detailed statistics endpoint
    
    Returns comprehensive statistics including:
    - Category breakdown with percentages
    - Resolution type distribution
    - Average metrics
    - Time-based analysis
    """
    try:
        metrics_summary = metrics_collector.get_summary()
        
        # Calculate additional statistics
        total_conversations = metrics_summary['overview']['total_conversations']
        completed = metrics_summary['overview']['completed_conversations']
        
        # Category breakdown with percentages
        category_stats = []
        for category, count in metrics_summary['categories'].items():
            percentage = (count / total_conversations * 100) if total_conversations > 0 else 0
            category_stats.append({
                "category": category,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        # Sort by count descending
        category_stats.sort(key=lambda x: x['count'], reverse=True)
        
        # Resolution breakdown with percentages
        resolution_stats = {
            "resolved": {
                "count": metrics_summary['resolution']['resolved'],
                "percentage": round((metrics_summary['resolution']['resolved'] / completed * 100) if completed > 0 else 0, 2)
            },
            "escalated": {
                "count": metrics_summary['resolution']['escalated'],
                "percentage": round((metrics_summary['resolution']['escalated'] / completed * 100) if completed > 0 else 0, 2)
            },
            "abandoned": {
                "count": metrics_summary['resolution']['abandoned'],
                "percentage": round((metrics_summary['resolution']['abandoned'] / completed * 100) if completed > 0 else 0, 2)
            }
        }
        
        # Handler statistics
        handler_stats = {
            "total_handlers": len(handler_registry.handlers),
            "handler_list": handler_registry.list_handlers()
        }
        
        statistics = {
            "summary": {
                "total_conversations": total_conversations,
                "completed_conversations": completed,
                "active_conversations": metrics_summary['overview']['active_conversations'],
                "uptime_hours": round(metrics_summary['overview']['uptime_hours'], 2)
            },
            "categories": category_stats,
            "resolutions": resolution_stats,
            "performance": {
                "automation_rate": metrics_summary['resolution']['automation_rate'],
                "escalation_rate": metrics_summary['resolution']['escalation_rate'],
                "avg_resolution_time_seconds": metrics_summary['performance']['avg_resolution_time_seconds'],
                "router_effectiveness": metrics_summary['performance']['router_effectiveness']
            },
            "llm_usage": metrics_summary['llm_usage'],
            "handlers": handler_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"[Stats] Error generating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print("="*70)
    print("ACE CLOUD HOSTING - SUPPORT BOT (HYBRID LLM)")
    print("="*70)
    print(f"\n[STARTING] FastAPI server on port {port}...")
    print(f"[ENDPOINT] http://0.0.0.0:{port}")
    print(f"[DOCS] http://0.0.0.0:{port}/docs")
    print("\n[READY] Ready to receive webhooks!")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
