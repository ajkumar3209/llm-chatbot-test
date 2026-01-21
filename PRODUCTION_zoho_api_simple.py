"""
PRODUCTION-READY zoho_api_simple.py
This is the EXACT code that needs to be on the server
Copy this entire file to /opt/llm-chatbot/zoho_api_simple.py
"""

import os
import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

API_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 1


def refresh_zoho_token(refresh_token: str, client_id: str, client_secret: str) -> Optional[str]:
    """Refresh Zoho OAuth token"""
    if not all([refresh_token, client_id, client_secret]):
        logger.error(f"Cannot refresh - missing creds")
        return None
    
    try:
        response = requests.post(
            "https://accounts.zoho.in/oauth/v2/token",
            params={
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token"
            },
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            new_token = response.json().get("access_token")
            logger.info(f"✅ Token refreshed successfully")
            return new_token
        else:
            logger.error(f"Token refresh failed HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Token refresh exception: {str(e)}")
        return None


class ZohoSalesIQAPI:
    """SalesIQ API for transfer and closure"""
    
    def __init__(self):
        # Closure tokens
        self.closure_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.closure_refresh = os.getenv("SALESIQ_REFRESH_TOKEN", "").strip()
        self.closure_client_id = os.getenv("SALESIQ_CLIENT_ID", "").strip()
        self.closure_client_secret = os.getenv("SALESIQ_CLIENT_SECRET", "").strip()
        
        # Transfer tokens (org token)
        self.visitor_token = os.getenv("SALESIQ_VISITOR_ACCESS_TOKEN", "").strip()
        self.visitor_refresh = os.getenv("SALESIQ_VISITOR_REFRESH_TOKEN", "").strip()
        self.visitor_client_id = os.getenv("SALESIQ_VISITOR_CLIENT_ID", "").strip()
        self.visitor_client_secret = os.getenv("SALESIQ_VISITOR_CLIENT_SECRET", "").strip()
        
        # Static IDs
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
        
        self.enabled = bool(self.visitor_token and self.app_id)
        
        if self.enabled:
            logger.info(f"[SalesIQ] ✓ ENABLED - dept: {self.department_id}, app: {self.app_id}")
        else:
            logger.warning(f"[SalesIQ] ✗ DISABLED")
    
    def create_chat_session(self, visitor_id: str, conversation_history: str = "", 
                           app_id: str = None, department_id: str = None,
                           visitor_info: Dict = None, past_messages: list = None) -> Dict:
        """Transfer chat to agent"""
        
        if not self.enabled:
            logger.info(f"[SalesIQ] Simulating transfer (disabled)")
            return {"success": True, "simulated": True}
        
        # Reject bot preview
        if str(visitor_id).startswith("botpreview_"):
            logger.warning(f"[SalesIQ] Cannot transfer bot preview session")
            return {"success": False, "error": "invalid_visitor_id"}
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.visitor_token}",
            "Content-Type": "application/json"
        }
        
        effective_app_id = app_id or self.app_id
        effective_department_id = department_id or self.department_id
        
        visitor_user_id = visitor_id
        visitor_name = "Chat User"
        visitor_email = "support@acecloudhosting.com"
        
        if visitor_info:
            visitor_user_id = visitor_info.get("email") or visitor_info.get("user_id") or visitor_user_id
            visitor_name = visitor_info.get("name") or visitor_info.get("email", "Chat User")
            visitor_email = visitor_info.get("email", "support@acecloudhosting.com")
        
        payload = {
            "app_id": effective_app_id,
            "department_id": effective_department_id,
            "question": conversation_history or "User requested human assistance",
            "visitor": {
                "user_id": visitor_user_id,
                "name": visitor_name,
                "email": visitor_email
            }
        }
        
        if past_messages:
            payload["past_messages"] = past_messages
        
        endpoint = f"https://salesiq.zoho.in/api/visitor/v1/{self.screen_name}/conversations"
        logger.info(f"[SalesIQ] Transfer: POST {endpoint}")
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=API_TIMEOUT)
            logger.info(f"[SalesIQ] Transfer response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"[SalesIQ] ✓ Transfer successful")
                return {"success": True, "data": response.json()}
            
            elif response.status_code in [401, 403]:
                logger.warning(f"[SalesIQ] Token expired, refreshing visitor token...")
                
                new_token = refresh_zoho_token(self.visitor_refresh, self.visitor_client_id, 
                                              self.visitor_client_secret)
                if new_token:
                    self.visitor_token = new_token
                    headers["Authorization"] = f"Zoho-oauthtoken {new_token}"
                    
                    retry = requests.post(endpoint, headers=headers, json=payload, timeout=API_TIMEOUT)
                    if retry.status_code == 200:
                        logger.info(f"[SalesIQ] ✓ Transfer successful (after refresh)")
                        return {"success": True, "data": retry.json()}
                    else:
                        logger.error(f"[SalesIQ] Transfer failed after refresh: {retry.status_code}")
                        return {"success": False, "error": f"HTTP {retry.status_code}"}
            
            else:
                logger.error(f"[SalesIQ] Transfer failed: {response.text[:200]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.error(f"[SalesIQ] Transfer exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def close_chat(self, session_id: str, reason: str = "resolved") -> Dict:
        """Close a conversation"""
        
        if not self.enabled:
            logger.info(f"[SalesIQ] Simulating closure (disabled)")
            return {"success": True, "simulated": True}
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.closure_token}",
            "Content-Type": "application/json"
        }
        
        endpoint = f"https://salesiq.zoho.in/api/v2/{self.screen_name}/conversations/{session_id}/close"
        logger.info(f"[SalesIQ] Closure: PUT {endpoint}, reason={reason}")
        
        try:
            response = requests.put(endpoint, headers=headers, timeout=API_TIMEOUT)
            logger.info(f"[SalesIQ] Closure response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"[SalesIQ] ✓ Chat closed")
                return {"success": True}
            
            elif response.status_code in [401, 403]:
                logger.warning(f"[SalesIQ] Token expired, refreshing closure token...")
                
                new_token = refresh_zoho_token(self.closure_refresh, self.closure_client_id,
                                              self.closure_client_secret)
                if new_token:
                    self.closure_token = new_token
                    headers["Authorization"] = f"Zoho-oauthtoken {new_token}"
                    
                    retry = requests.put(endpoint, headers=headers, timeout=API_TIMEOUT)
                    if retry.status_code == 200:
                        logger.info(f"[SalesIQ] ✓ Chat closed (after refresh)")
                        return {"success": True}
                    else:
                        logger.error(f"[SalesIQ] Closure failed after refresh: {retry.status_code}")
                        return {"success": False}
            
            else:
                logger.error(f"[SalesIQ] Closure failed: {response.text[:200]}")
                return {"success": False}
        
        except Exception as e:
            logger.error(f"[SalesIQ] Closure exception: {str(e)}")
            return {"success": False}


class ZohoDeskAPI:
    """Desk API for callbacks"""
    
    def __init__(self):
        self.access_token = os.getenv("DESK_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("DESK_REFRESH_TOKEN", "").strip()
        self.client_id = os.getenv("DESK_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("DESK_CLIENT_SECRET", "").strip()
        
        self.org_id = os.getenv("DESK_ORG_ID", "").strip()
        self.department_id = os.getenv("DESK_DEPARTMENT_ID", "").strip()
        
        self.enabled = bool(self.access_token and self.org_id)
        
        if self.enabled:
            logger.info(f"[Desk] ✓ ENABLED - org: {self.org_id}, dept: {self.department_id}")
        else:
            logger.warning(f"[Desk] ✗ DISABLED")
    
    def _headers(self) -> Dict:
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Content-Type": "application/json"
        }
    
    def create_callback_ticket(self, visitor_name: str, visitor_email: str, 
                              visitor_phone: str = "", subject: str = "", 
                              description: str = "") -> Dict:
        """Create callback - with contact creation"""
        
        if not self.enabled:
            logger.info(f"[Desk] Simulating callback (disabled)")
            return {"success": True, "simulated": True}
        
        logger.info(f"[Desk] Callback: Creating contact {visitor_email}")
        
        # Create/find contact
        headers = self._headers()
        contact_payload = {
            "lastName": visitor_name.split()[-1] if visitor_name else "User",
            "firstName": visitor_name.split()[0] if visitor_name else "Chat",
            "email": visitor_email,
            "phone": visitor_phone
        }
        
        try:
            contact_response = requests.post(
                "https://desk.zoho.in/api/v1/contacts",
                headers=headers,
                json=contact_payload,
                timeout=API_TIMEOUT
            )
            
            logger.info(f"[Desk] Contact response: {contact_response.status_code}")
            
            if contact_response.status_code == 200:
                contact_id = contact_response.json().get("id")
                logger.info(f"[Desk] ✓ Contact created: {contact_id}")
            
            elif contact_response.status_code in [401, 403]:
                logger.warning(f"[Desk] Token expired, refreshing...")
                new_token = refresh_zoho_token(self.refresh_token, self.client_id, self.client_secret)
                if new_token:
                    self.access_token = new_token
                    headers = self._headers()
                    
                    contact_response = requests.post(
                        "https://desk.zoho.in/api/v1/contacts",
                        headers=headers,
                        json=contact_payload,
                        timeout=API_TIMEOUT
                    )
                    
                    if contact_response.status_code == 200:
                        contact_id = contact_response.json().get("id")
                        logger.info(f"[Desk] ✓ Contact created (after refresh): {contact_id}")
                    else:
                        logger.error(f"[Desk] Contact creation failed after refresh")
                        return {"success": False, "error": "contact_creation_failed"}
                else:
                    return {"success": False, "error": "token_refresh_failed"}
            else:
                logger.error(f"[Desk] Contact creation failed: {contact_response.text[:200]}")
                return {"success": False, "error": "contact_creation_failed"}
            
            # Create callback
            logger.info(f"[Desk] Callback: Creating call for contact {contact_id}")
            
            call_payload = {
                "contactId": contact_id,
                "departmentId": self.department_id,
                "subject": subject or "Callback Request",
                "description": description or "Callback requested",
                "direction": "inbound",
                "startTime": "2026-01-16T00:00:00.000Z",
                "duration": 0,
                "status": "In Progress"
            }
            
            call_response = requests.post(
                "https://desk.zoho.in/api/v1/calls",
                headers=headers,
                json=call_payload,
                timeout=API_TIMEOUT
            )
            
            logger.info(f"[Desk] Callback response: {call_response.status_code}")
            
            if call_response.status_code == 200:
                call_id = call_response.json().get("id")
                logger.info(f"[Desk] ✓ Callback created: {call_id}")
                return {"success": True, "call_id": call_id}
            
            elif call_response.status_code in [401, 403]:
                logger.warning(f"[Desk] Token expired during callback, refreshing...")
                new_token = refresh_zoho_token(self.refresh_token, self.client_id, self.client_secret)
                if new_token:
                    self.access_token = new_token
                    headers = self._headers()
                    
                    call_response = requests.post(
                        "https://desk.zoho.in/api/v1/calls",
                        headers=headers,
                        json=call_payload,
                        timeout=API_TIMEOUT
                    )
                    
                    if call_response.status_code == 200:
                        call_id = call_response.json().get("id")
                        logger.info(f"[Desk] ✓ Callback created (after refresh): {call_id}")
                        return {"success": True, "call_id": call_id}
            
            logger.error(f"[Desk] Callback creation failed: {call_response.text[:200]}")
            return {"success": False, "error": f"HTTP {call_response.status_code}"}
        
        except Exception as e:
            logger.error(f"[Desk] Callback exception: {str(e)}")
            return {"success": False, "error": str(e)}
