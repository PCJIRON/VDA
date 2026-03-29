# Project: Enhanced Vision Mode

**Project Name:** Qwen Desktop - Enhanced Vision Mode  
**Version:** 0.5.0  
**Created:** 2026-03-29  
**Status:** Initialization Complete  

---

## Overview

Enhance the existing Vision Mode in Qwen Desktop with improved coordinate detection, multi-step automation, auto-execute capabilities, and visual feedback UI. This transforms the desktop assistant into a more autonomous and accurate automation tool.

---

## Goals

1. **Better Coordinate Detection** - Improve element detection accuracy with computer vision
2. **Multi-Step Automation** - Chain automation steps with feedback loops
3. **Auto-Execute Commands** - Run PyAutoGUI commands without manual confirmation
4. **Visual Feedback UI** - Show highlighted elements and action previews

---

## Inspiration

Based on the existing Vision Mode in Qwen Desktop v0.4.0 which already supports:
- Screenshot capture on interaction
- PyAutoGUI command execution via `[PYAUTOGUI]...[/PYAUTOGUI]` blocks
- Vision status display in chat popup

---

## Core Features

### Feature 1: Enhanced Coordinate Detection
- Use OpenCV for element template matching
- Improve coordinate scaling across different screen resolutions
- Add OCR for text-based element detection
- Support relative coordinate system (percentages)

### Feature 2: Multi-Step Automation
- Chain multiple PyAutoGUI commands
- Wait conditions between steps
- Screenshot verification after each step
- Rollback on failure

### Feature 3: Auto-Execute Mode
- Configurable trust levels (ask_first, auto_trusted, full_auto)
- Whitelist safe commands
- Rate limiting for auto-execution
- Emergency stop mechanism

### Feature 4: Visual Feedback UI
- Highlight detected elements with bounding boxes
- Show action preview before execution
- Display execution progress overlay
- Toast notifications for completion/errors

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.9+ |
| **GUI** | PyQt6 (existing) |
| **Computer Vision** | OpenCV (new) |
| **OCR** | pytesseract (new) |
| **Automation** | PyAutoGUI (existing) |
| **Screenshot** | pynput + Pillow (existing) |
| **Template Matching** | OpenCV (new) |

---

## Project Structure

```
qwen-desktop/
├── qwen_desktop/
│   ├── core/
│   │   ├── vision_capture.py         # Existing - enhance
│   │   ├── pyautogui_executor.py     # Existing - enhance
│   │   ├── element_detector.py       # NEW - OpenCV detection
│   │   └── automation_chain.py       # NEW - Multi-step logic
│   ├── ui/
│   │   ├── floating_assistant.py     # Existing - add visual feedback
│   │   └── components/
│   │       └── vision_overlay.py     # NEW - Highlight overlay
│   └── utils/
│       └── ocr.py                    # NEW - Tesseract wrapper
├── tests/
│   ├── test_element_detector.py
│   ├── test_automation_chain.py
│   └── test_ocr.py
└── .planning/
    ├── PROJECT.md                    # This file
    ├── REQUIREMENTS.md
    ├── ROADMAP.md
    └── STATE.md
```

---

## Key Decisions

1. **OpenCV over pure PyAutoGUI** - Better element detection accuracy
2. **Configurable trust levels** - Balance automation vs safety
3. **Overlay UI** - Non-intrusive visual feedback
4. **Backward compatible** - Existing vision mode still works

---

## Success Criteria Checklist

- [ ] Element detection accuracy >90% on test cases
- [ ] Multi-step automation with 5+ steps works reliably
- [ ] Auto-execute mode with safety controls
- [ ] Visual feedback overlay displays correctly
- [ ] All existing vision features still work
- [ ] 20+ new unit tests passing
- [ ] Documentation complete

---

## Next Steps

1. Review and approve this project document
2. Run `/gsd:plan-phase 1` to create detailed requirements
3. Execute Phase 1: Foundation (Element Detection)

---

**Status:** Ready for requirements phase
