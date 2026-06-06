"""Tests for safety utilities — FAILSAFE context manager."""

from unittest.mock import patch

import pyautogui

from qwen_desktop.utils.safety import restore_failsafe


class TestRestoreFailsafe:
    def test_saves_and_restores_failsafe(self):
        original = pyautogui.FAILSAFE
        with restore_failsafe():
            assert pyautogui.FAILSAFE is False
        assert pyautogui.FAILSAFE == original

    def test_restores_on_exception(self):
        original = pyautogui.FAILSAFE
        try:
            with restore_failsafe():
                assert pyautogui.FAILSAFE is False
                raise ValueError("test error")
        except ValueError:
            pass
        assert pyautogui.FAILSAFE == original

    def test_nested_context_managers(self):
        original = pyautogui.FAILSAFE
        with restore_failsafe():
            assert pyautogui.FAILSAFE is False
            with restore_failsafe():
                assert pyautogui.FAILSAFE is False
            assert pyautogui.FAILSAFE is False
        assert pyautogui.FAILSAFE == original

    def test_restores_when_failsafe_was_true(self):
        pyautogui.FAILSAFE = True
        with restore_failsafe():
            assert pyautogui.FAILSAFE is False
        assert pyautogui.FAILSAFE is True
