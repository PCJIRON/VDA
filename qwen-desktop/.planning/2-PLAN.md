# Phase 2 Plan: Core Chat Enhancements

**Phase:** 2  
**Title:** Core Chat Enhancements  
**Duration:** 2 weeks  
**Start Date:** 2026-03-28  
**Target End Date:** 2026-04-11

---

## 🎯 Phase Goal

Complete the remaining chat interface features and enhance the user experience with drag-and-drop attachments, typing indicators, conversation persistence, and copy functionality.

---

## 📊 Current Status (from Phase 1)

### Already Complete ✅
- Chat widget layout
- Message bubble component
- Input area with send button
- Qwen API client
- Send/receive messages
- Streaming responses
- Markdown rendering
- Syntax highlighting
- File picker dialog
- File validation

### Remaining Work ⚠️
- Drag-and-drop attachments
- Typing/loading indicator
- Copy message functionality
- Conversation history persistence
- Better error feedback

---

## 📋 Task Breakdown

### Wave 1: Drag-and-Drop Attachments (High Priority)

#### Task 2.1: Drag-and-Drop Event Handlers
**File:** `qwen_desktop/ui/input_area.py`

**Implementation:**
```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()

def dropEvent(self, event):
    for url in event.mimeData().urls():
        file_path = url.toLocalFile()
        self.add_attachment(file_path)
```

**Acceptance Criteria:**
- Drag file over input area → Highlight appears
- Drop file → File added as attachment
- Multiple files can be dropped at once

**Estimated Time:** 1 hour

---

#### Task 2.2: Drag-and-Drop Visual Feedback
**File:** `qwen_desktop/ui/input_area.py`

**Implementation:**
- Add drop zone highlight styling
- Show file count during drag
- Visual feedback on invalid file types

**Acceptance Criteria:**
- Blue border on drag enter
- File name preview during drag
- Red highlight for invalid files

**Estimated Time:** 1 hour

---

### Wave 2: Typing Indicator (High Priority)

#### Task 2.3: Typing Indicator Component
**File:** `qwen_desktop/ui/chat_widget.py`

**Implementation:**
```python
class TypingIndicator(QWidget):
    def __init__(self):
        # Three animated dots
        self.dot1 = QLabel("•")
        self.dot2 = QLabel("•")
        self.dot3 = QLabel("•")
        # Animation with QTimer
```

**Acceptance Criteria:**
- Shows when API request is in progress
- Three animated dots
- Disappears when response arrives
- Positioned at bottom of chat

**Estimated Time:** 2 hours

---

#### Task 2.4: Connect Typing Indicator to API
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
- Show indicator before API call
- Hide indicator when response starts streaming
- Handle error cases

**Acceptance Criteria:**
- Indicator appears immediately on send
- Disappears when first chunk arrives
- Shows error message if API fails

**Estimated Time:** 1 hour

---

### Wave 3: Copy Message Functionality (Medium Priority)

#### Task 2.5: Copy Button on Messages
**File:** `qwen_desktop/ui/message_bubble.py`

**Implementation:**
```python
def _setup_ui(self):
    # Add copy button in top-right corner
    self.copy_btn = QToolButton()
    self.copy_btn.setIcon(QIcon("copy.svg"))
    self.copy_btn.clicked.connect(self._copy_to_clipboard)

def _copy_to_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.text)
```

**Acceptance Criteria:**
- Copy icon appears on hover
- Click copies message text
- Toast notification on copy
- Works for both user and AI messages

**Estimated Time:** 2 hours

---

#### Task 2.6: Copy Code Block Button
**File:** `qwen_desktop/ui/message_bubble.py`

**Implementation:**
- Detect code blocks in markdown
- Add "Copy code" button to each code block
- Copy only the code content

**Acceptance Criteria:**
- "Copy" button on each code block
- Copies raw code (not markdown)
- Feedback on successful copy

**Estimated Time:** 2 hours

---

### Wave 4: Conversation Persistence (High Priority)

#### Task 2.7: Save Conversations to File
**File:** `qwen_desktop/core/conversation.py`

**Implementation:**
```python
class ConversationManager:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
    
    def save_conversation(self, conv: Conversation):
        # Save as JSON
        pass
    
    def load_conversation(self, conv_id: str) -> Conversation:
        # Load from JSON
        pass
    
    def list_conversations(self) -> List[Conversation]:
        # List all saved conversations
        pass
```

**Acceptance Criteria:**
- Auto-save on message add
- Save to `~/.qwen-desktop/conversations/`
- JSON format
- Include metadata (timestamp, model, token count)

**Estimated Time:** 3 hours

---

#### Task 2.8: Load Previous Conversations
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
- Add "Load Conversation" menu item
- Show conversation list in sidebar or dialog
- Load selected conversation into chat

**Acceptance Criteria:**
- File → Load Conversation menu
- Dialog shows conversation list with dates
- Click to load conversation
- Chat history displays correctly

**Estimated Time:** 3 hours

---

#### Task 2.9: Conversation Sidebar (Optional)
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
- Add collapsible sidebar
- Show recent conversations
- Quick switch between conversations

**Acceptance Criteria:**
- Sidebar toggle button
- List of last 10 conversations
- Click to switch
- Delete conversation option

**Estimated Time:** 4 hours

---

### Wave 5: Error Handling & Feedback (Medium Priority)

#### Task 2.10: Better Error Messages
**File:** `qwen_desktop/core/api_client.py`

**Implementation:**
- Catch specific HTTP errors
- Show user-friendly messages
- Suggest actions (retry, check connection, etc.)

