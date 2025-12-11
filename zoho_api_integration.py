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
        self.api_key = os.getenv("SALESIQ_API_KEY")
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID")
        self.base_url = "https://salesiq.zoho.com/api/v2"
        self.enabled = bool(self.api_key and self.department_id)
        
        if not self.enabled:
            logger.warning("SalesIQ API not configured - transfers will be simulated")
    
    def create_chat_session(self, visitor_id: str, conversation_history: str) -> Dict:
        """Create new chat session and transfer to agent"""
        
        if not self.enabled:
            logger.info(f"SalesIQ API disabled - simulating transfer for visitor {visitor_id}")
            return {
                "success": True,
                "simulated": True,
                "message": "Chat transfer initiated (simulated)"
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "visitor_id": visitor_id,
            "department_id": self.department_id,
            "conversation_history": conversation_history,
            "transfer_to": "human_agent"
        }
        
        try:
            logger.info(f"Creating SalesIQ chat session for visitor {visitor_id}")
            response = requests.post(
                f"{self.base_url}/chats",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"SalesIQ chat session created successfully")
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


class ZohoDeskAPI:
    """Zoho Desk API Integration for ticket creation"""
    
    def __init__(self):
        self.oauth_token = os.getenv("DESK_OAUTH_TOKEN")
        self.org_id = os.getenv("DESK_ORGANIZATION_ID")
        self.base_url = "https://desk.zoho.com/api/v1"
        self.enabled = bool(self.oauth_token and self.org_id)
        
        if not self.enabled:
            logger.warning("Desk API not configured - ticket creation will be simulated")
    
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
            "Authorization": f"Zoho-oauthtoken {self.oauth_token}",
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
            "Authorization": f"Zoho-oauthtoken {self.oauth_token}",
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
