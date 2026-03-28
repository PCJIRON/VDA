# Qwen Desktop - Project Context

**Project Name:** Qwen Desktop  
**Version:** 0.4.0  
**Created:** 2026-03-28  
**Status:** UI Evolution - Performance & Native Integration Complete

---

## Overview

Qwen Desktop is a PyQt-based desktop application that brings the Qwen Code AI agent experience to a native GUI environment. It replicates the core functionality of the qwen-code CLI extension with a modern, intuitive desktop interface, and shares a unified command/history backend.

---

## Goals (Achieved)

1. **Native Desktop Experience** - PyQt6 GUI application for Windows, macOS, and Linux
2. **OAuth Authentication** - Seamless Qwen OAuth integration for free tier access (1,000 requests/day)
3. **File Attachment System** - Drag-and-drop file attachments for code review and analysis
4. **Chat Interface** - Real-time conversation with Qwen AI models (streaming)
5. **Unified Session History** - Full compatibility with `qwen-code` JSONL format at `~/.qwen/tmp/`
6. **Modular Architecture** - Well-organized, component-based codebase

---

## Inspiration

Based on the [qwen-code](../qwen-code) CLI extension with GUI redesign:
- Terminal UI → PyQt Desktop UI
- CLI commands → Menu actions and buttons
- Text-based output → Rich chat interface with markdown support

---

## Core Features (Completed)

### Phase 1 (Foundation)
- [x] Project setup and structure
- [x] OAuth authentication flow setup
- [x] File attachment abstractions
- [x] Basic chat interface

### Phase 2 (Core Chat)
- [x] Message Bubbles and Input area
- [x] API integration with Qwen models / DashScope
- [x] Stream responses in real-time
- [x] Conversation Saving and Loading

### Phase 3 (Attachments & Polish)
- [x] Drag & drop file functionality
- [x] Base64 encoding and submission to Qwen
- [x] Async Background Queues for Chat messages

### Phase 4 (Polish & Robustness)
- [x] Rate limit indicator and quota sync
- [x] comprehensive test suite (63+ assertions)
- [x] Multi-file refactor and UI separation

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.9+ |
| **GUI Framework** | PyQt6 |
| **HTTP Client** | Requests |
| **OAuth** | Device Code Flow (Custom handler) |
| **Syntax Highlighting** | Markdown integrated rendering |
| **Configuration** | JSON local storage (`.qwen_desktop/`) |
| **Security** | OS Keyring for auth tokens |

---

## Project Structure

```text
qwen-desktop/
├── qwen_desktop/           # Main package
│   ├── app.py              # Application class
│   ├── ui/                 # UI components
│   ├── core/               # Business logic & APIs
│   ├── auth/               # OAuth & Tokens
│   ├── attachments/        # File handling
│   ├── config/             # Settings
│   └── utils/              # Rate limiters & formatters
├── tests/                  # Test suite
└── docs/                   # Full documentation suite
```

---

## Key Decisions Made

1. **PyQt6** - Used over Tkinter for modern UI and native look.
2. **Device Flow Auth** - Selected for stability in desktop apps without requiring local webservers.
3. **QThread background workers** - Prevented UI-blocking during long LLM text generation streams.
4. **Keyring storage** - Decided against plain text token storage.
5. **Floating Assistant Architecture** - Pivot from `QMainWindow` to `FloatingAssistant` (frameless `QWidget`) for better desktop integration.
6. **Native JSONL Integration** - Transitioned to `QwenSessionService` for full interoperability with `qwen-code` CLI/IDE history.
7. **Thread-Based Streaming** - Adopted `QThread` workers to ensure zero UI latency during token generation.
8. **Instant UI Response** - Removed expansion animation in favor of instant geometry snaps to ensure layout stability and a "Pro" feel.

---

## Success Criteria Checklist

- [x] Application launches without errors
- [x] OAuth authentication works end-to-end
- [x] Users can attach files and send messages
- [x] AI responses display correctly with markdown
- [x] Clean, intuitive UI matching the design reference
- [x] Chat history persists between sessions
- [x] Floating Assistant - Frameless and Animated
- [x] Global outside-click to collapse logic
- [x] Robust test coverage

---

## Next Steps

1. Create a GitHub Release offering the `.whl` binaries.
2. Publish architecture documentation for the broader community.
