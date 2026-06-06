"""ToolExecutor — dispatcher for file, shell, and search tools.

Extracted from the original monolithic ``tool_executor.py``.
"""

import os
from typing import Dict, Any

from ._tool_defs import get_tool_definitions
from ._file_ops import read_file as _read_file, write_file as _write_file, search_files as _search_files
from ._shell_ops import execute_shell as _execute_shell


class ToolExecutor:
    """Executes local tools (fileops, shell) for the AI assistant."""

    def __init__(self, workspace_dir: str = None) -> None:
        self.workspace_dir = workspace_dir or os.getcwd()

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible tool definitions."""
        return get_tool_definitions()

    def execute_tool(self, name: str, kwargs: Dict[str, Any]) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name.
            kwargs: Tool arguments.

        Returns:
            Tool result as string.
        """
        try:
            if name == "read_file":
                return self.read_file(**kwargs)
            if name == "write_file":
                return self.write_file(**kwargs)
            if name == "execute_shell":
                return self.execute_shell(**kwargs)
            if name == "search_files":
                return self.search_files(**kwargs)
            return f"Error: Unknown tool '{name}'"
        except Exception as exc:
            return f"Error executing {name}: {exc}"

    def read_file(self, filepath: str) -> str:
        """Read file contents."""
        return _read_file(filepath, self.workspace_dir)

    def write_file(self, filepath: str, content: str) -> str:
        """Write content to file."""
        return _write_file(filepath, content, self.workspace_dir)

    def execute_shell(self, command: str) -> str:
        """Execute a shell command."""
        return _execute_shell(command, self.workspace_dir)

    def search_files(self, query: str, search_type: str) -> str:
        """Search for files."""
        return _search_files(query, search_type, self.workspace_dir)
