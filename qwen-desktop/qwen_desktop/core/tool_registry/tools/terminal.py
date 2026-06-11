"""Terminal tool — skeleton for Phase 4.

Executes shell commands and returns stdout/stderr output.
"""

import logging

from qwen_desktop.core.tool_registry.base_tool import BaseTool
from qwen_desktop.core.tool_registry.registry import register_tool

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
        """Execute tool. Full implementation deferred to Phase 4.

        Args:
            **kwargs: Must include ``command``, optionally ``shell``.

        Returns:
            Error message indicating tool not yet implemented.
        """
        logger.warning("[%s] Stub called with args: %s", self.name, kwargs)
        return f"Error: {self.name} not implemented yet (Phase 4)"
