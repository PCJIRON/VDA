# Qwen Desktop

**Version:** 0.4.0  
**License:** Apache 2.0

A PyQt-based desktop application for Qwen AI assistant, bringing the Qwen Code CLI experience to a native GUI environment.

[![Tests](https://img.shields.io/badge/tests-63%20passed-green)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)]()
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-blue.svg)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)]()

---

## ✨ Features

- 🎨 **Modern GUI** - Clean, intuitive interface built with PyQt6
- 🔐 **OAuth Authentication** - Secure login with Qwen/Google account (1,000 free requests/day)
- 📎 **File Attachments** - Drag-and-drop files for code review and analysis
- 💬 **Real-time Chat** - Stream responses from Qwen AI models
- 🎯 **Code Support** - Syntax highlighting for code blocks
- 📚 **Conversation Management** - Save, load, and organize conversations
- ⚡ **Rate Limiting** - Built-in quota tracking and enforcement
- 🔄 **Auto-Reconnect** - Automatic token refresh and retry logic
- 📊 **Sidebar** - Quick access to recent conversations
- ⌨️ **Keyboard Shortcuts** - Productivity-focused key bindings

---

## 📸 Screenshots

### Main Interface
```
┌─────────────────────────────────────────────────────────┐
│  Qwen Desktop                              [_][□][X]   │
├─────────────────────────────────────────────────────────┤
│  [New Chat]  │  Not logged in  [Login]  │  API: 950    │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │  Conversations                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │ 📄 Code Review Session        Oct 28 • 45  │ │  │
│  │  │ 📄 Python Debugging Help      Oct 27 • 23  │ │  │
│  │  │ 📄 API Integration Question   Oct 26 • 12  │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  💬 Chat Area                                    │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  User: Can you review this code?     [📋]  │ │  │
│  │  │  Assistant: Sure! I'd be happy to... [📋]  │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  [📎] Type your message...             [Send]    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/qwen-desktop.git
cd qwen-desktop

# Install dependencies
py -m pip install -r requirements.txt

# Run application
py run.py
```

### First Login

1. Launch the application: `py run.py`
2. Click **"Login"** button
3. Authorize in browser
4. Start chatting!

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete usage instructions |
| [Developer Guide](docs/DEVELOPMENT.md) | Building and contributing |
| [Platform Testing](docs/PLATFORM_TESTING.md) | Cross-platform test guide |

---

## ⌨️ Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| New Chat | `Ctrl+N` | `Cmd+N` |
| Open Conversation | `Ctrl+O` | `Cmd+O` |
| Save Conversation | `Ctrl+S` | `Cmd+S` |
| Clear Conversation | `Ctrl+Shift+C` | `Cmd+Shift+C` |
| Preferences | `Ctrl+,` | `Cmd+,` |
| Send Message | `Enter` | `Enter` |
| New Line | `Shift+Enter` | `Shift+Enter` |
| Quit | `Ctrl+Q` | `Cmd+Q` |

---

## 📦 Project Structure

```
qwen-desktop/
├── qwen_desktop/           # Main package
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── app.py              # Application class
│   ├── ui/                 # UI components
│   │   ├── main_window.py
│   │   ├── chat_widget.py
│   │   ├── input_area.py
│   │   ├── message_bubble.py
│   │   ├── auth_dialog.py
│   │   ├── settings_dialog.py
│   │   └── components/     # Reusable components
│   ├── core/               # Core logic
│   │   ├── api_client.py
│   │   ├── conversation.py
│   │   └── conversation_manager.py
│   ├── auth/               # Authentication
│   │   ├── oauth_handler.py
│   │   ├── token_manager.py
│   │   └── credentials.py
│   ├── attachments/        # File handling
│   │   └── file_manager.py
│   ├── config/             # Configuration
│   │   ├── settings.py
│   │   └── defaults.py
│   └── utils/              # Utilities
│       ├── logger.py
│       ├── platform.py
│       ├── file_encoder.py
│       ├── rate_limiter.py
│       └── error_handler.py
├── tests/                  # Test suite (63 tests)
├── docs/                   # Documentation
├── .planning/              # Project planning
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
py -m pytest tests/ -v

# Run with coverage
py -m pytest tests/ --cov=qwen_desktop --cov-report=html

# Run specific test file
py -m pytest tests/test_auth.py -v
```

**Test Coverage:** 63 tests passing ✅

---

## 🛠️ Development

### Setup Development Environment

```bash
# Create virtual environment
py -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dev dependencies
py -m pip install -r requirements-dev.txt
```

### Code Quality

```bash
# Format code
py -m black .

# Lint code
py -m ruff check .

# Type checking
py -m mypy qwen_desktop/
```

---

## 📊 Release History

### [0.4.0] - 2026-03-28

**Added:**
- Phase 1: OAuth authentication, file attachments, chat UI
- Phase 2: Drag-and-drop, typing indicator, copy messages, conversation persistence
- Phase 3: Send files with API, rate limiting, error handling, conversation sidebar
- Phase 4 (Partial): Async conversation loading, rate limit UI, cross-platform testing guide

**Fixed:**
- Memory DoS prevention (10MB file limit)
- Rate limiter thread safety
- Token calculation edge cases
- 4xx error retry logic

### [0.1.0] - 2026-03-28

**Initial Release:**
- Project structure
- Basic OAuth flow
- File picker dialog

---

## 🤝 Contributing

We welcome contributions! Please see our [Developer Guide](docs/DEVELOPMENT.md) for:

- Setting up development environment
- Code style guide
- Adding new features
- Running tests
- Submitting PRs

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/qwen-desktop.git
cd qwen-desktop

# Install dependencies
py -m pip install -r requirements.txt
py -m pip install -r requirements-dev.txt

# Run tests
py -m pytest tests/ -v

# Start coding!
```

---

## 🙏 Acknowledgments

- Based on [qwen-code](https://github.com/QwenLM/qwen-code) CLI extension
- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Inspired by modern chat applications

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Repository:** https://github.com/YOUR_USERNAME/qwen-desktop
- **Issues:** https://github.com/YOUR_USERNAME/qwen-desktop/issues
- **Discussions:** https://github.com/YOUR_USERNAME/qwen-desktop/discussions
- **Documentation:** https://github.com/YOUR_USERNAME/qwen-desktop/tree/main/docs

---

**Happy Chatting! 🎉**
