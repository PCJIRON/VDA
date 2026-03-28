"""
Qwen OAuth authentication with GUI.

Exact copy of qwen-code flow:
1. Show auth dialog
2. User clicks "Login with Qwen"
3. Open browser to verification URL
4. Poll for token
5. Save credentials
"""

import json
import secrets
import hashlib
import base64
import time
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from qwen_desktop.auth.credentials import Credentials


def generate_code_verifier() -> str:
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge."""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip('=')


class QwenAuthDialog(QDialog):
    """Qwen OAuth authentication dialog."""
    
    # Qwen OAuth configuration (from qwen-code)
    CLIENT_ID = "f0304373b74a44d2b584a3fb70ca9e56"
    BASE_URL = "https://chat.qwen.ai"
    DEVICE_CODE_ENDPOINT = f"{BASE_URL}/api/v1/oauth2/device/code"
    TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/oauth2/token"
    SCOPE = "openid profile email model.completion"
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
    
    # Signals
    auth_success = pyqtSignal(dict)
    auth_failed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Qwen Desktop")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        # PKCE
        self.code_verifier = generate_code_verifier()
        self.code_challenge = generate_code_challenge(self.code_verifier)
        
        # OAuth state
        self.device_code: Optional[str] = None
        self.user_code: Optional[str] = None
        self.verification_uri: Optional[str] = None
        self.verification_uri_complete: Optional[str] = None
        self.expires_in: int = 900
        self.interval: int = 5
        
        # Tokens
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Polling
        self.poll_timer: Optional[QTimer] = None
        self.poll_start_time: float = 0
        self.poll_interval: int = 2000  # 2 seconds
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Login to Qwen Desktop")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Sign in with your Qwen account to access the AI assistant.\n"
            "You get 1,000 free requests per day."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        # Login button
        self.login_btn = QPushButton("Login with Qwen")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_btn)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setMaximum(0)
        layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Close button
        self.close_btn = QPushButton("Cancel")
        self.close_btn.clicked.connect(self.reject)
        layout.addWidget(self.close_btn)
    
    def _apply_styles(self):
        """Apply styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton#closeBtn {
                background-color: #f0f0f0;
                color: #333;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
            }
        """)
        self.close_btn.setObjectName("closeBtn")
    
    def _on_login_clicked(self):
        """Handle login button click."""
        self.login_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Requesting authorization...")
        
        # Start device code request
        self._request_device_code()
    
    def _request_device_code(self):
        """Request device authorization code."""
        try:
            with httpx.Client(follow_redirects=True, timeout=30) as client:
                client.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                })
                
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
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text[:100]}")
                
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"{data['error']}: {data.get('error_description', 'Unknown error')}")
                
                # Store device auth data
                self.device_code = data.get("device_code")
                self.user_code = data.get("user_code")
                self.verification_uri = data.get("verification_uri")
                self.verification_uri_complete = data.get("verification_uri_complete")
                self.expires_in = data.get("expires_in", 900)
                
                # Open browser
                self._open_browser()
                
                # Start polling
                self._start_polling()
                
        except Exception as e:
            self._on_auth_failed(f"Failed to request authorization: {e}")
    
    def _open_browser(self):
        """Open browser for user authorization."""
        url = self.verification_uri_complete or self.verification_uri
        if url:
            self.status_label.setText(f"Opening browser...\nEnter code {self.user_code} if prompted")
            webbrowser.open(url)
    
    def _start_polling(self):
        """Start polling for access token."""
        self.status_label.setText("Waiting for authorization...")
        self.poll_start_time = time.time()
        
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_for_token)
        self.poll_timer.start(self.poll_interval)
    
    def _poll_for_token(self):
        """Poll for access token."""
        # Check timeout
        elapsed = time.time() - self.poll_start_time
        if elapsed > self.expires_in:
            self._on_auth_failed("Authorization timeout")
            return
        
        try:
            with httpx.Client(follow_redirects=True, timeout=30) as client:
                client.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                })
                
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
                    # Check for error response
                    try:
                        data = response.json()
                        error = data.get("error", "")
                        
                        if error == "authorization_pending":
                            # Keep polling
                            return
                        elif error == "slow_down":
                            self.poll_interval = min(int(self.poll_interval * 1.5), 10000)
                            self.poll_timer.setInterval(self.poll_interval)
                            return
                        elif error == "expired_token":
                            self._on_auth_failed("Authorization expired")
                            return
                        elif error == "access_denied":
                            self._on_auth_failed("Authorization denied")
                            return
                        else:
                            self._on_auth_failed(f"Error: {error}")
                            return
                    except Exception as e:
                        self._on_auth_failed(f"JSON parse error: {e}")
                        return
                
                # Success!
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                # Save credentials with resource_url (same as qwen-code)
                credentials = {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": data.get("token_type", "Bearer"),
                    "expiry_date": int(self.token_expiry.timestamp() * 1000),  # Convert to milliseconds
                    "resource_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                }
                self._save_credentials_secure(credentials)

                self._on_auth_success()
                
        except Exception as e:
            self._on_auth_failed(f"Polling failed: {e}")
    
    def _on_auth_success(self):
        """Handle authentication success."""
        if self.poll_timer:
            self.poll_timer.stop()

        self.status_label.setText("✅ Authentication successful!")
        self.progress.setVisible(False)

        # Emit success signal
        credentials = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None,
        }
        self.auth_success.emit(credentials)

        # Save credentials to secure keyring
        self._save_credentials_secure(credentials)

        # Close dialog after short delay
        QTimer.singleShot(1500, self.accept)

    def _save_credentials_secure(self, credentials: dict):
        """Save credentials to secure keyring storage (same as qwen-code)."""
        creds = Credentials()
        creds.save_credentials(credentials)

    def _on_auth_failed(self, message: str):
        """Handle authentication failure."""
        if self.poll_timer:
            self.poll_timer.stop()

        self.progress.setVisible(False)
        self.login_btn.setEnabled(True)
        self.status_label.setText(f"❌ {message}")
        self.auth_failed.emit(message)

    def get_credentials(self) -> dict:
        """Get authentication credentials."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry,
        }
