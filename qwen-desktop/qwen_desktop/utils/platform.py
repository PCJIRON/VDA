"""
Platform detection utilities.

Provides functions to detect the current operating system.
"""

import sys
from typing import Literal


Platform = Literal["windows", "macos", "linux", "other"]


def get_platform() -> Platform:
    """Get the current platform name.
    
    Returns:
        Platform name: 'windows', 'macos', 'linux', or 'other'.
    """
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return "other"


def is_windows() -> bool:
    """Check if running on Windows.
    
    Returns:
        True if Windows, False otherwise.
    """
    return sys.platform.startswith("win")


def is_macos() -> bool:
    """Check if running on macOS.
    
    Returns:
        True if macOS, False otherwise.
    """
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux.
    
    Returns:
        True if Linux, False otherwise.
    """
    return sys.platform.startswith("linux")
