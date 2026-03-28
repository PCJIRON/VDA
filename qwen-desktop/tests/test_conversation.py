"""Tests for conversation management."""

import pytest
from datetime import datetime

from qwen_desktop.core.conversation import Conversation, Message
from qwen_desktop.core.models import ModelInfo, UserInfo, TokenUsage


class TestMessage:
    """Test Message dataclass."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(content="Hello", role="user")
        
        assert msg.content == "Hello"
        assert msg.role == "user"
        assert msg.id is not None

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(content="Test", role="assistant")
        data = msg.to_dict()
        
        assert data["content"] == "Test"
        assert data["role"] == "assistant"
        assert "id" in data
        assert "timestamp" in data

    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "content": "Hello",
            "role": "user",
            "timestamp": "2024-01-01T12:00:00",
            "id": "test-id",
        }
        
        msg = Message.from_dict(data)
        
        assert msg.content == "Hello"
        assert msg.role == "user"
        assert msg.id == "test-id"


class TestConversation:
    """Test Conversation dataclass."""

    def test_create_conversation(self):
        """Test creating a conversation."""
        conv = Conversation()
        
        assert conv.title == "New Conversation"
        assert len(conv.messages) == 0
        assert conv.model == "qwen-coder"

    def test_add_message(self):
        """Test adding a message to conversation."""
        conv = Conversation()
        msg = conv.add_message("Hello", role="user")
        
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"
        assert conv.title == "Hello"

    def test_add_message_truncates_title(self):
        """Test that long first message truncates title."""
        conv = Conversation()
        long_message = "x" * 100
        conv.add_message(long_message, role="user")
        
        assert len(conv.title) == 53  # 50 + "..."

    def test_get_messages_for_api(self):
        """Test getting messages formatted for API."""
        conv = Conversation()
        conv.add_message("Hello", role="user")
        conv.add_message("Hi there!", role="assistant")
        
        messages = conv.get_messages_for_api()
        
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi there!"}

    def test_clear_conversation(self):
        """Test clearing conversation."""
        conv = Conversation()
        conv.add_message("Hello", role="user")
        
        conv.clear()
        
        assert len(conv.messages) == 0

    def test_conversation_to_dict(self):
        """Test converting conversation to dictionary."""
        conv = Conversation()  # Don't set title since first message will set it
        conv.add_message("Hello", role="user")
        
        data = conv.to_dict()
        
        assert data["title"] == "Hello"  # Title is set from first message
        assert len(data["messages"]) == 1

    def test_conversation_from_dict(self):
        """Test creating conversation from dictionary."""
        data = {
            "id": "test-id",
            "title": "Test Chat",
            "messages": [
                {"content": "Hello", "role": "user", "timestamp": "2024-01-01T12:00:00"}
            ],
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "model": "qwen-plus",
        }
        
        conv = Conversation.from_dict(data)
        
        assert conv.id == "test-id"
        assert conv.title == "Test Chat"
        assert len(conv.messages) == 1
        assert conv.model == "qwen-plus"


class TestModelInfo:
    """Test ModelInfo dataclass."""

    def test_get_default_models(self):
        """Test getting default models."""
        models = ModelInfo.get_default_models()
        
        assert len(models) == 3
        assert models[0].id == "qwen-coder"
        assert models[1].id == "qwen-plus"
        assert models[2].id == "qwen-max"

    def test_model_supports_vision(self):
        """Test vision support detection."""
        models = ModelInfo.get_default_models()
        
        coder = models[0]
        plus = models[1]
        
        assert not coder.supports_vision
        assert plus.supports_vision


class TestUserInfo:
    """Test UserInfo dataclass."""

    def test_from_oauth_response(self):
        """Test creating UserInfo from OAuth response."""
        oauth_data = {
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        }
        
        user = UserInfo.from_oauth_response(oauth_data)
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.jpg"


class TestTokenUsage:
    """Test TokenUsage dataclass."""

    def test_from_api_response(self):
        """Test creating TokenUsage from API response."""
        api_data = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }
        
        usage = TokenUsage.from_api_response(api_data)
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
