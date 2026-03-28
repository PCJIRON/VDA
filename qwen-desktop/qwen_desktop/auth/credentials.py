"""
Credentials storage for OAuth tokens.

Uses system keyring for secure storage.
Matches qwen-code's QwenCredentials interface.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import keyring
import keyring.errors

logger = logging.getLogger(__name__)


class Credentials:
    """Secure credentials storage (same as qwen-code SharedTokenManager)."""

    SERVICE_NAME = "qwen-desktop"
    ACCESS_TOKEN_KEY = "access_token"
    REFRESH_TOKEN_KEY = "refresh_token"
    EXPIRY_KEY = "token_expiry"
    RESOURCE_URL_KEY = "resource_url"
    TOKEN_TYPE_KEY = "token_type"

    def __init__(self) -> None:
        """Initialize credentials manager."""
        self.service = self.SERVICE_NAME

    def save_credentials(self, credentials: Dict[str, Any]) -> None:
        """Save all OAuth credentials (same as qwen-code).
        
        Args:
            credentials: OAuth credentials dict with all fields.
        """
        try:
            # Save access token
            if "access_token" in credentials:
                keyring.set_password(self.service, self.ACCESS_TOKEN_KEY, credentials["access_token"])
            
            # Save refresh token
            if "refresh_token" in credentials:
                keyring.set_password(self.service, self.REFRESH_TOKEN_KEY, credentials["refresh_token"])
            
            # Save expiry
            if "expiry_date" in credentials:
                expiry = datetime.fromtimestamp(credentials["expiry_date"] / 1000)  # Convert from ms
                keyring.set_password(self.service, self.EXPIRY_KEY, expiry.isoformat())
            
            # Save resource URL (IMPORTANT for DashScope API!)
            if "resource_url" in credentials:
                keyring.set_password(self.service, self.RESOURCE_URL_KEY, credentials["resource_url"])
            
            # Save token type
            if "token_type" in credentials:
                keyring.set_password(self.service, self.TOKEN_TYPE_KEY, credentials["token_type"])
                
        except keyring.errors.KeyringError as e:
            logger.error(f"Failed to save credentials: {e}")
            raise

    def get_access_token(self) -> Optional[str]:
        """Get access token.
        
        Returns:
            Access token or None.
        """
        try:
            return keyring.get_password(self.service, self.ACCESS_TOKEN_KEY)
        except keyring.errors.KeyringError as e:
            logger.error(f"Keyring error getting access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {e}")
            return None

    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token.
        
        Returns:
            Refresh token or None.
        """
        try:
            return keyring.get_password(self.service, self.REFRESH_TOKEN_KEY)
        except keyring.errors.KeyringError as e:
            logger.error(f"Keyring error getting refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting refresh token: {e}")
            return None

    def get_resource_url(self) -> Optional[str]:
        """Get resource URL (DashScope API endpoint).
        
        Returns:
            Resource URL or None.
        """
        try:
            return keyring.get_password(self.service, self.RESOURCE_URL_KEY)
        except keyring.errors.KeyringError as e:
            logger.error(f"Keyring error getting resource URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting resource URL: {e}")
            return None

    def get_token_expiry(self) -> Optional[datetime]:
        """Get token expiry time.
        
        Returns:
            Expiry datetime or None.
        """
        try:
            expiry_str = keyring.get_password(self.service, self.EXPIRY_KEY)
            if expiry_str:
                return datetime.fromisoformat(expiry_str)
        except keyring.errors.KeyringError as e:
            logger.error(f"Keyring error getting token expiry: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid expiry format: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting token expiry: {e}")
            return None
        return None

    def get_all_credentials(self) -> Dict[str, Any]:
        """Get all credentials as dict (same as qwen-code).
        
        Returns:
            Credentials dict with all fields.
        """
        return {
            "access_token": self.get_access_token(),
            "refresh_token": self.get_refresh_token(),
            "resource_url": self.get_resource_url(),
            "token_type": self.get_token_type(),
            "expiry_date": self.get_token_expiry(),
        }

    def get_token_type(self) -> Optional[str]:
        """Get token type.
        
        Returns:
            Token type or None.
        """
        try:
            return keyring.get_password(self.service, self.TOKEN_TYPE_KEY)
        except keyring.errors.KeyringError as e:
            logger.error(f"Keyring error getting token type: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting token type: {e}")
            return None

    def clear_credentials(self) -> None:
        """Clear all stored credentials."""
        keys = [
            self.ACCESS_TOKEN_KEY,
            self.REFRESH_TOKEN_KEY,
            self.EXPIRY_KEY,
            self.RESOURCE_URL_KEY,
            self.TOKEN_TYPE_KEY,
        ]
        
        for key in keys:
            try:
                keyring.delete_password(self.service, key)
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            except keyring.errors.KeyringError as e:
                logger.error(f"Keyring error deleting {key}: {e}")
