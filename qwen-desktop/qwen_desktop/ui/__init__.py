"""UI module for Qwen Desktop."""

from qwen_desktop.ui.main_window import MainWindow
from qwen_desktop.ui.chat_widget import ChatWidget
from qwen_desktop.ui.input_area import InputArea
from qwen_desktop.ui.message_bubble import MessageBubble
from qwen_desktop.ui.theme_manager import ThemeManager

__all__ = [
    "MainWindow",
    "ChatWidget",
    "InputArea",
    "MessageBubble",
    "ThemeManager",
]
