# Phase 1 Plan: Wave 2 - Zero-Shot OpenCV Integration

**Wave:** 2  
**Priority:** High  
**Estimated Time:** 3 hours  

---

## Objective

Add zero-shot OpenCV for pixel-perfect coordinate detection.

**NO manual templates, NO training!** - Uses edge detection, contours, color detection.

**Expected Accuracy:** ~90%+ (perfect for MSPaint painting!)

---

## Tasks

### Task 1.4: Install OpenCV Dependency

**Command:**

```bash
pip install opencv-python
# That's it! numpy auto-installs, no configuration needed!
```

**Verification:**
- [ ] `import cv2` works without errors
- [ ] `import numpy` works
- [ ] OpenCV version >= 4.8.0

---

### Task 1.5: Create OpenCV Detector Module

**File:** `qwen_desktop/core/opencv_detector.py` (new file)

**Implementation:**

```python
"""
Zero-Shot OpenCV Detector.

Finds UI elements using edge detection, contours, and color - NO templates!
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OpenCVDetector:
    """Zero-shot element detection using OpenCV."""
    
    def __init__(self):
        """Initialize detector."""
        pass
    
    def detect(
        self,
        screenshot: np.ndarray,
        element_type: str,
        description: str,
        search_area: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[int, int]]:
        """Detect element using appropriate technique.
        
        Args:
            screenshot: Screenshot as numpy array (BGR format).
            element_type: Type of element ("button", "icon", "color", "text").
            description: Text description (e.g., "red", "submit", "brush").
            search_area: Optional (x1, y1, x2, y2) to narrow search.
        
        Returns:
            (x, y) coordinates or None if not found.
        """
        # Crop to search area if provided
        if search_area:
            x1, y1, x2, y2 = search_area
            roi = screenshot[y1:y2, x1:x2]
        else:
            roi = screenshot
            x1, y1 = 0, 0
        
        # Choose detection technique based on description
        coords = None
        
        # Try color detection first (most accurate)
        if self._is_color_name(description):
            coords = self._detect_by_color(roi, description)
        
        # Try button/rectangular shape detection
        if coords is None and element_type in ["button", "text_field"]:
            coords = self._detect_by_contour(roi)
        
        # Try icon detection
        if coords is None and element_type in ["icon", "tool"]:
            coords = self._detect_icon(roi)
        
        # Adjust coordinates if we cropped
        if coords and search_area:
            coords = (coords[0] + x1, coords[1] + y1)
        
        return coords
    
    def _is_color_name(self, text: str) -> bool:
        """Check if text describes a color."""
        colors = ["red", "green", "blue", "yellow", "orange", "purple", 
                  "pink", "cyan", "magenta", "lime", "violet", "gold", "silver"]
        return any(color in text.lower() for color in colors)
    
    def _detect_by_color(
        self,
        image: np.ndarray,
        color_name: str,
    ) -> Optional[Tuple[int, int]]:
        """Detect element by color - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
            color_name: Color name (e.g., "red", "blue").
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges
        color_ranges = {
            'red': ([0, 70, 50], [10, 255, 255]),
            'green': ([40, 70, 50], [80, 255, 255]),
            'blue': ([100, 70, 50], [130, 255, 255]),
            'yellow': ([20, 70, 50], [35, 255, 255]),
            'orange': ([10, 70, 50], [25, 255, 255]),
            'purple': ([130, 70, 50], [160, 255, 255]),
            'cyan': ([80, 70, 50], [100, 255, 255]),
        }
        
        if color_name.lower() not in color_ranges:
            return None
        
        lower, upper = color_ranges[color_name.lower()]
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        
        # Create mask
        mask = cv2.inRange(hsv, lower, upper)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            return (x + w // 2, y + h // 2)
        
        return None
    
    def _detect_by_contour(
        self,
        image: np.ndarray,
    ) -> Optional[Tuple[int, int]]:
        """Detect button by rectangular contour - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            # Approximate to polygon
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            
            # If 4 corners = rectangle
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (typical button dimensions)
                if 50 < w < 300 and 20 < h < 100:
                    buttons.append((x + w // 2, y + h // 2, w * h))
        
        if buttons:
            # Return largest button (by area)
            buttons.sort(key=lambda b: b[2], reverse=True)
            return (buttons[0][0], buttons[0][1])
        
        return None
    
    def _detect_icon(
        self,
        image: np.ndarray,
    ) -> Optional[Tuple[int, int]]:
        """Detect toolbar icon by shape - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        icons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Tool icons are typically small (20-50px)
            if 20 < w < 50 and 20 < h < 50:
                # Calculate solidity
                area = cv2.contourArea(contour)
                hull_area = cv2.contourArea(cv2.convexHull(contour))
                solidity = area / hull_area if hull_area > 0 else 0
                
                if 0.3 < solidity < 0.9:
                    icons.append((x + w // 2, y + h // 2))
        
        if icons:
            return icons[0]  # Return first match
        
        return None
```

