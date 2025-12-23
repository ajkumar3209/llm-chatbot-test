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
    """Manages Zoho OAuth tokens with automatic refresh"""
    
    def __init__(self):
        self.access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("SALESIQ_REFRESH_TOKEN", "").strip()
        self.client_id = os.getenv("SALESIQ_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("SALESIQ_CLIENT_SECRET", "").strip()
        
        self.token_endpoint = "https://accounts.zoho.in/oauth/v2/token"
        self.token_expiry_time: Optional[datetime] = None
        self.token_validity_seconds = 3600  # 1 hour
        self.refresh_threshold_seconds = 300  # Refresh 5 minutes before expiry
        self.lock = Lock()
        
        logger.info("[TokenManager] Initialized with OAuth credentials")
        logger.info(f"[TokenManager] Access Token: {self.access_token[:20]}...")
        logger.info(f"[TokenManager] Refresh Token: {self.refresh_token[:20] if self.refresh_token else 'NOT SET'}...")
    
    def is_token_expired(self) -> bool:
        """Check if current token is expired or about to expire"""
        if not self.token_expiry_time:
            # First run - assume token was just issued
            self.token_expiry_time = datetime.now() + timedelta(seconds=self.token_validity_seconds)
            logger.info(f"[TokenManager] First run - token expiry set to: {self.token_expiry_time}")
            return False
        
        now = datetime.now()
        time_until_expiry = (self.token_expiry_time - now).total_seconds()
        
        # If less than 5 minutes left, refresh now
        if time_until_expiry < self.refresh_threshold_seconds:
            logger.warning(f"[TokenManager] Token expiring in {time_until_expiry:.0f} seconds - refreshing now")
            return True
        
        return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        with self.lock:
            if not self.refresh_token:
                logger.error("[TokenManager] No refresh token available - cannot refresh!")
                return False
            
            logger.info(f"[TokenManager] Refreshing access token...")
            
            try:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "scope": "SalesIQ.conversations.CREATE,SalesIQ.conversations.READ,SalesIQ.conversations.UPDATE,SalesIQ.conversations.DELETE"
                }
                
                response = requests.post(
                    self.token_endpoint,
                    data=payload,
                    timeout=10
                )
                
                logger.info(f"[TokenManager] Refresh response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update tokens
                    old_token = self.access_token[:20]
                    self.access_token = data.get("access_token", "").strip()
                    new_refresh_token = data.get("refresh_token", "").strip()
                    
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                        logger.info(f"[TokenManager] Refresh token updated")
                    
                    # Update expiry time
                    expires_in = data.get("expires_in", self.token_validity_seconds)
                    self.token_expiry_time = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"[TokenManager] Access token refreshed!")
                    logger.info(f"[TokenManager] Old token: {old_token}...")
                    logger.info(f"[TokenManager] New token: {self.access_token[:20]}...")
                    logger.info(f"[TokenManager] New expiry: {self.token_expiry_time}")
                    logger.info(f"[TokenManager] Validity: {expires_in} seconds")
                    
                    # Update .env file with new tokens
                    self._update_env_file()
                    
                    return True
                else:
                    logger.error(f"[TokenManager] Refresh failed with status {response.status_code}")
                    logger.error(f"[TokenManager] Response: {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"[TokenManager] Refresh exception: {str(e)}")
                return False
    
    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        # Check if refresh needed
        if self.is_token_expired():
            logger.info(f"[TokenManager] Token expired - initiating refresh")
            self.refresh_access_token()
        
        return self.access_token
    
    def _update_env_file(self):
        """Update .env file with new token values"""
        try:
            env_file = ".env"
            
            if not os.path.exists(env_file):
                logger.warning(f"[TokenManager] .env file not found at {env_file}")
                return
            
            # Read current .env
            with open(env_file, "r") as f:
                lines = f.readlines()
            
            # Update token lines
            updated_lines = []
            for line in lines:
                if line.startswith("SALESIQ_ACCESS_TOKEN="):
                    updated_lines.append(f"SALESIQ_ACCESS_TOKEN={self.access_token}\n")
                elif line.startswith("SALESIQ_REFRESH_TOKEN="):
                    updated_lines.append(f"SALESIQ_REFRESH_TOKEN={self.refresh_token}\n")
                else:
                    updated_lines.append(line)
            
            # Write updated .env
            with open(env_file, "w") as f:
                f.writelines(updated_lines)
            
            logger.info(f"[TokenManager] .env file updated with new tokens")
            
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
