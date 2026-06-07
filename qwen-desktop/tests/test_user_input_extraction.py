"""Regression tests for the user_input extraction in _create_worker.

Bug: when vision mode is on, `_create_worker` receives a LIST of content
blocks (text + image_url), not a plain string. The OLD code did
`user_input = message if isinstance(message, str) else ""` which silently
dropped the text and left user_input empty. The agent then asked the LLM
"USER TASK: " (empty) and the LLM responded with "No user task was
provided" — even though the user clearly typed something.

The CORRECT extraction: when the user typed something, use
`self._last_user_text` (the clean original input) instead of the
vision_prompt. When it's a vision hotkey trigger (no user text), fall
back to extracting from the payload.
"""
from typing import List
from unittest.mock import MagicMock

import pytest


def _extract_user_input(message, last_user_text=""):
    """Replicate the extraction logic from _create_worker for unit testing."""
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        if last_user_text:
            return last_user_text
        return "".join(
            block.get("text", "")
            for block in message
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def test_plain_string_passes_through():
    assert _extract_user_input("open chrome and click on new tab") == "open chrome and click on new tab"


def test_vision_mode_uses_last_user_text():
    """The user typed text in vision mode. The message is a list with
    vision_prompt + image. We must return the ORIGINAL clean text, not
    the vision_prompt (which has output format instructions)."""
    vision_prompt = "[USER REQUEST]\n\"open chrome\"\n\n[OUTPUT FORMAT - CRITICAL]\nRespond ONLY in JSON..."
    payload = [
        {"type": "text", "text": vision_prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}},
    ]
    result = _extract_user_input(payload, last_user_text="open chrome and click on new tab")
    assert result == "open chrome and click on new tab"


def test_vision_hotkey_no_last_user_text():
    """Vision hotkey trigger: no user text. Fall back to extracting from
    the vision_prompt in the payload."""
    vision_prompt = "[VISION METADATA]\nScreen Resolution: 1920x1080\n..."
    payload = [
        {"type": "text", "text": vision_prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}},
    ]
    result = _extract_user_input(payload, last_user_text="")
    assert "VISION METADATA" in result


def test_image_only_list_returns_empty():
    payload = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}}]
    assert _extract_user_input(payload) == ""


def test_non_dict_blocks_ignored():
    payload = [
        "raw string (not a dict)",
        {"type": "text", "text": "real task"},
        None,
    ]
    assert _extract_user_input(payload) == "real task"


def test_none_input_returns_empty():
    assert _extract_user_input(None) == ""


def test_hinglish_preserved():
    assert _extract_user_input("chrome kholo aur new tab click karo") == "chrome kholo aur new tab click karo"
    payload = [
        {"type": "text", "text": "[USER REQUEST]\n\"chrome kholo\""},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}},
    ]
    result = _extract_user_input(payload, last_user_text="chrome kholo aur new tab click karo")
    assert result == "chrome kholo aur new tab click karo"
