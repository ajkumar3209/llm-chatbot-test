"""
Simple Zoho API Integration - Working Version
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Import token manager for automatic refresh
from token_manager import get_token_manager


class ZohoSalesIQAPI:
    """Simple SalesIQ API Integration (Visitor API)"""
    
    def __init__(self):
        # Get token manager for automatic refresh
        self.token_manager = get_token_manager()
        
        # Load configuration
        self.access_token = self.token_manager.access_token
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
        
        # Base URL for Visitor API v1 (official endpoint per API docs)
        self.base_url = f"https://salesiq.zoho.in/api/visitor/v1/{self.screen_name}"
        
        # Enable only if required config exists
        self.enabled = bool(self.access_token and self.department_id and self.app_id)
        if self.enabled:
            logger.info(f"SalesIQ Visitor API v1 configured - department: {self.department_id}, app_id: {self.app_id}, screen: {self.screen_name}")
        else:
            logger.warning(f"SalesIQ Visitor API not fully configured - token: {bool(self.access_token)}, dept: {bool(self.department_id)}, app_id: {bool(self.app_id)}, screen: {bool(self.screen_name)}")
    
    def create_chat_session(
        self,
        visitor_id: str,
        conversation_history: str,
        app_id: str | None = None,
        department_id: str | None = None,
        visitor_info: Dict | None = None,
        custom_wait_time: int | None = None,
    ) -> Dict:
        """Create a conversation via Visitor API to route to an agent.
        Allows overriding app_id/department_id/visitor_info from inbound webhook payload.
        
        IMPORTANT: Cannot use bot preview visitor IDs (botpreview_...).
        Must use real visitor IDs from actual chat widget interactions.
        """
        
        if not self.enabled:
            logger.info(f"SalesIQ: API disabled - simulating transfer for {visitor_id}")
            return {"success": True, "simulated": True, "message": "Transfer simulated"}
        
        # Reject bot preview IDs - they cannot be transferred
        if str(visitor_id).startswith("botpreview_"):
            logger.warning(f"SalesIQ: Cannot transfer bot preview session {visitor_id}. Need real visitor ID from actual chat widget.")
            return {
                "success": False,
                "error": "invalid_visitor_id",
                "details": "Bot preview sessions cannot be transferred. This is a SalesIQ limitation. Test with real visitor ID only."
            }
        
        import requests
        
        # Get fresh token (auto-refreshes if expired)
        valid_token = self.token_manager.get_valid_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {valid_token}",
            "Content-Type": "application/json"
        }
        
        # Effective configuration (prefer overrides from webhook)
        effective_app_id = str(app_id or self.app_id).strip()
        effective_department_id = str(department_id or self.department_id).strip()

        # Extract visitor details from visitor_info or use defaults
        visitor_user_id = str(visitor_id).strip()
        visitor_name = "Chat User"
        visitor_email = "support@acecloudhosting.com"
        
        if visitor_info:
            # Prefer "email" as user_id if available (most reliable unique ID)
            visitor_user_id = visitor_info.get("email") or visitor_info.get("user_id") or visitor_user_id
            visitor_name = visitor_info.get("name") or visitor_info.get("email", "Chat User")
            visitor_email = visitor_info.get("email", "support@acecloudhosting.com")

        # Visitor API v1 payload structure per official documentation
        payload: Dict = {
            "app_id": effective_app_id,
            "department_id": effective_department_id,
            "question": conversation_history or "User requested human assistance",
            "visitor": {
                "user_id": visitor_user_id,
                "name": visitor_name,
                "email": visitor_email
            }
        }
        
        # Add optional custom_wait_time if provided
        if custom_wait_time is not None:
            payload["custom_wait_time"] = custom_wait_time
        
        endpoint = f"{self.base_url}/conversations"
        logger.info(f"SalesIQ: Visitor API v1 call - POST {endpoint}")
        logger.info(
            f"SalesIQ: Payload - app_id={effective_app_id}, dept={effective_department_id}, visitor_user_id={visitor_user_id}, visitor_email={visitor_email}"
        )
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            logger.info(f"SalesIQ: Response Status: {response.status_code}")
            logger.info(f"SalesIQ: Response Body: {response.text[:500]}")
            
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                except Exception:
                    data = {"raw": response.text}
                return {"success": True, "endpoint": endpoint, "data": data}
            else:
                return {"success": False, "error": f"{response.status_code}", "details": response.text}
        except Exception as e:
            logger.error(f"SalesIQ: Visitor API exception: {str(e)}")
            return {"success": False, "error": "exception", "details": str(e)}
    
    def close_chat(self, session_id: str, reason: str = "resolved") -> Dict:
        """Log chat closure"""
        
        logger.info(f"SalesIQ: Chat closure requested for {session_id}, reason: {reason}")
        
        return {
            "success": True,
            "message": f"Chat {session_id} closure logged"
        }


class ZohoDeskAPI:
    """Simple Desk API Integration"""
    
    def __init__(self):
        self.enabled = False  # Keep disabled for now
        logger.info("Desk API disabled - ticket creation simulated")
    
    def create_callback_ticket(self, *args, **kwargs):
        logger.info("Desk: Callback ticket creation simulated")
        return {"success": True, "simulated": True, "ticket_number": "CB-SIM-001"}
    
    def create_support_ticket(self, *args, **kwargs):
        logger.info("Desk: Support ticket creation simulated")
        return {"success": True, "simulated": True, "ticket_number": "TK-SIM-001"}