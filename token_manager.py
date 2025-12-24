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
        # SalesIQ Tokens
        self.salesiq_access_token = os.getenv("SALESIQ_ACCESS_TOKEN", "").strip()
        self.salesiq_refresh_token = os.getenv("SALESIQ_REFRESH_TOKEN", "").strip()
        self.salesiq_client_id = os.getenv("SALESIQ_CLIENT_ID", "").strip()
        self.salesiq_client_secret = os.getenv("SALESIQ_CLIENT_SECRET", "").strip()
        
        # Desk Tokens (can use same OAuth client if scopes are included)
        self.desk_access_token = os.getenv("DESK_ACCESS_TOKEN", "").strip()
        self.desk_refresh_token = os.getenv("DESK_REFRESH_TOKEN", "").strip()
        self.desk_client_id = os.getenv("DESK_CLIENT_ID", os.getenv("SALESIQ_CLIENT_ID", "")).strip()
        self.desk_client_secret = os.getenv("DESK_CLIENT_SECRET", os.getenv("SALESIQ_CLIENT_SECRET", "")).strip()
        
        self.token_endpoint = "https://accounts.zoho.com/oauth/v2/token"
        
        # Track expiry for each API
        self.salesiq_token_expiry: Optional[datetime] = None
        self.desk_token_expiry: Optional[datetime] = None
        
        self.token_validity_seconds = 3600  # 1 hour
        self.refresh_threshold_seconds = 300  # Refresh 5 minutes before expiry
        self.lock = Lock()
        
        logger.info("[TokenManager] Initialized with OAuth credentials")
        logger.info(f"[TokenManager] SalesIQ Access Token: {self.salesiq_access_token[:20]}...")
        logger.info(f"[TokenManager] SalesIQ Refresh Token: {self.salesiq_refresh_token[:20] if self.salesiq_refresh_token else 'NOT SET'}...")
        logger.info(f"[TokenManager] Desk Access Token: {self.desk_access_token[:20] if self.desk_access_token else 'NOT SET'}...")
        logger.info(f"[TokenManager] Desk Refresh Token: {self.desk_refresh_token[:20] if self.desk_refresh_token else 'NOT SET'}...")
    
    def is_salesiq_token_expired(self) -> bool:
        """Check if SalesIQ token is expired or about to expire"""
        if self.salesiq_token_expiry is None:
            # First run - set token to expire in 1 hour from NOW
            self.salesiq_token_expiry = datetime.now() + timedelta(seconds=self.token_validity_seconds)
            logger.info(f"[TokenManager] First run - SalesIQ token expires at: {self.salesiq_token_expiry}")
            logger.warning(f"[TokenManager] First run - triggering SalesIQ token refresh for known expiry")
            return True
        
        now = datetime.now()
        time_until_expiry = (self.salesiq_token_expiry - now).total_seconds()
        
        # If less than 5 minutes left, refresh now
        if time_until_expiry < self.refresh_threshold_seconds:
            logger.warning(f"[TokenManager] SalesIQ token expiring in {time_until_expiry:.0f} seconds - refreshing now")
            return True
        
        return False
    
    def is_desk_token_expired(self) -> bool:
        """Check if Desk token is expired or about to expire"""
        if self.desk_token_expiry is None:
            # First run - set token to expire in 1 hour from NOW
            self.desk_token_expiry = datetime.now() + timedelta(seconds=self.token_validity_seconds)
            logger.info(f"[TokenManager] First run - Desk token expires at: {self.desk_token_expiry}")
            if self.desk_access_token:  # Only refresh if token exists
                logger.warning(f"[TokenManager] First run - triggering Desk token refresh for known expiry")
                return True
            return False
        
        now = datetime.now()
        time_until_expiry = (self.desk_token_expiry - now).total_seconds()
        
        # If less than 5 minutes left, refresh now
        if time_until_expiry < self.refresh_threshold_seconds:
            logger.warning(f"[TokenManager] Desk token expiring in {time_until_expiry:.0f} seconds - refreshing now")
            return True
        
        return False
    
    def refresh_salesiq_token(self) -> bool:
        """Refresh the SalesIQ access token using refresh token"""
        with self.lock:
            if not self.salesiq_refresh_token:
                logger.error("[TokenManager] No SalesIQ refresh token available - cannot refresh!")
                return False
            
            logger.info(f"[TokenManager] Refreshing SalesIQ access token...")
            
            try:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.salesiq_client_id,
                    "client_secret": self.salesiq_client_secret,
                    "refresh_token": self.salesiq_refresh_token,
                    "scope": "SalesIQ.conversations.CREATE,SalesIQ.conversations.READ,SalesIQ.conversations.UPDATE,SalesIQ.conversations.DELETE,Desk.tickets.CREATE,Desk.activities.calls.CREATE,Desk.activities.CREATE"
                }
                
                response = requests.post(
                    self.token_endpoint,
                    data=payload,
                    timeout=10
                )
                
                logger.info(f"[TokenManager] SalesIQ refresh response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update tokens
                    old_token = self.salesiq_access_token[:20]
                    self.salesiq_access_token = data.get("access_token", "").strip()
                    new_refresh_token = data.get("refresh_token", "").strip()
                    
                    if new_refresh_token:
                        self.salesiq_refresh_token = new_refresh_token
                        logger.info(f"[TokenManager] SalesIQ refresh token updated")
                    
                    # Update expiry time
                    expires_in = data.get("expires_in", self.token_validity_seconds)
                    self.salesiq_token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"[TokenManager] SalesIQ access token refreshed!")
                    logger.info(f"[TokenManager] Old token: {old_token}...")
                    logger.info(f"[TokenManager] New token: {self.salesiq_access_token[:20]}...")
                    logger.info(f"[TokenManager] New expiry: {self.salesiq_token_expiry}")
                    
                    # Update .env file with new tokens
                    self._update_env_file()
                    
                    return True
                else:
                    logger.error(f"[TokenManager] SalesIQ refresh failed with status {response.status_code}")
                    logger.error(f"[TokenManager] Response: {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"[TokenManager] SalesIQ refresh exception: {str(e)}")
                return False
    
    def refresh_desk_token(self) -> bool:
        """Refresh the Desk access token using refresh token"""
        if not self.desk_refresh_token:
            logger.warning("[TokenManager] No Desk refresh token available - skipping refresh")
            return False
        
        with self.lock:
            logger.info(f"[TokenManager] Refreshing Desk access token...")
            
            try:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.desk_client_id,
                    "client_secret": self.desk_client_secret,
                    "refresh_token": self.desk_refresh_token,
                    "scope": "Desk.tickets.CREATE,Desk.activities.calls.CREATE,Desk.activities.CREATE"
                }
                
                response = requests.post(
                    self.token_endpoint,
                    data=payload,
                    timeout=10
                )
                
                logger.info(f"[TokenManager] Desk refresh response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update tokens
                    old_token = self.desk_access_token[:20] if self.desk_access_token else "NEW"
                    self.desk_access_token = data.get("access_token", "").strip()
                    new_refresh_token = data.get("refresh_token", "").strip()
                    
                    if new_refresh_token:
                        self.desk_refresh_token = new_refresh_token
                        logger.info(f"[TokenManager] Desk refresh token updated")
                    
                    # Update expiry time
                    expires_in = data.get("expires_in", self.token_validity_seconds)
                    self.desk_token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"[TokenManager] Desk access token refreshed!")
                    logger.info(f"[TokenManager] Old token: {old_token}...")
                    logger.info(f"[TokenManager] New token: {self.desk_access_token[:20]}...")
                    logger.info(f"[TokenManager] New expiry: {self.desk_token_expiry}")
                    
                    return True
                else:
                    logger.error(f"[TokenManager] Desk refresh failed with status {response.status_code}")
                    logger.error(f"[TokenManager] Response: {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"[TokenManager] Desk refresh exception: {str(e)}")
                return False
    
    def get_valid_salesiq_token(self) -> str:
        """Get a valid SalesIQ access token, refreshing if necessary"""
        # Check if refresh needed
        if self.is_salesiq_token_expired():
            logger.info(f"[TokenManager] SalesIQ token expired - initiating refresh")
            self.refresh_salesiq_token()
        
        return self.salesiq_access_token
    
    def get_valid_desk_token(self) -> str:
        """Get a valid Desk access token, refreshing if necessary"""
        if not self.desk_access_token:
            logger.warning("[TokenManager] Desk token not configured")
            return ""
        
        # Check if refresh needed
        if self.is_desk_token_expired():
            logger.info(f"[TokenManager] Desk token expired - initiating refresh")
            self.refresh_desk_token()
        
        return self.desk_access_token
    
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
                    updated_lines.append(f"SALESIQ_ACCESS_TOKEN={self.salesiq_access_token}\n")
                elif line.startswith("SALESIQ_REFRESH_TOKEN="):
                    updated_lines.append(f"SALESIQ_REFRESH_TOKEN={self.salesiq_refresh_token}\n")
                elif line.startswith("DESK_ACCESS_TOKEN="):
                    updated_lines.append(f"DESK_ACCESS_TOKEN={self.desk_access_token}\n")
                elif line.startswith("DESK_REFRESH_TOKEN="):
                    updated_lines.append(f"DESK_REFRESH_TOKEN={self.desk_refresh_token}\n")
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
