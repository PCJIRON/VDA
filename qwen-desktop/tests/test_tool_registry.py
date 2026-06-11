"""Tests for the tool registry package.

Covers registration, lazy initialization, OpenAI-compatible definitions,
agent type scope filtering, thread safety, and BaseTool contract.
"""

import threading
from typing import Any, Optional

import pytest

from qwen_desktop.core.tool_registry import (
    ToolRegistry,
    BaseTool,
    register_tool,
    get_registry,
)


class _MockTool(BaseTool):
    """Mock tool for testing registration and lazy init."""

    name = "mock_tool"
    description = "A mock tool for testing"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "Test input",
            }
        },
        "required": ["input"],
    }

    def __init__(self) -> None:
        super().__init__()
        self.init_count: int = 0

    async def execute(self, **kwargs: Any) -> str:
        """Execute mock tool."""
        return f"Mock executed with: {kwargs}"


class _InitTrackingTool(BaseTool):
    """Tool that tracks whether __init__ was called."""

    name = "init_tracking"
    description = "Tracks initialization state"
    parameters: dict[str, Any] = {}

    initialized: bool = False

    def __init__(self) -> None:
        super().__init__()
        type(self).initialized = True
        self.init_count: int = 0

    async def execute(self, **kwargs: Any) -> str:
        """Execute tracking tool."""
        return "tracked"


