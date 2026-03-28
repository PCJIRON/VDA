"""
Qwen OAuth 2.0 Device Flow with PKCE.

Exact copy of qwen-code implementation:
packages/core/src/qwen/qwenOAuth2.ts
"""

import base64
import hashlib
import json
import secrets
import time
import webbrowser
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx


def generate_code_verifier() -> str:
    """Generate PKCE code verifier (random 32 bytes)."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge from verifier using SHA-256."""
    code_challenge = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(code_challenge).decode().rstrip('=')


class QwenDeviceFlow:
    """Qwen OAuth 2.0 Device Flow with PKCE authentication."""
    
    # Qwen OAuth configuration (EXACT from qwen-code)
    CLIENT_ID = "f0304373b74a44d2b584a3fb70ca9e56"
    BASE_URL = "https://chat.qwen.ai"
    DEVICE_CODE_ENDPOINT = f"{BASE_URL}/api/v1/oauth2/device/code"
    TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/oauth2/token"
    SCOPE = "openid profile email model.completion"
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
    
    def __init__(self):
        self.code_verifier = generate_code_verifier()
        self.code_challenge = generate_code_challenge(self.code_verifier)
        
        self.device_code: Optional[str] = None
        self.user_code: Optional[str] = None
        self.verification_uri: Optional[str] = None
        self.verification_uri_complete: Optional[str] = None
        self.expires_in: int = 0
        self.interval: int = 5
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.id_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    def request_device_code(self) -> bool:
        """Request device authorization code with PKCE."""
        try:
            # Use httpx Client with browser-like headers to bypass WAF
            with httpx.Client(
                follow_redirects=True,
                timeout=30,
            ) as client:
                # Set browser-like headers
                client.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                })
                
                print(f"📡 POST {self.DEVICE_CODE_ENDPOINT}")
                response = client.post(
                    self.DEVICE_CODE_ENDPOINT,
                    data={
                        "client_id": self.CLIENT_ID,
                        "scope": self.SCOPE,
                        "code_challenge": self.code_challenge,
                        "code_challenge_method": "S256",
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "x-request-id": secrets.token_hex(16),
                    },
                )
                print(f"📥 Response: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"📄 Content: {response.text[:300]}")
                    return False
                
                data = response.json()
            
            # Check for error response
            if "error" in data:
                print(f"❌ Error: {data['error']} - {data.get('error_description', 'Unknown error')}")
                return False
            
            # Store device authorization data
            self.device_code = data.get("device_code")
            self.user_code = data.get("user_code")
            self.verification_uri = data.get("verification_uri")
            self.verification_uri_complete = data.get("verification_uri_complete")
            self.expires_in = data.get("expires_in", 900)
            self.interval = data.get("interval", 5)
            
            print(f"✅ Device code received")
            return True
            
        except Exception as e:
            print(f"❌ Failed to request device code: {e}")
            return False
    
    def open_browser(self) -> None:
        """Open browser for user authorization."""
        if self.verification_uri_complete:
            print(f"\n🌐 Opening browser...")
            print(f"URL: {self.verification_uri_complete}")
            webbrowser.open(self.verification_uri_complete)
        elif self.verification_uri:
            print(f"\n🌐 Go to: {self.verification_uri}")
            print(f"📝 Enter code: {self.user_code}")
            webbrowser.open(self.verification_uri)
    
    def poll_for_token(self) -> bool:
        """Poll for access token."""
        if not self.device_code:
            return False
        
        start_time = time.time()
        timeout = self.expires_in
        poll_interval = 2  # 2 seconds (matches qwen-code)
        
        print(f"\n⏳ Waiting for authorization...")
        print(f"Enter code {self.user_code} at {self.verification_uri}")
        
        # Use httpx Client with browser-like headers
        with httpx.Client(
            follow_redirects=True,
            timeout=30,
        ) as client:
            # Set browser-like headers
            client.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            })
            
            while time.time() - start_time < timeout:
                time.sleep(poll_interval)
                
                try:
                    print(".", end="", flush=True)
                    response = client.post(
                        self.TOKEN_ENDPOINT,
                        data={
                            "grant_type": self.GRANT_TYPE,
                            "client_id": self.CLIENT_ID,
                            "device_code": self.device_code,
                            "code_verifier": self.code_verifier,
                        },
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "x-request-id": secrets.token_hex(16),
                        },
                    )

                    if response.status_code != 200:
                        print(f"\n📥 HTTP {response.status_code}: {response.text[:100]}")
                        continue

                    data = response.json()

                    # Check for error - NOW INSIDE TRY BLOCK
                    if "error" in data:
                        error = data["error"]
                        if error == "authorization_pending":
                            print(".", end="", flush=True)
                            continue  # Keep polling
                        elif error == "slow_down":
                            poll_interval = min(int(poll_interval * 1.5), 10000)
                            print(f"\n⏱️  Slowing down (interval: {poll_interval}ms)")
                            continue
                        elif error == "expired_token":
                            print("\n❌ Authorization expired. Please try again.")
                            return False
                        elif error == "access_denied":
                            print("\n❌ Authorization denied. Please try again.")
                            return False
                        else:
                            print(f"\n❌ Error: {error} - {data.get('error_description', 'Unknown error')}")
                            return False

                    # Success! Store tokens
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.id_token = data.get("id_token")

                    # Calculate expiry
                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

                    print("\n\n✅ Authentication successful!")
                    return True

            except Exception as e:
                print(f"\n❌ Polling failed: {e}")
                continue
        
        print("\n❌ Authorization timeout. Please try again.")
        return False
    
    def authenticate(self) -> bool:
        """Complete authentication flow."""
        print("🔐 Requesting device authorization...")
        
        if not self.request_device_code():
            return False
        
        print(f"\n📱 Device Code: {self.device_code}")
        print(f"🔢 User Code: {self.user_code}")
        print(f"🌐 URL: {self.verification_uri}")
        
        # Open browser
        self.open_browser()
        
        # Poll for token
        return self.poll_for_token()
    
    def get_credentials(self) -> Dict[str, Any]:
        """Get authentication credentials."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None,
        }


if __name__ == "__main__":
    # Test authentication
    auth = QwenDeviceFlow()
    if auth.authenticate():
        print("\n📋 Credentials:")
        print(json.dumps(auth.get_credentials(), indent=2))
    else:
        print("\n❌ Authentication failed")
