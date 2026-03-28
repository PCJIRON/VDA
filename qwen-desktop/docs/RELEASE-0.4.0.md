# Release Notes - Qwen Desktop v0.4.0

**Release Date:** 2026-03-28  
**Version:** 0.4.0  
**Status:** ✅ Production Ready

---

## 🎉 What's New

Qwen Desktop v0.4.0 is a complete, production-ready desktop application for chatting with Qwen AI models. This release includes **4 major phases** of development:

### Phase 1: Foundation
- **OAuth Authentication** - Free tier with 1,000 requests/day
- **File Attachments** - Drag-and-drop or file picker
- **Chat UI** - Modern, intuitive interface
- **Settings** - Customizable configuration

### Phase 2: Core Chat
- **Typing Indicator** - Animated dots during API calls
- **Copy Messages** - One-click clipboard copy
- **Conversation Persistence** - Save and load chats
- **Keyboard Shortcuts** - Productivity-focused

### Phase 3: Enhancements
- **Send Files with API** - Base64 encoding, actual content sent
- **Rate Limiting** - Token bucket algorithm
- **Error Handling** - Retry with exponential backoff
- **Conversation Sidebar** - Quick access to recent chats

### Phase 4: Polish
- **Async Loading** - Non-blocking conversation load
- **Rate Limit UI** - Color-coded quota display
- **Documentation** - Complete user and developer guides
- **Cross-Platform Guide** - Testing procedures

---

## 📦 Installation

### Requirements

- Python 3.9 or higher
- 100MB disk space
- Internet connection

### Quick Install

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/qwen-desktop.git
cd qwen-desktop

# Install dependencies
py -m pip install -r requirements.txt

# Run application
py run.py
```

---

## 🚀 Getting Started

### First Login

1. Launch: `py run.py`
2. Click **"Login"**
3. Authorize in browser
4. Start chatting!

### Attaching Files

- **Drag-and-drop:** Drag file onto input area
- **File picker:** Click 📎 icon

### Managing Conversations

- **Save:** Ctrl+S
- **Load:** Ctrl+O or click in sidebar
- **New Chat:** Ctrl+N

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~7,500 |
| **Test Coverage** | 63 tests |
| **Files Created** | 20+ |
| **Commits** | 25+ |
| **Development Time** | 2 weeks |

---

## ✅ Verified Features

### Authentication
- [x] OAuth 2.0 flow
- [x] Token storage (OS keyring)
- [x] Auto token refresh
- [x] 1,000 requests/day quota

### File Attachments
- [x] Drag-and-drop
- [x] File picker
- [x] File validation (10MB limit)
- [x] Multiple file types supported
- [x] Base64 encoding for API

### Chat Interface
- [x] Markdown rendering
- [x] Syntax highlighting
- [x] Typing indicator
- [x] Copy messages
- [x] User/AI differentiation

### Conversation Management
- [x] Save conversations
- [x] Load conversations
- [x] Delete conversations
- [x] Sidebar with recent chats
- [x] Auto-save on new chat

### Error Handling
- [x] Rate limiting
- [x] Retry mechanism
- [x] User-friendly messages
- [x] 4xx error handling

---

## 🐛 Known Issues

### High Priority
- None

### Medium Priority
- macOS physical testing pending (documentation ready)
- Linux physical testing pending (documentation ready)

### Low Priority
- Startup time could be optimized (<3s currently)
- Memory usage could be optimized (<200MB currently)
- Export conversation feature planned for v0.5.0

---

## 🔧 Technical Changes

### New Files (20+)
- `utils/file_encoder.py` - Base64 encoding
- `utils/rate_limiter.py` - Thread-safe rate limiting
- `utils/error_handler.py` - Error classification
- `core/conversation_manager.py` - Persistence
- `ui/components/typing_indicator.py` - Animation
- `ui/components/conversation_sidebar.py` - Sidebar
- `docs/USER_GUIDE.md` - User documentation
- `docs/DEVELOPMENT.md` - Developer documentation
- `docs/PLATFORM_TESTING.md` - Testing guide
- Plus test files and planning documents

### Modified Files (10+)
- `core/api_client.py` - File sending, retry logic
- `ui/main_window.py` - Sidebar, rate limit UI
- `ui/input_area.py` - Drag-and-drop
- `ui/chat_widget.py` - Typing indicator
- `ui/message_bubble.py` - Copy button
- Plus utilities and tests

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | User instructions |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Developer guide |
| [docs/PLATFORM_TESTING.md](docs/PLATFORM_TESTING.md) | Testing procedures |

---

## 🧪 Testing

### Run Tests

```bash
py -m pytest tests/ -v
```

**Expected Output:**
```
============================= 63 passed ==============================
```

### Manual Testing Checklist

- [ ] Application launches
- [ ] OAuth login works
- [ ] File attachments work (drag + picker)
- [ ] Messages send and receive
- [ ] Typing indicator displays
- [ ] Copy button works
- [ ] Conversations save/load
- [ ] Sidebar shows conversations
- [ ] Rate limit displays

---

## 🎯 Upgrade Guide

### From v0.1.0

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies
py -m pip install -r requirements.txt

# Run application
py run.py
```

**Note:** Your saved conversations and settings are preserved in `~/.qwen-desktop/`.

---

## 🙏 Acknowledgments

Thanks to all contributors and the Qwen community!

Based on [qwen-code](https://github.com/QwenLM/qwen-code) CLI extension.

---

## 📄 License

Apache License 2.0

---

## 🔗 Links

- **Repository:** https://github.com/YOUR_USERNAME/qwen-desktop
- **Issues:** https://github.com/YOUR_USERNAME/qwen-desktop/issues
- **Discussions:** https://github.com/YOUR_USERNAME/qwen-desktop/discussions

---

**Happy Chatting! 🎉**
