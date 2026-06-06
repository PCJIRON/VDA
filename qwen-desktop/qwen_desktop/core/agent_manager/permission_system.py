"""PermissionSystem — allow/deny/ask per tool, per agent type.

Full implementation added in Task 3. This placeholder exists so that
agent_manager.py can import and construct the subsystem reference
during incremental build.

The full system evaluates tool permissions against agent type config,
caches decisions per session, and returns ALLOW/DENY/ASK enum values.
"""

import enum
import logging
from typing import Any, Optional


logger = logging.getLogger(__name__)


class PermissionDecision(enum.Enum):
    """Three-state permission decision for tool access."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PermissionSystem:
    """Placeholder — evaluates allow/deny/ask per tool and agent type.

    Full implementation in Task 3 with AGENT_TYPES config-backed
    permission evaluation and per-session caching.
    """

    def __init__(self, settings: Optional[Any] = None) -> None:
        """Initialize permission system.

        Args:
            settings: Optional settings object for config-backed permissions.
        """
        self.settings = settings
        self._cache: dict[tuple, PermissionDecision] = {}

    def check_permission(
        self,
        tool_name: str,
        agent_type: str = "main",
        args: Optional[dict] = None,
    ) -> PermissionDecision:
        """Check if a tool call is allowed for the given agent type.

        Args:
            tool_name: Name of the tool being called.
            agent_type: Type of agent making the call.
            args: Arguments for the tool call (used for cache key).

        Returns:
            PermissionDecision.ALLOW, DENY, or ASK.
        """
        return PermissionDecision.ALLOW

    def cache_decision(
        self,
        tool_name: str,
        agent_type: str,
        args: Optional[dict],
        decision: PermissionDecision,
    ) -> None:
        """Cache a permission decision for the current session.

        Args:
            tool_name: Name of the tool.
            agent_type: Type of agent.
            args: Tool arguments (for cache key).
            decision: The permission decision to cache.
        """

    def clear_cache(self) -> None:
        """Reset all cached permission decisions."""
        self._cache.clear()
