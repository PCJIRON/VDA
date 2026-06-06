"""Web fetch tool — skeleton for Phase 3.

Fetches content from a URL and returns it as clean markdown.
"""

import logging

from qwen_desktop.core.tool_registry.base_tool import BaseTool
from qwen_desktop.core.tool_registry.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("web_fetch")
class WebFetchTool(BaseTool):
    """Fetch content from a URL and return as clean markdown."""

    name = "web_fetch"
    description = "Fetch content from a URL and return as clean markdown"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch",
            }
        },
        "required": ["url"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool. Full implementation deferred to Phase 3.

        Args:
            **kwargs: Must include ``url``.

        Returns:
            Error message indicating tool not yet implemented.
        """
        logger.warning("[%s] Stub called with args: %s", self.name, kwargs)
        return f"Error: {self.name} not implemented yet (Phase 3)"
