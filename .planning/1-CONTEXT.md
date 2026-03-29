# Phase 1 Context: Enhanced Coordinate Detection

**Phase:** 1  
**Date:** 2026-03-29  

---

## Implementation Decisions

### Detection Approach: Hybrid

**Decision:** Combine OpenCV template matching + pytesseract OCR

**Rationale:**
- Template matching excels at UI elements (buttons, icons)
- OCR detects text labels, input fields, menus
- Combined approach achieves >90% accuracy target
- Fallback: if template fails, try OCR; if OCR fails, try template

**Implementation Strategy:**
```python
def detect_element(name, template=None, text=None):
    # Try template matching first
    if template:
        result = template_match(template)
        if result.confidence > 0.9:
            return result
    
    # Fallback to OCR
    if text:
        result = ocr_match(text)
        if result:
            return result
    
    return None
```

---

### Resolution Support: All Resolutions

**Decision:** Support 1080p, 1440p, 4K with automatic scaling

**Supported Resolutions:**
- 1920x1080 (Full HD) - baseline
- 2560x1440 (QHD)
- 3840x2160 (4K UHD)
- Custom resolutions (detected automatically)

**Scaling Strategy:**
- Store templates at 1080p (baseline)
- Scale templates dynamically based on current resolution
- Use relative coordinates (0.0-1.0) internally
- Convert to absolute pixels only for PyAutoGUI

**Implementation:**
```python
class CoordinateScaler:
    def __init__(self, base_width=1920, base_height=1080):
        self.base_w, self.base_h = base_width, base_height
    
    def scale(self, x, y):
        curr_w, curr_h = get_screen_size()
        scale_x = curr_w / self.base_w
        scale_y = curr_h / self.base_h
        return x * scale_x, y * scale_y
    
    def to_relative(self, x, y):
        return x / self.base_w, y / self.base_h
```

---

### Dependencies: OpenCV + pytesseract

**Decision:** Add both dependencies for full capability

**New Dependencies:**
```txt
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0  # For extra features
pytesseract>=0.3.10
tesseract-ocr  # System package (Linux/macOS)
```

**Installation Notes:**
- Windows: `pip install opencv-python pytesseract`
  - Tesseract installer: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract` + `pip install ...`
- Linux: `sudo apt install tesseract-ocr` + `pip install ...`

**Fallback Plan:**
- If OpenCV fails to install: provide pre-built wheel
- If tesseract unavailable: graceful degradation to template-only mode

---

## Technical Architecture

### Module Structure

```
qwen_desktop/core/
├── element_detector.py      # Main detection engine
│   ├── ElementDetector class
│   ├── template_match()
│   ├── ocr_match()
│   └── detect() - unified API
├── coordinate_scaler.py     # Resolution scaling
│   ├── CoordinateScaler class
│   ├── scale_to_screen()
│   └── to_relative()
└── element_cache.py         # Caching layer
    ├── ElementCache class
    ├── get() / set()
    └── invalidate()

qwen_desktop/utils/
└── ocr.py                   # Tesseract wrapper
    ├── OCRService class
    ├── detect_text()
    └── find_text_region()
```

### API Design

```python
# High-level API for vision mode
detector = ElementDetector()

# Detect by template
result = detector.detect_template("submit_button.png")
if result:
    pyautogui.click(result.center_x, result.center_y)

# Detect by text
result = detector.detect_text("Submit")
if result:
    pyautogui.click(result.center_x, result.center_y)

# Detect with scaling
result = detector.detect("submit_button.png", scale=True)

# Use relative coordinates
rel_x, rel_y = 0.5, 0.5  # Center of screen
abs_x, abs_y = detector.scaler.scale(rel_x, rel_y)
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Template Match Time | <200ms | Benchmark test |
| OCR Detection Time | <500ms | Benchmark test |
| Cache Hit Rate | >60% | Runtime stats |
| Memory Usage | <100MB | Process monitor |

---

## Testing Strategy

### Unit Tests
- Template matching accuracy
- OCR text detection
- Coordinate scaling correctness
- Cache invalidation

### Integration Tests
- End-to-end element detection
- Multi-resolution testing
- Performance benchmarks

### Test Data
- Screenshot library with known element positions
- Templates for common UI elements
- Expected coordinates for validation

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenCV install fails | High | Provide wheels, fallback instructions |
| Tesseract not available | Medium | Graceful degradation, clear error messages |
| Performance too slow | Medium | Caching, resolution limits, async execution |
| Low accuracy on some UIs | Medium | Manual template creation, user training |

---

## Success Criteria

- [ ] Element detection accuracy >90% on test suite
- [ ] Template matching <200ms
- [ ] OCR detection <500ms
- [ ] All resolutions (1080p/1440p/4K) supported
- [ ] 10+ unit tests passing
- [ ] Documentation complete

---

**Status:** Ready for detailed planning
