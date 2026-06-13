"""Terminal tool — skeleton for Phase 4.

Executes shell commands and returns stdout/stderr output.
"""

import logging
import os

from vda.core.tool_executor._shell_ops import execute_shell
from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("terminal")
class TerminalTool(BaseTool):
    """Execute a shell command and return stdout/stderr."""

    name = "terminal"
    description = "Execute a shell command and return stdout/stderr"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Command to execute",
            },
            "shell": {
                "type": "string",
                "description": "Shell to use (powershell, cmd, bash)",
                "default": "powershell",
            },
        },
        "required": ["command"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``command``.

        Returns:
            Command output or error message.
        """
        command = kwargs.get("command")
        if not command:
            return "Error: No command specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Executing command: %s", self.name, command)
        return execute_shell(command, workspace_dir)