**Error Types:**
- 401: Authentication failed → "Please login again"
- 429: Rate limit → "Too many requests, waiting..."
- 500: Server error → "API error, please retry"
- Timeout: "Request timed out"

**Estimated Time:** 2 hours

---

#### Task 2.11: Toast Notifications
**File:** `qwen_desktop/ui/main_window.py`

**Implementation:**
```python
class Toast(QFrame):
    def __init__(self, message, type="info"):
        # info, success, warning, error
        # Auto-dismiss after 3 seconds
```

**Acceptance Criteria:**
- Toast appears at bottom-right
- Different colors for different types
- Auto-dismiss after 3 seconds
- Manual dismiss on click

**Estimated Time:** 2 hours

---

#### Task 2.12: Retry Mechanism
**File:** `qwen_desktop/core/api_client.py`

**Implementation:**
- Add retry button to failed messages
- Exponential backoff
- Max 3 retries

**Acceptance Criteria:**
- Failed message shows "Retry" button
- Click retries same request
- Shows retry count

**Estimated Time:** 2 hours

---

### Wave 6: Polish & UX (Low Priority)

#### Task 2.13: Message Timestamps
**File:** `qwen_desktop/ui/message_bubble.py`

**Implementation:**
- Show timestamp on each message
- Format: "HH:MM" or "Yesterday" or "2 days ago"

**Acceptance Criteria:**
- Timestamp visible on hover or always
- Relative time for recent messages
- Full timestamp in tooltip

**Estimated Time:** 1 hour

---

#### Task 2.14: Scroll to Bottom Button
**File:** `qwen_desktop/ui/chat_widget.py`

**Implementation:**
- Show button when new messages arrive while scrolled up
- Click scrolls to latest message

**Acceptance Criteria:**
- Button appears when needed
- Smooth scroll animation
- Button hides at bottom

**Estimated Time:** 1 hour

---

#### Task 2.15: Improved Code Block Styling
**File:** `qwen_desktop/ui/message_bubble.py`

**Implementation:**
- Better syntax highlighting colors
- Language label on code blocks
- Line numbers (optional)

**Estimated Time:** 2 hours

---

## 📅 Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **Week 1** | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 | Drag-and-drop, Typing indicator, Copy functionality |
| **Week 2** | 2.7, 2.8, 2.9, 2.10, 2.11, 2.12 | Conversation persistence, Error handling |
| **Buffer** | 2.13, 2.14, 2.15 | Polish features |

---

## 🎯 Success Criteria

```bash
# All features working
py run.py
# → Can drag files onto input
# → Typing indicator shows during API calls
# → Can copy messages
# → Conversations persist across sessions
# → Clear error messages
```

### Metrics

| Metric | Target |
|--------|--------|
| Drag-and-drop | ✅ Working |
| Typing indicator | ✅ Shows during API calls |
| Copy messages | ✅ Works for all messages |
| Conversation save | ✅ Auto-saves |
| Conversation load | ✅ Loads correctly |
| Error messages | ✅ User-friendly |
| Test coverage | >75% |

---

## 📦 Files to Create/Modify

### Create
- `qwen_desktop/core/conversation_manager.py`
- `qwen_desktop/ui/components/toast.py`
- `qwen_desktop/ui/components/typing_indicator.py`
- `qwen_desktop/ui/dialogs/conversation_loader.py`
- `tests/test_conversation_manager.py`

### Modify
- `qwen_desktop/ui/input_area.py` (drag-drop)
- `qwen_desktop/ui/chat_widget.py` (typing indicator)
- `qwen_desktop/ui/message_bubble.py` (copy button)
- `qwen_desktop/ui/main_window.py` (menu, sidebar)
- `qwen_desktop/core/api_client.py` (error handling)

---

## 🔗 Dependencies

### Internal
- Phase 1 must be complete ✅
- OAuth authentication working ✅
- API client functional ✅

### External
- None (no new dependencies needed)

---

## ⚠️ Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Drag-and-drop complexity | Medium | Test on all platforms |
| Conversation sync issues | High | Use file locks |
| Performance with large history | Medium | Pagination |
| Cross-platform clipboard | Low | Use PyQt6 clipboard API |

---

## 📝 Notes

1. **Priority Order:** Drag-and-drop > Typing indicator > Copy > Persistence > Polish
2. **Testing:** Write tests alongside each feature
3. **Documentation:** Update README with new features
4. **Phase 3 Prep:** Keep conversation manager extensible for cloud sync

---

## ✅ Phase 2 Checklist

- [ ] Task 2.1: Drag-and-drop event handlers
- [ ] Task 2.2: Drag-and-drop visual feedback
- [ ] Task 2.3: Typing indicator component
- [ ] Task 2.4: Connect typing indicator to API
- [ ] Task 2.5: Copy button on messages
- [ ] Task 2.6: Copy code block button
- [ ] Task 2.7: Save conversations to file
- [ ] Task 2.8: Load previous conversations
- [ ] Task 2.9: Conversation sidebar (optional)
- [ ] Task 2.10: Better error messages
- [ ] Task 2.11: Toast notifications
- [ ] Task 2.12: Retry mechanism
- [ ] Task 2.13: Message timestamps
- [ ] Task 2.14: Scroll to bottom button
- [ ] Task 2.15: Improved code block styling

**Total Tasks:** 15  
**Estimated Time:** 30 hours  
**Duration:** 2 weeks

---

**Ready to Execute:** Run `/gsd:execute-phase 2` to start implementation.
