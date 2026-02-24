"""
Zoho SalesIQ + Desk integration with auto token refresh.

Three separate token sets:
  1. SalesIQ Standard  → chat closure (after issue resolved)
  2. SalesIQ Visitor/Org → chat transfer to agent
  3. Desk Standard      → callback activities

Each auto-refreshes on 401/400 "Invalid OAuthToken" errors.
"""

from __future__ import annotations

import os
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

ZOHO_ACCOUNTS_URL = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")


class TokenManager:
    """Manages three Zoho OAuth token sets with automatic refresh."""

    def __init__(self):
        # ── SalesIQ Standard Token (chat closure) ──
        self.salesiq_access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self._salesiq_refresh = os.getenv("SALESIQ_REFRESH_TOKEN", "").strip()
        self._salesiq_client_id = os.getenv("SALESIQ_CLIENT_ID", "").strip()
        self._salesiq_client_secret = os.getenv("SALESIQ_CLIENT_SECRET", "").strip()

        # ── SalesIQ Visitor / Org Token (chat transfer) ──
        self.visitor_access_token = os.getenv("SALESIQ_VISITOR_ACCESS_TOKEN", "").strip()
        self._visitor_refresh = os.getenv("SALESIQ_VISITOR_REFRESH_TOKEN", "").strip()
        self._visitor_client_id = os.getenv("SALESIQ_VISITOR_CLIENT_ID", "").strip()
        self._visitor_client_secret = os.getenv("SALESIQ_VISITOR_CLIENT_SECRET", "").strip()

        # ── Desk Standard Token (callback activities) ──
        self.desk_access_token = os.getenv("DESK_ACCESS_TOKEN", "").strip()
        self._desk_refresh = os.getenv("DESK_REFRESH_TOKEN", "").strip()
        self._desk_client_id = os.getenv("DESK_CLIENT_ID", "").strip()
        self._desk_client_secret = os.getenv("DESK_CLIENT_SECRET", "").strip()

        # ── SalesIQ static config ──
        self.app_id = os.getenv("SALESIQ_APP_ID", "").strip()
        self.department_id = os.getenv("SALESIQ_DEPARTMENT_ID", "").strip()
        self.screen_name = os.getenv("SALESIQ_SCREEN_NAME", "rtdsportal").strip()

        # ── Desk static config ──
        self.desk_org_id = os.getenv("DESK_ORG_ID", "").strip()
        self.desk_dept_id = os.getenv("DESK_DEPARTMENT_ID", "").strip()

        self._log_status()

    # ── Internal helpers ──────────────────────────────────────────

    def _log_status(self):
        salesiq_ok = bool(self.salesiq_access_token and self._salesiq_client_id)
        visitor_ok = bool(self.visitor_access_token and self._visitor_client_id)
        desk_ok = bool(self.desk_access_token and self._desk_client_id)
        logger.info(
            "Zoho tokens configured: salesiq_standard=%s, salesiq_visitor=%s, desk=%s",
            salesiq_ok, visitor_ok, desk_ok,
        )

    async def _refresh(self, client_id: str, client_secret: str,
                       refresh_token: str, label: str) -> Optional[str]:
        """Generic OAuth2 token refresh. Returns new access token or None."""
        if not all([client_id, client_secret, refresh_token]):
            logger.warning("Token refresh skipped (%s) — missing credentials", label)
            return None

        try:
            url = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"
            payload = {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, data=payload)

            if resp.status_code == 200:
                data = resp.json()
                new_token = data.get("access_token", "")
                logger.info("%s token refreshed (expires_in=%s)", label, data.get("expires_in"))
                return new_token

            logger.error("%s refresh failed: %s — %s", label, resp.status_code, resp.text[:200])
            return None
        except Exception as exc:
            logger.error("%s refresh exception: %s", label, exc)
            return None

    # ── Public refresh methods ────────────────────────────────────

    async def refresh_salesiq_standard(self) -> bool:
        """Refresh the SalesIQ standard token (chat closure)."""
        new = await self._refresh(
            self._salesiq_client_id, self._salesiq_client_secret,
            self._salesiq_refresh, "SalesIQ-Standard",
        )
        if new:
            self.salesiq_access_token = new
            return True
        return False

    async def refresh_salesiq_visitor(self) -> bool:
        """Refresh the SalesIQ visitor/org token (chat transfer)."""
        new = await self._refresh(
            self._visitor_client_id, self._visitor_client_secret,
            self._visitor_refresh, "SalesIQ-Visitor",
        )
        if new:
            self.visitor_access_token = new
            return True
        return False

    async def refresh_desk(self) -> bool:
        """Refresh the Desk standard token (callbacks)."""
        new = await self._refresh(
            self._desk_client_id, self._desk_client_secret,
            self._desk_refresh, "Desk",
        )
        if new:
            self.desk_access_token = new
            return True
        return False


