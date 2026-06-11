"""Floating assistant sub-package — chat controller, worker, message bubbles, and history popup."""

from qwen_desktop.ui.assistant.worker import APIServerWorker
from qwen_desktop.ui.assistant.message_bubble import MessageBubble
from qwen_desktop.ui.assistant.chat_popup import ChatHistoryPopup
from qwen_desktop.ui.assistant.controller import FloatingAssistant

__all__ = ["APIServerWorker", "MessageBubble", "ChatHistoryPopup", "FloatingAssistant"]
