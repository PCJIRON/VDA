"""Utilities module."""

from qwen_desktop.utils.logger import setup_logger
from qwen_desktop.utils.platform import get_platform, is_windows, is_macos, is_linux
from qwen_desktop.utils.file_encoder import encode_file, is_image_file, get_file_category

__all__ = [
    "setup_logger",
    "get_platform",
    "is_windows",
    "is_macos",
    "is_linux",
    "encode_file",
    "is_image_file",
    "get_file_category",
]
