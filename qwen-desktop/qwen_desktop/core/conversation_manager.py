"""
Conversation manager for persistence.

Handles saving and loading conversations to/from disk.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from qwen_desktop.core.conversation import Conversation


class ConversationManager:
    """Manages conversation persistence."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize conversation manager.
        
        Args:
            storage_path: Path to store conversations.
        """
        if storage_path is None:
            # Default to user's home directory
            from qwen_desktop.utils.platform import is_windows, is_macos, is_linux
            
            if is_windows():
                base = Path.home() / "AppData" / "Local" / "Qwen" / "Qwen Desktop"
            elif is_macos():
                base = Path.home() / "Library" / "Preferences" / "Qwen"
            elif is_linux():
                base = Path.home() / ".config" / "qwen-desktop"
            else:
                base = Path.home() / ".qwen-desktop"
            
            storage_path = base / "conversations"
        
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_conversation(self, conv: Conversation) -> Path:
        """Save a conversation to disk.
        
        Args:
            conv: Conversation to save.
            
        Returns:
            Path to saved file.
        """
        # Generate filename from conversation ID and timestamp
        timestamp = conv.updated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{conv.id}_{timestamp}.json"
        filepath = self.storage_path / filename
        
        # Save as JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conv.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath

    def load_conversation(self, filepath: Path) -> Optional[Conversation]:
        """Load a conversation from disk.
        
        Args:
            filepath: Path to conversation file.
            
        Returns:
            Loaded conversation or None.
        """
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return Conversation.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading conversation: {e}")
            return None

    def list_conversations(self) -> List[dict]:
        """List all saved conversations.
        
        Returns:
            List of conversation metadata (id, title, updated_at, filepath).
        """
        conversations = []
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                conversations.append({
                    "id": data.get("id", ""),
                    "title": data.get("title", "Untitled"),
                    "updated_at": data.get("updated_at", ""),
                    "model": data.get("model", "qwen-coder"),
                    "filepath": str(filepath),
                    "message_count": len(data.get("messages", [])),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return conversations

    def delete_conversation(self, filepath: Path) -> bool:
        """Delete a conversation.
        
        Args:
            filepath: Path to conversation file.
            
        Returns:
            True if deleted successfully.
        """
        try:
            filepath.unlink()
            return True
        except OSError:
            return False

    def get_recent_conversations(self, limit: int = 10) -> List[dict]:
        """Get most recent conversations.
        
        Args:
            limit: Maximum number to return.
            
        Returns:
            List of conversation metadata.
        """
        return self.list_conversations()[:limit]

    def search_conversations(self, query: str) -> List[dict]:
        """Search conversations by title.
        
        Args:
            query: Search query.
            
        Returns:
            List of matching conversation metadata.
        """
        all_convs = self.list_conversations()
        query_lower = query.lower()
        
        return [
            conv for conv in all_convs
            if query_lower in conv["title"].lower()
        ]
