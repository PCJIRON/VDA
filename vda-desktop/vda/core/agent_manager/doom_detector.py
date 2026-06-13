"""DoomLoopDetector — detects 3+ identical consecutive tool calls.

Uses a rolling deque window to compare the (name, args_hash, result_hash)
triple of recent tool calls. When threshold identical calls are found,
returns loop info so the AgentManager can pause execution.

Result-hash comparison distinguishes real loops from legitimate polling
(where args stay the same but results change).
"""

import hashlib
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """Record of a single tool call for doom loop analysis.

    Attributes:
        name: Name of the tool that was called.
        args_hash: MD5 hash of the serialized arguments.
        result_hash: MD5 hash of the result string.
        timestamp: Unix timestamp when the call was recorded.
    """

    name: str
    args_hash: str
    result_hash: str
    timestamp: float = field(default_factory=time.time)


class DoomLoopDetector:
    """Detects 3+ identical consecutive tool calls and triggers pause.

    Uses a fixed-size rolling window (collections.deque) of recent tool call
    records. On each check, compares the last N entries for identical
    (name, args_hash, result_hash) triples.

    Args:
        threshold: Number of identical consecutive calls to detect a loop.
        window_size: Maximum rolling window size (deque maxlen).
    """

    def __init__(self, threshold: int = 3, window_size: int = 10) -> None:
        self.threshold = threshold
        self.history: deque[ToolCallRecord] = deque(maxlen=window_size)

    @staticmethod
    def _hash(obj: dict) -> str:
        """Deterministic MD5 hash of a JSON-serializable dict.

        Sorts keys for consistent hashing across calls with the same
        logical content but different key ordering.

        Args:
            obj: Dictionary to hash.

        Returns:
            MD5 hex digest string.
        """
        return hashlib.md5(
            json.dumps(obj, sort_keys=True, default=str).encode()
        ).hexdigest()

    def record_call(self, tool_name: str, args: dict, result: str) -> None:
        """Record a tool call for doom loop analysis.

        Creates a ToolCallRecord from the call's name, hashed args, hashed
        result, and current timestamp. Appends to the rolling window.

        Args:
            tool_name: Name of the tool called.
            args: Arguments passed to the tool.
            result: Result string returned by the tool.
        """
        record = ToolCallRecord(
            name=tool_name,
            args_hash=self._hash(args),
            result_hash=self._hash({"result": result[:1000]}),
            timestamp=time.time(),
        )
        self.history.append(record)
        logger.debug("[Doom] Recorded: %s args=%s", tool_name, record.args_hash[:8])

    def check_loop(self) -> Optional[dict]:
        """Check if the most recent calls form a doom loop.

        Compares the last ``threshold`` calls for identical name, args_hash,
        AND result_hash. If results differ (even with same args), it's
        considered legitimate polling — not a loop.

        Returns:
            Dict with keys (tool, count, first_at, last_at) if a loop is
            detected, or None if threshold not reached or no loop found.
        """
        if len(self.history) < self.threshold:
            return None

        recent = list(self.history)[-self.threshold:]

        # Check: all same tool, all same args
        first = recent[0]
        for record in recent[1:]:
            if record.name != first.name:
                return None
            if record.args_hash != first.args_hash:
                return None

        # Check: results are also identical (or failed identically)
        # If results differ, it's polling, not a loop
        if not all(r.result_hash == first.result_hash for r in recent):
            return None

        logger.warning(
            "[Doom] Loop detected: %s called %dx with same args+result",
            first.name,
            self.threshold,
        )
        return {
            "tool": first.name,
            "count": self.threshold,
            "first_at": recent[0].timestamp,
            "last_at": recent[-1].timestamp,
        }

    def clear(self) -> None:
        """Clear all recorded tool call history."""
        self.history.clear()
        logger.debug("[Doom] History cleared")
