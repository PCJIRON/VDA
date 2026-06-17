"""File tools — powered by opencode Go engine.

Tools delegate to the opencode Go toolserver binary via subprocess,
preserving opencode's exact implementation for view, glob, grep, and ls.
"""

import logging
import os

from vda.core.tool_executor._file_ops import read_file, write_file
from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool
from vda.opencode_bridge import call_tool

logger = logging.getLogger(__name__)


@register_tool("file_read")
class FileReadTool(BaseTool):
    """Read a file with line numbers (powered by opencode view tool)."""

    name = "file_read"
    description = "Read a file and return its contents with line numbers"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read",
            },
            "offset": {
                "type": "integer",
                "description": "The line number to start reading from (0-based). Defaults to 0.",
            },
            "limit": {
                "type": "integer",
                "description": "The number of lines to read. Defaults to 2000.",
            },
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        if not path:
            return "Error: No path specified"
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 2000)
        logger.info("[%s] Reading file: %s (offset=%d, limit=%d)", self.name, path, offset, limit)
        result = call_tool("view", {"file_path": path, "offset": offset, "limit": limit})
        if result.get("is_error"):
            return result["content"]
        return result["content"]


@register_tool("file_write")
class FileWriteTool(BaseTool):
    """Write content to a file (Python native)."""

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
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        if not path:
            return "Error: No path specified"
        workspace_dir = os.getcwd()
        logger.info("[%s] Writing to file: %s", self.name, path)
        return write_file(path, content, workspace_dir)


@register_tool("file_glob")
class FileGlobTool(BaseTool):
    """Find files matching a glob pattern (powered by opencode glob tool)."""

    name = "file_glob"
    description = "Find files matching a glob pattern, sorted by modification time (newest first)"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The glob pattern to match (e.g. **/*.py, *.js, src/**/*.{ts,tsx})",
            },
            "path": {
                "type": "string",
                "description": "The directory to search in. Defaults to current working directory.",
            },
        },
        "required": ["pattern"],
    }

    async def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        if not pattern:
            return "Error: No pattern specified"
        search_path = kwargs.get("path")
        logger.info("[%s] Glob searching: %s in %s", self.name, pattern, search_path or ".")
        result = call_tool("glob", {"pattern": pattern, "path": search_path})
        if result.get("is_error"):
            return result["content"]
        return result["content"]


@register_tool("file_grep")
class FileGrepTool(BaseTool):
    """Search file contents using a regex pattern (powered by opencode grep tool)."""

    name = "file_grep"
    description = "Search file contents using a regex or literal pattern, sorted by modification time"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regex pattern to search for in file contents",
            },
            "path": {
                "type": "string",
                "description": "The directory to search in. Defaults to current working directory.",
            },
            "include": {
                "type": "string",
                "description": "File pattern to include (e.g. *.py, *.{ts,tsx})",
            },
            "literal_text": {
                "type": "boolean",
                "description": "If true, pattern is treated as literal text. Default: false",
            },
        },
        "required": ["pattern"],
    }

    async def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        if not pattern:
            return "Error: No pattern specified"
        search_path = kwargs.get("path")
        include = kwargs.get("include")
        literal_text = kwargs.get("literal_text", False)
        logger.info("[%s] Grep searching: %s", self.name, pattern)
        result = call_tool(
            "grep",
            {
                "pattern": pattern,
                "path": search_path,
                "include": include,
                "literal_text": literal_text,
            },
        )
        if result.get("is_error"):
            return result["content"]
        return result["content"]


@register_tool("dir_list")
class DirListTool(BaseTool):
    """List directory contents in a tree structure (powered by opencode ls tool)."""

    name = "dir_list"
    description = "Directory listing tool that shows files and subdirectories in a tree structure"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the directory to list. Defaults to current working directory.",
            },
            "ignore": {
                "type": "array",
                "description": "List of glob patterns to ignore",
                "items": {"type": "string"},
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        search_path = kwargs.get("path")
        ignore = kwargs.get("ignore")
        logger.info("[%s] Listing directory: %s", self.name, search_path or ".")
        result = call_tool("ls", {"path": search_path, "ignore": ignore})
        if result.get("is_error"):
            return result["content"]
        return result["content"]