**Verification:**
- [ ] OpenCVDetector class created
- [ ] Color detection works (red, green, blue, etc.)
- [ ] Contour detection finds buttons
- [ ] Icon detection finds toolbar icons
- [ ] All methods return (x, y) or None
- [ ] NO templates required

---

### Task 1.6: Integrate OpenCV with Vision Mode

**File:** `qwen_desktop/ui/floating_assistant.py` (modify)

**Implementation:**

```python
# Add imports
from qwen_desktop.core.opencv_detector import OpenCVDetector
import cv2
import numpy as np

# In FloatingAssistant.__init__
self.opencv_detector = OpenCVDetector()

# Modify _on_vision_screenshot or add new method
def _execute_vision_with_opencv(
    self,
    user_request: str,
    screenshot_b64: str,
    mouse_coords: Tuple[int, int],
    screen_resolution: Tuple[int, int],
):
    """Two-stage detection: Qwen + OpenCV."""
    
    # Stage 1: Qwen identifies element type & rough area
    qwen_response = self._get_qwen_vision_response(
        user_request, screenshot_b64, mouse_coords, screen_resolution
    )
    
    # Parse Qwen's response
    parsed = self.pyautogui_executor.parse_response(qwen_response)
    if not parsed:
        return
    
    # Extract rough area from description
    # Qwen might say: "red button at bottom-right, around [400-500, 300-400]"
    rough_area = self._extract_area_from_description(parsed.get("description", ""))
    
    # Stage 2: OpenCV finds exact coordinates
    screenshot = self._decode_screenshot(screenshot_b64)
    exact_coords = self.opencv_detector.detect(
        screenshot=screenshot,
        element_type=self._infer_element_type(user_request),
        description=parsed.get("description", ""),
        search_area=rough_area,
    )
    
    if exact_coords:
        # Use OpenCV's precise coordinates
        parsed["target"] = list(exact_coords)
        parsed["confidence"] = 0.9  # High confidence from OpenCV
        
        # Execute with precise coords
        self.pyautogui_executor.execute(
            parsed["action"],
            parsed["target"],
            parsed["confidence"],
        )
    else:
        # Fallback to Qwen's coordinates
        self.pyautogui_executor.execute(
            parsed["action"],
            parsed["target"],
            parsed.get("confidence", 0.5),
        )
```

**Verification:**
- [ ] Two-stage detection works (Qwen → OpenCV)
- [ ] OpenCV precision improves coordinates
- [ ] Fallback to Qwen if OpenCV fails
- [ ] User sees accuracy improvement

---

## Verification Checklist

- [ ] OpenCV installed successfully
- [ ] OpenCVDetector class works
- [ ] Color detection finds colored elements
- [ ] Contour detection finds buttons
- [ ] Icon detection finds toolbar icons
- [ ] Integration with vision mode works
- [ ] Accuracy improved to ~90%+

---

## Output

**Files Created:**
- `qwen_desktop/core/opencv_detector.py` - Zero-shot OpenCV detector

**Files Modified:**
- `qwen_desktop/ui/floating_assistant.py` - Integrate OpenCV

**Dependencies Added:**
- `opencv-python>=4.8.0` (~80MB)
- `numpy>=1.24.0` (auto-installed)

**Lines of Code:** ~250

**Expected Accuracy:** ~90%+ (perfect for MSPaint painting!)

---

**Ready to Execute:** Run `/gsd:execute-phase 1` after Wave 1 completes.

---

## Tasks

### Task 1.4: Create OCRService Class

**File:** `qwen_desktop/utils/ocr.py`

**Implementation:**

