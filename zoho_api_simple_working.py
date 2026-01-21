"""
Simple Zoho API Integration - Working Version
"""

import os
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)


class ZohoSalesIQAPI:
    """Simple SalesIQ API Integration (Visitor API)"""
    
    def __init__(self):
        self.access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
        
        # Base URL for Visitor API v1
        self.base_url = f"https://salesiq.zoho.in/api/visitor/v1/{self.screen_name}"
        
        # Enable only if required config exists
        self.enabled = bool(self.access_token and self.department_id and self.app_id)
        if self.enabled:
            logger.info(f"SalesIQ Visitor API v1 configured - department: {self.department_id}, app_id: {self.app_id}, screen: {self.screen_name}")
        else:
            logger.warning(f"SalesIQ Visitor API not fully configured - token: {bool(self.access_token)}, dept: {bool(self.department_id)}, app_id: {bool(self.app_id)}, screen: {bool(self.screen_name)}")

    def create_chat_session(self, visitor_id: str, conversation_history: str) -> Dict:
        """Create a conversation via Visitor API to route to an agent."""
        
        if not self.enabled:
            logger.info(f"SalesIQ: API disabled - simulating transfer for {visitor_id}")
            return {"success": True, "simulated": True, "message": "Transfer simulated"}
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Visitor API v1 payload structure per official documentation
        payload = {
            "app_id": self.app_id,
            "department_id": self.department_id,
            "question": conversation_history or "User requested human assistance",
            "visitor": {
                "user_id": visitor_id,
                "name": "Chat User",
                "email": "support@acecloudhosting.com"
            }
        }
        
        endpoint = f"{self.base_url}/conversations"
        logger.info(f"SalesIQ: Visitor API v1 call - POST {endpoint}")
        
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
            logger.error(f"SalesIQ: Exception: {str(e)}")
            return {"success": False, "error": "exception", "details": str(e)}
    
    def close_chat(self, session_id: str, reason: str = "resolved") -> Dict:
        """Close a SalesIQ conversation via API"""
        if not self.enabled:
            logger.info(f"SalesIQ: API disabled - simulating closure for {session_id}")
            return {"success": True, "simulated": True}
        
        logger.info(f"SalesIQ: Close chat called for {session_id}, reason: {reason}")
        return {"success": True, "simulated": True}


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
