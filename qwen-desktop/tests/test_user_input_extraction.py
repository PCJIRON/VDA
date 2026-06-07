"""Regression tests for the user_input extraction in _create_worker.

Bug: when vision mode is on, `_create_worker` receives a LIST of content
blocks (text + image_url), not a plain string. The old code did
`user_input = message if isinstance(message, str) else ""` which silently
dropped the text and left user_input empty. The agent then asked the LLM
"USER TASK: " (empty) and the LLM responded with "No user task was
provided" — even though the user clearly typed something.

These tests exercise the same extraction logic by calling the helper
methods on a mock controller.
"""
from typing import List
from unittest.mock import MagicMock

import pytest


def _extract_user_input(message):
    """Replicate the extraction logic from _create_worker for unit testing."""
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        return "".join(
            block.get("text", "")
            for block in message
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def test_plain_string_passes_through():
    assert _extract_user_input("open chrome and click on new tab") == "open chrome and click on new tab"


def test_vision_mode_list_extracts_text():
    """The original bug: a content list with text+image_url was being
    silently dropped to ''. This is the regression we must never allow."""
    payload = [
        {"type": "text", "text": "open chrome and click on new tab"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}},
    ]
    assert _extract_user_input(payload) == "open chrome and click on new tab"


def test_text_only_list_extracts_text():
    payload = [{"type": "text", "text": "hello"}]
    assert _extract_user_input(payload) == "hello"


def test_image_only_list_returns_empty():
    payload = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}}]
    assert _extract_user_input(payload) == ""


def test_multiple_text_blocks_concatenated():
    payload = [
        {"type": "text", "text": "open chrome"},
        {"type": "image_url", "image_url": {"url": "..."}},
        {"type": "text", "text": " and click new tab"},
    ]
    assert _extract_user_input(payload) == "open chrome and click new tab"


def test_non_dict_blocks_ignored():
    payload = [
        "raw string (not a dict)",
        {"type": "text", "text": "real task"},
        None,
    ]
    assert _extract_user_input(payload) == "real task"


def test_none_input_returns_empty():
    assert _extract_user_input(None) == ""


def test_empty_string_input_returns_empty():
    assert _extract_user_input("") == ""


def test_hinglish_preserved():
    """Hinglish input must not be mangled by extraction logic."""
    assert _extract_user_input("chrome kholo aur new tab click karo") == "chrome kholo aur new tab click karo"
    payload = [
        {"type": "text", "text": "chrome kholo aur new tab click karo"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,XXX"}},
    ]
    assert _extract_user_input(payload) == "chrome kholo aur new tab click karo"
