"""AgentTool — spawns sub-agents with read-only tools (matches opencode's agent-tool.go).

Architecture (mirrors opencode):
  1. Creates child AgentManager with scoped read-only tools
  2. Creates task session linked to parent via SessionService
  3. Runs sub-agent synchronously (blocking await) or asynchronously (background)
  4. Reports step progress to parent UI via _on_step callback
  5. Propagates cost/usage back to parent session

Background execution (opencode's background: true):
  - When background=True, AgentTool returns immediately with a running task tag
  - The sub-agent completes in the background
  - AgentManager._check_background_tasks() injects results into the next PLAN
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

logger = logging.getLogger(__name__)

# Module-level tracker for background sub-agent tasks
_background_tasks: dict[str, asyncio.Task] = {}
_background_results: dict[str, str] = {}


@register_tool("agent")
class AgentTool(BaseTool):
    """Tool that spawns a new sub-agent with read-only tools."""

    name = "agent"
    description = (
        "Launch a new sub-agent that has access to read-only tools like "
        "web_search, web_fetch, file_read, file_glob, file_grep, and sourcegraph. "
        "When you need to perform research, code exploration, or multi-step analysis "
        "without modifying files, use the Agent tool to delegate the work.\n\n"
        "Usage notes:\n"
        "1. Launch multiple agents concurrently whenever possible; to do that, "
        "use a single plan step with multiple agent tool uses.\n"
        "2. Each agent invocation is independent. Your prompt should contain a "
        "highly detailed task description specifying exactly what to return.\n"
        "3. The sub-agent CANNOT use terminal, file_write, file_edit, or vision tools.\n"
        "4. If background=True, the agent runs asynchronously — you continue working\n"
        "   and the result is injected into your context when it completes."
    )
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The detailed task description for the sub-agent to perform",
            },
            "background": {
                "type": "boolean",
                "description": "Run in background and inject result when done (default: false)",
            },
        },
        "required": ["prompt"],
    }

    def __init__(self):
        super().__init__()
        self.api_client: Optional[Any] = None
        self.session_service: Optional[Any] = None
        self.parent_session_id: Optional[str] = None
        self._on_step: Optional[Callable] = None  # set by AgentWorker for UI updates

    async def execute(self, prompt: str = "", **kwargs: Any) -> str:
        """Spawn a sub-agent with read-only tools (matches opencode's agentTool.Run).

        When background=True, returns immediately with a running-task tag.
        The sub-agent completes asynchronously — AgentManager injects results
        into the next PLAN via _check_background_tasks().

        Args:
            prompt: Task description for the sub-agent.
            background: If True, run asynchronously (default: False).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Synchronous: <task id="..." state="completed">result</task>
            Background:  <task id="..." state="running">Background task started</task>
        """
        if not prompt:
            return "Error: AgentTool requires a 'prompt' argument with the task description for the sub-agent."
        if not self.api_client:
            return "Error: api_client not injected into AgentTool."

        background = kwargs.get("background", False)
        logger.info("[AgentTool] Spawning sub-agent (background=%s): %s...", background, prompt[:60])

        # 1. Create task session linked to parent (opencode: CreateTaskSession)
        child_session_id = "agent-" + str(int(time.time()))
        if self.session_service and self.parent_session_id:
            child_session_id = self.session_service.create_task_session(
                tool_call_id=child_session_id,
                parent_session_id=self.parent_session_id,
                title=f"Sub-agent: {prompt[:40]}",
            )

        # 2. Build scoped registry with read-only tools (opencode: TaskAgentTools)
        from vda.core.tool_registry.registry import ToolRegistry, get_registry
        scoped_registry = ToolRegistry()
        global_registry = get_registry()
        allowed_tools = ["web_search", "web_fetch", "file_read", "file_glob", "file_grep", "sourcegraph"]
        for t_name in allowed_tools:
            tool_cls = global_registry._registry.get(t_name)
            if tool_cls:
                scoped_registry.register(t_name, tool_cls)

        # 3. Create sub-agent (opencode: NewAgent with AgentTask config)
        from vda.core.agent_manager.agent_manager import AgentManager, AgentState

        sub_manager = AgentManager(
            api_client=self.api_client,
            tool_registry=scoped_registry,
            vision_mode=False,
            max_iterations=30,
        )
        sub_manager.agent_type = "subagent"
        sub_manager.session_service = self.session_service
        sub_manager._session_id = child_session_id
        sub_manager._on_step = self._on_step  # forward step callback to UI
        sub_manager.reset()
        sub_manager._user_input = prompt
        sub_manager.state = AgentState.INIT

        task_id = child_session_id or "unknown"

        if background:
            # <!-- BACKGROUND EXECUTION (opencode background: true) -->
            async def _run_and_store():
                try:
                    result = await sub_manager.run_to_completion_async()
                    _background_results[task_id] = result
                    # Propagate cost
                    sub_cost = sub_manager.total_cost
                    if sub_cost > 0 and self.session_service and self.parent_session_id:
                        try:
                            self.session_service.add_session_cost(self.parent_session_id, sub_cost)
                        except Exception:
                            pass
                    logger.info("[AgentTool] Background task %s completed", task_id[:20])
                except Exception as e:
                    _background_results[task_id] = f"Error: Background task failed: {e}"
                    logger.error("[AgentTool] Background task %s failed: %s", task_id[:20], e)
                finally:
                    _background_tasks.pop(task_id, None)

            task = asyncio.create_task(_run_and_store())
            _background_tasks[task_id] = task

            if self._on_step:
                self._on_step("agent", {"summary": "Background task started"}, "started", task_id)

            return (
                f'<task id="{task_id}" state="running">\n'
                f"Background task started for: {prompt[:100]}\n"
                f"</task>"
            )

        # --- SYNCHRONOUS EXECUTION (default) ---
        start = time.monotonic()
        result = await sub_manager.run_to_completion_async()
        elapsed = time.monotonic() - start

        # 5. Propagate cost to parent (opencode: parentSession.Cost += updatedSession.Cost)
        sub_cost = sub_manager.total_cost
        if sub_cost > 0 and self.session_service and self.parent_session_id:
            try:
                self.session_service.add_session_cost(self.parent_session_id, sub_cost)
            except Exception as e:
                logger.debug("[AgentTool] Cost propagation failed: %s", e)

        logger.info("[AgentTool] Sub-agent completed in %.1fs (tokens: %d+%d, cost: %.6f)",
                    elapsed, sub_manager.total_prompt_tokens,
                    sub_manager.total_completion_tokens, sub_cost)

        # 6. Wrap result in <task> tags (opencode style: <task id="..." state="...">)
        task_xml = (
            f'<task id="{task_id}" state="completed">\n'
            f"{result}\n"
            f"</task>"
        )

        # 7. Report completion to parent UI
        if self._on_step:
            self._on_step("agent", {"summary": result[:200]}, "completed", result[:200])

        return task_xml
