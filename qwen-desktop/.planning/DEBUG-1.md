# Debug Session 1

**Date:** 2026-03-28  
**Issue:** Critical bugs from code review blocking Phase 1 ship  

---

## Issues to Fix

### Critical (Must Fix Before Ship)

1. **OAuth Callback Flow Not Implemented** - `auth_dialog.py:131`
2. **Silent Keyring Failures** - `credentials.py:33-37, 45-49`
3. **Misleading Enter-to-Send UX** - `input_area.py:94`
4. **Unused Import** - `main_window.py:20`

### Suggestion (Recommended Before Ship)

5. **Missing Markdown Library** - `message_bubble.py:55`
6. **Token Refresh Not Automatic** - `api_client.py:47-95`
7. **Platform-Specific Shortcuts Lost** - `main_window.py:136`

---

## Context

- **Phase:** 1 - Foundation
- **Status:** UAT PASSED but code review found critical gaps
- **Files Affected:** 6 Python files

---

## Hypotheses & Testing

### Issue 1: OAuth Callback Flow

**Hypothesis:** The OAuth flow cannot complete because there's no HTTP server listening for the callback.

**Evidence:**
- `auth_dialog.py` line 131: `# TODO: Start local server to handle callback`
- `oauth_handler.py` expects callback URL but nothing receives it
- `_on_auth_complete()` called immediately without waiting

**Test:** Check if Flask/httpx server is started
```python
# Current code just calls _on_auth_complete() immediately
# No server listening on localhost:8080
```

**Status:** ✅ **CONFIRMED** - OAuth flow is broken

---

### Issue 2: Silent Keyring Failures

**Hypothesis:** Exceptions from keyring are swallowed, causing silent auth failures.

**Evidence:**
```python
# credentials.py lines 33-37
def get_access_token(self) -> Optional[str]:
    try:
        return keyring.get_password(self.service, self.ACCESS_TOKEN_KEY)
    except Exception:  # Bare exception!
        return None
```

**Test:** Check exception handling pattern
- No logging of errors
- No user feedback
- Returns `None` silently

**Status:** ✅ **CONFIRMED** - Silent failures possible

---

### Issue 3: Enter-to-Send UX

**Hypothesis:** Placeholder text promises Enter-to-send but handler not implemented.

**Evidence:**
- `input_area.py` line 94: `"Enter to send, Shift+Enter for new line"`
- No key press event handler installed
- Only `textChanged` signal connected

**Test:** Check for Enter key handling
- No `eventFilter()` method
- No `keyPressEvent()` override

**Status:** ✅ **CONFIRMED** - Misleading UX

---

### Issue 4: Unused Import

**Hypothesis:** `QIcon` imported but never used.

**Evidence:**
- `main_window.py` line 20: `from PyQt6.QtGui import QIcon, QAction`
- `QIcon` never referenced in file

**Test:** Grep for `QIcon` usage
- No matches found

**Status:** ✅ **CONFIRMED** - Unused import

---

## Root Causes

1. **OAuth Callback:** Incomplete implementation - server code not written
2. **Keyring Errors:** Defensive programming gone wrong - hiding errors instead of handling them
3. **Enter-to-Send:** Placeholder text added before feature implementation
4. **Unused Import:** Leftover from initial code that was removed

---

## Fix Plan

### Phase 1A: Critical Fixes (Required for Ship)

#### Fix 1: Implement OAuth Callback Server
**File:** `qwen_desktop/ui/auth_dialog.py`

**Steps:**
1. Add Flask server to handle callback
2. Start server in background thread
3. Wait for callback with timeout
4. Update UI after successful callback

**Dependencies:** Flask already in `requirements.txt`

---

#### Fix 2: Add Keyring Error Handling
**File:** `qwen_desktop/auth/credentials.py`

**Steps:**
1. Import `keyring.errors`
2. Add specific exception handling
3. Log errors with logger
4. Show user feedback on failure

---

#### Fix 3: Fix Enter-to-Send or Update UX
**File:** `qwen_desktop/ui/input_area.py`

**Steps:**
1. Install event filter on text input
2. Handle Enter/Shift+Enter key combinations
3. Call `_on_send()` on Enter without Shift

