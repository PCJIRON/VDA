"""
Conversation management.

Handles conversation history and message storage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Message:
    """Represents a single message in a conversation."""

    content: str
    role: str  # "user", "assistant", or "system"
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attachments: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert message to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "attachments": self.attachments,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create message from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            Message instance.
        """
        return cls(
            content=data["content"],
            role=data["role"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            id=data.get("id", str(uuid.uuid4())),
            attachments=data.get("attachments", []),
        )


@dataclass
class Conversation:
    """Represents a conversation session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    model: str = "qwen-coder"

    def add_message(
        self,
        content: str,
        role: str,
        attachments: Optional[list[dict]] = None,
    ) -> Message:
        """Add a message to the conversation.
        
        Args:
            content: Message content.
            role: Message role.
            attachments: Optional attachments.
            
        Returns:
            The created message.
        """
        message = Message(
            content=content,
            role=role,
            attachments=attachments or [],
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Update title from first user message
        if role == "user" and len(self.messages) == 1:
            self.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return message

    def get_messages_for_api(self) -> list[dict]:
        """Get messages formatted for API request.
        
        Returns:
            List of message dictionaries.
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert conversation to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model": self.model,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Create conversation from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            Conversation instance.
        """
        conv = cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "New Conversation"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            model=data.get("model", "qwen-coder"),
        )
        conv.messages = [
            Message.from_dict(msg) for msg in data.get("messages", [])
        ]
        return conv
