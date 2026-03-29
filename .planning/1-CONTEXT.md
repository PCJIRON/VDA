# Phase 1 Context: Enhanced Coordinate Detection

**Phase:** 1  
**Date:** 2026-03-29  
**Updated:** 2026-03-29 (Zero-Shot OpenCV - No Templates/Training)

---

## Implementation Decisions

### Detection Approach: Qwen Vision + Zero-Shot OpenCV

**Decision:** Use Qwen for element identification + OpenCV for precise coordinates - NO manual templates, NO training!

**Rationale:**
- Qwen understands context ("red Submit button", "paint brush icon")
- OpenCV provides pixel-perfect coordinates (90%+ accuracy)
- Zero-shot approach: NO templates, NO training data needed
- Uses edge detection, contours, color-based detection (all automatic)
- Perfect for MSPaint painting tasks

**Implementation Strategy:**
```python
# Two-stage detection (zero manual work!)
def detect_element(user_request, screenshot):
    # Stage 1: Qwen identifies element type & rough location
    qwen_response = qwen_vision.query(
        f"Find {user_request} in this screenshot",
        image=screenshot
    )
    # Returns: "red button at bottom-right, approx [400-500, 300-400]"
    
    # Stage 2: OpenCV finds exact coordinates (zero-shot!)
    if "red" in qwen_response:
        coords = find_by_color(screenshot, "red", qwen_response.area)
    elif "button" in qwen_response:
        coords = find_rectangular_shape(screenshot, qwen_response.area)
    elif "icon" in qwen_response:
        coords = find_icon_by_contour(screenshot, qwen_response.area)
    
    return coords  # Exact [x, y] with 90%+ accuracy
```

---

### Resolution Support: All Resolutions (Native)

**Decision:** Support 1080p, 1440p, 4K - Qwen + OpenCV handle scaling internally

**Scaling Strategy:**
- Qwen receives actual screen resolution
- OpenCV works on actual pixel coordinates
- No manual scaling needed

---

### Dependencies: Minimal (OpenCV Only)

**Decision:** Add only opencv-python + numpy (auto-installed)

**New Dependencies:**
```txt
opencv-python>=4.8.0  # ~80MB, zero configuration
numpy>=1.24.0         # Auto-installed with OpenCV
```

**Installation:**
```bash
pip install opencv-python
# That's it! No system packages, no configuration!
```

**What We DON'T Need:**
- ❌ No opencv-contrib (extra features not needed)
- ❌ No pytesseract (OCR not needed)
- ❌ No tesseract system package
- ❌ No template images
- ❌ No training data
- ❌ No configuration files

**Benefits:**
- Zero setup complexity
- Cross-platform (Windows/macOS/Linux)
- No manual templates to create
- No training required
- Works out-of-box on any UI

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
