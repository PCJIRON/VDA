# Cross-Platform Testing Guide

**Version:** 0.4.0  
**Date:** 2026-03-28  
**Platforms:** Windows 10/11, macOS 11+, Ubuntu 20.04+

---

## Overview

This guide provides test procedures for verifying Qwen Desktop across all supported platforms.

---

## Pre-Test Setup

### Requirements
- Python 3.9+
- PyQt6 installed
- OAuth credentials configured
- Internet connection

### Install Dependencies
```bash
py -m pip install -r requirements.txt
```

---

## Test Suite

### 1. Application Launch

**Test:** Application starts without errors

**Steps:**
1. Run `py run.py`
2. Verify window appears within 3 seconds
3. Check no error messages in console

**Expected:**
- Window title: "Qwen Desktop"
- Login button visible
- Status bar shows "Ready"

**Platform Notes:**
- **macOS:** Check menu bar integration
- **Linux:** Check system tray (if available)

---

### 2. OAuth Authentication

**Test:** OAuth login flow works correctly

**Steps:**
1. Click "Login" button
2. Browser opens to OAuth provider
3. Authorize application
4. Browser redirects/callback completes
5. App shows "Logged In" status

**Expected:**
- Browser opens automatically
- Token saved to OS keyring
- UI updates to show logged-in state

**Platform Notes:**
- **Windows:** Credential Manager stores token
- **macOS:** Keychain stores token
- **Linux:** SecretService/Keyring stores token

---

### 3. File Picker Dialog

**Test:** File picker opens and selects files

**Steps:**
1. Click attachment icon (📎)
2. Navigate to a file
3. Select file
4. Verify file appears as attachment chip

**Expected:**
- Native file picker opens
- File preview shows
- File can be removed with X button

**Platform Notes:**
- **Windows:** Common Item Dialog
- **macOS:** NSOpenPanel
- **Linux:** GTK or Qt file dialog

---

### 4. Drag-and-Drop

**Test:** Files can be dragged onto input area

**Steps:**
1. Open file explorer
2. Drag file over input area
3. Verify blue dashed border appears
4. Drop file
5. Verify file appears as attachment

**Expected:**
- Visual feedback on drag (blue border)
- File validated on drop
- Invalid files show error

**Platform Notes:**
- **macOS:** Verify drag from Finder works
- **Linux:** Test with Nautilus/Dolphin
- **Windows:** Test with Explorer

---

### 5. Send Message

**Test:** Messages send and receive responses

**Steps:**
1. Type message in input area
2. Press Enter
3. Verify typing indicator appears
4. Verify AI response streams in
5. Verify markdown renders

**Expected:**
- User message appears (right, blue)
- Typing indicator shows during API call
- AI response appears (left, gray)
- Code blocks highlighted

**Platform Notes:**
- **All:** Verify no UI freezing during API call

---

### 6. Copy Message

**Test:** Messages can be copied to clipboard

**Steps:**
1. Hover over AI message
2. Click 📋 button
3. Verify button changes to ✅
4. Paste into text editor

**Expected:**
- Message content copied
- Visual feedback (📋 → ✅)

**Platform Notes:**
- **macOS:** Cmd+C vs Ctrl+C
- **Linux:** X11 clipboard vs system clipboard
- **Windows:** Standard clipboard

---

### 7. Conversation Persistence

**Test:** Conversations save and load correctly

**Steps:**
1. Send a few messages
2. Press Ctrl+S (or Cmd+S on macOS)
3. Start new chat (Ctrl+N)
4. Press Ctrl+O (or Cmd+O)
5. Select saved conversation
6. Verify messages restore

**Expected:**
- Conversation saves to `~/.qwen-desktop/conversations/`
- Messages restore correctly
- Attachments noted (but not re-loaded)