# ── Singleton ─────────────────────────────────────────────────────
tokens = TokenManager()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CHAT TRANSFER — SalesIQ Visitor API (org token)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def transfer_to_agent(
    session_id: str,
    visitor_info: Optional[Dict] = None,
    conversation_summary: str = "",
) -> Dict:
    """Initiate a live chat transfer via SalesIQ Visitor API.

    Uses the visitor/org token. Auto-refreshes on token expiry.
    Returns {"success": True/False, ...}.
    """
    # Reject bot preview IDs — they can't be transferred
    if str(session_id).startswith("botpreview_"):
        logger.warning("Cannot transfer bot preview session %s", session_id)
        return {
            "success": False,
            "error": "bot_preview",
            "message": "Bot preview sessions cannot be transferred. Use a real visitor session.",
        }

    base_url = f"https://salesiq.zoho.in/api/visitor/v1/{tokens.screen_name}"
    endpoint = f"{base_url}/conversations"

    # Fallback defaults — overridden below by real visitor data from SalesIQ
    visitor_name = "Chat User"
    visitor_email = "support@acecloudhosting.com"
    visitor_user_id = str(session_id).strip()

    # Use real visitor details from SalesIQ webhook payload (dynamic per user)
    if visitor_info:
        visitor_name = visitor_info.get("name", visitor_info.get("email", "Chat User"))
        visitor_email = visitor_info.get("email", "support@acecloudhosting.com")
        visitor_user_id = (
            visitor_info.get("email")
            or visitor_info.get("user_id")
            or visitor_user_id
        )

    payload = {
        "app_id": tokens.app_id,
        "department_id": tokens.department_id,
        "question": conversation_summary or "User requested human assistance",
        "visitor": {
            "user_id": visitor_user_id,
            "name": visitor_name,
            "email": visitor_email,
        },
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {tokens.visitor_access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)

        # Auto-refresh on expired token
        if response.status_code in (400, 401) and "Invalid" in response.text:
            logger.warning("Visitor token expired (%s). Refreshing…", response.status_code)
            if await tokens.refresh_salesiq_visitor():
                headers["Authorization"] = f"Zoho-oauthtoken {tokens.visitor_access_token}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                logger.info("Transfer retry response: %s", response.status_code)
            else:
                return {"success": False, "error": "token_refresh_failed",
                        "message": "Could not refresh SalesIQ token."}

        if response.status_code in (200, 201):
            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}
            logger.info("Chat transfer initiated for session %s", session_id)
            return {"success": True, "data": data}

        logger.error("Transfer failed: %s — %s", response.status_code, response.text[:200])
        return {
            "success": False,
            "error": str(response.status_code),
            "message": f"SalesIQ API returned {response.status_code}",
        }

    except httpx.TimeoutException:
        logger.error("Transfer timed out for session %s", session_id)
        return {"success": False, "error": "timeout", "message": "SalesIQ API timed out."}
    except Exception as exc:
        logger.error("Transfer exception: %s", exc)
        return {"success": False, "error": "exception", "message": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. SCHEDULE CALLBACK — Zoho Desk Activities API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def create_callback_activity(
    session_id: str,
    user_name: str,
    user_email: str = "",
    user_phone: str = "",
    conversation_summary: str = "",
) -> Dict:
    """Create a callback activity in Zoho Desk.

    Uses the Desk standard token. Auto-refreshes on token expiry.
    Returns {"success": True/False, ...}.
    """
    activity_data = {
        "subject": f"Callback Request — {user_name}",
        "departmentId": tokens.desk_dept_id,
        "description": (
            "Callback requested via chatbot.\n\n"
            f"User: {user_name}\n"
            f"Email: {user_email or 'Not provided'}\n"
            f"Phone: {user_phone or 'Not provided'}\n"
            f"Session: {session_id}\n\n"
            "--- Conversation Summary ---\n"
            f"{conversation_summary or 'No summary available.'}"
        ),
        "priority": "High",
        "status": "Open",
        "activityType": "Calls",
        "category": "Callback from Chatbot",
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {tokens.desk_access_token}",
        "Content-Type": "application/json",
        "orgId": tokens.desk_org_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://desk.zoho.com/api/v1/activities",
                json=activity_data,
                headers=headers,
            )

        # Auto-refresh on expired token
        if response.status_code in (400, 401) and "Invalid" in response.text.lower():
            logger.warning("Desk token expired (%s). Refreshing…", response.status_code)
            if await tokens.refresh_desk():
                headers["Authorization"] = f"Zoho-oauthtoken {tokens.desk_access_token}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "https://desk.zoho.com/api/v1/activities",
                        json=activity_data,
                        headers=headers,
                    )
                logger.info("Callback retry response: %s", response.status_code)
            else:
                return {"success": False, "error": "token_refresh_failed",
                        "message": "Could not refresh Desk token."}

        if response.status_code in (200, 201):
            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}
            activity_id = data.get("id", "unknown") if isinstance(data, dict) else "unknown"
            logger.info("Callback activity created: %s", activity_id)
            return {"success": True, "activity_id": activity_id, "data": data}

        logger.error("Desk activity failed: %s — %s", response.status_code, response.text[:200])
        return {
            "success": False,
            "error": str(response.status_code),
            "message": f"Desk API returned {response.status_code}",
        }

    except httpx.TimeoutException:
        logger.error("Callback activity timed out for session %s", session_id)
        return {"success": False, "error": "timeout", "message": "Desk API timed out."}
    except Exception as exc:
        logger.error("Callback activity exception: %s", exc)
        return {"success": False, "error": "exception", "message": str(exc)}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CLOSE CHAT — SalesIQ Standard Token
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def close_chat(session_id: str) -> Dict:
    """Close a SalesIQ chat session (standard token).

    Called when the issue is resolved and confirmed by the user.
    """
    base_url = f"https://salesiq.zoho.in/api/visitor/v1/{tokens.screen_name}"
    endpoint = f"{base_url}/conversations/{session_id}/end"

    headers = {
        "Authorization": f"Zoho-oauthtoken {tokens.salesiq_access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, headers=headers)

        # Auto-refresh on expired token
        if response.status_code in (400, 401) and "Invalid" in response.text:
            logger.warning("SalesIQ standard token expired. Refreshing…")
            if await tokens.refresh_salesiq_standard():
                headers["Authorization"] = f"Zoho-oauthtoken {tokens.salesiq_access_token}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(endpoint, headers=headers)
            else:
                return {"success": False, "error": "token_refresh_failed"}

        if response.status_code in (200, 201, 204):
            logger.info("Chat closed for session %s", session_id)
            return {"success": True}

        logger.error("Chat close failed: %s — %s", response.status_code, response.text[:200])
        return {"success": False, "error": str(response.status_code)}

    except Exception as exc:
        logger.error("Chat close exception: %s", exc)
        return {"success": False, "error": "exception", "message": str(exc)}
