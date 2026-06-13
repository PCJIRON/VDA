"""JSON response parsing for VDA/LLM action commands.

Extracted from the original monolithic ``PyAutoGUIExecutor``.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from VDA's response.

    Args:
        text: Response text (may contain JSON in markdown).

    Returns:
        Parsed dict or None if parsing fails.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    json_match = re.search(r'\{[^}]*"action"[^}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning(f"Failed to parse JSON from: {text[:200]}")
    return None


def has_commands(text: str) -> bool:
    """Check if text contains PyAutoGUI commands."""
    return bool(re.search(r'\[PYAUTOGUI\]', text, re.IGNORECASE))


def extract_commands(text: str) -> List[str]:
    """Extract PyAutoGUI commands from text."""
    match = re.search(r'\[PYAUTOGUI\](.*?)\[/PYAUTOGUI\]', text, re.DOTALL | re.IGNORECASE)
    if match:
        commands_text = match.group(1)
        commands = [
            line.strip()
            for line in commands_text.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        return commands
    return []
