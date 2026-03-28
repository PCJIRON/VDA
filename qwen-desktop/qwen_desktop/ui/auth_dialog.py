"""Authentication dialog for OAuth login."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from qwen_desktop.auth.qwen_auth_gui import QwenAuthDialog as QwenAuthWidget


class AuthDialog(QDialog):
    """OAuth authentication dialog."""

    login_successful = pyqtSignal(dict)  # user_info

    def __init__(self, parent=None) -> None:
        """Initialize the auth dialog.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.setWindowTitle("Login to Qwen Desktop")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use the Qwen auth widget
        self.auth_widget = QwenAuthWidget(self)
        self.auth_widget.auth_success.connect(self._on_auth_success)
        self.auth_widget.auth_failed.connect(self._on_auth_failed)
        
        layout.addWidget(self.auth_widget)
    
    def _on_auth_success(self, credentials: dict):
        """Handle auth success."""
        self.login_successful.emit({
            "email": "authenticated@qwen.ai",
            "name": "Qwen User",
        })
        self.accept()
    
    def _on_auth_failed(self, error: str):
        """Handle auth failure."""
        # Keep dialog open, user can retry
        pass
