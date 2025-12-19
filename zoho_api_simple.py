"""
Simple Zoho API Integration - Working Version
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ZohoSalesIQAPI:
    """Simple SalesIQ API Integration (Visitor API)"""
    
    def __init__(self):
        # Load configuration
        self.access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
        
        # Base URL for Operator API v2 (accepts OAuth tokens)
        self.base_url = f"https://salesiq.zoho.in/api/v2/{self.screen_name}"
        self.org_id = os.getenv("SALESIQ_ORG_ID", "60000687661").strip()
        # Default tag id for conversations (required by Operator API)
        self.default_tag_id = os.getenv("SALESIQ_DEFAULT_TAG_ID", "2782000005718505").strip()
        
        # Enable only if required config exists
        self.enabled = bool(self.access_token and self.department_id and self.app_id)
        if self.enabled:
            logger.info(f"SalesIQ Operator API v2 configured - department: {self.department_id}, app_id: {self.app_id}, screen: {self.screen_name}, org: {self.org_id}, default_tag_id: {self.default_tag_id}")
        else:
            logger.warning(f"SalesIQ Operator API not fully configured - token: {bool(self.access_token)}, dept: {bool(self.department_id)}, app_id: {bool(self.app_id)}, screen: {bool(self.screen_name)}")
    
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
        """
        
        if not self.enabled:
            logger.info(f"SalesIQ: API disabled - simulating transfer for {visitor_id}")
            return {"success": True, "simulated": True, "message": "Transfer simulated"}
        
        import requests
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
            "orgId": self.org_id
        }
        
        # Effective configuration (prefer overrides from webhook)
        effective_department_id = str(department_id or self.department_id).strip()

        # Extract visitor details from visitor_info or use defaults
        visitor_name = "Chat User"
        visitor_email = "support@acecloudhosting.com"
        effective_visitor_id = visitor_id
        
        if visitor_info:
            effective_visitor_id = str(visitor_info.get("id") or visitor_id)
            visitor_name = visitor_info.get("name") or visitor_info.get("email", "Chat User")
            visitor_email = visitor_info.get("email", "support@acecloudhosting.com")

        # Operator API v2 payload structure
        payload: Dict = {
            "visitor_id": effective_visitor_id,
            "name": visitor_name,
            "email": visitor_email,
            "department_id": effective_department_id,
            "question": conversation_history or "User requested human assistance",
            "ids": [int(self.default_tag_id)]
        }
        
        endpoint = f"{self.base_url}/conversations"
        logger.info(f"SalesIQ: Operator API v2 call - POST {endpoint}")
        logger.info(
            f"SalesIQ: Payload: visitor_id={effective_visitor_id}, dept={effective_department_id}, name={visitor_name}, ids=[{self.default_tag_id}]"
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
            logger.error(f"SalesIQ: Operator API exception: {str(e)}")
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