# Phase 3 Research: File Attachments Enhancements

**Phase:** 3  
**Title:** File Attachments Enhancements  
**Research Date:** 2026-03-28

---

## 🎯 Phase Goal

Enhance the file attachment system with drag-and-drop improvements, rate limiting, conversation sidebar, and cross-platform testing.

---

## 📋 Requirements from ROADMAP.md

### Phase 3 Tasks (Original)
- [ ] 3.1 Create attachment preview component
- [ ] 3.2 Implement drag-and-drop handler
- [ ] 3.3 File picker dialog integration
- [ ] 3.4 File type detection
- [ ] 3.5 File validation (size, type)
- [ ] 3.6 Remove attachments UI
- [ ] 3.7 Send files with API requests
- [ ] 3.8 Image preview for multimodal

### Current Status (Post Phase 1 & 2)
- [x] 3.1 Attachment preview component ✅ (Phase 1)
- [x] 3.2 Drag-and-drop handler ✅ (Phase 2)
- [x] 3.3 File picker dialog ✅ (Phase 1)
- [x] 3.4 File type detection ✅ (Phase 1)
- [x] 3.5 File validation ✅ (Phase 1)
- [x] 3.6 Remove attachments UI ✅ (Phase 1)
- [ ] 3.7 Send files with API requests ⚠️ **Partial**
- [x] 3.8 Image preview ✅ (Phase 1)

**Additional Features Needed:**
- Rate limiting
- Conversation sidebar UI
- Enhanced error handling
- macOS/Linux testing

---

## 🔍 Implementation Research

### 1. Send Files with API Requests

**Current Status:** File attachments are collected but not sent to API.

**Approach Options:**

#### Option A: Base64 Encoding (Recommended)
**Pros:**
- Simple implementation
- Works with most APIs
- No external dependencies

**Cons:**
- Increases payload size (~33%)
- Memory usage for large files

**Implementation:**
```python
import base64

def encode_file(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# In api_client.py
attachment_data = {
    "type": "file",
    "name": attachment.name,
    "content": encode_file(attachment.file_path),
    "mime_type": mimetypes.guess_type(attachment.file_path)[0]
}
```

#### Option B: Multipart Form Data
**Pros:**
- Efficient for large files
- Standard for file uploads

**Cons:**
- More complex implementation
- Requires API support

**Recommendation:** Use Option A (Base64) for simplicity. Most LLM APIs support base64-encoded images/files.

---

### 2. Rate Limiting

**Requirement:** Implement rate limiting to handle API quotas (1,000 requests/day for free tier).

**Approach Options:**

#### Option A: Token Bucket Algorithm (Recommended)
**Implementation:**
```python
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, period_seconds: int):
        self.max_requests = max_requests
        self.period = timedelta(seconds=period_seconds)
        self.tokens = max_requests
        self.last_refill = datetime.now()
    
    def acquire(self) -> bool:
        self._refill()
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False
    
    def wait_time(self) -> timedelta:
        self._refill()
        if self.tokens > 0:
            return timedelta(0)
        return self.last_refill + self.period - datetime.now()
    
    def _refill(self):
        now = datetime.now()
        elapsed = now - self.last_refill
        tokens_to_add = int(elapsed / self.period * self.max_requests)
        self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
        self.last_refill = now
```

**Usage:**
```python
# In api_client.py
rate_limiter = RateLimiter(max_requests=1000, period_seconds=86400)  # 1000/day

async def chat(self, ...):
    if not self.rate_limiter.acquire():
        wait_time = self.rate_limiter.wait_time()
        raise RateLimitError(f"Rate limit exceeded. Wait {wait_time}")
```

#### Option B: Sliding Window
**Pros:** More accurate rate limiting  
**Cons:** More complex, requires storage

**Recommendation:** Use Option A (Token Bucket) for simplicity.

---

### 3. Conversation Sidebar UI

**Requirement:** Quick access to recent conversations.

**Approach Options:**

#### Option A: QDockWidget (Recommended)
**Pros:**
- Native Qt component
- Collapsible
- Can be floated

**Cons:**
- Less customization

**Implementation:**
```python
from PyQt6.QtWidgets import QDockWidget, QListWidget

class ConversationSidebar(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Conversations", parent)
        
        self.list_widget = QListWidget()
        self.setWidget(self.list_widget)
        
        # Load recent conversations
        self.load_conversations()
    
    def load_conversations(self):
        convs = conversation_manager.get_recent_conversations(limit=10)
        for conv in convs:
            item = QListWidgetItem(conv["title"])
            item.setData(Qt.ItemDataRole.UserRole, conv["filepath"])
            self.list_widget.addItem(item)
```

#### Option B: Custom QWidget with Toggle
**Pros:** Full customization  
**Cons:** More code to maintain

**Recommendation:** Use Option A (QDockWidget) for native integration.

---

