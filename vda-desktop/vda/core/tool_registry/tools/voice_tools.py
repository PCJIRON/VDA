"""Voice tool — skeleton for Phase 6.

Speaks text responses via text-to-speech (TTS).
"""

import logging
import subprocess

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
        """Execute tool.

        Args:
            **kwargs: Must include ``text``.

        Returns:
            Success message or error message.
        """
        text = kwargs.get("text")
        if not text:
            return "Error: No text specified to speak"

        logger.info("[%s] Speaking text: %s", self.name, text)

        # Clean quotes for PowerShell commands
        escaped_text = text.replace("'", "''").replace('"', '`"')

        # Primary: System.Speech.Synthesis
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{escaped_text}')"
        )

        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                return f"Successfully spoke: '{text}'"
        except Exception as e:
            logger.warning("[%s] Failed to speak via System.Speech: %s. Trying fallback.", self.name, e)

        # Fallback: SAPI.SpVoice COM Object
        sapi_cmd = f"(New-Object -ComObject SAPI.SpVoice).Speak('{escaped_text}')"
        try:
            result = subprocess.run(
                ["powershell", "-Command", sapi_cmd],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                return f"Successfully spoke: '{text}' (fallback)"
            return f"Error speaking: {result.stderr}"
        except Exception as e:
            logger.error("[%s] TTS speech failed completely: %s", self.name, e, exc_info=True)
            return f"Error speaking: {e}"
