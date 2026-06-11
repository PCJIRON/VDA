"""Tool definitions for OpenAI-compatible function calling.

Extracted from the original monolithic ``tool_executor.py``.
"""

from typing import Dict, Any, List


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Get OpenAI-compatible tool definitions.

    Returns:
        List of tool schemas.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file.",
                "parameters": {
                    "type": "object",
                    "properties": {"filepath": {"type": "string", "description": "Path to the file to read"}},
                    "required": ["filepath"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file. Overwrites if exists.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Path to the file to write"},
                        "content": {"type": "string", "description": "Content to write to the file"},
                    },
                    "required": ["filepath", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_shell",
                "description": "Execute a shell command. Requires user approval for destructive commands.",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string", "description": "The shell command to execute"}},
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Search for files using glob pattern or grep regex.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Regex pattern to search for (grep) or glob pattern"},
                        "type": {"type": "string", "enum": ["grep", "glob"], "description": "Type of search"},
                    },
                    "required": ["query", "type"],
                },
            },
        },
    ]
