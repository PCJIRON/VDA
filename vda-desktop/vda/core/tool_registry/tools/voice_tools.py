"""Voice tool — skeleton for Phase 6.

Speaks text responses via text-to-speech (TTS).
"""

import logging

from vda.core.tool_registry.base_tool import BaseTool
from vda.core.tool_registry.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("voice")
class VoiceTool(BaseTool):
    """Speak text response via TTS."""

    name = "voice"
    description = "Speak text response via TTS"
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to speak",
            }
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        """Execute tool. Full implementation deferred to Phase 6.

        Args:
            **kwargs: Must include ``text``.

        Returns:
            Error message indicating tool not yet implemented.
        """
        logger.warning("[%s] Stub called with args: %s", self.name, kwargs)
        return f"Error: {self.name} not implemented yet (Phase 6)"
