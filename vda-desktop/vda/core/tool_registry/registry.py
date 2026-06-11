"""ToolRegistry — decorator-based registry with lazy initialization.

Provides thread-safe lazy tool instantiation using double-checked
locking, OpenAI-compatible tool definition generation, and agent type
scope filtering for sub-agent tool sets.
"""

import logging
import threading
from typing import Any, Optional

from vda.core.tool_registry.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for tool classes with lazy initialization.

    Tools are registered as class references and instantiated on first
    use via get_tool(). Thread safety is achieved through double-checked
    locking with per-tool locks.

    Attributes:
        loaded_count: Number of tool instances currently initialized.
        registered_count: Number of tool classes registered.
    """

    def __init__(self, settings: Optional[dict[str, Any]] = None) -> None:
        """Initialize empty registry.

        Args:
            settings: Optional settings dict for config-backed agent type
                tool filtering (e.g. permission config per agent type).
        """
        self._registry: dict[str, type[BaseTool]] = {}
        self._instances: dict[str, BaseTool] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._settings = settings or {}

    def register(self, name: str, tool_cls: type[BaseTool]) -> None:
        """Register a tool class by name.

        Does NOT instantiate the tool — initialization is deferred until
        the first call to get_tool().

        Args:
            name: Unique tool name identifier.
            tool_cls: Tool class inheriting from BaseTool.
        """
        self._registry[name] = tool_cls
        self._locks[name] = threading.Lock()
        logger.debug("[ToolRegistry] Registered: %s", name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool instance, lazily initializing on first access.

        Uses double-checked locking for thread-safe lazy initialization.
        Returns None if the tool name is not registered.

        Args:
            name: Tool name to retrieve.

        Returns:
            Tool instance or None if not registered.
        """
        if name not in self._registry:
            return None
        if name not in self._instances:
            with self._locks[name]:
                if name not in self._instances:
                    self._instances[name] = self._registry[name]()
                    logger.info("[ToolRegistry] Initialized: %s", name)
        return self._instances.get(name)

    def get_definitions(
        self, agent_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get OpenAI-compatible function schemas for registered tools.

        If agent_type is provided, only tools allowed for that agent
        type are returned (scope filtering).

        Args:
            agent_type: Optional agent type for scope filtering.

        Returns:
            List of OpenAI-compatible tool definition dicts.
        """
        if agent_type:
            allowlist = self._get_tool_allowlist(agent_type)
            names = allowlist
        else:
            names = list(self._registry.keys())

        definitions: list[dict[str, Any]] = []
        for name in names:
            cls = self._registry.get(name)
            if cls is None:
                continue
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": cls.name,
                        "description": cls.description,
                        "parameters": cls.parameters,
                    },
                }
            )
        return definitions

    def get_definitions_for_tools(
        self, tool_names: list[str]
    ) -> list[dict[str, Any]]:
        """Get schemas only for the specified tool names.

        Args:
            tool_names: List of tool names to include.

        Returns:
            List of OpenAI-compatible tool definition dicts.
        """
        definitions: list[dict[str, Any]] = []
        for name in tool_names:
            cls = self._registry.get(name)
            if cls is None:
                continue
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": cls.name,
                        "description": cls.description,
                        "parameters": cls.parameters,
                    },
                }
            )
        return definitions

    def is_loaded(self, name: str) -> bool:
        """Check if a tool has been instantiated.

        Args:
            name: Tool name to check.

        Returns:
            True if the tool instance exists.
        """
        return name in self._instances

    @property
    def loaded_count(self) -> int:
        """Number of tool instances currently initialized."""
        return len(self._instances)

    @property
    def registered_count(self) -> int:
        """Number of tool classes registered."""
        return len(self._registry)

    def get_agent_type_tools(self, agent_type: str) -> list[str]:
        """Return tool names allowed for a given agent type.

        Reads from AGENT_TYPES config if settings are available,
        otherwise returns all registered tool names.

        Args:
            agent_type: Agent type identifier (e.g. 'main', 'web').

        Returns:
            List of tool name strings.
        """
        agent_types = self._settings.get("agent_types", {})
        type_config = agent_types.get(agent_type, {})
        tools = type_config.get("tools", [])
        if tools:
            return tools
        return list(self._registry.keys())

    def _get_tool_allowlist(self, agent_type: str) -> list[str]:
        """Get tool allowlist for an agent type from config.

        Args:
            agent_type: Agent type identifier.

        Returns:
            List of allowed tool names.
        """
        agent_types = self._settings.get("agent_types", {})
        type_config = agent_types.get(agent_type, {})
        return type_config.get("tools", []) or list(self._registry.keys())


# Module-level singleton registry
_registry = ToolRegistry()


def register_tool(name: str):
    """Decorator that registers a tool class with the global registry.

    Usage::

        @register_tool("web_search")
        class WebSearchTool(BaseTool):
            name = "web_search"
            ...

    Args:
        name: Tool name to register under.

    Returns:
        Decorator function that registers the class.
    """

    def decorator(cls):
        cls.name = name
        _registry.register(name, cls)
        return cls

    return decorator


def get_registry() -> ToolRegistry:
    """Get the module-level singleton ToolRegistry instance.

    Returns:
        The global ToolRegistry instance.
    """
    return _registry
