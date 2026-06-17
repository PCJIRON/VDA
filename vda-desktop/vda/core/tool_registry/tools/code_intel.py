"""Code intelligence tools — diagnostics and sourcegraph search via opencode Go engine.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool
from vda.opencode_bridge import call_tool

logger = logging.getLogger(__name__)


@register_tool("diagnostics")
class DiagnosticsTool(BaseTool):
    """Get diagnostics for a file or project via LSP (powered by opencode diagnostics tool)."""

    name = "diagnostics"
    description = "Get diagnostics (errors, warnings, hints) for a file or project via LSP"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to get diagnostics for. Leave empty for project-wide.",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file_path", "")
        logger.info("[%s] Getting diagnostics for: %s", self.name, file_path or "project")
        result = call_tool("diagnostics", {"file_path": file_path})
        if result.get("is_error"):
            return result["content"]
        return result["content"]


@register_tool("sourcegraph")
class SourcegraphTool(BaseTool):
    """Search code across public repositories using Sourcegraph (powered by opencode sourcegraph tool)."""

    name = "sourcegraph"
    description = "Search code across public repositories using Sourcegraph's GraphQL API"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (supports Sourcegraph query syntax e.g. repo:, lang:, file:)",
            },
            "count": {
                "type": "integer",
                "description": "Number of results to return (default: 10)",
            },
            "context_window": {
                "type": "integer",
                "description": "Lines of context around each match (default: 5)",
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds (default: 15)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return "Error: query is required"
        count = kwargs.get("count", 10)
        context_window = kwargs.get("context_window", 5)
        timeout = kwargs.get("timeout", 15)
        logger.info("[%s] Sourcegraph search: %s", self.name, query[:100])
        result = call_tool("sourcegraph", {
            "query": query,
            "count": count,
            "context_window": context_window,
            "timeout": timeout,
        })
        if result.get("is_error"):
            return result["content"]
        return result["content"]
