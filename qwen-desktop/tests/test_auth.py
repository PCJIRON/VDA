"""Tests for OAuth authentication."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from qwen_desktop.auth.oauth_handler import OAuthHandler
from qwen_desktop.auth.token_manager import TokenManager
from qwen_desktop.auth.credentials import Credentials


class TestCredentials:
    """Test credentials storage."""

    def test_save_and_get_access_token(self):
        """Test saving and retrieving access token."""
        creds = Credentials()
        creds.save_access_token("test_token_123")
        
        token = creds.get_access_token()
        assert token == "test_token_123"
        
        creds.clear_credentials()

    def test_save_and_get_refresh_token(self):
        """Test saving and retrieving refresh token."""
        creds = Credentials()
        creds.save_refresh_token("refresh_token_456")
        
        token = creds.get_refresh_token()
        assert token == "refresh_token_456"
        
        creds.clear_credentials()

    def test_clear_credentials(self):
        """Test clearing all credentials."""
        creds = Credentials()
        creds.save_access_token("access_token")
        creds.save_refresh_token("refresh_token")
        
        creds.clear_credentials()
        
        assert creds.get_access_token() is None
        assert creds.get_refresh_token() is None


class TestTokenManager:
    """Test token management."""

    def test_is_token_valid_no_token(self):
        """Test token validation with no token."""
        manager = TokenManager()
        
        # Clear any existing token
        manager.clear_tokens()
        
        assert not manager.is_token_valid()

    def test_save_and_get_tokens(self):
        """Test saving and retrieving tokens."""
        manager = TokenManager()
        
        token_data = {
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "expires_in": 3600,
        }
        
        manager.save_tokens(token_data)
        
        assert manager.get_access_token() == "access_123"
        assert manager.get_refresh_token() == "refresh_456"
        
        manager.clear_tokens()


class TestOAuthHandler:
    """Test OAuth handler."""

    def test_init_default_values(self):
        """Test OAuth handler initialization."""
        handler = OAuthHandler()

        assert handler.redirect_uri == "http://localhost:8080/callback"
        # Scopes is space-separated string for OAuth (not list)
        assert handler.scopes == "openid profile email model.completion"

    def test_is_authenticated_no_token(self):
        """Test authentication status with no token."""
        handler = OAuthHandler()
        
        # Clear any existing token
        handler.logout()
        
        assert not handler.is_authenticated()

    def test_logout_clears_tokens(self):
        """Test that logout clears tokens."""
        handler = OAuthHandler()
        
        # Save a token
        handler.token_manager.save_tokens({
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_in": 3600,
        })
        
        handler.logout()
        
        assert not handler.is_authenticated()
