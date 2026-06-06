"""Shim module — re-exports from ui.assistant sub-package.

This file exists for backward compatibility. New code should import
directly from qwen_desktop.ui.assistant.
"""

from qwen_desktop.ui.assistant import FloatingAssistant, APIServerWorker, MessageBubble, ChatHistoryPopup  # noqa: F401

__all__ = ["FloatingAssistant", "APIServerWorker", "MessageBubble", "ChatHistoryPopup"]
