"""
Data models for Qwen Desktop.

Contains dataclasses and types used throughout the application.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    """Information about an AI model."""

    id: str
    name: str
    description: str = ""
    max_tokens: int = 8192
    supports_vision: bool = False
    supports_function_calling: bool = False

    @classmethod
    def get_default_models(cls) -> list["ModelInfo"]:
        """Get list of default Qwen models.
        
        Returns:
            List of model info.
        """
        return [
            cls(
                id="qwen-coder",
                name="Qwen Coder",
                description="Optimized for coding tasks",
                max_tokens=8192,
                supports_vision=False,
                supports_function_calling=True,
            ),
            cls(
                id="qwen-plus",
                name="Qwen Plus",
                description="Balanced performance and capability",
                max_tokens=8192,
                supports_vision=True,
                supports_function_calling=True,
            ),
            cls(
                id="qwen-max",
                name="Qwen Max",
                description="Most capable model",
                max_tokens=8192,
                supports_vision=True,
                supports_function_calling=True,
            ),
        ]


@dataclass
class UserInfo:
    """User account information."""

    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    
    @classmethod
    def from_oauth_response(cls, data: dict) -> "UserInfo":
        """Create UserInfo from OAuth response.
        
        Args:
            data: OAuth response data.
            
        Returns:
            UserInfo instance.
        """
        return cls(
            id=data.get("sub", ""),
            email=data.get("email", ""),
            name=data.get("name", ""),
            avatar_url=data.get("picture"),
        )


@dataclass
class TokenUsage:
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @classmethod
    def from_api_response(cls, data: dict) -> "TokenUsage":
        """Create TokenUsage from API response.
        
        Args:
            data: Usage data from API.
            
        Returns:
            TokenUsage instance.
        """
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )
