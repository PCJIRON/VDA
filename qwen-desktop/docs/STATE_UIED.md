# UIED Feature - Current State

## 📋 Overview

Manual box creation tool for capturing UI elements with custom labels.

## ✅ Completed Features

### 1. Manual Box Creation
- ✅ Box tool (B) - User draws rectangles manually
- ✅ Move tool (V) - Drag boxes to reposition
- ✅ Delete tool (D) - Remove unwanted boxes
- ✅ Resize from 8 corner handles
- ✅ Right-click to delete
- ✅ Keyboard shortcuts (V, B, D, Delete, Backspace, Esc)

### 2. Labeling System
- ✅ Label editor dialog on box creation
- ✅ Double-click to edit existing labels
- ✅ Type selector (app_icon, button, container, etc.)
- ✅ User has 100% control over labels

### 3. Template Capture
- ✅ RGB color saving (not grayscale)
- ✅ Templates stored in memory during editing
- ✅ Templates saved to disk on Done click
- ✅ Filename format: `{id}_{label}_{type}.png`

### 4. UI/UX
- ✅ Figma-style draggable toolbar
- ✅ Done/Exit buttons at bottom
- ✅ Toolbar hides on Done/Exit click
- ✅ Bright yellow hover effect
- ✅ Green selection border
- ✅ Visual feedback on all actions

## ❌ Current Critical Issue

### Problem: Wrong Area Being Cropped

**What's Happening:**
- User draws box around Chrome icon (e.g., 50x50 pixels)
- Console logs show: "User drew box: (100, 100) 50x50"
- Template saved shows different area (larger or offset)

**Expected:**
- User draws 50x50 box around Chrome icon
- Template saved should be EXACT 50x50 Chrome icon
- No extra padding, no offset

**Actual:**
- Template includes area outside user selection
- OR template captures different location entirely

### Root Cause Analysis

**Coordinate System Confusion:**

```
Widget covers entire screen:
- Widget position: (0, 0) to (1920, 1080)
- Widget covers screen starting at screen origin

User draws at widget position (100, 100):
- Widget coordinates: (100, 100)
- Screen coordinates: SHOULD BE (100, 100) if widget starts at (0,0)
- BUT widget might start at screen position (1920, 0) on multi-monitor

Current code tries:
1. Direct widget coords → Wrong if widget not at (0,0)
2. screen_origin + widget_coords → Still wrong
3. mapToGlobal() → Still wrong
4. self.pos() + widget_coords → Still wrong
```

**The Real Issue:**

```python
# Widget is created with:
screen = QApplication.primaryScreen().geometry()
self.setGeometry(screen)

# This sets widget to cover screen, but widget's internal (0,0)
# might not match screen's (0,0)

# When user draws at widget (100, 100):
# - We need ACTUAL screen pixel (100, 100)
# - But widget might be rendering at different position

# pyautogui.screenshot() captures from ACTUAL screen pixels
# So we need to convert widget coords to ACTUAL screen coords
```

## 🔧 Attempted Fixes (All Failed)

### Fix 1: Direct Widget Coordinates
```python
screen_x = rect.x()
screen_y = rect.y()
```
**Result:** Wrong area captured

### Fix 2: Screen Origin Addition
```python
screen_x = self.screen_origin.x() + rect.x()
screen_y = self.screen_origin.y() + rect.y()
```
**Result:** Wrong area captured

### Fix 3: mapToGlobal
```python
global_pos = self.mapToGlobal(QPoint(rect.x(), rect.y()))
screen_x = global_pos.x()
screen_y = global_pos.y()
```
**Result:** Wrong area captured

### Fix 4: Widget Position
```python
widget_pos = self.pos()
screen_x = widget_pos.x() + rect.x()
screen_y = widget_pos.y() + rect.y()
```
**Result:** Wrong area captured

## 🎯 Next Steps to Fix

### Debug Information Needed

1. **Widget Geometry:**
   - `self.geometry()` - Widget's position and size
   - `self.pos()` - Widget's top-left position
   - `self.screen_origin` - Screen's top-left position

2. **Actual Screen Capture:**
   - Log `pyautogui.position()` before capture
   - Log actual pixel color at captured location
   - Compare with what user saw

3. **Test on Single Monitor:**
   - Disable secondary monitors
   - Test if issue persists
   - Isolate multi-monitor as cause

### Potential Solutions

**Option 1: Use QScreen to Capture**
```python
# Instead of pyautogui, use Qt's screen capture
screen = QApplication.primaryScreen()
screenshot = screen.grabWindow(0, x, y, w, h)
# This uses same coordinate system as widget
```

**Option 2: Calibrate Coordinates**
```python
# Show test box at known widget position
# Capture and check what area was actually captured
# Calculate offset
# Apply offset to all future captures
```

**Option 3: Remove Widget, Use Raw Coordinates**
```python
# Don't use full-screen widget
# Just capture mouse position directly
# Use global mouse coordinates
```

## 📊 Current Code State

### Files Modified:
1. `core/uied_service.py` - Detection removed, manual mode only
2. `ui/uied_overlay.py` - Box creation, drag, resize, template capture
3. `ui/floating_assistant.py` - Integration, saving logic

### Key Functions:
- `mouseReleaseEvent()` - Converts widget coords to screen coords ❌
- `_handle_drag()` - Recaptures template on drag ❌
- `_handle_resize()` - Recaptures template on resize ❌
- `_on_uied_component_added()` - Captures initial template ❌
- `_on_uied_overlay_closed()` - Saves templates to disk ✅

### Working Correctly:
- ✅ Box drawing
- ✅ Label editing
- ✅ Drag and resize
- ✅ RGB saving
- ✅ Toolbar hide/show
- ✅ Delete functionality

### Not Working:
- ❌ Correct screen coordinate conversion
- ❌ Exact area cropping

## 💭 Notes

**Chinese Programmer Mindset:**
- Problem is SIMPLE, solution is SIMPLE
- Overthinking complex coordinate systems
- Widget covers screen → Widget coords = Screen coords
- Something else is wrong

**Check:**
1. Is widget REALLY covering entire screen?
2. Is there a border/offset we're not seeing?
3. Is pyautogui using different coordinate system?
4. Is there DPI scaling issue?

**Next Debug Step:**
```python
# Add this in mouseReleaseEvent:
logger.info(f"Widget geometry: {self.geometry()}")
logger.info(f"Widget pos: {self.pos()}")
logger.info(f"Screen geometry: {QApplication.primaryScreen().geometry()}")
logger.info(f"Cursor pos: {QCursor.pos()}")

# Draw test rectangle at captured coordinates
# Verify visually if it matches what user drew
```

## 📅 Timeline

- **Feature Started:** Manual box creation concept
- **Completed:** UI, labeling, RGB saving, toolbar
- **Blocked On:** Coordinate conversion bug (multiple failed attempts)
- **ETA:** Need fresh perspective on coordinate system

---

**Status:** 🟨 **85% Complete - Critical Bug Remaining**
