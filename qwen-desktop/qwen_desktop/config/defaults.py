"""
Default settings for Qwen Desktop.

Contains all default configuration values.
"""

from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    # API Configuration - Qwen OAuth uses DashScope API (same as qwen-code)
    # OAuth token is used as API key with OpenAI SDK
    "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_model": "qwen-coder-plus",
    "api_timeout": 60,
    
    # OAuth Configuration
    "oauth_client_id": "",
    "oauth_client_secret": "",
    "oauth_redirect_uri": "http://localhost:8080/callback",
    "oauth_scopes": ["openid", "email", "profile"],
    
    # UI Configuration
    "theme": "dark",
    "font_size": 12,
    "window_width": 1200,
    "window_height": 800,
    
    # File Attachments
    "max_file_size_mb": 10,
    "max_attachments": 10,
    "allowed_extensions": [
        # Code files
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp",
        ".cs", ".php", ".rb", ".swift", ".kt", ".scala",
        # Config files
        ".json", ".yaml", ".yml", ".toml", ".ini", ".xml",
        # Documents
        ".md", ".txt", ".rst", ".html", ".css",
        # Images (for multimodal)
        ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ],
    
    # Application
    "check_for_updates": True,
    "send_analytics": False,
    "auto_save_conversations": True,
}

# OAuth endpoints (Qwen/Google OAuth)
OAUTH_ENDPOINTS = {
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
}
