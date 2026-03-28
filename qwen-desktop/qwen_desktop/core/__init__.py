"""Core module for API and conversation management."""

from qwen_desktop.core.api_client import APIClient
from qwen_desktop.core.conversation import Conversation, Message
from qwen_desktop.core.models import ModelInfo
from qwen_desktop.core.command_registry import CommandRegistry

__all__ = ["APIClient", "Conversation", "Message", "ModelInfo", "CommandRegistry"]
