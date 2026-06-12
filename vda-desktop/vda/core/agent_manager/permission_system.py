"""PermissionSystem — allow/deny/ask per tool, per agent type.

Evaluates tool permissions against AGENT_TYPES configuration, caches
decisions per session, and returns ALLOW/DENY/ASK enum values so the
UI layer can present inline prompts for ASK decisions.

Default hierarchy:
  1. Check session cache first.
  2. Look up tool in AGENT_TYPES[agent_type] config.
  3. Classify tool as read/mutation/destructive.
  4. Apply permission_defaults from agent type config.
  5. Unknown tools default to ASK.
"""

import enum
import logging
from typing import Any, Optional


logger = logging.getLogger(__name__)


try:
    from vda.config.defaults import AGENT_TYPES
except ImportError:
    AGENT_TYPES: dict[str, Any] = {}


class PermissionDecision(enum.Enum):
    """Three-state permission decision for tool access.

    ALLOW: Tool execution permitted without user prompt.
    DENY: Tool execution blocked without user prompt.
    ASK: User must explicitly approve this tool call.
    """

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PermissionSystem:
    """Evaluates allow/deny/ask per tool, per agent type.

    Permissions are evaluated against AGENT_TYPES configuration which
    defines which tools each agent type can use and their default
    permission policies (allow_read, ask_mutation, deny_destructive).

    Permission decisions are cached per session (keyed by agent_type,
    tool_name, and args_hash) to avoid repeated prompts.

    Args:
        settings: Optional settings object/dict. If provided, AGENT_TYPES
            is read from settings["agent_types"]; otherwise the module-level
            AGENT_TYPES constant from defaults.py is used.
    """

    def __init__(self, settings: Optional[Any] = None) -> None:
        self._settings = settings
        self._cache: dict[tuple, PermissionDecision] = {}

    def check_permission(
        self,
        tool_name: str,
        agent_type: str = "main",
        args: Optional[dict] = None,
    ) -> PermissionDecision:
        """Check if a tool call is permitted for the given agent type.

        Evaluation order:
          1. Session cache — return cached decision if found.
          2. Agent type config — look up tool in AGENT_TYPES.
          3. Tool classification — read / mutation / destructive.
          4. Permission defaults — map classification to ALLOW/DENY/ASK.
          5. Unknown tools → ASK.

        Args:
            tool_name: Name of the tool being called.
            agent_type: Type of agent making the call.
            args: Tool arguments (used for cache key only).

        Returns:
            PermissionDecision.ALLOW, DENY, or ASK.
        """
        # Step 0: Check global permission mode setting (YOLO vs ASK)
        if self._get_permission_mode() == "yolo":
            return PermissionDecision.ALLOW

        # Step 1: Check session cache
        args_hash = self._hash_args(args or {})
        cache_key = (agent_type, tool_name, args_hash)
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "[Permissions] Cache hit: %s/%s -> %s",
                agent_type, tool_name, cached.value,
            )
            return cached

        # Step 2: Look up agent type config
        agent_types = self._get_agent_types()
        agent_config = agent_types.get(agent_type, {})

        # Step 3: Check if tool is in allowed list
        allowed_tools = agent_config.get("tools", [])
        if tool_name not in allowed_tools and allowed_tools:
            logger.debug(
                "[Permissions] Tool '%s' not in agent_type '%s' allowed list",
                tool_name, agent_type,
            )
            return PermissionDecision.ASK

        # Step 4: Classify tool and check permission defaults
        classification = self._classify_tool(tool_name)
        permission_defaults = agent_config.get("permission_defaults", {})

        if classification == "read" and permission_defaults.get("allow_read", True):
            return PermissionDecision.ALLOW
        elif classification == "mutation" and permission_defaults.get("ask_mutation", True):
            return PermissionDecision.ASK
        elif classification == "destructive" and permission_defaults.get("deny_destructive", True):
            return PermissionDecision.DENY

        # Step 5: Unknown tool or fallback
        logger.debug(
            "[Permissions] Unknown tool '%s' for agent_type '%s' -> ASK",
            tool_name, agent_type,
        )
        return PermissionDecision.ASK

    def cache_decision(
        self,
        tool_name: str,
        agent_type: str,
        args: Optional[dict],
        decision: PermissionDecision,
    ) -> None:
        """Cache a permission decision for the current session.

        Cached decisions are keyed by (agent_type, tool_name, args_hash)
        and persist until clear_cache() is called or the session ends.

        Args:
            tool_name: Name of the tool.
            agent_type: Type of agent.
            args: Tool arguments (used for cache key).
            decision: The permission decision to cache.
        """
        args_hash = self._hash_args(args or {})
        cache_key = (agent_type, tool_name, args_hash)
        self._cache[cache_key] = decision
        logger.debug(
            "[Permissions] Cached: %s/%s -> %s",
            agent_type, tool_name, decision.value,
        )

    def clear_cache(self) -> None:
        """Reset all cached permission decisions."""
        self._cache.clear()
        logger.debug("[Permissions] Cache cleared")

    def _get_agent_types(self) -> dict:
        """Get AGENT_TYPES config from settings or module constant.

        If a settings object was provided at construction, reads
        agent_types from settings. Otherwise uses the module-level
        AGENT_TYPES constant from defaults.py.
        """
        if self._settings is not None:
            if isinstance(self._settings, dict):
                return self._settings.get("agent_types", {})
            if hasattr(self._settings, "get"):
                return self._settings.get("agent_types", {})
        return AGENT_TYPES

    def _get_permission_mode(self) -> str:
        """Get the active permission mode from settings.

        Defaults to 'ask' if not specified in settings, so that unit tests
        and custom configurations default to standard permission prompting.
        In production, the settings object is pre-populated with the
        default value 'yolo' from defaults.py.
        """
        if self._settings is not None:
            if isinstance(self._settings, dict):
                return self._settings.get("permission_mode", "ask")
            if hasattr(self._settings, "get"):
                val = self._settings.get("permission_mode")
                if val is not None:
                    return val
        return "ask"

    @staticmethod
    def _classify_tool(tool_name: str) -> str:
        """Classify a tool name into a permission category.

        Heuristic classification based on tool naming conventions:
        - "read" tools: read-only operations (file_read, file_glob,
          file_grep, web_search, web_fetch)
        - "mutation" tools: state-changing operations (terminal,
          file_write, voice)
        - "destructive" tools: potentially dangerous operations
          (any tool not matching read or mutation)

        Args:
            tool_name: Name of the tool to classify.

        Returns:
            One of "read", "mutation", or "destructive".
        """
        read_tools = {
            "file_read", "file_glob", "file_grep",
            "web_search", "web_fetch",
        }
        mutation_tools = {"terminal", "file_write", "voice"}

        if tool_name in read_tools:
            return "read"
        elif tool_name in mutation_tools:
            return "mutation"
        else:
            return "destructive"

    @staticmethod
    def _hash_args(args: dict) -> str:
        """Create a deterministic string key from tool arguments.

        Used for cache key generation. Hashes sorted JSON keys
        with string representation fallback for non-serializable values.

        Args:
            args: Tool arguments dict.

        Returns:
            String representation suitable as a cache key component.
        """
        return str(sorted((k, str(v)) for k, v in args.items()))
