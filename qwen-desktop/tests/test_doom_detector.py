"""Tests for the DoomLoopDetector.

Covers loop detection, false positive prevention for polling,
partial window behavior, history clearing, and window maxlen.
"""

import hashlib
import json

import pytest

from qwen_desktop.core.agent_manager.doom_detector import (
    DoomLoopDetector,
    ToolCallRecord,
)


class TestToolCallRecord:
    """Verify ToolCallRecord dataclass fields."""

    def test_dataclass_fields(self):
        """Verify all required fields exist."""
        record = ToolCallRecord(
            name="test_tool",
            args_hash="abc123",
            result_hash="def456",
            timestamp=1000.0,
        )
        assert record.name == "test_tool"
        assert record.args_hash == "abc123"
        assert record.result_hash == "def456"
        assert record.timestamp == 1000.0


class TestDoomLoopDetector:
    """Test doom loop detection and false positive prevention."""

    def test_detects_identical_calls(self):
        """Three identical (name+args+result) calls should trigger detection."""
        detector = DoomLoopDetector(threshold=3)
        for _ in range(3):
            detector.record_call("web_search", {"q": "test"}, "result_data")

        loop_info = detector.check_loop()
        assert loop_info is not None
        assert loop_info["tool"] == "web_search"
        assert loop_info["count"] == 3
        assert "first_at" in loop_info
        assert "last_at" in loop_info

    def test_polling_no_false_positive(self):
        """Same name+args but changing results should NOT trigger detection."""
        detector = DoomLoopDetector(threshold=3)
        for i in range(3):
            detector.record_call("web_search", {"q": "poll"}, f"result_{i}")

        loop_info = detector.check_loop()
        assert loop_info is None, "Polling with changing results should not be a loop"

    def test_partial_window_no_detection(self):
        """Fewer calls than threshold should not trigger detection."""
        detector = DoomLoopDetector(threshold=3)
        detector.record_call("terminal", {"cmd": "ls"}, "files")
        detector.record_call("terminal", {"cmd": "ls"}, "files")

        loop_info = detector.check_loop()
        assert loop_info is None

    def test_diff_args_no_detection(self):
        """Different args should not trigger detection."""
        detector = DoomLoopDetector(threshold=3)
        detector.record_call("web_search", {"q": "first"}, "result_a")
        detector.record_call("web_search", {"q": "second"}, "result_b")
        detector.record_call("web_search", {"q": "third"}, "result_c")

        loop_info = detector.check_loop()
        assert loop_info is None

    def test_clear_resets_history(self):
        """After clear(), check_loop() should return None."""
        detector = DoomLoopDetector(threshold=3)
        for _ in range(3):
            detector.record_call("web_search", {"q": "test"}, "result_data")

        assert detector.check_loop() is not None
        detector.clear()
        assert detector.check_loop() is None
        assert len(detector.history) == 0

    def test_window_maxlen(self):
        """Deque should cap at window_size (not grow indefinitely)."""
        detector = DoomLoopDetector(threshold=3, window_size=5)
        for i in range(10):
            detector.record_call("test_tool", {"i": i}, str(i))

        assert len(detector.history) == 5

    def test_detailed_loop_info(self):
        """Returned dict should have tool, count, first_at, last_at keys."""
        import time

        detector = DoomLoopDetector(threshold=3)
        start = time.time()
        for _ in range(3):
            detector.record_call("terminal", {"cmd": "ls"}, "output")
        end = time.time()

        loop_info = detector.check_loop()
        assert loop_info is not None
        assert "tool" in loop_info
        assert "count" in loop_info
        assert "first_at" in loop_info
        assert "last_at" in loop_info
        assert loop_info["count"] == 3
        assert start <= loop_info["first_at"] <= end
        assert start <= loop_info["last_at"] <= end

    def test_different_tool_no_detection(self):
        """Different tool names should not trigger detection."""
        detector = DoomLoopDetector(threshold=3)
        detector.record_call("web_search", {"q": "test"}, "result")
        detector.record_call("web_fetch", {"url": "test"}, "result")
        detector.record_call("terminal", {"cmd": "ls"}, "result")

        loop_info = detector.check_loop()
        assert loop_info is None

    def test_hash_deterministic(self):
        """_hash() should produce same output for same input regardless of key order."""
        h1 = DoomLoopDetector._hash({"b": 2, "a": 1})
        h2 = DoomLoopDetector._hash({"a": 1, "b": 2})
        assert h1 == h2

    def test_mixed_tool_within_window(self):
        """Mixed calls in window should not produce false detection."""
        detector = DoomLoopDetector(threshold=3)
        detector.record_call("web_search", {"q": "a"}, "r1")
        detector.record_call("web_search", {"q": "a"}, "r1")
        detector.record_call("terminal", {"cmd": "ls"}, "out")
        detector.record_call("web_search", {"q": "a"}, "r1")
        detector.record_call("web_search", {"q": "a"}, "r1")

        # Last 3 calls: [terminal, web_search, web_search] — not all same tool
        loop_info = detector.check_loop()
        assert loop_info is None, "Mixed call types should not trigger loop detection"
