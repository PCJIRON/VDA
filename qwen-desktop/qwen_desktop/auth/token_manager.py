"""
Token management for OAuth.

Handles secure storage and retrieval of OAuth tokens.
"""

import json
import time
from typing import Optional
from datetime import datetime, timedelta

import keyring
from qwen_desktop.auth.credentials import Credentials


class TokenManager:
    """Manages OAuth tokens."""

    SERVICE_NAME = "qwen-desktop"

    def __init__(self) -> None:
        """Initialize token manager."""
        self.credentials = Credentials()

    def save_tokens(self, token_data: dict) -> None:
        """Save OAuth tokens.
        
        Args:
            token_data: Token data from OAuth provider.
        """
        # Save all credentials using the new method (same as qwen-code)
        self.credentials.save_credentials(token_data)

    def get_access_token(self) -> Optional[str]:
        """Get the current access token.
        
        Returns:
            Access token or None.
        """
        return self.credentials.get_access_token()

    def get_refresh_token(self) -> Optional[str]:
        """Get the refresh token.
        
        Returns:
            Refresh token or None.
        """
        return self.credentials.get_refresh_token()

    def is_token_valid(self) -> bool:
        """Check if access token is still valid.
        
        Returns:
            True if token is valid.
        """
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        expiry = self.credentials.get_token_expiry()
        if not expiry:
            return False
        
        # Token is valid if it expires in more than 5 minutes
        return expiry > datetime.now() + timedelta(minutes=5)

    def refresh_access_token(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
    ) -> bool:
        """Refresh the access token.
        
        Args:
            client_id: OAuth client ID.
            client_secret: OAuth client secret.
            token_url: Token endpoint URL.
            
        Returns:
            True if refresh was successful.
        """
        refresh_token = self.get_refresh_token()
        if not refresh_token:
            return False
        
        try:
            import httpx
            
            # Use a standard user-agent to prevent Cloudflare WAF from blocking the request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            
            response = httpx.post(
                token_url,
                headers=headers,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.save_tokens(token_data)
            
            return True
            
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False

    def clear_tokens(self) -> None:
        """Clear all stored tokens."""
        self.credentials.clear_credentials()
