# Phase 1 Plan: Wave 3 - Testing & Integration

**Wave:** 3  
**Priority:** High  
**Estimated Time:** 3 hours  

---

## Objective

Create comprehensive tests for element detection and integrate with existing vision mode.

---

## Tasks

### Task 1.6: Create Unit Tests

**File:** `tests/test_element_detector.py`

**Implementation:**

```python
"""
Tests for Element Detection Engine.
"""

import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from pathlib import Path

from qwen_desktop.core.element_detector import ElementDetector, DetectionResult
from qwen_desktop.core.coordinate_scaler import CoordinateScaler
from qwen_desktop.core.element_cache import ElementCache


class TestCoordinateScaler:
    """Test coordinate scaling."""
    
    def test_scale_to_screen_1080p(self):
        """Test scaling at 1080p."""
        with patch('pyautogui.size') as mock_size:
            mock_size.return_value = MagicMock(width=1920, height=1080)
            scaler = CoordinateScaler()
            
            # Center of screen
            x, y = scaler.scale_to_screen(0.5, 0.5)
            assert x == 960
            assert y == 540
    
    def test_scale_to_screen_4k(self):
        """Test scaling at 4K."""
        with patch('pyautogui.size') as mock_size:
            mock_size.return_value = MagicMock(width=3840, height=2160)
            scaler = CoordinateScaler()
            
            # Center of screen
            x, y = scaler.scale_to_screen(0.5, 0.5)
            assert x == 1920
            assert y == 1080
    
    def test_to_relative(self):
        """Test converting to relative coordinates."""
        scaler = CoordinateScaler()
        rel_x, rel_y = scaler.to_relative(960, 540)
        assert abs(rel_x - 0.5) < 0.01
        assert abs(rel_y - 0.5) < 0.01
    
    def test_scale_bbox(self):
        """Test bounding box scaling."""
        with patch('pyautogui.size') as mock_size:
            mock_size.return_value = MagicMock(width=3840, height=2160)
            scaler = CoordinateScaler()
            
            bbox = (100, 100, 200, 200)
            scaled = scaler.scale_bbox(bbox)
            
            # 4K is 2x 1080p
            assert scaled == (200, 200, 400, 400)


class TestElementCache:
    """Test element caching."""
    
    def test_cache_set_get(self):
        """Test basic cache operations."""
        cache = ElementCache(default_ttl=10.0)
        result = {'found': True, 'x': 100}
        
        cache.set('test_key', result)
        cached = cache.get('test_key')
        
        assert cached == result
    
    def test_cache_expires(self):
        """Test cache expiration."""
        cache = ElementCache(default_ttl=0.1)  # 100ms TTL
        result = {'found': True}
        
        cache.set('test_key', result)
        
        import time
        time.sleep(0.2)  # Wait for expiration
        
        cached = cache.get('test_key')
        assert cached is None
    
    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = ElementCache()
        cache.set('key1', {'val': 1})
        cache.set('key2', {'val': 2})
        
        cache.invalidate('key1')
        assert cache.get('key1') is None
        assert cache.get('key2') is not None
    
    def test_cache_clear(self):
        """Test clearing all cache."""
        cache = ElementCache()
        cache.set('key1', {'val': 1})
        cache.set('key2', {'val': 2})
        
        cache.invalidate()
        assert len(cache) == 0


class TestElementDetector:
    """Test element detection."""
    
    def test_detector_init(self):
        """Test detector initialization."""
        detector = ElementDetector()
        assert detector.scaler is not None
        assert detector.cache is not None
        assert detector.ocr_service is not None
    
    @patch('qwen_desktop.core.element_detector.pyautogui.screenshot')
    @patch('qwen_desktop.core.element_detector.cv2.imread')
    @patch('qwen_desktop.core.element_detector.cv2.matchTemplate')
    def test_template_match_success(
        self,
        mock_match,
        mock_imread,
        mock_screenshot,
    ):
        """Test successful template matching."""
        # Mock screenshot
        mock_screenshot.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # Mock template
        mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Mock match result (high confidence)
        mock_match.return_value = np.array([[0.95]])
        
        detector = ElementDetector()
        result = detector.detect('test', template_path='button.png')
        
        assert result is not None
        assert result.confidence > 0.9
        assert result.method == 'template'
    
    def test_cache_hit(self):
        """Test cache is used on repeated calls."""
        detector = ElementDetector()
        
        # First call - cache miss
        with patch.object(detector, '_capture_screen') as mock_capture:
            mock_capture.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
            detector.detect('test', template_path='button.png')
            assert mock_capture.called
        
        # Second call - cache hit
        with patch.object(detector, '_capture_screen') as mock_capture:
            mock_capture.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
            detector.detect('test', template_path='button.png')
            assert not mock_capture.called  # Cache hit!


class TestIntegration:
    """Integration tests."""
    
    def test_detector_with_real_template(self):
        """Test with actual template file."""
        # Create test template
        template_path = Path(__file__).parent / 'fixtures' / 'test_button.png'
        if not template_path.exists():
            pytest.skip("Test fixture not available")
        
        detector = ElementDetector()
        result = detector.detect('test_button', template_path=str(template_path))
        
        # Should find or not find, but not crash
        assert result is None or result.confidence > 0
```

