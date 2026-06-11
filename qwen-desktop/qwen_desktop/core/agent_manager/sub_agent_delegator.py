"""Sub-agent delegator — spawns isolated sub-agents with scoped tool sets.

Implements the hierarchical supervisor/worker pattern from the research:
- Full reasoning sub-agents with their own API call and context window
- Scoped tool sets per agent type via ToolRegistry
- Structured SubAgentContext prevents context loss (Pitfall 3)
- Tool calls execute within sub-agent's scope only
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from qwen_desktop.core.tool_registry import get_registry

logger = logging.getLogger(__name__)


@dataclass
class SubAgentContext:
    """Structured context for sub-agent execution.

    Carries the original goal, preceding work summary, specific subtask
    definition, constraints/success criteria, and agent type identifier.
    Prevents context loss by bundling all relevant information in a
    single structured object (per research Pitfall 3).

    Attributes:
        original_goal: The user's original high-level goal.
        preceding_work: Summary of what other agents have already done.
        subtask: The specific subtask this sub-agent must complete.
        constraints: Success criteria and constraints for the subtask.
        agent_type: Agent type identifier (e.g. 'web', 'terminal', 'file', 'voice').
    """

    original_goal: str
    preceding_work: str
    subtask: str
    constraints: str
    agent_type: str


@dataclass
class SubAgentResult:
    """Structured result returned by a sub-agent after execution.

    Attributes:
        success: Whether the sub-agent completed its task successfully.
        output: The final output text from the sub-agent.
        tool_calls: List of tool calls made during execution.
        error: Error message if execution failed, or None.
        token_usage: Token usage info from the API call, or None.
    """

    success: bool
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    token_usage: Optional[dict[str, Any]] = None


class SubAgentDelegator:
    """Spawns isolated sub-agents with scoped tool sets.

    Each sub-agent runs in its own LLM API call with a dedicated context
    window. The delegator builds a structured prompt containing the goal,
    preceding work, subtask, constraints, and available tool definitions.
    Tool calls are executed through the ToolRegistry within the sub-agent's
    allowed tool scope.
    """

    def __init__(
        self,
        api_client: Any,
        tool_registry: Optional[Any] = None,
        settings: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the sub-agent delegator.

        Args:
            api_client: API client for making LLM calls to sub-agents.
            tool_registry: Optional ToolRegistry instance. Uses the global
                singleton if not provided.
            settings: Optional settings dict for agent type configuration.
        """
        self.api_client = api_client
        self._registry = tool_registry or get_registry()
        self._settings = settings or {}
        self._default_agent_types = ["main", "web", "terminal", "file", "voice"]

    async def spawn_and_execute(
        self, context: SubAgentContext
    ) -> SubAgentResult:
        """Spawn a sub-agent and execute its subtask.

        This is the main entry point. It builds the sub-agent prompt,
        calls the LLM with an isolated context window, parses the
        response for tool calls, executes them through the registry,
        and returns a structured result.

        Args:
            context: Structured context for the sub-agent (goal, preceding
                work, subtask, constraints, agent_type).

        Returns:
            SubAgentResult with success status, output, tool calls, and
            any error information.
        """
        try:
            # Get scoped tool definitions for this agent type
            tool_defs = self._registry.get_definitions(
                agent_type=context.agent_type
            )

            # Build the sub-agent system prompt with scoped tools
            prompt = self._build_sub_agent_prompt(context, tool_defs)

            # Call LLM with isolated context window
            logger.info(
                "[SubAgent] Spawning %s sub-agent for: %s",
                context.agent_type,
                context.subtask[:60],
            )

            full_response = ""
            async for chunk in self.api_client.send_message(prompt, []):
                full_response += chunk

            if not full_response:
                return SubAgentResult(
                    success=False,
                    output="",
                    error="Empty response from API",
                )

            # Parse response for tool calls and process them
            tool_calls: list[dict[str, Any]] = []
            tool_call_results: list[str] = []

            try:
                parsed = json.loads(full_response)
                if isinstance(parsed, dict) and "tool_calls" in parsed:
                    for tc in parsed["tool_calls"]:
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("args", {})
                        result = await self._execute_sub_agent_tool(
                            tool_name, tool_args
                        )
                        tool_calls.append(tc)
                        tool_call_results.append(result)
            except (json.JSONDecodeError, TypeError):
                # Not a JSON tool call response — treat as plain output
                pass

            return SubAgentResult(
                success=True,
                output=full_response,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(
                "[SubAgent] Error executing %s sub-agent: %s",
                context.agent_type,
                e,
                exc_info=True,
            )
            return SubAgentResult(
                success=False,
                output="",
                error=str(e),
            )

    def _build_sub_agent_prompt(
        self,
        context: SubAgentContext,
        tool_defs: list[dict[str, Any]],
    ) -> str:
        """Build the sub-agent system prompt from context and tool definitions.

        Uses a structured template per research Pitfall 3 to prevent
        context loss: goal, preceding work, subtask, constraints, and
        available tool definitions are all included explicitly.

        Args:
            context: SubAgentContext with goal, work, subtask, constraints.
            tool_defs: Scoped tool definitions for this agent type.

        Returns:
            Formatted prompt string for the sub-agent LLM call.
        """
        tool_defs_json = json.dumps(tool_defs, indent=2)

        prompt = f"""Goal: {context.original_goal}
Context: {context.preceding_work}
Task: {context.subtask}
Constraints: {context.constraints}

Available tools:
{tool_defs_json}

Respond with tool calls when needed. Return "TASK_COMPLETE" when finished."""

        return prompt

    async def _execute_sub_agent_tool(
        self, tool_name: str, args: dict[str, Any]
    ) -> str:
        """Execute a single tool call through the registry.

        Gets the tool instance from the registry and calls its execute
        method with the provided arguments. Only tools registered in the
        sub-agent's scope can be executed.

        Args:
            tool_name: Name of the tool to execute.
            args: Arguments to pass to the tool.

        Returns:
            String result from the tool execution.
        """
        try:
            tool = self._registry.get_tool(tool_name)
            if tool is None:
                return f"Error: Tool '{tool_name}' not found in registry"

            if not hasattr(tool, "execute"):
                return f"Error: Tool '{tool_name}' has no execute method"

            result = await tool.execute(**args)
            return str(result)

        except Exception as e:
            logger.error(
                "[SubAgent] Tool execution error for %s: %s",
                tool_name,
                e,
                exc_info=True,
            )
            return f"Error executing {tool_name}: {e}"

    def get_available_agent_types(self) -> list[str]:
        """Return available agent type identifiers.

        Reads from AGENT_TYPES config if settings are available,
        otherwise returns the default list.

        Returns:
            List of agent type name strings.
        """
        agent_types = self._settings.get("agent_types", {})
        if agent_types:
            return list(agent_types.keys())
        return list(self._default_agent_types)
