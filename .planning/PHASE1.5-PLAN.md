# Phase 1.5: Remove OpenCV + Fix Vision Trigger

**Date:** 2026-03-29  
**Goal:** Simplify vision mode - remove OpenCV, capture only on user input

---

## Changes Required

### 1. Remove OpenCV Imports

**File:** `floating_assistant.py`

Remove:
```python
from qwen_desktop.core.opencv_detector import OpenCVDetector
import cv2
import numpy as np
```

### 2. Remove OpenCV Detector Initialization

**File:** `floating_assistant.py`

Remove:
```python
# Initialize OpenCV detector for precise coordinate detection
self.opencv_detector = OpenCVDetector()
```

### 3. Simplify Vision Handler

**Remove:**
- Mouse movement threshold check (`_last_mouse_pos`)
- Worker creation flag (`_worker_creating`)
- Race condition prevention (no longer needed)

**Keep:**
- Rate limit handling
- Screenshot capture
- Qwen API call with metadata

### 4. Enhanced Prompt for Qwen

**New vision_text:**
```python
vision_text = (
    f"[VISION METADATA]\n"
    f"Screen Resolution: {sw}x{sh}\n"
    f"Current Mouse Position: ({mx}, {my})\n"
    f"Relative Position: ({xp:.3f}, {yp:.3f}) of screen\n\n"
    f"[TASK]\n"
    f"Analyze the attached screenshot. The user wants to interact with a UI element.\n"
    f"Use the current mouse position as context for what they're looking at.\n\n"
    f"[OUTPUT FORMAT]\n"
    f"Respond in this EXACT JSON format:\n"
    f"{{\n"
    f'  "action": "click",\n'
    f'  "target": [x, y],  // Pixel-perfect coordinates for {sw}x{sh} screen\n'
    f'  "confidence": 0.95,\n'
    f'  "description": "What element you found and why these coordinates"\n'
    f"}}\n\n"
    f"[IMPORTANT]\n"
    f"- Calculate coordinates for the FULL screen resolution ({sw}x{sh})\n"
    f"- If element is near current mouse, use those coordinates\n"
    f"- Be PRECISE - user will click exactly where you specify\n"
    f"- Center of buttons/icons is the best target\n"
)
```

### 5. Remove OpenCV Refinement

**File:** `floating_assistant.py`

Remove from `_execute_vision_action`:
```python
# If confidence is low (<80%), try OpenCV for better precision
if confidence < 0.8 and hasattr(self, 'opencv_detector'):
    # ... OpenCV refinement code ...
```

---

## How Vision Mode Works Now

### Before (Broken):
```
User moves mouse → Screenshot → API → Click → Screenshot → API → Click
                    ↑                                                ↑
                    └──────────── Infinite Loop ────────────────────┘
```

### After (Fixed):
```
User enables vision → Types "click submit" → Screenshot → API → Click → Done
                      ↑
                      └── Only captures on EXPLICIT user input
```

---

## Benefits

1. **No Infinite Loop** - No auto-triggering on mouse movement
2. **No Quota Waste** - Only 1 API call per user request
3. **Simpler Code** - Removed OpenCV complexity
4. **Qwen Does Everything** - Bounding box + coordinate calculation
5. **Pixel-Perfect** - Qwen calculates coordinates with full screen context

---

## Testing

**Test Scenario:**
1. Enable vision mode (click eye icon)
2. Type: "Click the submit button"
3. Press Enter
4. Screenshot captured ONCE
5. Qwen analyzes with metadata
6. Returns coordinates
7. Executes click

**Expected:**
- 1 API call per user input
- No infinite loops
- Accurate coordinates from Qwen

---

**Status:** Ready to implement
