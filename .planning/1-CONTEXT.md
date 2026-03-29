# Phase 1 Context: Enhanced Coordinate Detection

**Phase:** 1  
**Date:** 2026-03-29  
**Updated:** 2026-03-29 (No OpenCV/OCR - Pure Qwen Vision)

---

## Implementation Decisions

### Detection Approach: Qwen Vision + Mouse Coordinates

**Decision:** Use Qwen's vision capabilities with mouse coordinates - NO OpenCV, NO OCR

**Rationale:**
- Existing vision mode already captures screenshots automatically
- Mouse coordinates + screen resolution Qwen ko context deta hai
- Qwen calculation karke exact target location find kar sakta hai
- Zero dependencies, zero templates, zero training
- Qwen already trained hai UI elements recognize karne ke liye

**Implementation Strategy:**
```python
# Jab user input aata hai:
# 1. Auto screenshot
# 2. Get mouse coordinates
# 3. Send to Qwen with metadata
# 4. Qwen returns target coordinates
# 5. Execute click/drag/drop

def send_vision_request(user_input):
    screenshot = pyautogui.screenshot()
    mouse_x, mouse_y = pyautogui.position()
    screen_w, screen_h = get_screen_size()
    
    # Qwen ko bhejo with metadata
    payload = f"""
    [VISION METADATA]
    Screen: {screen_w}x{screen_h}
    Mouse: ({mouse_x}, {mouse_y})
    
    [USER REQUEST]
    {user_input}
    
    Analyze screenshot and return target coordinates for action.
    """
```

---

### Resolution Support: All Resolutions (Native)

**Decision:** Support 1080p, 1440p, 4K - Qwen handles scaling internally

**Supported Resolutions:**
- 1920x1080 (Full HD)
- 2560x1440 (QHD)
- 3840x2160 (4K UHD)
- Custom (auto-detected)

**Scaling Strategy:**
- Qwen receives actual screen resolution
- Qwen internally calculates relative positions
- Returns absolute coordinates for current screen
- No manual scaling needed

**Implementation:**
```python
# Qwen already understands coordinate scaling
# Just send actual resolution + mouse position
# Qwen returns correct coordinates
```

---

### Dependencies: NONE (Existing Only)

**Decision:** No new dependencies - use existing pyautogui + Pillow

**Existing Stack:**
```txt
pyautogui>=0.9.54  # Already installed
Pillow>=10.0.0     # Already installed
pynput>=1.7.6      # Already installed (for listeners)
```

**No Installation Required:**
- ✅ No OpenCV
- ✅ No pytesseract
- ✅ No tesseract system package
- ✅ Everything already works!

**Benefits:**
- Zero setup complexity
- Cross-platform (Windows/macOS/Linux)
- No system dependencies

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
