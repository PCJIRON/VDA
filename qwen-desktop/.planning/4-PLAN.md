# Phase 4 Plan: Polish & Testing

**Phase:** 4  
**Title:** Polish & Testing  
**Duration:** 2 weeks  
**Start Date:** 2026-03-28  
**Target End Date:** 2026-04-11

---

## 🎯 Phase Goal

Refine the application with cross-platform testing, performance optimization, additional polish features, and comprehensive documentation for release.

---

## 📊 Current Status (Post Phase 3)

### Already Complete ✅
- OAuth authentication
- File attachments (picker + drag-and-drop)
- Send files with API
- Chat UI with markdown
- Typing indicator
- Copy messages
- Conversation persistence + sidebar
- Rate limiting (1,000/day)
- Enhanced error handling with retry
- 63 unit tests passing

### Remaining Work ⚠️
- Cross-platform testing (macOS, Linux)
- Performance optimization
- Additional polish features
- Release documentation
- Installer creation (optional)

---

## 📋 Task Breakdown

### Wave 1: Cross-Platform Testing (High Priority)

#### Task 4.1: macOS Testing
**Platform:** macOS 11+

**Test Checklist:**
- [ ] Application launches
- [ ] OAuth flow works (browser opens, callback received)
- [ ] File picker opens
- [ ] Drag-and-drop works
- [ ] Typing indicator displays
- [ ] Copy to clipboard works (Cmd+C vs Ctrl+C)
- [ ] Conversations save/load
- [ ] Keyboard shortcuts work (Cmd vs Ctrl)
- [ ] Sidebar docks correctly
- [ ] UI renders correctly (Retina display)

**Platform-Specific Issues to Check:**
- Cmd vs Ctrl for shortcuts
- File path separators
- Keychain integration for tokens
- Retina display scaling

**Estimated Time:** 4 hours

---

#### Task 4.2: Linux Testing
**Platform:** Ubuntu 20.04+

**Test Checklist:**
- [ ] Application launches
- [ ] OAuth flow works
- [ ] File picker opens
- [ ] Drag-and-drop works
- [ ] Typing indicator displays
- [ ] Copy to clipboard works
- [ ] Conversations save/load
- [ ] Keyboard shortcuts work
- [ ] Sidebar docks correctly
- [ ] System keyring works (for tokens)

**Platform-Specific Issues to Check:**
- Keyring integration (secretstorage)
- File permissions
- X11/Wayland compatibility
- GTK file picker vs Qt file picker

**Estimated Time:** 4 hours

---

#### Task 4.3: Windows Testing (Verification)
**Platform:** Windows 10/11

**Test Checklist:**
- [ ] All existing tests pass (already verified)
- [ ] Credential Manager integration works
- [ ] File paths work correctly
- [ ] Drag-and-drop works

**Estimated Time:** 1 hour (already mostly tested)

---

### Wave 2: Performance Optimization (High Priority)

#### Task 4.4: Startup Performance
**Goal:** Launch in <2 seconds

**Optimization Targets:**
- Reduce import overhead
- Lazy-load heavy components
- Profile startup time

**Implementation:**
```python
# Lazy import heavy modules
def _load_heavy_module():
    if not hasattr(self, '_heavy'):
        import some_heavy_module
        self._heavy = some_heavy_module
    return self._heavy
```

**Estimated Time:** 3 hours

---

#### Task 4.5: Conversation Loading Performance
**Goal:** Load 100 conversations in <1 second

**Optimization Targets:**
- Async conversation loading
- Cache conversation metadata
- Virtual scrolling for long lists

**Implementation:**
```python
# In conversation_sidebar.py
from PyQt6.QtCore import QThread, pyqtSignal

class ConversationLoader(QThread):
    loaded = pyqtSignal(list)
    
    def run(self):
        convs = self.manager.get_recent_conversations()
        self.loaded.emit(convs)
```

**Estimated Time:** 4 hours

---

#### Task 4.6: Memory Optimization
**Goal:** Keep memory usage <200MB

