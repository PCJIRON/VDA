"""
PyAutoGUI Executor with JSON Response Parsing.

Parses Qwen's JSON output and executes mouse actions.
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
import pyautogui

logger = logging.getLogger(__name__)


class PyAutoGUIExecutor:
    """Execute mouse actions based on Qwen's coordinates."""
    
    # Action types
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE = "move"
    DRAG_START = "drag_start"
    DRAG_END = "drag_end"
    
    # Execution modes
    ASK_FIRST = "ask_first"
    AUTO_TRUSTED = "auto_trusted"
    FULL_AUTO = "full_auto"
    
    def __init__(self, safety_margin: int = 10):
        """Initialize executor.
        
        Args:
            safety_margin: Pixels to keep within screen bounds.
        """
        self.safety_margin = safety_margin
        self.screen_w, self.screen_h = pyautogui.size()
    
    def parse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Qwen's response.
        
        Args:
            text: Response text (may contain JSON in markdown).
        
        Returns:
            Parsed dict or None if parsing fails.
        """
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Look for JSON in markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for JSON-like structure
        json_match = re.search(r'\{[^}]*"action"[^}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Failed to parse JSON from: {text[:200]}")
        return None
    
    def validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Validate and clamp coordinates to screen bounds.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
        
        Returns:
            Clamped (x, y) within valid range.
        """
        x = max(self.safety_margin, min(x, self.screen_w - self.safety_margin))
        y = max(self.safety_margin, min(y, self.screen_h - self.safety_margin))
        return x, y
    
    def execute(
        self,
        action: str,
        target: List[int],
        confidence: float = 1.0,
        **kwargs,
    ) -> bool:
        """Execute mouse action.
        
        Args:
            action: Action type (click, double_click, etc.).
            target: [x, y] coordinates.
            confidence: Confidence score (0.0-1.0).
            **kwargs: Additional action-specific params.
        
        Returns:
            True if executed successfully.
        """
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
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False
    
    def execute_drag(
        self,
        start: List[int],
        end: List[int],
        duration: float = 0.5,
    ) -> bool:
        """Execute drag operation.
        
        Args:
            start: [x1, y1] start coordinates.
            end: [x2, y2] end coordinates.
            duration: Drag duration in seconds.
        
        Returns:
            True if executed successfully.
        """
        try:
            x1, y1 = self.validate_coordinates(start[0], start[1])
            x2, y2 = self.validate_coordinates(end[0], end[1])
            
            pyautogui.moveTo(x1, y1, duration=duration/2)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration/2)
            
            return True
        except Exception as e:
            logger.error(f"Drag execution failed: {e}")
            return False
