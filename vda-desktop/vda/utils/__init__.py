"""Utilities module."""

from vda.utils.logger import setup_logger
from vda.utils.platform import get_platform, is_windows, is_macos, is_linux
from vda.utils.screen import ScreenEnv, ScreenDetector
from vda.utils.safety import restore_failsafe

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