### 4. Enhanced Error Handling

**Current Issues:**
- Generic error messages
- No retry mechanism
- No network status indicator

**Approach:**

#### Error Types to Handle:
1. **Authentication Errors (401)**
   - Auto-logout
   - Show login dialog
   
2. **Rate Limit Errors (429)**
   - Show countdown timer
   - Auto-retry after wait
   
3. **Network Errors**
   - Retry with exponential backoff
   - Show offline indicator
   
4. **Server Errors (500, 503)**
   - Retry up to 3 times
   - Show user-friendly message

#### Implementation:
```python
from enum import Enum
from typing import Optional

class ErrorType(Enum):
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"

def classify_error(status_code: Optional[int], error: Exception) -> ErrorType:
    if status_code == 401:
        return ErrorType.AUTH_ERROR
    elif status_code == 429:
        return ErrorType.RATE_LIMIT
    elif status_code and status_code >= 500:
        return ErrorType.SERVER_ERROR
    elif isinstance(error, (httpx.NetworkError, httpx.ConnectError)):
        return ErrorType.NETWORK_ERROR
    return ErrorType.UNKNOWN

def get_user_message(error_type: ErrorType) -> str:
    messages = {
        ErrorType.AUTH_ERROR: "Please log in again",
        ErrorType.RATE_LIMIT: "Too many requests. Waiting...",
        ErrorType.NETWORK_ERROR: "Network error. Check connection.",
        ErrorType.SERVER_ERROR: "API error. Retrying...",
    }
    return messages.get(error_type, "An error occurred")
```

---

### 5. Cross-Platform Testing

**Platforms to Test:**
- Windows 10/11 ✅ (Already tested)
- macOS 11+ ⚠️ Needs testing
- Linux (Ubuntu 20.04+) ⚠️ Needs testing

**Testing Checklist:**
- [ ] Application launches
- [ ] OAuth flow works
- [ ] File picker opens
- [ ] Drag-and-drop works
- [ ] Typing indicator displays
- [ ] Copy to clipboard works
- [ ] Conversations save/load
- [ ] Keyboard shortcuts work

**Platform-Specific Issues to Watch:**
- **macOS:** Cmd vs Ctrl shortcuts, file paths
- **Linux:** Keyring integration, file permissions
- **Windows:** Path separators, line endings

---

## 📦 Dependencies

### New Dependencies Needed
```txt
# Rate limiting (optional, can implement manually)
pyrate-limiter>=3.0.0

# MIME type detection (stdlib has mimetypes, but this is better)
python-magic>=0.4.27
```

**Recommendation:** No new dependencies needed. Use stdlib `mimetypes` and implement rate limiting manually.

---

## 🎯 Recommended Phase 3 Tasks

### Wave 1: Send Files with API (High Priority)
- Task 3.1: Base64 encode attachments
- Task 3.2: Add to API request payload
- Task 3.3: Handle API response with file context

### Wave 2: Rate Limiting (High Priority)
- Task 3.4: Implement TokenBucket rate limiter
- Task 3.5: Integrate with API client
- Task 3.6: Show rate limit status in UI

### Wave 3: Enhanced Error Handling (Medium Priority)
- Task 3.7: Error classification system
- Task 3.8: Retry mechanism with backoff
- Task 3.9: User-friendly error messages

### Wave 4: Conversation Sidebar (Medium Priority)
- Task 3.10: Create QDockWidget sidebar
- Task 3.11: Load recent conversations
- Task 3.12: Click to switch conversations

### Wave 5: Cross-Platform Testing (Low Priority)
- Task 3.13: Test on macOS (or document for testing)
- Task 3.14: Test on Linux (or document for testing)
- Task 3.15: Fix platform-specific issues

---

## ⏱️ Time Estimates

| Wave | Tasks | Estimated Time |
|------|-------|----------------|
| Wave 1 | 3.1-3.3 | 3 hours |
| Wave 2 | 3.4-3.6 | 2 hours |
| Wave 3 | 3.7-3.9 | 3 hours |
| Wave 4 | 3.10-3.12 | 4 hours |
| Wave 5 | 3.13-3.15 | 2 hours |
| **Total** | **15 tasks** | **14 hours** |

**Duration:** 1-2 weeks (part-time)

---

## ⚠️ Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API doesn't support file attachments | High | Check API docs first |
| Rate limiting too aggressive | Medium | Configurable limits |
| Sidebar UI conflicts with layout | Low | Test thoroughly |
| Cross-platform bugs | Medium | Test on VMs |

---

## 📝 Notes

1. **Priority Order:** Send files > Rate limiting > Error handling > Sidebar > Testing
2. **Dependencies:** None required (use stdlib)
3. **Testing:** Write tests alongside each feature
4. **Documentation:** Update README with new features

---

**Ready to Plan:** Run `/gsd:plan-phase 3` to create detailed task plans.
