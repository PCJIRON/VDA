# Phase 1 Research: Enhanced Coordinate Detection

**Phase:** 1  
**Research Date:** 2026-03-29  

---

## Research Goals

Investigate implementation approaches for:
1. OpenCV template matching for UI elements
2. pytesseract OCR for text detection
3. Coordinate scaling across resolutions
4. Element caching strategies

---

## 1. OpenCV Template Matching

### Overview

Template matching finds regions in an image that match a template image.

**Algorithm:** Cross-correlation between template and screenshot

### Implementation Options

#### Option A: `cv2.matchTemplate()` (Recommended)

```python
import cv2
import numpy as np

def match_template(screenshot, template_path, threshold=0.9):
    # Load template
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    
    # Match
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        return {
            'confidence': max_val,
            'top_left': max_loc,
            'bottom_right': (max_loc[0] + template.shape[1], 
                            max_loc[1] + template.shape[0]),
            'center': (max_loc[0] + template.shape[1]//2,
                      max_loc[1] + template.shape[0]//2)
        }
    return None
```

**Pros:**
- Built into OpenCV
- Fast (<100ms for typical templates)
- Good accuracy for UI elements

**Cons:**
- Scale-sensitive (template must match size)
- Rotation-sensitive
- Lighting-sensitive

### Multi-Scale Template Matching

For resolution independence:

```python
def match_template_multiscale(screenshot, template, scales=[0.8, 0.9, 1.0, 1.1, 1.2]):
    best_result = None
    best_confidence = 0
    
    for scale in scales:
        scaled = cv2.resize(template, None, fx=scale, fy=scale)
        result = match_template(screenshot, scaled)
        if result and result['confidence'] > best_confidence:
            best_confidence = result['confidence']
            best_result = result
    
    return best_result
```

### References

- OpenCV Template Matching: https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html
- Best practices: https://pyimagesearch.com/2021/03/29/opencv-template-matching/

---

## 2. pytesseract OCR

### Overview

Tesseract OCR engine with Python bindings for text detection in screenshots.

### Installation

```bash
# Python package
pip install pytesseract

# System package
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt install tesseract-ocr
```

### Implementation

```python
import pytesseract
from PIL import Image
import cv2
import numpy as np

def detect_text_regions(screenshot, text_query):
    # Convert to PIL Image
    img = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
    
    # Get OCR data with bounding boxes
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    # Find matching text
    for i, word in enumerate(data['text']):
        if text_query.lower() in word.lower():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            return {
                'text': word,
                'confidence': data['conf'][i],
                'bbox': (x, y, x + w, y + h),
                'center': (x + w//2, y + h//2)
            }
    return None
```

### Preprocessing for Better OCR

```python
def preprocess_for_ocr(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    return denoised
```

### References

- pytesseract docs: https://pypi.org/project/pytesseract/
- Tesseract OCR: https://tesseract-ocr.github.io/
- Best practices: https://pyimagesearch.com/2021/05/12/ocr-with-tesseract-and-python/

---

## 3. Coordinate Scaling

### Problem

Templates created at 1080p need to work on 1440p and 4K displays.

### Solution: Relative Coordinates

```python
class CoordinateScaler:
    def __init__(self, base_resolution=(1920, 1080)):
        self.base_w, self.base_h = base_resolution
    
    def get_current_resolution(self):
        import pyautogui
        return pyautogui.size()
    
    def scale_to_screen(self, rel_x, rel_y):
        """Convert relative (0-1) to absolute pixels"""
        curr_w, curr_h = self.get_current_resolution()
        abs_x = int(rel_x * curr_w)
        abs_y = int(rel_y * curr_h)
        return abs_x, abs_y
    
    def to_relative(self, abs_x, abs_y):
        """Convert absolute pixels to relative (0-1)"""
        rel_x = abs_x / self.base_w
        rel_y = abs_y / self.base_h
        return rel_x, rel_y
    
    def scale_template(self, template_bbox):
        """Scale template bounding box to current resolution"""
        x1, y1, x2, y2 = template_bbox
        curr_w, curr_h = self.get_current_resolution()
        scale_x = curr_w / self.base_w
        scale_y = curr_h / self.base_h
        return (
            int(x1 * scale_x),
            int(y1 * scale_y),
            int(x2 * scale_x),
            int(y2 * scale_y)
        )
```

### Testing Strategy

```python
def test_scaling():
    scaler = CoordinateScaler()
    
    # Test at 1080p baseline
    rel_x, rel_y = 0.5, 0.5
    abs_x, abs_y = scaler.scale_to_screen(rel_x, rel_y)
    assert abs_x == 960  # 1920 * 0.5
    assert abs_y == 540  # 1080 * 0.5
    
    # Test at 4K
    # Mock pyautogui.size() to return (3840, 2160)
    abs_x, abs_y = scaler.scale_to_screen(rel_x, rel_y)
    assert abs_x == 1920  # 3840 * 0.5
    assert abs_y == 1080  # 2160 * 0.5
```

