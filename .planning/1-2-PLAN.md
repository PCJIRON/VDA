# Phase 1 Plan: Wave 2 - OCR Integration

**Wave:** 2  
**Priority:** High  
**Estimated Time:** 3 hours  

---

## Objective

Implement OCR service using pytesseract for text-based element detection.

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
