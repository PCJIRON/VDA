"""Abstract base class for all tools.

All tool implementations inherit from BaseTool and must implement
the async execute method. Tools register themselves via the
@register_tool decorator from the registry module.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseTool:
    """Abstract base class for tool implementations.

    Subclasses set name, description, and parameters as class attributes.
    The execute method is the main entry point for tool invocation.

    Attributes:
        name: Tool name identifier used for registration and invocation.
        description: Human-readable description of what the tool does.
        parameters: JSON Schema dict describing accepted parameters.
    """

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the given arguments.

        All tool implementations must override this method.

        Args:
            **kwargs: Tool-specific keyword arguments matching the
                parameter schema defined in ``parameters``.

        Returns:
            String result of tool execution.

        Raises:
            NotImplementedError: If the subclass does not override
                this method.
        """
        raise NotImplementedError(
            f"Tool '{self.name}' has not implemented execute()"
        )
