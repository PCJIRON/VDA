"""AgentTool — allows the main agent to delegate tasks to sub-agents."""

import logging
from typing import Any, Optional

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

# Module-level imports removed to prevent circular dependency

logger = logging.getLogger(__name__)


@register_tool("agent")
class AgentTool(BaseTool):
    """Tool that spawns a new sub-agent to perform complex tasks."""

    name = "agent"
    description = (
        "Launch a new sub-agent that has access to read-only tools like "
        "web_search, web_fetch, file_read, file_glob, and file_grep. "
        "When you are searching for a keyword or file, or need to perform "
        "a multi-step research task, use the Agent tool to perform the work for you. "
        "For example:\n\n"
        "- If you are searching for a keyword like 'config' or 'logger', or for questions "
        "like 'which file does X?', the Agent tool is strongly recommended.\n"
        "- If you want to read a specific file path, use the file_read tool instead of the "
        "Agent tool to find the match more quickly.\n\n"
        "Usage notes:\n"
        "1. Launch multiple agents concurrently whenever possible, to maximize performance; "
        "to do that, use a single plan step with multiple agent tool uses.\n"
        "2. When the agent is done, it will return a single text output back to you. The result "
        "returned by the agent is not directly visible to the user (only a summary is shown). "
        "To show the user the result, you should summarize the agent's output in your final message.\n"
        "3. Each agent invocation is stateless. You will not be able to send additional messages "
        "to the agent, nor will the agent communicate with you outside of its final report. "
        "Therefore, your prompt should contain a highly detailed task description for the agent "
        "to perform autonomously, and you should specify exactly what information the agent should return.\n"
        "4. IMPORTANT: The agent cannot use terminal, write_file, or vision tools. If you want to use "
        "these tools, use them directly instead of going through the agent."
    )
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The highly detailed task description for the agent to perform",
            }
        },
        "required": ["prompt"],
    }

    def __init__(self):
        super().__init__()
        # This will be injected dynamically by AgentWorker before execution
        self.api_client: Optional[Any] = None

    async def execute(self, prompt: str, **kwargs: Any) -> str:
        """Execute the agent tool by delegating to an isolated AgentManager."""
        if not self.api_client:
            return "Error: api_client not injected into AgentTool."

        logger.info(f"[AgentTool] Spawning sub-agent for task: {prompt[:50]}...")

        # 1. Create a scoped ToolRegistry with only read/research tools
        # OpenCode allows: GlobTool, GrepTool, LS, View.
        # VDA equivalent: web_search, web_fetch, file_read, file_glob, file_grep
        from vda.core.tool_registry.registry import ToolRegistry, get_registry
        scoped_registry = ToolRegistry()
        global_registry = get_registry()

        allowed_tools = ["web_search", "web_fetch", "file_read", "file_glob", "file_grep"]
        for t_name in allowed_tools:
            tool_cls = global_registry._registry.get(t_name)
            if tool_cls:
                # Copy the tool class to the scoped registry
                scoped_registry.register(t_name, tool_cls)

        # 2. Instantiate a fresh AgentManager with the scoped registry and NO vision
        from vda.core.agent_manager.agent_manager import AgentManager

        sub_manager = AgentManager(
            api_client=self.api_client,
            tool_registry=scoped_registry,
            vision_mode=False,
            # Pass a high max iterations to ensure it can finish complex searches
            max_iterations=50
        )

        # We start the agent directly in the INIT state with the prompt
        sub_manager.reset()
        sub_manager._user_input = prompt
        from vda.core.agent_manager.agent_manager import AgentState
        sub_manager.state = AgentState.INIT

        # 3. Run the agent loop until it reaches COMPLETE or ERROR
        result = await sub_manager.run_to_completion_async()

        return result