**Optimization Targets:**
- Clear old conversations from cache
- Limit attachment preview size
- Optimize image encoding

**Implementation:**
```python
# Add LRU cache for conversations
from functools import lru_cache

@lru_cache(maxsize=50)
def get_conversation(filepath: str):
    ...
```

**Estimated Time:** 3 hours

---

### Wave 3: Polish Features (Medium Priority)

#### Task 4.7: Rate Limit UI Indicator
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
```python
# In toolbar or status bar
self.rate_limit_label = QLabel("API: 950 left")

def update_rate_limit():
    usage = self.api_client.rate_limiter.get_usage()
    remaining = usage["tokens_remaining"]
    color = "#44aa44" if remaining > 100 else "#ffaa00" if remaining > 10 else "#ff4444"
    self.rate_limit_label.setText(f"API: {remaining} left")
    self.rate_limit_label.setStyleSheet(f"color: {color}")
```

**Estimated Time:** 2 hours

---

#### Task 4.8: Message Timestamps
**File:** `qwen_desktop/ui/message_bubble.py`

**Implementation:**
```python
# Add timestamp label
from datetime import datetime

timestamp = datetime.now().strftime("%H:%M")
self.timestamp_label = QLabel(timestamp)
self.timestamp_label.setStyleSheet("color: #888; font-size: 10px;")
```

**Estimated Time:** 2 hours

---

#### Task 4.9: Scroll to Bottom Button
**File:** `qwen_desktop/ui/chat_widget.py`

**Implementation:**
```python
# Show button when scrolled up
self.scroll_btn = QPushButton("↓")
self.scroll_btn.setFixedSize(30, 30)
self.scroll_btn.clicked.connect(self._scroll_to_bottom)
self.scroll_btn.hide()

def _scroll_to_bottom(self):
    self.scroll_area.verticalScrollBar().setValue(
        self.scroll_area.verticalScrollBar().maximum()
    )
```

**Estimated Time:** 2 hours

---

#### Task 4.10: Export Conversation
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
```python
def export_conversation(format="md"):
    """Export conversation to Markdown/PDF/JSON."""
    from PyQt6.QtWidgets import QFileDialog
    
    filepath, _ = QFileDialog.getSaveFileName(
        self, "Export Conversation", "", "Markdown (*.md);;PDF (*.pdf);;JSON (*.json)"
    )
    
    if filepath:
        # Export based on format
        ...
```

**Estimated Time:** 4 hours

---

### Wave 4: Documentation (High Priority)

#### Task 4.11: User Guide
**File:** `docs/USER_GUIDE.md`

**Sections:**
- Installation
- First-time setup (OAuth)
- Using the application
  - Sending messages
  - Attaching files
  - Managing conversations
- Keyboard shortcuts
- Troubleshooting
- FAQ

**Estimated Time:** 4 hours

---

#### Task 4.12: Developer Documentation
**File:** `docs/DEVELOPMENT.md`

**Sections:**
- Project structure
- Building from source
- Running tests
- Code style guide
- Adding new features
- Debugging tips

**Estimated Time:** 3 hours

---

#### Task 4.13: API Documentation
**File:** `docs/API.md`

**Sections:**
- OAuth setup
- API endpoints
- Rate limits
- Error codes
- File attachment format

**Estimated Time:** 2 hours

---

#### Task 4.14: README Update
**File:** `README.md`

**Updates:**
- Add Phase 1-3 features
- Add screenshots
- Update installation instructions
- Add usage examples
- Add badges (tests, license, etc.)

**Estimated Time:** 3 hours

---

### Wave 5: Release Preparation (Medium Priority)

#### Task 4.15: Version Numbering
**File:** `qwen_desktop/__init__.py`

**Change:**
```python
__version__ = "0.4.0"  # Bump from 0.1.0
```

**Estimated Time:** 0.5 hours

---

#### Task 4.16: CHANGELOG
**File:** `CHANGELOG.md`

