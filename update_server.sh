#!/bin/bash

# Update zoho_api_simple.py on server with proper multi-token handling
cat > /opt/llm-chatbot/zoho_api_simple_new.py << 'PYTHON_EOF'
"""
Zoho API Integration - Multi-Token Support
Handles 3 separate tokens:
1. SalesIQ Closure (Standard Token - 1000.xxx)
2. SalesIQ Transfer (Org Token - 1005.xxx) 
3. Desk Callback (Standard Token - 1000.xxx)
"""

import os
import logging
import time
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

API_TIMEOUT = 10
MAX_RETRIES = 4
RETRY_DELAY = 1


def refresh_zoho_token(refresh_token: str, client_id: str, client_secret: str, base_accounts_url: str = "https://accounts.zoho.in") -> Optional[str]:
    """Exchanges refresh token for new access token"""
    if not refresh_token or not client_id or not client_secret:
        logger.warning(f"Cannot refresh token - missing credentials")
        return None
    
    url = f"{base_accounts_url}/oauth/v2/token"
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    
    try:
        logger.info(f"[Token Refresh] Attempting refresh...")
        response = requests.post(url, params=params, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            if new_token:
                logger.info(f"[Token Refresh] ✓ SUCCESS - New token: {new_token[:20]}...{new_token[-10:]}")
                return new_token
            else:
                logger.error(f"[Token Refresh] Response missing access_token: {data}")
        else:
            logger.error(f"[Token Refresh] Failed HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        logger.error(f"[Token Refresh] Exception: {str(e)}")
    
    return None


class ZohoSalesIQAPI:
    """SalesIQ API - Handles both Closure and Transfer"""
    
    def __init__(self):
        # CLOSURE TOKEN (Standard - 1000.xxx)
        self.closure_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.closure_refresh = os.getenv("SALESIQ_REFRESH_TOKEN", "").strip()
        self.closure_client_id = os.getenv("SALESIQ_CLIENT_ID", "").strip()
        self.closure_client_secret = os.getenv("SALESIQ_CLIENT_SECRET", "").strip()
        
        # TRANSFER TOKEN (Org - 1005.xxx)
        self.visitor_token = os.getenv("SALESIQ_VISITOR_ACCESS_TOKEN", "").strip()
        self.visitor_refresh = os.getenv("SALESIQ_VISITOR_REFRESH_TOKEN", "").strip()
        self.visitor_client_id = os.getenv("SALESIQ_VISITOR_CLIENT_ID", "").strip()
        self.visitor_client_secret = os.getenv("SALESIQ_VISITOR_CLIENT_SECRET", "").strip()
        
        # Static IDs
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
        
        self.base_url = f"https://salesiq.zoho.in/api/visitor/v1/{self.screen_name}"
        self.enabled = bool(self.visitor_token and self.department_id and self.app_id)
        
        if self.enabled:
            logger.info(f"[SalesIQ] ✓ ENABLED - dept: {self.department_id}, app: {self.app_id}")
        else:
            logger.warning(f"[SalesIQ] ✗ DISABLED - Missing config")
    
    def _refresh_visitor_token(self) -> bool:
        """Refresh the visitor (transfer) token"""
        if not self.visitor_refresh or not self.visitor_client_id or not self.visitor_client_secret:
            logger.warning("[SalesIQ Transfer] Cannot refresh - missing credentials")
            return False
        
        new_token = refresh_zoho_token(
            self.visitor_refresh,
            self.visitor_client_id,
            self.visitor_client_secret
        )
        
        if new_token:
            self.visitor_token = new_token
            logger.info("[SalesIQ Transfer] ✓ Token refreshed")
            return True
        
        return False
    
    def create_chat_session(
        self,
        visitor_id: str,
        conversation_history: str,
        app_id: str = None,
        department_id: str = None,
        visitor_info: Dict = None,
        past_messages: list = None,
    ) -> Dict:
        """Create chat session (transfer to agent) using Visitor API"""
        
        if not self.enabled:
            logger.info(f"[SalesIQ Transfer] API disabled - simulating")
            return {"success": True, "simulated": True}
        
        if str(visitor_id).startswith("botpreview_"):
            logger.warning(f"[SalesIQ Transfer] Cannot transfer bot preview ID")
            return {"success": False, "error": "Cannot transfer bot preview"}
        
        url = f"{self.base_url}/conversations"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.visitor_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "app_id": app_id or self.app_id,
            "department_id": department_id or self.department_id,
            "question": conversation_history or "Customer needs assistance",
            "visitor": visitor_info or {
                "user_id": visitor_id,
                "name": "Chat Visitor",
                "email": f"{visitor_id}@visitor.com"
            }
        }
        
        if past_messages:
            payload["past_messages"] = past_messages
        
        # Try API call with auto-retry on 401
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"[SalesIQ Transfer] Attempt {attempt + 1}/{MAX_RETRIES}")
                response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"[SalesIQ Transfer] ✓ SUCCESS - {data.get('data', {}).get('id', 'unknown')}")
                    return {"success": True, "data": data}
                
                elif response.status_code in [401, 403]:
                    logger.warning(f"[SalesIQ Transfer] HTTP {response.status_code} - Attempting refresh...")
                    
                    if self._refresh_visitor_token():
                        headers["Authorization"] = f"Zoho-oauthtoken {self.visitor_token}"
                        continue
                    else:
                        logger.error(f"[SalesIQ Transfer] Token refresh failed")
                        return {"success": False, "error": "Token refresh failed"}
                
                else:
                    logger.error(f"[SalesIQ Transfer] HTTP {response.status_code}: {response.text[:200]}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                logger.error(f"[SalesIQ Transfer] Exception: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def close_chat(self, conversation_id: str, reason: str = "resolved") -> Dict:
        """Close chat using closure token"""
        logger.info(f"[SalesIQ Closure] Closing chat {conversation_id}")
        # Note: Zoho doesn't allow bot-initiated closures via API
        # This is a no-op that returns success
        return {"success": True, "message": "Chat will auto-close via timeout"}


class ZohoDeskAPI:
    """Zoho Desk API - Callback Creation"""
    
    def __init__(self):
        self.access_token = os.getenv("DESK_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("DESK_REFRESH_TOKEN", "").strip()
        self.client_id = os.getenv("DESK_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("DESK_CLIENT_SECRET", "").strip()
        
        self.org_id = os.getenv("DESK_ORG_ID", "").strip()
        self.department_id = os.getenv("DESK_DEPARTMENT_ID", "").strip()
        
        self.base_url = "https://desk.zoho.in/api/v1"
        self.enabled = bool(self.access_token and self.org_id and self.department_id)
        
        if self.enabled:
            logger.info(f"[Desk] ✓ ENABLED - org: {self.org_id}, dept: {self.department_id}")
        else:
            logger.warning(f"[Desk] ✗ DISABLED - Missing config")
    
    def _refresh_token(self) -> bool:
        """Refresh Desk access token"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.warning("[Desk] Cannot refresh - missing credentials")
            return False
        
        new_token = refresh_zoho_token(
            self.refresh_token,
            self.client_id,
            self.client_secret
        )
        
        if new_token:
            self.access_token = new_token
            logger.info("[Desk] ✓ Token refreshed")
            return True
        
        return False
    
    def _get_or_create_contact(self, email: str, name: str, phone: str = None) -> Optional[str]:
        """Get existing contact or create new one"""
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Content-Type": "application/json"
        }
        
        # Search for existing contact
        url = f"{self.base_url}/contacts"
        try:
            response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                contacts = response.json().get('data', [])
                for contact in contacts:
                    if contact.get('email') == email:
                        logger.info(f"[Desk] Found existing contact: {contact['id']}")
                        return contact['id']
        except Exception as e:
            logger.warning(f"[Desk] Error searching contacts: {e}")
        
        # Create new contact
        name_parts = name.split(' ', 1)
        payload = {
            'firstName': name_parts[0],
            'lastName': name_parts[1] if len(name_parts) > 1 else '',
            'email': email
        }
        if phone:
            payload['phone'] = phone
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
            
            if response.status_code in [200, 201]:
                contact_id = response.json().get('id')
                logger.info(f"[Desk] Created contact: {contact_id}")
                return contact_id
        except Exception as e:
            logger.error(f"[Desk] Error creating contact: {e}")
        
        return None
    
    def create_callback_ticket(
        self,
        visitor_email: str,
        visitor_name: str,
        visitor_phone: str,
        preferred_time: str = None,
        issue_description: str = None
    ) -> Dict:
        """Create callback in Desk"""
        
        if not self.enabled:
            logger.info(f"[Desk Callback] API disabled - simulating")
            return {"success": True, "simulated": True}
        
        # Get or create contact
        contact_id = self._get_or_create_contact(visitor_email, visitor_name, visitor_phone)
        
        if not contact_id:
            logger.error(f"[Desk Callback] Failed to get/create contact")
            return {"success": False, "error": "Contact creation failed"}
        
        url = f"{self.base_url}/calls"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Content-Type": "application/json"
        }
        
        start_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        payload = {
            "departmentId": self.department_id,
            "contactId": contact_id,
            "subject": f"Callback Request - {visitor_name}",
            "description": issue_description or f"Callback requested for {preferred_time or 'ASAP'}",
            "direction": "inbound",
            "startTime": start_time,
            "duration": "0",
            "status": "In Progress"
        }
        
        # Try API call with auto-retry on 401/403
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"[Desk Callback] Attempt {attempt + 1}/{MAX_RETRIES}")
                response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    call_id = data.get('id')
                    logger.info(f"[Desk Callback] ✓ SUCCESS - Call ID: {call_id}")
                    return {"success": True, "call_id": call_id, "data": data}
                
                elif response.status_code in [401, 403]:
                    logger.warning(f"[Desk Callback] HTTP {response.status_code} - Attempting refresh...")
                    
                    if self._refresh_token():
                        headers["Authorization"] = f"Zoho-oauthtoken {self.access_token}"
                        continue
                    else:
                        logger.error(f"[Desk Callback] Token refresh failed")
                        return {"success": False, "error": "Token refresh failed"}
                
                else:
                    logger.error(f"[Desk Callback] HTTP {response.status_code}: {response.text[:200]}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                logger.error(f"[Desk Callback] Exception: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
PYTHON_EOF

echo "Backing up old file..."
cp /opt/llm-chatbot/zoho_api_simple.py /opt/llm-chatbot/zoho_api_simple.py.backup

echo "Installing new file..."
mv /opt/llm-chatbot/zoho_api_simple_new.py /opt/llm-chatbot/zoho_api_simple.py

echo "Restarting service..."
sudo systemctl restart llm-chatbot

echo "Done! Checking status..."
sleep 2
sudo systemctl status llm-chatbot --no-pager -l | head -20