```python
"""
OCR Service using pytesseract.

Provides text detection and recognition capabilities for
finding UI elements by their text content.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None


class OCRService:
    """OCR service for text detection."""
    
    def __init__(self, lang: str = 'eng'):
        """Initialize OCR service.
        
        Args:
            lang: OCR language (default: English).
        """
        self.lang = lang
        self.available = TESSERACT_AVAILABLE
        
        if not self.available:
            print("Warning: pytesseract not available. OCR disabled.")
    
    def find_text(
        self,
        image: np.ndarray,
        text_query: str,
        min_confidence: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """Find text region in image.
        
        Args:
            image: OpenCV image (BGR format).
            text_query: Text to search for.
            min_confidence: Minimum OCR confidence (0-100).
        
        Returns:
            Dict with bbox, center, confidence if found.
        """
        if not self.available:
            return None
        
        # Preprocess image
        processed = self._preprocess(image)
        
        # Get OCR data with bounding boxes
        data = pytesseract.image_to_data(
            processed,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
            config='--psm 6',  # Assume uniform block of text
        )
        
        # Search for matching text
        best_match = None
        best_confidence = 0
        
        for i, word in enumerate(data['text']):
            if not word.strip():
                continue
            
            confidence = data['conf'][i]
            if confidence < min_confidence:
                continue
            
            # Check if query text is in word
            if text_query.lower() in word.lower():
                if confidence > best_confidence:
                    best_confidence = confidence
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    best_match = {
                        'text': word,
                        'confidence': confidence,
                        'bbox': (x, y, x + w, y + h),
                        'center': (x + w // 2, y + h // 2),
                    }
        
        return best_match
    
    def find_all_text(
        self,
        image: np.ndarray,
        min_confidence: int = 60,
    ) -> List[Dict[str, Any]]:
        """Find all text regions in image.
        
        Args:
            image: OpenCV image (BGR format).
            min_confidence: Minimum OCR confidence (0-100).
        
        Returns:
            List of dicts with text, bbox, confidence.
        """
        if not self.available:
            return []
        
        # Preprocess image
        processed = self._preprocess(image)
        
        # Get OCR data
        data = pytesseract.image_to_data(
            processed,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
            config='--psm 6',
        )
        
        results = []
        for i, word in enumerate(data['text']):
            if not word.strip():
                continue
            
            confidence = data['conf'][i]
            if confidence < min_confidence:
                continue
            
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            
            results.append({
                'text': word,
                'confidence': confidence,
                'bbox': (x, y, x + w, y + h),
                'center': (x + w // 2, y + h // 2),
            })
        
        return results
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy.
        
        Args:
            image: OpenCV image (BGR format).
        
        Returns:
            Preprocessed grayscale image.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def get_ocr_text(self, image: np.ndarray) -> str:
        """Extract all text from image.
        
        Args:
            image: OpenCV image (BGR format).
        
        Returns:
            Extracted text as string.
        """
        if not self.available:
            return ""
        
        processed = self._preprocess(image)
        return pytesseract.image_to_string(
            processed,
            lang=self.lang,
            config='--psm 6',
        )
```

**Verification:**
- [ ] find_text() locates text in screenshot
- [ ] find_all_text() returns all detected text
- [ ] Preprocessing improves OCR accuracy
- [ ] Graceful degradation if pytesseract unavailable

---

### Task 1.5: Add OCR to ElementDetector

**File:** `qwen_desktop/core/element_detector.py` (modify)

**Changes:**

Add multi-scale template matching:

```python
def _match_template_multiscale(
    self,
    screenshot: np.ndarray,
    template_path: str,
    threshold: float = 0.9,
    scales: Optional[List[float]] = None,
) -> Optional[DetectionResult]:
    """Match template at multiple scales.
    
    Args:
        screenshot: Current screen as OpenCV image.
        template_path: Path to template image.
        threshold: Confidence threshold.
        scales: List of scale factors (default: [0.8, 0.9, 1.0, 1.1, 1.2]).
    
    Returns:
        DetectionResult if found, None otherwise.
    """
    if scales is None:
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return None
    
    best_result = None
    best_confidence = 0
    
    for scale in scales:
        scaled_template = cv2.resize(
            template,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )
        
        result = cv2.matchTemplate(
            screenshot,
            scaled_template,
            cv2.TM_CCOEFF_NORMED,
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold and max_val > best_confidence:
            h, w = scaled_template.shape[:2]
            best_confidence = max_val
            best_result = DetectionResult(
                name=template_path,
                confidence=max_val,
                bbox=(max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h),
                center_x=max_loc[0] + w // 2,
                center_y=max_loc[1] + h // 2,
                method='template',
                scaled=True,
            )
    
    return best_result
```

**Verification:**
- [ ] Multi-scale matching finds templates at different sizes
- [ ] Best confidence result is returned
- [ ] scaled=True in DetectionResult

---

## Verification Checklist

- [ ] OCRService class created
- [ ] find_text() works with screenshots
- [ ] Preprocessing improves accuracy
- [ ] Graceful degradation if tesseract unavailable
- [ ] ElementDetector uses OCR service
- [ ] Multi-scale template matching works

---

## Output

**Files Created:**
- `qwen_desktop/utils/ocr.py` - OCR service

**Files Modified:**
- `qwen_desktop/core/element_detector.py` - Add multi-scale matching

**Lines of Code:** ~200

---

**Ready to Execute:** Run `/gsd:execute-phase 1` to implement Wave 2.
