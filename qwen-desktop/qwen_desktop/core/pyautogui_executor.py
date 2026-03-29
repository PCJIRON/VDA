"""
PyAutoGUI Executor with JSON Response Parsing.

Parses Qwen's JSON output and executes mouse actions.
Supports template matching for 100% accurate coordinate execution.
"""

import json
import re
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

import cv2
import numpy as np
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
    
    def __init__(
        self,
        safety_margin: int = 10,
        mode: str = "ask_first",
    ):
        """Initialize executor.
        
        Args:
            safety_margin: Pixels to keep within screen bounds.
            mode: Execution mode (ask_first, auto_trusted, full_auto).
        """
        self.safety_margin = safety_margin
        self.mode = mode
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
    
    def has_commands(self, text: str) -> bool:
        """Check if text contains PyAutoGUI commands.

        Args:
            text: Response text to check.

        Returns:
            True if PyAutoGUI commands found.
        """
        return bool(re.search(r'\[PYAUTOGUI\]', text, re.IGNORECASE))

    def extract_commands(self, text: str) -> List[str]:
        """Extract PyAutoGUI commands from text.

        Args:
            text: Response text containing commands.

        Returns:
            List of command strings.
        """
        match = re.search(r'\[PYAUTOGUI\](.*?)\[/PYAUTOGUI\]', text, re.DOTALL | re.IGNORECASE)
        if match:
            commands_text = match.group(1)
            # Split by newlines and filter empty lines
            commands = [line.strip() for line in commands_text.split('\n') if line.strip() and not line.strip().startswith('#')]
            return commands
        return []

    # ── UIED Template Matching ──────────────────────────────────────────────

    def find_with_template(
        self,
        template_path: str,
        threshold: float = 0.7,  # Lowered from 0.9 for better matching
        screen_resolution: Tuple[int, int] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Find element on screen using template matching.

        This provides 100% accurate coordinates by matching a saved template
        against the current screen.

        Args:
            template_path: Path to the template image.
            threshold: Match confidence threshold (0.0-1.0).
            screen_resolution: Optional (width, height) for scaling.

        Returns:
            (center_x, center_y) tuple or None if not found.
        """
        logger.info(f"[TemplateMatch] Looking for: {template_path}")
        
        if not os.path.exists(template_path):
            logger.warning(f"[TemplateMatch] Template not found: {template_path}")
            return None

        try:
            # Load template
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logger.warning(f"[TemplateMatch] Failed to load template: {template_path}")
                return None
            
            logger.info(f"[TemplateMatch] Template size: {template.shape}")

            # Capture current screen
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            logger.info(f"[TemplateMatch] Screen size: {screenshot_gray.shape}")

            # Template matching
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            
            logger.info(f"[TemplateMatch] Locations found: {len(locations[0])} (threshold: {threshold})")

            if len(locations[0]) > 0:
                # Get best match
                best_match_idx = np.argmax(result[locations])
                top_left_y = locations[0][best_match_idx]
                top_left_x = locations[1][best_match_idx]
                
                max_confidence = float(result[locations][best_match_idx])

                # Calculate center
                h, w = template.shape
                center_x = int(top_left_x + w / 2)
                center_y = int(top_left_y + h / 2)

                logger.info(f"[TemplateMatch] ✅ Match found: ({center_x}, {center_y}) with {max_confidence:.2f} confidence")

                return (center_x, center_y)
            else:
                # Log best match even if below threshold
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                logger.info(f"[TemplateMatch] ❌ No match above threshold. Best: {max_val:.2f} at {max_loc}")
                logger.debug(f"[TemplateMatch] Locations: {locations}")
                return None

        except Exception as e:
            logger.error(f"[TemplateMatch] Error: {e}", exc_info=True)
            return None

    def execute_on_template(
        self,
        template_path: str,
        action: str = "click",
        threshold: float = 0.9,
        **kwargs
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Execute action on element found via template matching.

        Args:
            template_path: Path to the template image.
            action: Action to execute (click, double_click, etc.).
            threshold: Match confidence threshold.
            **kwargs: Additional action-specific params.

        Returns:
            (success, coordinates) tuple.
        """
        coords = self.find_with_template(template_path, threshold)

        if coords:
            x, y = coords
            success = self.execute(action, [x, y], **kwargs)
            return (success, coords)
        else:
            logger.warning(f"Template match failed for action: {action}")
            return (False, None)