class TestToolRegistry:
    """Test ToolRegistry registration, lazy init, and definitions."""

    def setup_method(self) -> None:
        """Create a fresh registry for each test."""
        self.registry = ToolRegistry()

    def test_register_and_get_tool(self) -> None:
        """Register a tool and verify get_tool returns an instance."""
        self.registry.register("mock", _MockTool)

        tool = self.registry.get_tool("mock")
        assert tool is not None
        assert isinstance(tool, _MockTool)

        # Verify instances are shared (same object for same name)
        tool2 = self.registry.get_tool("mock")
        assert tool2 is tool

    def test_lazy_initialization(self) -> None:
        """Verify tool class is NOT instantiated until first get_tool call."""
        _InitTrackingTool.initialized = False

        # Register - should NOT instantiate
        self.registry.register("tracker", _InitTrackingTool)
        assert _InitTrackingTool.initialized is False, (
            "Tool should not be initialized after register"
        )
        assert self.registry.loaded_count == 0

        # First get_tool - should instantiate
        tool = self.registry.get_tool("tracker")
        assert tool is not None
        assert _InitTrackingTool.initialized is True
        assert self.registry.loaded_count == 1

    def test_get_definitions(self) -> None:
        """Verify returned schema matches expected OpenAI-compatible format."""
        self.registry.register("mock", _MockTool)

        definitions = self.registry.get_definitions()
        assert len(definitions) == 1

        definition = definitions[0]
        assert definition["type"] == "function"

        func = definition["function"]
        assert func["name"] == "mock_tool"
        assert func["description"] == "A mock tool for testing"
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"
        assert "input" in func["parameters"]["properties"]

    def test_get_definitions_agent_type_filter(self) -> None:
        """Verify get_definitions(agent_type) returns only scoped tools."""
        class _WebSearchTool(BaseTool):
            name = "web_search"
            description = "Web search tool"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "search"

        class _WebFetchTool(BaseTool):
            name = "web_fetch"
            description = "Web fetch tool"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "fetch"

        class _TerminalTool(BaseTool):
            name = "terminal"
            description = "Terminal tool"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "term"

        class _VoiceTool(BaseTool):
            name = "voice"
            description = "Voice tool"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "voice"

        # Create a scoped registry with settings (like the real one)
        scoped_registry = ToolRegistry(
            settings={
                "agent_types": {
                    "web": {
                        "tools": ["web_search", "web_fetch"],
                    },
                    "voice": {
                        "tools": ["voice"],
                    },
                }
            }
        )
        scoped_registry.register("web_search", _WebSearchTool)
        scoped_registry.register("web_fetch", _WebFetchTool)
        scoped_registry.register("terminal", _TerminalTool)
        scoped_registry.register("voice", _VoiceTool)

        web_defs = scoped_registry.get_definitions(agent_type="web")
        assert len(web_defs) == 2
        web_names = [d["function"]["name"] for d in web_defs]
        assert "web_search" in web_names
        assert "web_fetch" in web_names
        assert "terminal" not in web_names

        voice_defs = scoped_registry.get_definitions(agent_type="voice")
        assert len(voice_defs) == 1
        assert voice_defs[0]["function"]["name"] == "voice"

    def test_thread_safety(self) -> None:
        """Verify concurrent get_tool calls produce single instantiation."""
        self.registry.register("safe_tool", _MockTool)

        results: list[Optional[BaseTool]] = [None, None]
        barrier = threading.Barrier(2, timeout=5)

        def _get_tool(index: int) -> None:
            barrier.wait()  # Sync both threads to start simultaneously
            results[index] = self.registry.get_tool("safe_tool")

        threads = [
            threading.Thread(target=_get_tool, args=(0,)),
            threading.Thread(target=_get_tool, args=(1,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # Both should get the same instance
        assert results[0] is not None
        assert results[1] is not None
        assert results[0] is results[1]

        # Only one instance should exist
        assert self.registry.loaded_count == 1

    def test_is_loaded(self) -> None:
        """Verify is_loaded - False before first get_tool, True after."""
        self.registry.register("test_tool", _MockTool)

        assert self.registry.is_loaded("test_tool") is False
        self.registry.get_tool("test_tool")
        assert self.registry.is_loaded("test_tool") is True

    def test_unknown_tool_returns_none(self) -> None:
        """Verify get_tool('nonexistent') returns None."""
        result = self.registry.get_tool("nonexistent")
        assert result is None

    def test_get_definitions_for_tools(self) -> None:
        """Verify get_definitions_for_tools returns only specified tools."""
        class _ToolA(BaseTool):
            name = "tool_a"
            description = "Tool A"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "a"

        class _ToolB(BaseTool):
            name = "tool_b"
            description = "Tool B"
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return "b"

        self.registry.register("tool_a", _ToolA)
        self.registry.register("tool_b", _ToolB)

        # Only return definitions for tool_a
        defs = self.registry.get_definitions_for_tools(["tool_a"])
        assert len(defs) == 1
        assert defs[0]["function"]["name"] == "tool_a"

    def test_get_agent_type_tools(self) -> None:
        """Verify get_agent_type_tools returns correct tools for agent type."""
        class _ATWebTool(BaseTool):
            name = "web_search"
            description = ""
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return ""

        class _ATTermTool(BaseTool):
            name = "terminal"
            description = ""
            parameters: dict[str, Any] = {}
            async def execute(self, **kwargs: Any) -> str:
                return ""

        scoped = ToolRegistry(
            settings={
                "agent_types": {
                    "web": {"tools": ["web_search"]},
                }
            }
        )
        scoped.register("web_search", _ATWebTool)
        scoped.register("terminal", _ATTermTool)

        tools = scoped.get_agent_type_tools("web")
        assert tools == ["web_search"]

    def test_registered_count(self) -> None:
        """Verify registered_count property."""
        assert self.registry.registered_count == 0
        self.registry.register("a", _MockTool)
        assert self.registry.registered_count == 1
        self.registry.register("b", _MockTool)
        assert self.registry.registered_count == 2

    def test_loaded_count(self) -> None:
        """Verify loaded_count property."""
        assert self.registry.loaded_count == 0
        self.registry.register("a", _MockTool)
        self.registry.register("b", _MockTool)
        self.registry.get_tool("a")
        assert self.registry.loaded_count == 1
        self.registry.get_tool("b")
        assert self.registry.loaded_count == 2


class TestBaseTool:
    """Test BaseTool abstract class contract."""

    def test_execute_raises_not_implemented(self) -> None:
        """Verify direct BaseTool usage raises NotImplementedError."""
        tool = BaseTool()
        tool.name = "test"
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(tool.execute())


class TestGlobalRegistry:
    """Test the module-level singleton registry."""

    def test_get_registry_returns_singleton(self) -> None:
        """Verify get_registry() returns the module-level singleton."""
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_register_tool_decorator(self) -> None:
        """Verify @register_tool decorator registers class in singleton."""
        @register_tool("test_decorator_tool")
        class _DecoratedTool(BaseTool):
            name = "test_decorator_tool"
            description = "Tool registered via decorator"
            parameters: dict[str, Any] = {}

            async def execute(self, **kwargs: Any) -> str:
                return "decorated"

        registry = get_registry()
        tool = registry.get_tool("test_decorator_tool")
        assert tool is not None
        assert isinstance(tool, _DecoratedTool)
        assert registry.is_loaded("test_decorator_tool")
