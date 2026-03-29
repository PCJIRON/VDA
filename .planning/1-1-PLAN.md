# Phase 1 Plan: Wave 1 - Element Detection Core

**Wave:** 1  
**Priority:** High  
**Estimated Time:** 4 hours  

---

## Objective

Implement the core element detection engine with OpenCV template matching and pytesseract OCR integration.

---

## Tasks

### Task 1.1: Create ElementDetector Class

**File:** `qwen_desktop/core/element_detector.py`

**Implementation:**

```python
"""
Element Detection Engine.

Combines OpenCV template matching with pytesseract OCR for
accurate UI element detection across multiple resolutions.
"""

import cv2
import numpy as np
import pyautogui
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .coordinate_scaler import CoordinateScaler
from .element_cache import ElementCache
from ..utils.ocr import OCRService


@dataclass
class DetectionResult:
    """Result of element detection."""
    name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    center_x: int
    center_y: int
    method: str  # 'template' or 'ocr'
    scaled: bool


class ElementDetector:
    """Main element detection engine."""
    
    def __init__(self, base_resolution: tuple = (1920, 1080)):
        """Initialize detector.
        
        Args:
            base_resolution: Base resolution for templates (default: 1080p).
        """
        self.scaler = CoordinateScaler(base_resolution)
        self.cache = ElementCache(default_ttl=5.0)
        self.ocr_service = OCRService()
    
    def detect(
        self,
        name: str,
        template_path: Optional[str] = None,
        text_query: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[DetectionResult]:
        """Detect element by template or text.
        
        Args:
            name: Element name for caching.
            template_path: Path to template image (optional).
            text_query: Text to search for (optional).
            use_cache: Whether to use caching (default: True).
        
        Returns:
            DetectionResult if found, None otherwise.
        """
        # Check cache
        if use_cache:
            cache_key = f"{name}:{template_path}:{text_query}"
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Capture screenshot
        screenshot = self._capture_screen()
        
        # Try template matching
        if template_path:
            result = self._match_template(screenshot, template_path)
            if result:
                if use_cache:
                    self.cache.set(cache_key, result)
                return result
        
        # Try OCR
        if text_query:
            result = self.ocr_service.find_text(screenshot, text_query)
            if result:
                detection_result = DetectionResult(
                    name=name,
                    confidence=result['confidence'] / 100.0,
                    bbox=result['bbox'],
                    center_x=result['center'][0],
                    center_y=result['center'][1],
                    method='ocr',
                    scaled=False,
                )
                if use_cache:
                    self.cache.set(cache_key, detection_result)
                return detection_result
        
        return None
    
    def _capture_screen(self) -> np.ndarray:
        """Capture current screen as OpenCV image."""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def _match_template(
        self,
        screenshot: np.ndarray,
        template_path: str,
        threshold: float = 0.9,
    ) -> Optional[DetectionResult]:
        """Match template against screenshot.
        
        Args:
            screenshot: Current screen as OpenCV image.
            template_path: Path to template image.
            threshold: Confidence threshold (default: 0.9).
        
        Returns:
            DetectionResult if found, None otherwise.
        """
        # Load template
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            return None
        
        # Match
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h, w = template.shape[:2]
            return DetectionResult(
                name=template_path,
                confidence=max_val,
                bbox=(max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h),
                center_x=max_loc[0] + w // 2,
                center_y=max_loc[1] + h // 2,
                method='template',
                scaled=False,
            )
        
        return None
```

**Verification:**
- [ ] Class initializes without errors
- [ ] detect() method accepts template_path and text_query
- [ ] Returns DetectionResult with correct fields
- [ ] Cache is checked before detection

---

### Task 1.2: Create CoordinateScaler

**File:** `qwen_desktop/core/coordinate_scaler.py`

**Implementation:**

