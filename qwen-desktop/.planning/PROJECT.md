# Qwen Desktop - Project Context

**Project Name:** Qwen Desktop  
**Version:** 0.1.0  
**Created:** 2026-03-28  
**Status:** In Development

---

## Overview

Qwen Desktop is a PyQt-based desktop application that brings the Qwen Code AI agent experience to a native GUI environment. It replicates the core functionality of the qwen-code CLI extension with a modern, intuitive desktop interface.

---

## Goals

1. **Native Desktop Experience** - PyQt5/PyQt6 GUI application for Windows, macOS, and Linux
2. **OAuth Authentication** - Seamless Qwen OAuth integration for free tier access (1,000 requests/day)
3. **File Attachment System** - Drag-and-drop file attachments for code review and analysis
4. **Chat Interface** - Real-time conversation with Qwen AI models
5. **Modular Architecture** - Well-organized, component-based codebase

---

## Inspiration

Based on the [qwen-code](../qwen-code) CLI extension with GUI redesign:
- Terminal UI → PyQt Desktop UI
- CLI commands → Menu actions and buttons
- Text-based output → Rich chat interface with markdown support

---

## Core Features

### Phase 1 (MVP)
- [x] Project setup and structure
- [ ] OAuth authentication flow
- [ ] Basic chat interface
- [ ] File attachment system
- [ ] API integration with Qwen models

### Phase 2 (Enhanced)
- [ ] Conversation history management
- [ ] Settings and configuration UI
- [ ] Syntax highlighting for code
- [ ] Export conversations

### Phase 3 (Advanced)
- [ ] Multi-model support
- [ ] Plugin system
- [ ] Custom themes
- [ ] System tray integration

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.9+ |
| **GUI Framework** | PyQt5 or PyQt6 |
| **HTTP Client** | httpx or requests |
| **OAuth** | requests-oauthlib |
| **Markdown** | markdown or mistune |
| **Syntax Highlighting** | pygments |
| **Configuration** | JSON + QSettings |

---

## Project Structure

```
qwen-desktop/
├── qwen_desktop/           # Main package
│   ├── __init__.py
│   ├── __main__.py         # Entry point (py -m qwen_desktop)
│   ├── app.py              # Application class
│   ├── ui/                 # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py  # Main application window
│   │   ├── chat_widget.py  # Chat interface
│   │   ├── message_bubble.py  # Message display
│   │   ├── input_area.py   # Input field with attachments
│   │   ├── attachment_preview.py  # File preview
│   │   ├── auth_dialog.py  # OAuth login dialog
│   │   └── settings_dialog.py  # Settings UI
│   ├── core/               # Core logic
│   │   ├── __init__.py
│   │   ├── api_client.py   # Qwen API client
│   │   ├── conversation.py # Conversation management
│   │   └── models.py       # Data models
│   ├── auth/               # Authentication
│   │   ├── __init__.py
│   │   ├── oauth_handler.py  # OAuth flow
│   │   ├── token_manager.py  # Token storage/refresh
│   │   └── credentials.py    # Credential management
│   ├── attachments/        # File handling
│   │   ├── __init__.py
│   │   ├── file_manager.py   # File operations
│   │   ├── file_preview.py   # Preview generation
│   │   └── supported_types.py  # File type definitions
│   ├── config/             # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py     # Settings management
│   │   └── defaults.py     # Default values
│   ├── utils/              # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py       # Logging setup
│   │   ├── async_utils.py  # Async helpers
│   │   └── platform.py     # Platform detection
│   └── resources/          # Assets
│       ├── __init__.py
│       ├── icons/          # Icon files
│       ├── styles/         # QSS stylesheets
│       └── images/         # Image assets
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_attachments.py
│   └── test_api.py
├── .planning/              # Project planning
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   └── config.json
├── pyproject.toml          # Python project config
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies
├── README.md               # Project readme
└── run.py                  # Development runner
```

---

## Key Decisions

1. **PyQt over Tkinter** - Modern UI, better styling, cross-platform
2. **Modular structure** - Separate concerns (UI, core, auth, attachments)
3. **OAuth first** - Free tier access for users
4. **File attachments** - Core feature from qwen-code CLI
5. **Python 3.9+** - Modern Python features, wide compatibility

---

## Success Criteria

- [ ] Application launches without errors
- [ ] OAuth authentication works end-to-end
- [ ] Users can attach files and send messages
- [ ] AI responses display correctly with markdown
- [ ] Clean, intuitive UI matching the design reference

---

## Related Projects

- **qwen-code** - Source of inspiration and API patterns
- **Qwen Models** - AI backend (qwen-coder, etc.)

---

## Next Steps

1. Review REQUIREMENTS.md for detailed specifications
2. Follow ROADMAP.md for phased implementation
3. Run `py run.py` to start development
4. Run `py -m pytest tests/` to run tests
