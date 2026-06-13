"""Tool registry package — decorator-based registry with lazy initialization.

Provides BaseTool abstract class, ToolRegistry singleton, and
@register_tool decorator for registering tool implementations.
"""

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import ToolRegistry, get_registry, register_tool

# Import tools sub-package to trigger @register_tool decorators
from . import tools  # noqa: F401

__all__ = [
    "ToolRegistry",
    "BaseTool",
    "register_tool",
    "get_registry",
]