**Verification:**
- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] No flaky tests

---

### Task 1.7: Create OCR Tests

**File:** `tests/test_ocr.py`

**Implementation:**

```python
"""
Tests for OCR Service.
"""

import pytest
import cv2
import numpy as np
from pathlib import Path

from qwen_desktop.utils.ocr import OCRService


class TestOCRService:
    """Test OCR functionality."""
    
    def test_service_available(self):
        """Test if OCR service is available."""
        service = OCRService()
        # Service should initialize even if tesseract unavailable
        assert service is not None
    
    @pytest.mark.skip(reason="Requires tesseract installation")
    def test_find_text(self):
        """Test finding text in image."""
        service = OCRService()
        if not service.available:
            pytest.skip("Tesseract not available")
        
        # Create test image with text
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(
            image,
            "Submit",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        
        result = service.find_text(image, "Submit")
        assert result is not None
        assert 'Submit' in result['text']
    
    @pytest.mark.skip(reason="Requires tesseract installation")
    def test_find_all_text(self):
        """Test finding all text in image."""
        service = OCRService()
        if not service.available:
            pytest.skip("Tesseract not available")
        
        # Create test image with multiple words
        image = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.putText(image, "Hello", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, "World", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        results = service.find_all_text(image)
        assert len(results) >= 2
    
    def test_preprocessing(self):
        """Test image preprocessing."""
        service = OCRService()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        processed = service._preprocess(image)
        
        assert processed is not None
        assert len(processed.shape) == 2  # Grayscale
        assert processed.shape[:2] == image.shape[:2]
```

**Verification:**
- [ ] Tests pass when tesseract installed
- [ ] Graceful skip when tesseract unavailable

---

### Task 1.8: Integration with Vision Mode

**File:** `qwen_desktop/ui/floating_assistant.py` (modify)

**Changes:**

Add element detection to vision mode:

```python
from qwen_desktop.core.element_detector import ElementDetector

class FloatingAssistant(QWidget):
    def __init__(self, settings, parent=None):
        # ... existing init ...
        
        # Initialize element detector
        self.element_detector = ElementDetector()
    
    def detect_and_click(self, element_name: str, template: str = None, text: str = None):
        """Detect element and click it."""
        result = self.element_detector.detect(
            element_name,
            template_path=template,
            text_query=text,
        )
        
        if result:
            import pyautogui
            pyautogui.click(result.center_x, result.center_y)
            return True
        return False
```

**Verification:**
- [ ] ElementDetector integrates with FloatingAssistant
- [ ] detect_and_click() works in vision mode
- [ ] No regressions in existing vision features

---

## Verification Checklist

- [ ] 10+ unit tests for element detection
- [ ] 5+ tests for OCR
- [ ] Integration test with vision mode
- [ ] All tests pass
- [ ] Code coverage >80%

---

## Output

**Files Created:**
- `tests/test_element_detector.py` - Detection tests
- `tests/test_ocr.py` - OCR tests

**Files Modified:**
- `qwen_desktop/ui/floating_assistant.py` - Integration

**Lines of Code:** ~250 (tests)

---

**Ready to Execute:** Run `/gsd:execute-phase 1` to implement Wave 3.
