"""Utilities module."""

from qwen_desktop.utils.logger import setup_logger
from qwen_desktop.utils.platform import get_platform, is_windows, is_macos, is_linux
from qwen_desktop.utils.screen import ScreenEnv, ScreenDetector
from qwen_desktop.utils.safety import restore_failsafe

__all__ = [
    "setup_logger",
    "get_platform",
    "is_windows",
    "is_macos",
    "is_linux",
    "ScreenEnv",
    "ScreenDetector",
    "restore_failsafe",
]
