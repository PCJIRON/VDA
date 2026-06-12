"""File tools — skeletons for Phase 5.

Provides file read, write, glob search, and grep search tools.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

import os
from vda.core.tool_executor._file_ops import read_file, write_file, search_files

logger = logging.getLogger(__name__)


@register_tool("file_read")
class FileReadTool(BaseTool):
    """Read a file and return its contents."""

    name = "file_read"
    description = "Read a file and return its contents"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read",
            }
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``path``.

        Returns:
            File content or error message.
        """
        path = kwargs.get("path")
        if not path:
            return "Error: No path specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Reading file: %s", self.name, path)
        return read_file(path, workspace_dir)


@register_tool("file_write")
class FileWriteTool(BaseTool):
    """Write content to a file."""

    name = "file_write"
    description = "Write content to a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["path", "content"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``path`` and ``content``.

        Returns:
            Success message or error message.
        """
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        if not path:
            return "Error: No path specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Writing to file: %s", self.name, path)
        return write_file(path, content, workspace_dir)


@register_tool("file_glob")
class FileGlobTool(BaseTool):
    """Find files matching a glob pattern."""

    name = "file_glob"
    description = "Find files matching a glob pattern"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match (e.g. **/*.py)",
            }
        },
        "required": ["pattern"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``pattern``.

        Returns:
            Glob search results.
        """
        pattern = kwargs.get("pattern")
        if not pattern:
            return "Error: No pattern specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Glob searching: %s", self.name, pattern)
        return search_files(pattern, "glob", workspace_dir)


@register_tool("file_grep")
class FileGrepTool(BaseTool):
    """Search file contents using a regex pattern."""

    name = "file_grep"
    description = "Search file contents using a regex pattern"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regex pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "Directory path to search in",
            },
        },
        "required": ["pattern", "path"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool.

        Args:
            **kwargs: Must include ``pattern`` and ``path``.

        Returns:
            Grep search results.
        """
        pattern = kwargs.get("pattern")
        path = kwargs.get("path")
        if not pattern:
            return "Error: No pattern specified"
        if not path:
            return "Error: No path specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Grep searching: %s in %s", self.name, pattern, path)
        # Resolve search path relative to workspace if it's not absolute
        resolved_path = path
        if not os.path.isabs(path):
            resolved_path = os.path.join(workspace_dir, path)
        return search_files(pattern, "grep", resolved_path)
