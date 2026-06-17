"""Patch tool — powered by opencode Go engine.

Applies patches to multiple files in one operation.
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool
from vda.opencode_bridge import call_tool

logger = logging.getLogger(__name__)


@register_tool("patch")
class PatchTool(BaseTool):
    """Apply a patch to multiple files in one operation (powered by opencode patch tool)."""

    name = "patch"
    description = """Apply patch to multiple files in one operation.

Patch format:
```
*** Begin Patch
*** Update File: /path/to/file
@@ Context line (unique within the file)
 Line to keep
-Line to remove
+Line to add
 Line to keep
*** Add File: /path/to/new/file
+Content of the new file
+More content
*** Delete File: /path/to/file/to/delete
*** End Patch
```

Each context line MUST uniquely identify the section. Include surrounding
lines for precise matching. Whitespace must match exactly.
"""
    parameters = {
        "type": "object",
        "properties": {
            "patch_text": {
                "type": "string",
                "description": "Patch text in the opencode patch format (see description)",
            },
        },
        "required": ["patch_text"],
    }

    async def execute(self, **kwargs) -> str:
        patch_text = kwargs.get("patch_text")
        if not patch_text:
            return "Error: patch_text is required"
        logger.info("[%s] Applying patch (%d chars)", self.name, len(patch_text))
        result = call_tool("patch", {"patch_text": patch_text})
        if result.get("is_error"):
            return result["content"]
        return result["content"]
