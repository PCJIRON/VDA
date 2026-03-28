"""
OAuth authentication handler for Qwen.

Handles the OAuth 2.0 flow for Qwen/Google authentication.
"""

import webbrowser
from typing import Optional
from urllib.parse import urlencode, parse_qs, urlparse
import secrets

from requests_oauthlib import OAuth2Session
import keyring

from qwen_desktop.auth.token_manager import TokenManager


class OAuthHandler:
    """Handles OAuth 2.0 authentication flow."""

    SERVICE_NAME = "qwen-desktop"
    TOKEN_KEY = "oauth_token"
    REFRESH_TOKEN_KEY = "oauth_refresh_token"

    # Qwen OAuth credentials (from qwen-code extension)
    # Source: packages/core/src/qwen/qwenOAuth2.ts
    QWEN_OAUTH_CLIENT_ID = "f0304373b74a44d2b584a3fb70ca9e56"
    QWEN_OAUTH_CLIENT_SECRET = ""  # Not required for device flow
    
    # Qwen OAuth endpoints (NOT Google OAuth directly)
    QWEN_BASE_URL = "https://chat.qwen.ai"
    AUTHORIZATION_URL = f"{QWEN_BASE_URL}/api/v1/oauth2/device/code"
    TOKEN_URL = f"{QWEN_BASE_URL}/api/v1/oauth2/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    REDIRECT_URI = "http://localhost:8080/callback"
    SCOPES = "openid profile email model.completion"
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scopes: Optional[list[str]] = None,
    ) -> None:
        """Initialize OAuth handler.
        
        Args:
            client_id: OAuth client ID (or set QWEN_OAUTH_CLIENT_ID env var).
            client_secret: OAuth client secret (or set QWEN_OAUTH_CLIENT_SECRET env var).
            redirect_uri: Redirect URI for callback.
            scopes: OAuth scopes.
        """
        import os
        
        # Get credentials from parameters or environment variables
        # Defaults to Qwen's official OAuth client (no need for personal credentials)
        self.client_id = client_id or os.getenv("QWEN_OAUTH_CLIENT_ID", self.QWEN_OAUTH_CLIENT_ID)
        self.client_secret = client_secret or os.getenv("QWEN_OAUTH_CLIENT_SECRET", self.QWEN_OAUTH_CLIENT_SECRET)
        self.redirect_uri = redirect_uri or self.REDIRECT_URI
        self.scopes = scopes or self.SCOPES
        
        # OAuth session
        self.oauth_session: Optional[OAuth2Session] = None
        
        # State for CSRF protection
        self.state: Optional[str] = None
        
        # Token storage
        self.token_manager = TokenManager()

    def start_auth_flow(self) -> Optional[str]:
        """Start the OAuth authentication flow.
        
        Returns:
            Authorization URL or None if failed.
        """
        try:
            # Generate state for CSRF protection
            self.state = secrets.token_urlsafe(32)
            
            # Create OAuth session
            self.oauth_session = OAuth2Session(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                state=self.state,
            )
            
            # Generate authorization URL
            authorization_url, _ = self.oauth_session.authorization_url(
                self.AUTHORIZATION_URL,
                access_type="offline",
                prompt="consent",
            )
            
            # Open browser
            webbrowser.open(authorization_url)
            
            return authorization_url
            
        except Exception as e:
            print(f"OAuth error: {e}")
            return None

    def handle_callback(self, callback_url: str) -> bool:
        """Handle OAuth callback.
        
        Args:
            callback_url: The callback URL from OAuth provider.
            
        Returns:
            True if successful.
        """
        if not self.oauth_session:
            return False
        
        try:
            # Parse callback URL
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            
            # Verify state
            if params.get("state", [None])[0] != self.state:
                raise ValueError("State mismatch - possible CSRF attack")
            
            # Check for error
            if "error" in params:
                raise ValueError(f"OAuth error: {params['error'][0]}")
            
            # Get authorization code
            code = params.get("code", [None])[0]
            if not code:
                raise ValueError("No authorization code received")
            
            # Exchange code for token
            token_response = self.oauth_session.fetch_token(
                self.TOKEN_URL,
                authorization_response=callback_url,
                client_secret=self.client_secret,
            )
            
            # Add resource_url to token data (same as qwen-code)
            token_response["resource_url"] = self.QWEN_BASE_URL
            
            # Store tokens
            self.token_manager.save_tokens(token_response)
            
            return True
            
        except Exception as e:
            print(f"Callback error: {e}")
            return False

    def get_user_info(self) -> Optional[dict]:
        """Get authenticated user information.
        
        Returns:
            User info dictionary or None.
        """
        token = self.token_manager.get_access_token()
        
        if not token:
            return None
        
        try:
            import httpx
            
            response = httpx.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Get user info error: {e}")
            return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.
        
        Returns:
            True if authenticated.
        """
        token = self.token_manager.get_access_token()
        return token is not None

    def logout(self) -> None:
        """Logout and clear tokens."""
        self.token_manager.clear_tokens()
        self.oauth_session = None
        self.state = None

    def refresh_token_if_needed(self) -> bool:
        """Refresh access token if expired.
        
        Returns:
            True if token was refreshed or still valid.
        """
        if not self.token_manager.is_token_valid():
            return self.token_manager.refresh_access_token(
                self.client_id,
                self.client_secret,
                self.TOKEN_URL,
            )
        return True
