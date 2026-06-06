"""Tool registry package — decorator-based registry with lazy initialization.

Provides BaseTool abstract class, ToolRegistry singleton, and
@register_tool decorator for registering tool implementations.
"""

from qwen_desktop.core.tool_registry.registry import ToolRegistry, register_tool, get_registry
from qwen_desktop.core.tool_registry.base_tool import BaseTool

__all__ = [
    "ToolRegistry",
    "BaseTool",
    "register_tool",
    "get_registry",
]
