"""
Zoho Desk/SalesIQ live integration helpers used by the chatbot webhook.

This module isolates external API calls from webhook orchestration logic.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


async def send_salesiq_message(
    session_id: str,
    message: str,
    access_token: str,
    org_id: str,
    suggestions: Optional[List[Dict]] = None,
) -> bool:
    """Send a message to a Zoho chat session."""
    try:
        url = f"https://desk.zoho.com/api/v1/portals/{org_id}/chats/{session_id}/messages"
        payload: Dict = {"type": "message", "text": message}
        if suggestions:
            payload["suggestions"] = suggestions

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info("Message sent to Zoho chat session %s", session_id)
                return True

            logger.error("Zoho chat API error: %s - %s", response.status_code, response.text)
            return False

    except Exception as exc:
        logger.error("Failed to send Zoho chat message: %s", exc)
        return False


async def create_desk_ticket(
    session_id: str,
    user_name: str,
    conversation_history: List[Dict],
    access_token: str,
    org_id: str,
    dept_id: str,
) -> Optional[str]:
    """Create a Zoho Desk ticket for chat escalation."""
    try:
        conversation_text = "\n\n".join(
            [
                f"{'User' if msg['role'] == 'user' else 'Bot'}: {msg['content']}"
                for msg in conversation_history[-10:]
            ]
        )

        ticket_data = {
            "subject": f"Chat Escalation - {user_name}",
            "departmentId": dept_id,
            "contactId": session_id,
            "description": (
                "Chat escalation from AI assistant.\n\n"
                "--- Conversation History ---\n\n"
                f"{conversation_text}"
            ),
            "status": "Open",
            "priority": "High",
            "channel": "Chat",
        }

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
            "orgId": org_id,
        }

        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(
                "https://desk.zoho.com/api/v1/tickets",
                json=ticket_data,
                headers=headers,
            )

            if response.status_code in (200, 201):
                ticket = response.json()
                ticket_id = ticket.get("id", "unknown")
                logger.info("Desk ticket created: %s", ticket_id)
                return ticket_id

            logger.error("Desk API error: %s - %s", response.status_code, response.text)
            return None

    except Exception as exc:
        logger.error("Failed to create Desk ticket: %s", exc)
        return None
