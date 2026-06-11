"""Web search tool — skeleton for Phase 3.

Searches the web via configured search API and returns structured results.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("web_search")
class WebSearchTool(BaseTool):
    """Search the web for a query and return structured results."""

    name = "web_search"
    description = "Search the web for a query and return structured results"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            }
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool. Full implementation deferred to Phase 3.

        Args:
            **kwargs: Must include ``query``.

        Returns:
            Error message indicating tool not yet implemented.
        """
        logger.warning("[%s] Stub called with args: %s", self.name, kwargs)
        return f"Error: {self.name} not implemented yet (Phase 3)"
