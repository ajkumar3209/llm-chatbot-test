"""
Zoho API Integration Module
Handles SalesIQ chat transfers and Desk ticket creation
"""

import requests
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ZohoSalesIQAPI:
    """Zoho SalesIQ API Integration for chat transfers"""
    
    def __init__(self):
        # Initialize with safe defaults
        self.enabled = False
        self.access_token = None
        self.department_id = None
        self.app_id = None
        self.screen_name = "rtdsportal"
        self.base_url = "https://salesiq.zoho.in/api/visitor/v1/rtdsportal"
        
        try:
            # Safely get environment variables
            self.access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
            self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
            self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
            self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()
            
            # Use Operator API instead of Visitor API (token has operator scopes)
            self.base_url = "https://salesiq.zoho.in/api/v2"
            
            # Enable only if we have minimum required config
            self.enabled = bool(self.access_token and self.department_id)
            
            if not self.enabled:
                logger.warning("SalesIQ API not configured - missing token or department_id")
            else:
                logger.info(f"SalesIQ API configured - department: {self.department_id}")
                
        except Exception as e:
            logger.error(f"Error initializing SalesIQ API: {str(e)}")
            self.enabled = False
    
    def create_chat_session(self, visitor_id: str, conversation_history: str) -> Dict:
        """Create new conversation using official SalesIQ Visitor API"""
        
        if not self.enabled:
            logger.info(f"SalesIQ API disabled - simulating transfer for visitor {visitor_id}")
            return {
                "success": True,
                "simulated": True,
                "message": "Chat transfer initiated (simulated)"
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Use Operator API payload structure (token has operator scopes)
        payload = {
            "visitor_id": visitor_id,
            "department_id": self.department_id,
            "conversation_history": conversation_history,
            "message": "User requesting chat transfer"
        }
        
        logger.info(f"SalesIQ Operator API payload: visitor_id={visitor_id}, department_id={self.department_id}")
        
        try:
            logger.info(f"Creating SalesIQ chat session for visitor {visitor_id}")
            response = requests.post(
                f"{self.base_url}/chats",  # Operator API endpoint
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"SalesIQ conversation created successfully")
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                logger.error(f"SalesIQ API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except requests.exceptions.Timeout:
            logger.error("SalesIQ API timeout")
            return {
                "success": False,
                "error": "API timeout"
            }
        except Exception as e:
            logger.error(f"SalesIQ API error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close_chat(self, session_id: str, reason: str = "resolved") -> Dict:
        """Close chat session in SalesIQ"""
        
        if not self.enabled:
            logger.info(f"SalesIQ API disabled - simulating chat closure for session {session_id}")
            return {
                "success": True,
                "simulated": True,
                "message": f"Chat {session_id} closed (simulated)"
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "status": "closed",
            "reason": reason,
            "closed_by": "bot"
        }
        
        try:
            logger.info(f"Closing SalesIQ chat session {session_id}")
            response = requests.patch(
                f"{self.base_url}/chats/{session_id}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"SalesIQ chat {session_id} closed successfully")
                return {
                    "success": True,
                    "message": f"Chat {session_id} closed"
                }
            else:
                logger.error(f"SalesIQ close chat error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except requests.exceptions.Timeout:
            logger.error("SalesIQ API timeout during chat closure")
            return {
                "success": False,
                "error": "API timeout"
            }
        except Exception as e:
            logger.error(f"SalesIQ close chat error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class ZohoDeskAPI:
    """Zoho Desk API Integration for ticket creation"""
    
    def __init__(self):
        # Initialize with safe defaults
        self.enabled = False
        self.access_token = None
        self.org_id = None
        self.base_url = "https://desk.zoho.in/api/v1"
        
        try:
            # Safely get environment variables
            self.access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
            self.org_id = os.getenv("DESK_ORGANIZATION_ID", "").strip()
            
            # Keep Desk API disabled for now - focus on SalesIQ first
            self.enabled = False
            
            logger.warning("Desk API disabled - ticket creation will be simulated")
            
        except Exception as e:
            logger.error(f"Error initializing Desk API: {str(e)}")
            self.enabled = False
    
    def create_callback_ticket(self, 
                              user_email: str,
                              phone: str,
                              preferred_time: str,
                              issue_summary: str) -> Dict:
        """Create callback ticket in Zoho Desk"""
        
        if not self.enabled:
            logger.info(f"Desk API disabled - simulating callback ticket for {user_email}")
            return {
                "success": True,
                "simulated": True,
                "ticket_number": "CALLBACK-SIM-001",
                "message": "Callback ticket created (simulated)"
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subject": "Callback Request",
            "description": f"User requested callback at {preferred_time}\n\nIssue: {issue_summary}",
            "email": user_email,
            "phone": phone,
            "priority": "medium",
            "status": "open",
            "type": "callback",
            "customFields": {
                "callback_time": preferred_time,
                "issue_description": issue_summary
            }
        }
        
        try:
            logger.info(f"Creating callback ticket for {user_email}")
            response = requests.post(
                f"{self.base_url}/tickets",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                ticket_number = data.get("data", {}).get("ticketNumber", "UNKNOWN")
                logger.info(f"Callback ticket created: {ticket_number}")
                return {
                    "success": True,
                    "ticket_number": ticket_number,
                    "data": data
                }
            else:
                logger.error(f"Desk API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except requests.exceptions.Timeout:
            logger.error("Desk API timeout")
            return {
                "success": False,
                "error": "API timeout"
            }
        except Exception as e:
            logger.error(f"Desk API error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_support_ticket(self,
                             user_name: str,
                             user_email: str,
                             phone: str,
                             description: str,
                             issue_type: str,
                             conversation_history: str) -> Dict:
        """Create support ticket in Zoho Desk"""
        
        if not self.enabled:
            logger.info(f"Desk API disabled - simulating support ticket for {user_email}")
            return {
                "success": True,
                "simulated": True,
                "ticket_number": "TICKET-SIM-001",
                "message": "Support ticket created (simulated)"
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subject": f"Support Request - {issue_type}",
            "description": f"{description}\n\n--- Conversation History ---\n{conversation_history}",
            "email": user_email,
            "phone": phone,
            "name": user_name,
            "priority": "medium",
            "status": "open",
            "type": "support",
            "customFields": {
                "issue_type": issue_type,
                "conversation_history": conversation_history
            }
        }
        
        try:
            logger.info(f"Creating support ticket for {user_email}")
            response = requests.post(
                f"{self.base_url}/tickets",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                ticket_number = data.get("data", {}).get("ticketNumber", "UNKNOWN")
                logger.info(f"Support ticket created: {ticket_number}")
                return {
                    "success": True,
                    "ticket_number": ticket_number,
                    "data": data
                }
            else:
                logger.error(f"Desk API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except requests.exceptions.Timeout:
            logger.error("Desk API timeout")
            return {
                "success": False,
                "error": "API timeout"
            }
        except Exception as e:
            logger.error(f"Desk API error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
