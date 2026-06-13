"""Utilities module."""

from vda.utils.logger import setup_logger
from vda.utils.platform import get_platform, is_linux, is_macos, is_windows
from vda.utils.safety import restore_failsafe
from vda.utils.screen import ScreenDetector, ScreenEnv

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
