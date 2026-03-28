# Codebase Map

**Project:** Qwen Desktop  
**Version:** 0.4.0

---

## Top-Level Structure

```text
qwen-desktop/
├── qwen_desktop/           # Main Python Package Source
├── tests/                  # Unit and Integration Test Suite
├── docs/                   # Markdown Documentation
├── .planning/              # Current GSD Planning Documents
├── pyproject.toml          # Build system and project metadata
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Dev/Test dependencies
├── run.py                  # Entry Point Script
└── README.md               # Quick Start
```

---

## `qwen_desktop/` Source Map

```text
qwen_desktop/
├── __init__.py
├── __main__.py             # Executable module entry
├── app.py                  # PyQt Application Initialization
│
├── ui/                     # Presentation Layer Built on PyQt6
│   ├── main_window.py      # Main application frame
│   ├── chat_widget.py      # Conversation scrolling view
│   ├── input_area.py       # User typing input block
│   ├── message_bubble.py   # Bubble renderer for user/assistant
│   ├── auth_dialog.py      # OAuth graphical prompt
│   ├── settings_dialog.py  # User preferences GUI
│   └── components/         # Reusable widgets (Loading spinners, etc)
│
├── core/                   # Business Logic & State
│   ├── api_client.py               # DashScope/Qwen REST wrapper
│   ├── conversation.py             # Conversation data model
│   └── conversation_manager.py     # Saver/Loader for chat history
│
├── auth/                   # Identity & Security
│   ├── oauth_handler.py    # OAuth device code flow
│   ├── token_manager.py    # Keyring integration
│   └── credentials.py      # Secrets abstractions
│
├── attachments/            # File Management
│   └── file_manager.py     # IO limit checks & temp handlers
│
├── config/                 # Static Values & Preferences
│   ├── settings.py         # App config structure
│   └── defaults.py         # System defaults
│
└── utils/                  # Cross-Cutting Concerns
    ├── logger.py           # Standardized logger
    ├── platform.py         # OS-specific hacks
    ├── file_encoder.py     # Base64 parsing for API
    ├── rate_limiter.py     # Throttling logic
    └── error_handler.py    # Retry managers
```

---

## `tests/` Test Suite Map

```text
tests/
├── test_auth.py            # Authentication logic checks
├── test_api.py             # Mocked HTTP requests
├── test_ui.py              # QtBot GUI testing
├── test_storage.py         # Save/Load assertions
└── test_attachments.py     # File IO validators
```