**Sections:**
- [0.4.0] - 2026-04-11
  - Phase 1: Foundation
  - Phase 2: Core Chat
  - Phase 3: File Attachments
  - Phase 4: Polish & Testing

**Estimated Time:** 1 hour

---

#### Task 4.17: Release Notes
**File:** `docs/RELEASE-0.4.0.md`

**Sections:**
- What's new
- Installation
- Known issues
- Upgrade guide

**Estimated Time:** 2 hours

---

#### Task 4.18: Installer Creation (Optional)
**Platform:** Windows, macOS, Linux

**Options:**
- Windows: NSIS or Inno Setup
- macOS: .dmg creator
- Linux: .deb/.rpm packages

**Estimated Time:** 6 hours (optional)

---

## 📅 Timeline

| Week | Waves | Deliverables |
|------|-------|--------------|
| **Week 1** | Wave 1 + Wave 2 | Cross-platform tests, Performance optimizations |
| **Week 2** | Wave 3 + Wave 4 + Wave 5 | Polish features, Documentation, Release prep |

---

## 🎯 Success Criteria

```bash
# All tests pass
py -m pytest tests/ -v
# → 63+ tests passing

# Application launches quickly
time py run.py
# → <2 seconds to visible UI

# Memory usage is reasonable
# → <200MB during normal use

# Documentation is complete
# → USER_GUIDE.md, DEVELOPMENT.md, API.md all present
```

### Metrics

| Metric | Target |
|--------|--------|
| Tests | >63 |
| Platforms Tested | 3 (Win, macOS, Linux) |
| Documentation | 4 files |
| Performance | <2s startup |
| Memory | <200MB |

---

## 📦 Files to Create

### Documentation
- `docs/USER_GUIDE.md`
- `docs/DEVELOPMENT.md`
- `docs/API.md`
- `docs/RELEASE-0.4.0.md`
- `CHANGELOG.md`

### Tests (Optional)
- `tests/test_rate_limiter.py` - Additional rate limiter tests
- `tests/test_platform.py` - Platform detection tests

---

## 🔗 Dependencies

### Internal
- Phase 1-3 must be complete ✅
- PR for Phases 1-3 should be merged first

### External
- None (no new dependencies needed)

---

## ⚠️ Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| macOS/Linux testing reveals bugs | High | Test early, fix before release |
| Performance optimizations break features | Medium | Test after each optimization |
| Documentation takes longer than expected | Low | Prioritize user guide |
| Installer creation is complex | Medium | Make optional for first release |

---

## 📝 Notes

1. **Priority Order:** Cross-platform testing > Documentation > Performance > Polish features
2. **Testing:** Use VMs or cloud services for macOS/Linux if not available locally
3. **Documentation:** Write as you go, not at the end
4. **Release:** Consider a beta release first for community testing

---

## ✅ Phase 4 Checklist

- [ ] Task 4.1: macOS Testing
- [ ] Task 4.2: Linux Testing
- [ ] Task 4.3: Windows Testing (Verification)
- [ ] Task 4.4: Startup Performance
- [ ] Task 4.5: Conversation Loading Performance
- [ ] Task 4.6: Memory Optimization
- [ ] Task 4.7: Rate Limit UI Indicator
- [ ] Task 4.8: Message Timestamps
- [ ] Task 4.9: Scroll to Bottom Button
- [ ] Task 4.10: Export Conversation
- [ ] Task 4.11: User Guide
- [ ] Task 4.12: Developer Documentation
- [ ] Task 4.13: API Documentation
- [ ] Task 4.14: README Update
- [ ] Task 4.15: Version Numbering
- [ ] Task 4.16: CHANGELOG
- [ ] Task 4.17: Release Notes
- [ ] Task 4.18: Installer Creation (Optional)

**Total Tasks:** 18  
**Estimated Time:** 50 hours  
**Duration:** 2 weeks

---

**Ready to Execute:** Run `/gsd:execute-phase 4` to start Phase 4.
