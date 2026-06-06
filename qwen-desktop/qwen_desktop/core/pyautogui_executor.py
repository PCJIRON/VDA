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
        threshold: float = 0.55,  # Lowered for robust multi-scale matching
        screen_resolution: Tuple[int, int] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Find element on screen using multi-scale template matching.

        Tries matching at multiple scales (0.7x to 1.3x) to handle DPI
        mismatches between Qt grabWindow (physical pixels) and pyautogui
        screenshot output.

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
            template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template_orig is None:
                logger.warning(f"[TemplateMatch] Failed to load template: {template_path}")
                return None
            
            logger.info(f"[TemplateMatch] Template size: {template_orig.shape}")

            # Capture current screen
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            logger.info(f"[TemplateMatch] Screen size: {screenshot_gray.shape}")

            # Determine DPI ratio for intelligent scale selection
            dpr = 1.0
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                    if screen:
                        dpr = screen.devicePixelRatio()
            except Exception:
                pass

            # Multi-scale template matching
            # Primary scales: 1.0x (same resolution), 1/dpr (physical→logical), dpr (logical→physical)
            # Additional scales around those for robustness
            scales_set = set()
            for base_scale in [1.0, 1.0 / dpr if dpr > 1.0 else 1.0, dpr if dpr > 1.0 else 1.0]:
                for delta in [-0.15, -0.05, 0.0, 0.05, 0.15]:
                    s = round(base_scale + delta, 2)
                    if 0.4 <= s <= 2.0:
                        scales_set.add(s)
            scales = sorted(scales_set)
            
            logger.info(f"[TemplateMatch] DPR={dpr}, trying {len(scales)} scales: {scales}")

            best_score = -1.0
            best_location = None
            best_scale = None
            best_template_shape = None

            for scale in scales:
                h_orig, w_orig = template_orig.shape[:2]
                new_w = max(1, int(w_orig * scale))
                new_h = max(1, int(h_orig * scale))
                
                # Skip if template is too large for the screenshot
                if new_w >= screenshot_gray.shape[1] or new_h >= screenshot_gray.shape[0]:
                    continue
                # Skip if template is too small to be meaningful
                if new_w < 8 or new_h < 8:
                    continue

                if scale == 1.0:
                    template_scaled = template_orig
                else:
                    template_scaled = cv2.resize(template_orig, (new_w, new_h), interpolation=cv2.INTER_AREA)

                result = cv2.matchTemplate(screenshot_gray, template_scaled, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val > best_score:
                    best_score = max_val
                    best_location = max_loc
                    best_scale = scale
                    best_template_shape = template_scaled.shape

            logger.info(f"[TemplateMatch] Best match: score={best_score:.3f} at {best_location} scale={best_scale}")

            if best_score >= threshold and best_location is not None and best_template_shape is not None:
                h, w = best_template_shape[:2]
                center_x = int(best_location[0] + w / 2)
                center_y = int(best_location[1] + h / 2)

                logger.info(f"[TemplateMatch] ✅ Match found: ({center_x}, {center_y}) with {best_score:.3f} confidence at scale {best_scale}")
                return (center_x, center_y)
            else:
                logger.info(f"[TemplateMatch] ❌ No match above threshold {threshold}. Best: {best_score:.3f} at {best_location} scale={best_scale}")
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
