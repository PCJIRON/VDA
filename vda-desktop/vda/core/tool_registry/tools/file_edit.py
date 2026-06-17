"""File edit tool — powered by opencode Go engine.

Provides precise string replacement with uniqueness enforcement
and read-before-edit stale-file guard.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool
from vda.opencode_bridge import call_tool

logger = logging.getLogger(__name__)


@register_tool("file_edit")
class FileEditTool(BaseTool):
    """Edit a file by replacing text (powered by opencode edit tool)."""

    name = "file_edit"
    description = """Edit files by replacing text, creating new files, or deleting content.

CRITICAL: The old_string MUST be unique within the file. Include 3-5 lines
of context BEFORE and AFTER the change point to ensure uniqueness.

To make a file edit:
1. file_path: The path to the file to modify (absolute or relative)
2. old_string: The text to replace (must match EXACTLY, including whitespace)
3. new_string: The edited text to replace the old_string

Special cases:
- To create a new file: provide file_path and new_string, leave old_string empty
- To delete content: provide file_path and old_string, leave new_string empty
"""
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to modify (use absolute path if possible)",
            },
            "old_string": {
                "type": "string",
                "description": "The text to replace (must be unique and match EXACTLY)",
            },
            "new_string": {
                "type": "string",
                "description": "The new text to replace the old_string with",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file_path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")

        if not file_path:
            return "Error: file_path is required"
        if old_string is None or new_string is None:
            return "Error: both old_string and new_string are required"

        logger.info("[%s] Editing file: %s", self.name, file_path)
        result = call_tool("edit", {"file_path": file_path, "old_string": old_string, "new_string": new_string})
        if result.get("is_error"):
            return result["content"]
        return result["content"]