---

## 4. Element Caching

### Problem

Repeated detection of same elements is wasteful.

### Solution: Time-based Cache

```python
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class CachedElement:
    result: Dict[str, Any]
    timestamp: float
    ttl: float  # Time to live in seconds

class ElementCache:
    def __init__(self, default_ttl=5.0):
        self.cache: Dict[str, CachedElement] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self.cache:
            return None
        
        cached = self.cache[key]
        if time.time() - cached.timestamp > cached.ttl:
            del self.cache[key]
            return None
        
        return cached.result
    
    def set(self, key: str, result: Dict[str, Any], ttl: Optional[float] = None):
        self.cache[key] = CachedElement(
            result=result,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )
    
    def invalidate(self, key: Optional[str] = None):
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
```

### Cache Invalidation Triggers

- Screen resolution change
- User interaction (click, scroll)
- Time-based expiration (5 seconds default)
- Manual invalidation

---

## 5. Recommended Implementation

### Combined Detector

```python
class ElementDetector:
    def __init__(self):
        self.scaler = CoordinateScaler()
        self.cache = ElementCache(default_ttl=5.0)
        self.ocr_service = OCRService()
    
    def detect(self, name: str, template: str = None, text: str = None):
        """Unified detection API"""
        
        # Check cache first
        cache_key = f"{name}:{template}:{text}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Take screenshot
        screenshot = self._capture_screen()
        
        # Try template matching
        if template:
            result = self._match_template(screenshot, template)
            if result:
                self.cache.set(cache_key, result)
                return result
        
        # Try OCR
        if text:
            result = self.ocr_service.find_text(screenshot, text)
            if result:
                self.cache.set(cache_key, result)
                return result
        
        return None
    
    def _capture_screen(self):
        import pyautogui
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
```

---

## 6. Dependencies Summary

### Required

```txt
opencv-python>=4.8.0
pytesseract>=0.3.10
Pillow>=10.0.0  # Already installed
pyautogui>=0.9.54  # Already installed
```

### System Packages

```bash
# Windows
# Download tesseract installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract

# Linux (Ubuntu/Debian)
sudo apt install tesseract-ocr

# Linux (Fedora/RHEL)
sudo dnf install tesseract
```

### Optional (for better OCR)

```txt
numpy>=1.24.0  # For image processing
```

---

## 7. Testing Approach

### Test Fixtures

```python
# tests/fixtures/screenshots/
# - 1080p_desktop.png
# - 1440p_desktop.png
# - 4k_desktop.png

# tests/fixtures/templates/
# - submit_button.png
# - close_icon.png
# - menu_item.png
```

### Test Cases

```python
def test_template_matching():
    detector = ElementDetector()
    result = detector.detect("submit", template="submit_button.png")
    assert result is not None
    assert result['confidence'] > 0.9

def test_ocr_detection():
    detector = ElementDetector()
    result = detector.detect("Submit Button", text="Submit")
    assert result is not None

def test_scaling():
    detector = ElementDetector()
    # Mock different resolutions
    result = detector.detect("submit", template="submit_button.png")
    assert result['scaled'] == True

def test_cache():
    detector = ElementDetector()
    result1 = detector.detect("submit", template="submit_button.png")
    result2 = detector.detect("submit", template="submit_button.png")
    assert result1 == result2  # Cache hit
```

---

## 8. Performance Benchmarks

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Template Match (1080p) | <100ms | Single template |
| Template Match (4K) | <200ms | Larger screenshot |
| OCR Full Screen | <500ms | Tesseract default |
| OCR Region (100x100) | <50ms | Small region |
| Cache Lookup | <1ms | In-memory dict |
| Coordinate Scale | <1ms | Simple math |

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OpenCV install fails | Low | High | Provide wheels, conda package |
| Tesseract not available | Medium | Medium | Graceful degradation |
| Poor accuracy on some UIs | Medium | Medium | Manual template creation guide |
| Performance issues | Low | Medium | Caching, async execution |
| Memory leaks | Low | Low | Cache size limits, TTL |

---

## 10. References

1. OpenCV Template Matching: https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html
2. pytesseract Documentation: https://pypi.org/project/pytesseract/
3. Tesseract OCR: https://tesseract-ocr.github.io/
4. PyAutoGUI: https://pyautogui.readthedocs.io/
5. Coordinate Scaling Best Practices: https://pyimagesearch.com/

---

**Research Complete** ✅

**Ready for detailed task planning.**
