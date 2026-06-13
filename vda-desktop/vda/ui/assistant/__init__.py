"""Floating assistant sub-package — chat controller, worker, message bubbles, and history popup."""

from vda.ui.assistant.chat_popup import ChatHistoryPopup
from vda.ui.assistant.controller import FloatingAssistant
from vda.ui.assistant.message_bubble import MessageBubble
from vda.ui.assistant.worker import APIServerWorker

__all__ = ["APIServerWorker", "MessageBubble", "ChatHistoryPopup", "FloatingAssistant"]