```python
"""
Coordinate Scaling for Multi-Resolution Support.

Converts between relative (0.0-1.0) and absolute coordinates,
and scales templates across different screen resolutions.
"""

import pyautogui
from typing import Tuple, Optional


class CoordinateScaler:
    """Scale coordinates across different resolutions."""
    
    def __init__(self, base_resolution: Tuple[int, int] = (1920, 1080)):
        """Initialize scaler.
        
        Args:
            base_resolution: Base resolution (width, height).
        """
        self.base_w, self.base_h = base_resolution
    
    def get_current_resolution(self) -> Tuple[int, int]:
        """Get current screen resolution."""
        size = pyautogui.size()
        return size.width, size.height
    
    def scale_to_screen(
        self,
        rel_x: float,
        rel_y: float,
    ) -> Tuple[int, int]:
        """Convert relative coordinates to absolute pixels.
        
        Args:
            rel_x: Relative X (0.0-1.0).
            rel_y: Relative Y (0.0-1.0).
        
        Returns:
            Absolute (x, y) in pixels.
        """
        curr_w, curr_h = self.get_current_resolution()
        abs_x = int(rel_x * curr_w)
        abs_y = int(rel_y * curr_h)
        return abs_x, abs_y
    
    def to_relative(
        self,
        abs_x: int,
        abs_y: int,
    ) -> Tuple[float, float]:
        """Convert absolute pixels to relative coordinates.
        
        Args:
            abs_x: Absolute X in pixels.
            abs_y: Absolute Y in pixels.
        
        Returns:
            Relative (x, y) in 0.0-1.0 range.
        """
        rel_x = abs_x / self.base_w
        rel_y = abs_y / self.base_h
        return rel_x, rel_y
    
    def scale_bbox(
        self,
        bbox: Tuple[int, int, int, int],
    ) -> Tuple[int, int, int, int]:
        """Scale bounding box to current resolution.
        
        Args:
            bbox: (x1, y1, x2, y2) at base resolution.
        
        Returns:
            Scaled (x1, y1, x2, y2) for current resolution.
        """
        curr_w, curr_h = self.get_current_resolution()
        scale_x = curr_w / self.base_w
        scale_y = curr_h / self.base_h
        
        x1, y1, x2, y2 = bbox
        return (
            int(x1 * scale_x),
            int(y1 * scale_y),
            int(x2 * scale_x),
            int(y2 * scale_y),
        )
```

**Verification:**
- [ ] scale_to_screen() converts 0.5, 0.5 to screen center
- [ ] to_relative() converts pixels to 0.0-1.0 range
- [ ] scale_bbox() scales all four coordinates correctly

---

### Task 1.3: Create ElementCache

**File:** `qwen_desktop/core/element_cache.py`

**Implementation:**

```python
"""
Element Caching for Performance Optimization.

Time-based cache to avoid redundant element detection.
"""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class CachedElement:
    """Cached detection result."""
    result: Any
    timestamp: float
    ttl: float  # Time to live in seconds


class ElementCache:
    """Time-based element cache."""
    
    def __init__(self, default_ttl: float = 5.0):
        """Initialize cache.
        
        Args:
            default_ttl: Default time to live in seconds.
        """
        self.cache: Dict[str, CachedElement] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached result or None if expired/missing.
        """
        if key not in self.cache:
            return None
        
        cached = self.cache[key]
        if time.time() - cached.timestamp > cached.ttl:
            del self.cache[key]
            return None
        
        return cached.result
    
    def set(
        self,
        key: str,
        result: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Cache a result.
        
        Args:
            key: Cache key.
            result: Detection result to cache.
            ttl: Time to live (optional, uses default if not specified).
        """
        self.cache[key] = CachedElement(
            result=result,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl,
        )
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entries.
        
        Args:
            key: Specific key to invalidate, or None to clear all.
        """
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
    
    def __len__(self) -> int:
        """Get number of cached entries."""
        return len(self.cache)
```

**Verification:**
- [ ] get() returns cached value before TTL expires
- [ ] get() returns None after TTL expires
- [ ] invalidate(key) removes specific entry
- [ ] invalidate() clears all entries

---

## Verification Checklist

- [ ] ElementDetector class created with detect() method
- [ ] CoordinateScaler handles all resolutions
- [ ] ElementCache with TTL support
- [ ] Type hints on all functions
- [ ] Docstrings on all public methods
- [ ] No circular imports

---

## Output

**Files Created:**
- `qwen_desktop/core/element_detector.py` - Main detection engine
- `qwen_desktop/core/coordinate_scaler.py` - Resolution scaling
- `qwen_desktop/core/element_cache.py` - Caching layer

**Lines of Code:** ~300

---

**Ready to Execute:** Run `/gsd:execute-phase 1` to implement Wave 1.
