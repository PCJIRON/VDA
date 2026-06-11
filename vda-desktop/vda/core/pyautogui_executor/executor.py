"""PyAutoGUI Executor - mouse actions based on VDA's coordinates.

Extracted from the original monolithic ``PyAutoGUIExecutor``.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

import pyautogui

from .response_parser import parse_response as _parse_response
from .response_parser import has_commands as _has_commands
from .response_parser import extract_commands as _extract_commands
from .template_matcher import find_with_template as _find_template
from .template_matcher import find_with_template

logger = logging.getLogger(__name__)


class PyAutoGUIExecutor:
    """Execute mouse actions based on VDA's coordinates."""

    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE = "move"
    DRAG_START = "drag_start"
    DRAG_END = "drag_end"

    ASK_FIRST = "ask_first"
    AUTO_TRUSTED = "auto_trusted"
    FULL_AUTO = "full_auto"

    def __init__(self, safety_margin: int = 10, mode: str = "ask_first"):
        self.safety_margin = safety_margin
        self.mode = mode
        self.screen_w, self.screen_h = pyautogui.size()

    def parse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from VDA's response."""
        return _parse_response(text)

    def validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Validate and clamp coordinates to screen bounds."""
        x = max(self.safety_margin, min(x, self.screen_w - self.safety_margin))
        y = max(self.safety_margin, min(y, self.screen_h - self.safety_margin))
        return x, y

    def execute(self, action: str, target: List[int], confidence: float = 1.0, **kwargs) -> bool:
        """Execute mouse action at target coordinates."""
        if len(target) != 2:
            logger.error(f"Invalid target coordinates: {target}")
            return False
        x, y = self.validate_coordinates(target[0], target[1])
        logger.info(f"Executing {action} at [{x}, {y}] (confidence: {confidence})")
        try:
            if action == self.CLICK:
                pyautogui.click(x, y)
            elif action == self.DOUBLE_CLICK:
                pyautogui.doubleClick(x, y)
            elif action == self.RIGHT_CLICK:
                pyautogui.rightClick(x, y)
            elif action == self.MOVE:
                pyautogui.moveTo(x, y, duration=0.3)
            elif action == self.DRAG_START:
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.mouseDown()
            elif action == self.DRAG_END:
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.mouseUp()
            else:
                logger.warning(f"Unknown action: {action}")
                return False
            return True
        except Exception as exc:
            logger.error(f"Action execution failed: {exc}")
            return False

    def execute_drag(self, start: List[int], end: List[int], duration: float = 0.5) -> bool:
        """Execute drag operation from start to end."""
        try:
            x1, y1 = self.validate_coordinates(start[0], start[1])
            x2, y2 = self.validate_coordinates(end[0], end[1])
            pyautogui.moveTo(x1, y1, duration=duration / 2)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration / 2)
            return True
        except Exception as exc:
            logger.error(f"Drag execution failed: {exc}")
            return False

    def has_commands(self, text: str) -> bool:
        """Check if text contains PyAutoGUI commands."""
        return _has_commands(text)

    def extract_commands(self, text: str) -> List[str]:
        """Extract PyAutoGUI commands from text."""
        return _extract_commands(text)

    def find_with_template(self, template_path: str, threshold: float = 0.55,
                           screen_resolution: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """Find element on screen using multi-scale template matching."""
        return _find_template(template_path, threshold, screen_resolution)

    def execute_on_template(self, template_path: str, action: str = "click",
                            threshold: float = 0.9, **kwargs) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Execute action on element found via template matching."""
        coords = _find_template(template_path, threshold)
        if coords:
            x, y = coords
            success = self.execute(action, [x, y], **kwargs)
            return success, coords
        logger.warning(f"Template match failed for action: {action}")
        return False, None
