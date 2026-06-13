"""Shim module — re-exports from ui.assistant sub-package.

This file exists for backward compatibility. New code should import
directly from vda.ui.assistant.
"""

from vda.ui.assistant import (  # noqa: F401
    APIServerWorker,
    ChatHistoryPopup,
    FloatingAssistant,
    MessageBubble,
)

__all__ = ["FloatingAssistant", "APIServerWorker", "MessageBubble", "ChatHistoryPopup"]