**Platform Notes:**
- **Windows:** Path: `C:\Users\%USER%\AppData\Local\Qwen\`
- **macOS:** Path: `~/Library/Preferences/Qwen/`
- **Linux:** Path: `~/.config/qwen-desktop/`

---

### 8. Conversation Sidebar

**Test:** Sidebar shows and loads conversations

**Steps:**
1. Verify sidebar on left shows conversations
2. Click a conversation
3. Verify it loads in main chat
4. Right-click conversation
5. Click "Delete"
6. Verify it's removed from list

**Expected:**
- Recent conversations listed
- Click loads conversation
- Delete removes from list and disk

**Platform Notes:**
- **All:** Verify sidebar can be docked/undocked

---

### 9. Keyboard Shortcuts

**Test:** All shortcuts work correctly

**Shortcuts:**
| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| New Chat | Ctrl+N | Cmd+N |
| Open Conversation | Ctrl+O | Cmd+O |
| Save Conversation | Ctrl+S | Cmd+S |
| Clear Conversation | Ctrl+Shift+C | Cmd+Shift+C |
| Preferences | Ctrl+, | Cmd+, |
| Send Message | Enter | Enter |
| New Line | Shift+Enter | Shift+Enter |

**Platform Notes:**
- **macOS:** Verify Cmd vs Ctrl mapping
- **Linux:** Verify WM doesn't intercept shortcuts

---

### 10. Rate Limiting

**Test:** Rate limit displays and enforces

**Steps:**
1. Check status bar for API quota
2. Send many messages (simulate high usage)
3. Verify rate limit error when exceeded

**Expected:**
- Remaining quota visible
- Error message when limit reached
- Wait time displayed

**Platform Notes:**
- **All:** Same behavior expected

---

## Platform-Specific Tests

### macOS 11+

| Test | Status | Notes |
|------|--------|-------|
| App launches | ⬜ | |
| Menu bar integration | ⬜ | |
| Retina display scaling | ⬜ | |
| Cmd shortcuts | ⬜ | |
| Keychain integration | ⬜ | |
| Drag from Finder | ⬜ | |
| Native file picker | ⬜ | |

### Ubuntu 20.04+

| Test | Status | Notes |
|------|--------|-------|
| App launches | ⬜ | |
| System tray (if available) | ⬜ | |
| GTK file picker | ⬜ | |
| SecretService keyring | ⬜ | |
| X11/Wayland compatibility | ⬜ | |
| Drag from Nautilus | ⬜ | |

### Windows 10/11

| Test | Status | Notes |
|------|--------|-------|
| App launches | ⬜ | Already verified ✅ |
| Credential Manager | ⬜ | Already verified ✅ |
| File paths | ⬜ | Already verified ✅ |
| Drag from Explorer | ⬜ | Already verified ✅ |

---

## Performance Benchmarks

| Metric | Target | Windows | macOS | Linux |
|--------|--------|---------|-------|-------|
| Launch Time | <3s | ⬜ | ⬜ | ⬜ |
| OAuth Flow | <10s | ⬜ | ⬜ | ⬜ |
| File Pick | <1s | ⬜ | ⬜ | ⬜ |
| Message Send | <2s | ⬜ | ⬜ | ⬜ |
| Conversation Load | <1s | ⬜ | ⬜ | ⬜ |

---

## Known Platform Issues

### Windows
- None currently known

### macOS
- [To be filled during testing]

### Linux
- [To be filled during testing]

---

## Test Results Summary

| Platform | Tester | Date | Pass Rate | Issues |
|----------|--------|------|-----------|--------|
| Windows 11 | GSD Agent | 2026-03-28 | 100% | 0 |
| macOS 11+ | [Pending] | - | - | - |
| Ubuntu 22.04 | [Pending] | - | - | - |

---

## Reporting Issues

When reporting platform-specific issues, include:
1. Platform and version
2. Python version
3. PyQt6 version
4. Steps to reproduce
5. Expected vs actual behavior
6. Screenshots if applicable

---

**Status:** Windows testing complete. macOS and Linux testing pending.
