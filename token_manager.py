"""
Zoho OAuth Token Manager - Handles automatic token refresh
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ZohoTokenManager:
    """Manages Zoho OAuth tokens with automatic refresh (Unified for SalesIQ + Desk)"""
    
    def __init__(self):
        # Single unified OAuth token (combined scopes for SalesIQ + Desk)
        self.access_token = os.getenv("OAUTH_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("OAUTH_REFRESH_TOKEN", "").strip()
        self.client_id = os.getenv("OAUTH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET", "").strip()
        
        # Legacy property names for backward compatibility
        self.salesiq_access_token = self.access_token
        self.salesiq_refresh_token = self.refresh_token
        self.desk_access_token = self.access_token
        self.desk_refresh_token = self.refresh_token
        
        self.token_endpoint = "https://accounts.zoho.com/oauth/v2/token"
        
        # Track expiry for unified token
        self.token_expiry: Optional[datetime] = None
        
        self.token_validity_seconds = 3600  # 1 hour
        self.refresh_threshold_seconds = 300  # Refresh 5 minutes before expiry
        self.lock = Lock()
        
        logger.info("[TokenManager] Initialized with unified OAuth credentials")
        logger.info(f"[TokenManager] Access Token: {self.access_token[:20]}...")
        logger.info(f"[TokenManager] Refresh Token: {self.refresh_token[:20] if self.refresh_token else 'NOT SET'}...")
        logger.info(f"[TokenManager] Scopes: SalesIQ + Desk (combined)")
        logger.info(f"[TokenManager] Desk Refresh Token: {self.desk_refresh_token[:20] if self.desk_refresh_token else 'NOT SET'}...")
    
    def is_token_expired(self) -> bool:
        """Check if OAuth token is expired or about to expire (works for both APIs)"""
        if self.token_expiry is None:
            # First run - set token to expire in 1 hour from NOW
            self.token_expiry = datetime.now() + timedelta(seconds=self.token_validity_seconds)
            logger.info(f"[TokenManager] First run - token expires at: {self.token_expiry}")
            logger.warning(f"[TokenManager] First run - triggering token refresh for known expiry")
            return True
        
        now = datetime.now()
        time_until_expiry = (self.token_expiry - now).total_seconds()
        
        # If less than 5 minutes left, refresh now
        if time_until_expiry < self.refresh_threshold_seconds:
            logger.warning(f"[TokenManager] Token expiring in {time_until_expiry:.0f} seconds - refreshing now")
            return True
        
        return False
    
    def refresh_token(self) -> bool:
        """Refresh the unified OAuth access token using refresh token (works for both APIs)"""
        with self.lock:
            if not self.refresh_token:
                logger.error("[TokenManager] No refresh token available - cannot refresh!")
                return False
            
            logger.info(f"[TokenManager] Refreshing unified OAuth token...")
            
            try:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "scope": "Desk.tickets.CREATE,Desk.activities.calls.CREATE,Desk.activities.CREATE,SalesIQ.Conversations.READ,SalesIQ.Conversations.CREATE,SalesIQ.departments.READ,SalesIQ.departments.CREATE,SalesIQ.operators.READ"
                }
                
                response = requests.post(self.token_endpoint, data=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
                    
                    # Update legacy properties
                    self.salesiq_access_token = self.access_token
                    self.salesiq_refresh_token = self.refresh_token
                    self.desk_access_token = self.access_token
                    self.desk_refresh_token = self.refresh_token
                    
                    # Set expiry to 1 hour from now
                    self.token_expiry = datetime.now() + timedelta(seconds=self.token_validity_seconds)
                    
                    logger.info(f"[TokenManager] Token refreshed successfully - expires at {self.token_expiry}")
                    self._update_env_file()
                    return True
                else:
                    logger.error(f"[TokenManager] Token refresh failed: {response.status_code} - {response.text[:200]}")
                    return False
            
            except Exception as e:
                logger.error(f"[TokenManager] Token refresh exception: {str(e)}")
                return False
    
    def get_valid_token(self) -> str:
        """Get valid OAuth token, auto-refreshing if needed (works for both SalesIQ and Desk)"""
        if self.is_token_expired():
            self.refresh_token()
        return self.access_token
    
    # Backward compatibility aliases
    def get_valid_salesiq_token(self) -> str:
        """Alias for get_valid_token() - backward compatibility"""
        return self.get_valid_token()
    
    def get_valid_desk_token(self) -> str:
        """Alias for get_valid_token() - backward compatibility"""
        return self.get_valid_token()
    
    def _update_env_file(self):
        """Update .env file with new token values"""
        try:
            env_file = ".env"
            
            if not os.path.exists(env_file):
                logger.warning(f"[TokenManager] .env file not found at {env_file}")
                return
            
            # Read current .env
            with open(env_file, "r") as f:
                content = f.read()
            
            # Update unified OAuth tokens
            content = re.sub(r'OAUTH_ACCESS_TOKEN=.*', f'OAUTH_ACCESS_TOKEN={self.access_token}', content)
            content = re.sub(r'OAUTH_REFRESH_TOKEN=.*', f'OAUTH_REFRESH_TOKEN={self.refresh_token}', content)
            
            # Write updated .env
            with open(env_file, "w") as f:
                f.write(content)
            
            logger.info(f"[TokenManager] .env file updated with refreshed unified OAuth tokens")
            
        except Exception as e:
            logger.error(f"[TokenManager] Failed to update .env file: {str(e)}")


# Global token manager instance
_token_manager: Optional[ZohoTokenManager] = None


def get_token_manager() -> ZohoTokenManager:
    """Get or create the global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = ZohoTokenManager()
    return _token_manager
