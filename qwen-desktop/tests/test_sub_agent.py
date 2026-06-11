"""Tests for the SubAgentDelegator subsystem.

Covers SubAgentContext and SubAgentResult dataclass fields, delegator
initialization, prompt building with context fields, agent type scoping,
and tool execution through the registry.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from qwen_desktop.core.agent_manager import (
    SubAgentContext,
    SubAgentDelegator,
    SubAgentResult,
)


class TestSubAgentContext:
    """Verify SubAgentContext dataclass fields."""

    def test_all_fields_present(self):
        """Verify all required fields exist with correct defaults."""
        context = SubAgentContext(
            original_goal="Test goal",
            preceding_work="Some work done",
            subtask="Do specific thing",
            constraints="Must be fast",
            agent_type="web",
        )
        assert context.original_goal == "Test goal"
        assert context.preceding_work == "Some work done"
        assert context.subtask == "Do specific thing"
        assert context.constraints == "Must be fast"
        assert context.agent_type == "web"

    def test_empty_context_allowed(self):
        """Verify empty strings are acceptable defaults."""
        context = SubAgentContext(
            original_goal="",
            preceding_work="",
            subtask="",
            constraints="",
            agent_type="",
        )
        assert context.original_goal == ""
        assert context.agent_type == ""


class TestSubAgentResult:
    """Verify SubAgentResult dataclass fields."""

    def test_minimal_result(self):
        """Verify result with only required fields."""
        result = SubAgentResult(success=True, output="Done")
        assert result.success is True
        assert result.output == "Done"
        assert result.tool_calls == []
        assert result.error is None
        assert result.token_usage is None

    def test_full_result(self):
        """Verify result with all fields populated."""
        result = SubAgentResult(
            success=True,
            output="Task complete",
            tool_calls=[{"name": "web_search", "args": {"q": "test"}}],
            error=None,
            token_usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
        assert result.success is True
        assert result.output == "Task complete"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "web_search"
        assert result.error is None
        assert result.token_usage["prompt_tokens"] == 100

    def test_failed_result(self):
        """Verify result with error state."""
        result = SubAgentResult(
            success=False,
            output="",
            error="API call failed",
        )
        assert result.success is False
        assert result.error == "API call failed"


class TestSubAgentDelegator:
    """Test SubAgentDelegator initialization, prompt building, and scoping."""

    def test_initialization(self):
        """Delegator created with mock api_client stores reference."""
        mock_client = MagicMock()
        delegator = SubAgentDelegator(mock_client)
        assert delegator.api_client is mock_client

    def test_initialization_with_registry(self):
        """Delegator accepts custom tool registry."""
        mock_client = MagicMock()
        mock_registry = MagicMock()
        delegator = SubAgentDelegator(mock_client, tool_registry=mock_registry)
        assert delegator._registry is mock_registry

    def test_get_available_agent_types_default(self):
        """Returns default list when no settings configured."""
        mock_client = MagicMock()
        delegator = SubAgentDelegator(mock_client)
        types = delegator.get_available_agent_types()
        assert "main" in types
        assert "web" in types
        assert "terminal" in types
        assert "file" in types
        assert "voice" in types
        assert len(types) >= 5

    def test_get_available_agent_types_from_settings(self):
        """Returns agent types from settings when configured."""
        mock_client = MagicMock()
        delegator = SubAgentDelegator(
            mock_client,
            settings={
                "agent_types": {
                    "web": {},
                    "voice": {},
                }
            },
        )
        types = delegator.get_available_agent_types()
        assert "web" in types
        assert "voice" in types
        assert len(types) == 2

    def test_build_sub_agent_prompt(self):
        """Prompt contains all context fields and tool definitions."""
        mock_client = MagicMock()
        delegator = SubAgentDelegator(mock_client)

        context = SubAgentContext(
            original_goal="Research AI trends",
            preceding_work="Nothing yet",
            subtask="Search web for AI trends",
            constraints="Use reliable sources only",
            agent_type="web",
        )
        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        prompt = delegator._build_sub_agent_prompt(context, tool_defs)

        # Verify all context fields appear in the prompt
        assert "Research AI trends" in prompt
        assert "Nothing yet" in prompt
        assert "Search web for AI trends" in prompt
        assert "Use reliable sources only" in prompt
        assert "web_search" in prompt
        assert "TASK_COMPLETE" in prompt
        assert "Available tools:" in prompt

    def test_agent_type_scoping(self):
        """Web agent type gets definitions scoped to web tools."""
        mock_client = MagicMock()
        # Mock registry that returns scoped definitions
        mock_registry = MagicMock()
        mock_registry.get_definitions.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {},
                },
            }
        ]

        delegator = SubAgentDelegator(mock_client, tool_registry=mock_registry)

        context = SubAgentContext(
            original_goal="Test",
            preceding_work="",
            subtask="Search",
            constraints="",
            agent_type="web",
        )

        prompt = delegator._build_sub_agent_prompt(
            context,
            mock_registry.get_definitions(agent_type="web"),
        )

        # Verify get_definitions was called with the correct agent type
        mock_registry.get_definitions.assert_called_with(agent_type="web")
        assert "web_search" in prompt

    def test_spawn_and_execute_empty_response(self):
        """Empty API response returns failed result."""
        mock_client = MagicMock()
        # Simulate empty async generator
        async def _empty_gen():
            return
            yield  # pragma: no cover

        mock_client.send_message.return_value = _empty_gen()

        delegator = SubAgentDelegator(mock_client)

        context = SubAgentContext(
            original_goal="Test",
            preceding_work="",
            subtask="Do thing",
            constraints="",
            agent_type="web",
        )

        import asyncio

        result = asyncio.run(delegator.spawn_and_execute(context))
        assert result.success is False
        assert result.error == "Empty response from API"

    def test_execute_sub_agent_tool_missing_tool(self):
        """Calling a non-existent tool returns error string."""
        mock_client = MagicMock()
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = None

        delegator = SubAgentDelegator(mock_client, tool_registry=mock_registry)

        import asyncio

        result = asyncio.run(
            delegator._execute_sub_agent_tool("nonexistent", {})
        )
        assert "not found" in result
        mock_registry.get_tool.assert_called_with("nonexistent")

    def test_execute_sub_agent_tool_success(self):
        """Calling a valid tool returns its result."""
        mock_client = MagicMock()
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = "Tool executed"

        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = mock_tool

        delegator = SubAgentDelegator(mock_client, tool_registry=mock_registry)

        import asyncio

        result = asyncio.run(
            delegator._execute_sub_agent_tool("valid_tool", {"arg": "val"})
        )
        assert result == "Tool executed"
        mock_tool.execute.assert_called_once_with(arg="val")

    def test_spawn_and_execute_api_error(self):
        """API exception returns failed result with error message."""
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("API connection failed")

        delegator = SubAgentDelegator(mock_client)

        context = SubAgentContext(
            original_goal="Test",
            preceding_work="",
            subtask="Do thing",
            constraints="",
            agent_type="web",
        )

        import asyncio

        result = asyncio.run(delegator.spawn_and_execute(context))
        assert result.success is False
        assert "API connection failed" in result.error
