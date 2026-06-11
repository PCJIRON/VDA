"""Safety utilities — FAILSAFE context manager and related automation safety helpers."""

import logging
from contextlib import contextmanager

import pyautogui

logger = logging.getLogger(__name__)


@contextmanager
def restore_failsafe():
    """Save pyautogui.FAILSAFE before entering block and restore it in finally."""
    original = pyautogui.FAILSAFE
    pyautogui.FAILSAFE = False
    try:
        yield
    finally:
        pyautogui.FAILSAFE = original
        logger.debug(f"FAILSAFE restored to {original}")


__all__ = ["restore_failsafe"]
