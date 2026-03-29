# Project Roadmap

**Project:** Enhanced Vision Mode  
**Version:** 0.5.0  

---

## Phase 1: Enhanced Coordinate Detection (Week 1-2)

**Goal:** Implement computer vision-based element detection

### Tasks

- [ ] 1.1 Create `element_detector.py` with OpenCV template matching
- [ ] 1.2 Implement OCR wrapper with pytesseract
- [ ] 1.3 Add coordinate scaling for different resolutions
- [ ] 1.4 Support relative coordinates (percentages)
- [ ] 1.5 Create element caching system
- [ ] 1.6 Write unit tests for detection

### Deliverables

- `qwen_desktop/core/element_detector.py` - Main detection logic
- `qwen_desktop/utils/ocr.py` - OCR wrapper
- `tests/test_element_detector.py` - 10+ tests
- Element detection accuracy >90%

---

## Phase 2: Multi-Step Automation (Week 3-4)

**Goal:** Chain automation commands with verification

### Tasks

- [ ] 2.1 Create `automation_chain.py` for command chaining
- [ ] 2.2 Implement wait conditions (element appears/disappears)
- [ ] 2.3 Add screenshot verification after each step
- [ ] 2.4 Implement rollback mechanism
- [ ] 2.5 Add support for loops and conditionals
- [ ] 2.6 Write integration tests

### Deliverables

- `qwen_desktop/core/automation_chain.py` - Chain logic
- `tests/test_automation_chain.py` - 10+ tests
- 5+ step automation works reliably

---

## Phase 3: Auto-Execute & Visual Feedback (Week 5-6)

**Goal:** Safe auto-execution with visual UI feedback

### Tasks

- [ ] 3.1 Implement trust level system (ask_first, auto_trusted, full_auto)
- [ ] 3.2 Create command whitelist
- [ ] 3.3 Add rate limiting for auto-execution
- [ ] 3.4 Implement emergency stop (Ctrl+Shift+Esc)
- [ ] 3.5 Create `vision_overlay.py` for visual feedback
- [ ] 3.6 Add bounding box highlights
- [ ] 3.7 Show action preview before execution
- [ ] 3.8 Add toast notifications
- [ ] 3.9 Update settings dialog for vision options
- [ ] 3.10 Write final integration tests

### Deliverables

- `qwen_desktop/ui/components/vision_overlay.py` - Visual feedback
- Updated `pyautogui_executor.py` with trust levels
- Settings UI for vision configuration
- 20+ total tests passing
- Documentation complete

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Coordinate Detection | Week 1-2 | Pending |
| Phase 2: Multi-Step Automation | Week 3-4 | Pending |
| Phase 3: Auto-Execute & UI | Week 5-6 | Pending |

---

## Phase Dependencies

```
Phase 1 → Phase 2 → Phase 3
   ↓         ↓         ↓
Detection  Chains   Auto + UI
```

---

## Risk Management

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenCV installation issues | Medium | Provide wheel packages, fallback to pure Python |
| OCR accuracy low | Medium | Use multiple OCR engines, template matching fallback |
| Auto-execute safety concerns | High | Conservative defaults, explicit consent, audit logs |
| Performance issues | Medium | Background threads, caching, resolution limits |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Element Detection Accuracy | >90% | Test suite with known elements |
| Multi-Step Success Rate | >85% | Integration tests with 5+ steps |
| User Trust Score | >4/5 | User feedback survey |
| Performance | <500ms detection | Benchmark tests |
| Test Coverage | >80% | pytest coverage report |

---

## Current Status

**Active Phase:** None (Initialization Complete)  
**Next Task:** Run `/gsd:plan-phase 1` to start Phase 1 planning