**Alternative (quick fix):** Update placeholder text to remove promise

---

#### Fix 4: Remove Unused Import
**File:** `qwen_desktop/ui/main_window.py`

**Steps:**
1. Remove `QIcon` from import line

---

### Phase 1B: Recommended Fixes

#### Fix 5: Add Markdown Support
**Files:** `requirements.txt`, `message_bubble.py`

**Steps:**
1. Add `markdown` and `pygments` to requirements
2. Import in message_bubble.py
3. Render markdown with `markdown.markdown()`
4. Use `setHtml()` instead of `setPlainText()`

---

#### Fix 6: Auto Token Refresh
**File:** `qwen_desktop/core/api_client.py`

**Steps:**
1. Call `refresh_token_if_needed()` in `_get_auth_header()`
2. Handle refresh failure gracefully

---

#### Fix 7: Platform Shortcuts
**File:** `qwen_desktop/ui/main_window.py`

**Steps:**
1. Detect platform
2. Use `Meta+,` on macOS, `Ctrl+,` elsewhere

---

## Execution Order

1. ✅ Fix 4 (Unused import) - 2 minutes
2. ✅ Fix 2 (Keyring errors) - 10 minutes
3. ✅ Fix 3 (Enter-to-send) - 15 minutes
4. ✅ Fix 1 (OAuth server) - 30 minutes
5. ⏸️ Fix 5 (Markdown) - 10 minutes
6. ⏸️ Fix 6 (Token refresh) - 10 minutes
7. ⏸️ Fix 7 (Platform shortcuts) - 5 minutes

**Total Critical:** ~1 hour  
**Total Recommended:** ~25 minutes

---

## Status: ✅ FIXED - All critical issues resolved

**Test Results:** 31/31 tests passing ✅
**Application:** Initializes successfully ✅

---

## Fixes Applied

### ✅ Fix 1: OAuth Callback Server (CRITICAL)
**File:** `qwen_desktop/ui/auth_dialog.py`

**Changes:**
- Added Flask HTTP server to listen on `localhost:8080/callback`
- Server runs in background daemon thread
- QTimer polls for callback completion every 500ms
- Proper callback handling with `handle_callback()` method

**Code Added:**
- `_start_callback_server()` - Starts Flask server
- `_check_callback()` - Polls for callback
- `_handle_callback()` - Processes OAuth response
- `_stop_callback_server()` - Cleanup

---

### ✅ Fix 2: Keyring Error Handling (CRITICAL)
**File:** `qwen_desktop/auth/credentials.py`

**Changes:**
- Added `keyring.errors` import
- Specific exception handling for `KeyringError`
- Logging for all errors
- Proper error propagation on save operations

---

### ✅ Fix 3: Enter-to-Send (CRITICAL)
**File:** `qwen_desktop/ui/input_area.py`

**Changes:**
- Installed event filter on text input
- `eventFilter()` handles Enter/Shift+Enter
- Enter alone sends message
- Shift+Enter creates new line

---

### ✅ Fix 4: Unused Import (CRITICAL)
**File:** `qwen_desktop/ui/main_window.py`

**Changes:**
- Removed `QIcon` from import

---

### ✅ Fix 5: Markdown Rendering (RECOMMENDED)
**Files:** `qwen_desktop/ui/message_bubble.py`

**Changes:**
- Import `markdown` library
- Render AI messages with `markdown.markdown()`
- Use `setHtml()` instead of `setPlainText()`
- Enable external links

---

### ✅ Fix 6: Auto Token Refresh (RECOMMENDED)
**File:** `qwen_desktop/core/api_client.py`

**Changes:**
- Added `AuthenticationError` exception class
- Call `refresh_token_if_needed()` in `_get_auth_header()`
- Raise error on refresh failure

---

### ✅ Fix 7: Platform Shortcuts (RECOMMENDED)
**File:** `qwen_desktop/ui/main_window.py`

**Changes:**
- Import `is_macos()` utility
- Use `Meta+,` on macOS, `Ctrl+,` elsewhere

---

## Test Plan Results

1. ✅ `py -m pytest tests/` - 31/31 passed
2. ✅ Application launches without errors
3. ✅ All imports resolve correctly
