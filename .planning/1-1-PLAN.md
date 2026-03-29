# Phase 1 Plan: Wave 1 - Enhanced Vision Mode

**Wave:** 1  
**Priority:** High  
**Estimated Time:** 2 hours  

---

## Objective

Enhance existing vision mode with better prompt engineering and structured JSON output for coordinate prediction.

**NO OpenCV, NO OCR, NO new dependencies** - Pure Qwen Vision!

---

## Tasks

### Task 1.1: Enhance Vision System Prompt

**File:** `qwen_desktop/core/api_client.py` (modify VISION_SYSTEM_PROMPT)

**Implementation:**

```python
# Enhanced system prompt for better coordinate prediction
VISION_SYSTEM_PROMPT = """
You are an expert UI automation assistant with vision capabilities.

=== YOUR TASK ===
When you receive a screenshot with mouse coordinates:
1. Analyze all visible UI elements
2. Find the target element based on user request
3. Return EXACT pixel coordinates [x, y] for the action

=== COORDINATE RULES ===
- Screen resolution: {screen_w}x{screen_h}
- Valid X range: 0 to {screen_w}
- Valid Y range: 0 to {screen_h}
- Origin (0,0) is TOP-LEFT corner
- X increases going RIGHT
- Y increases going DOWN

=== OUTPUT FORMAT ===
Respond in this EXACT JSON format:
{
  "action": "click",
  "target": [x, y],
  "confidence": 0.95,
  "description": "Found Submit button at bottom of form"
}

Action types: click, double_click, right_click, move, drag_start, drag_end

=== IMPORTANT ===
- Be PRECISE - user will click exactly where you specify
- Center of buttons/icons is usually the best target
- If multiple elements match, pick the most prominent one
- If unsure, ask for clarification in description
- Never return coordinates outside screen bounds
"""
```

**Verification:**
- [ ] System prompt includes screen resolution context
- [ ] Clear coordinate rules defined
- [ ] JSON output format specified
- [ ] Action types documented

---

### Task 1.2: Add JSON Response Parser

**File:** `qwen_desktop/core/pyautogui_executor.py` (new file)

**Implementation:**

```python
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
```

**Verification:**
- [ ] JSON parsing handles markdown code blocks
- [ ] Coordinate validation clamps to screen bounds
- [ ] All action types supported
- [ ] Error handling in place

---

### Task 1.3: Integrate Parser with Floating Assistant

**File:** `qwen_desktop/ui/floating_assistant.py` (modify `_on_api_finished`)

**Implementation:**

```python
# Add at top of file
from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor

# In FloatingAssistant.__init__
self.pyautogui_executor = PyAutoGUIExecutor()

# Modify _on_api_finished method
def _on_api_finished(self, full_text):
    self._set_send_mode()  # restore send button
    self.history_popup.update_last_message(full_text)
    
    # Save to session
    self.last_msg_uuid = self.session_service.save_message(
        self.session_id, "assistant", full_text, parent_uuid=self.last_msg_uuid
    )
    self._chat_history.append({"role": "assistant", "content": full_text})
    
    # ── NEW: Parse and execute vision actions ──────────────────────────────
    parsed = self.pyautogui_executor.parse_response(full_text)
    
    if parsed and "target" in parsed:
        # Extract action details
        action = parsed.get("action", "click")
        target = parsed["target"]
        confidence = parsed.get("confidence", 1.0)
        description = parsed.get("description", "")
        
        # Show what we're doing
        self.history_popup.add_message(
            f"🎯 {description}\nExecuting: {action} at {target}",
            "ai",
        )
        
        # Execute after short delay (user can see what's happening)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(
            500,
            lambda: self._execute_vision_action(action, target, confidence),
        )
    
    # ── PyAutoGUI command detection (existing) ────────────────────────────
    if self._pyautogui_executor.has_commands(full_text):
        commands = self._pyautogui_executor.extract_commands(full_text)
        if commands:
            self._handle_pyautogui_commands(commands)

def _execute_vision_action(
    self,
    action: str,
    target: List[int],
    confidence: float,
):
    """Execute vision-based action with confirmation."""
    # Low confidence - ask for confirmation
    if confidence < 0.7:
        self.history_popup.add_message(
            f"⚠️ Low confidence ({confidence:.0%}). Should I proceed?",
            "ai",
        )
        # Add confirm/skip buttons (implement later)
        return
    
    # Execute directly
    success = self.pyautogui_executor.execute(action, target, confidence)
    
    if success:
        self.history_popup.add_message("✅ Action completed!", "ai")
    else:
        self.history_popup.add_message("❌ Action failed!", "ai")
```

**Verification:**
- [ ] Parser imported
- [ ] JSON response parsed automatically
- [ ] Coordinates validated before execution
- [ ] User sees what's happening
- [ ] Low confidence asks for confirmation

---

## Verification Checklist

- [ ] Enhanced system prompt with coordinate rules
- [ ] JSON parser handles all response formats
- [ ] Coordinate validation prevents out-of-bounds clicks
- [ ] All action types supported (click, drag, etc.)
- [ ] Floating assistant integrates parser
- [ ] User feedback shows what's happening

---

## Output

**Files Created:**
- `qwen_desktop/core/pyautogui_executor.py` - JSON parser + action executor

**Files Modified:**
- `qwen_desktop/core/api_client.py` - Enhanced VISION_SYSTEM_PROMPT
- `qwen_desktop/ui/floating_assistant.py` - Integrate parser

**Lines of Code:** ~200

---

**Ready to Execute:** Run `/gsd:execute-phase 1` to implement Wave 1.
