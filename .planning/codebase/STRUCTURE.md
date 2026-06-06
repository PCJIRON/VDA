# Codebase Structure

**Analysis Date:** 2026-06-06

## Directory Layout

```
VDA/
├── .planning/              # Project planning documents
├── graphify-out/            # Knowledge graph artifacts (generated)
├── qwen-desktop/            # Main application (Python package)
│   ├── qwen_desktop/       # Source package
│   │   ├── __main__.py     # Module entry point
│   │   ├── app.py          # Application class
│   │   ├── ui/             # PyQt6 UI layer
│   │   │   ├── floating_assistant.py  # Main floating window + chat
│   │   │   ├── settings_dialog.py      # AI provider settings
│   │   │   ├── uied_overlay.py         # UI element editor overlay
│   │   │   └── components/             # Reusable button widgets
│   │   ├── core/           # Business logic + services
│   │   │   ├── api_client.py           # OpenAI-compatible API
│   │   │   ├── zen_client.py           # OpenCode Zen API
│   │   │   ├── vision_capture.py       # Desktop screenshot service
│   │   │   ├── session_service.py      # Chat session persistence
│   │   │   ├── pyautogui_executor.py   # Mouse action executor
│   │   │   ├── enhanced_executor.py    # Enhanced coordinate clicker
│   │   │   ├── tool_executor.py        # File/shell tool execution
│   │   │   ├── uied_service.py         # UI element detection (OpenCV)
│   │   │   ├── opencv_detector.py      # Zero-shot OpenCV detection
│   │   │   ├── auto_template_extractor.py  # Template-based matching
│   │   │   ├── memory_manager.py       # Short/long-term memory
│   │   │   ├── behavior_tracker.py     # Action tracking and learning
│   │   │   ├── task_decomposer.py      # Task breakdown into steps
│   │   │   ├── thinking_filter.py      # Extract/remove thinking tags
│   │   │   ├── command_registry.py     # Slash commands (/help, /clear)
│   │   │   ├── default_prompt.py       # System prompt builder
│   │   │   ├── models.py               # Data models (ModelInfo, TokenUsage)
│   │   │   ├── universal_clicker.py    # Self-calibrating clicker
│   │   │   ├── perfect_clicker.py      # Alternative clicker
│   │   │   ├── pixel_perfect_clicker.py    # Pixel-precise clicker
│   │   │   ├── qwen_screen_clicker.py      # Qwen vision clicker
│   │   │   ├── opencv_qwen_clicker.py      # OpenCV+Qwen hybrid
│   │   │   ├── opencv_qwen_clicker_enhanced.py  # Enhanced hybrid
│   │   │   ├── local_vision_clicker.py   # Local-only vision clicker
│   │   │   └── debug_clicker.py         # Debug clicker
│   │   ├── auth/            # AI provider configuration
│   │   │   └── provider_config.py       # Provider credential management
│   │   ├── config/          # Application configuration
│   │   │   ├── settings.py              # JSON file-backed settings
│   │   │   └── defaults.py              # Provider registry + defaults
│   │   ├── attachments/     # File attachment management
│   │   │   └── file_manager.py          # Attachment dataclass + validation
│   │   ├── utils/           # Cross-cutting utilities
│   │   │   ├── logger.py                # Centralized logging setup
│   │   │   ├── error_handler.py         # Error classification + messages
│   │   │   ├── file_encoder.py          # Base64 file encoding
│   │   │   └── platform.py             # OS detection (win/mac/linux)
│   │   └── resources/       # Static resources
│   │       └── icons/                   # SVG icons (attach, send, settings, vision)
│   ├── tests/               # Test suite
│   │   ├── test_auth.py                 # Auth/credential tests
│   │   ├── test_attachments.py          # File attachment tests
│   │   ├── test_conversation.py         # Conversation model tests
│   │   ├── test_error_handler.py        # Error classification tests
│   │   └── test_file_encoder.py         # File encoding tests
│   ├── docs/                # Documentation
│   │   ├── USER_GUIDE.md                # User instructions
│   │   ├── DEVELOPMENT.md               # Developer setup guide
│   │   ├── PLATFORM_TESTING.md          # Cross-platform test matrix
│   │   ├── UIED_FEATURE.md              # UIED feature description
│   │   ├── UIED_VISION_PROMPT.md        # Vision prompt for UIED
│   │   ├── STATE_UIED.md                # UIED state machine design
│   │   └── RELEASE-0.4.0.md             # Release notes
│   ├── run.py               # Quick-start runner script
│   ├── pyproject.toml       # Build/package config
│   ├── requirements.txt     # Runtime dependencies
│   ├── requirements-dev.txt # Dev dependencies (testing, linting)
│   ├── README.md            # Project overview
│   └── CHANGELOG.md         # Version history
├── temp_make/               # Figma/design exports (Floating Button App mockup)
├── $null                    # Empty file (artifact)
├── .gitignore               # Git ignore rules
└── Floating Button App.make # Design file (placeholder)
```

## Directory Purposes

**`qwen-desktop/qwen_desktop/`:**
- Purpose: Main application source package
- Contains: All Python source code for the PyQt6 desktop assistant
- Key files: `__main__.py` (entry point), `app.py` (DesktopApp class), `__init__.py` (version: 0.5.0)
- Subdirectories: `ui/`, `core/`, `auth/`, `config/`, `attachments/`, `utils/`, `resources/`

**`qwen-desktop/qwen_desktop/ui/`:**
- Purpose: PyQt6 user interface widgets and windows
- Contains: `floating_assistant.py` (1988 lines — main window + chat bubbles + input + automation), `settings_dialog.py` (provider settings modal), `uied_overlay.py` (971 lines — Figma-style UI element editor overlay)
- Key files: `floating_assistant.py` (the largest file, contains FloatingAssistant, MessageBubble, APIServerWorker), `settings_dialog.py` (SettingsDialog, TestWorker)
- Subdirectories: `components/` — reusable button widgets

**`qwen-desktop/qwen_desktop/ui/components/`:**
- Purpose: Reusable floating toolbar button components
- Contains: `base_button.py` (BaseButton with translucent hover + Fluent Icons), `vision_button.py` (camera icon, toggles vision mode), `attach_button.py` (paperclip icon, opens file picker), `send_button.py` (send arrow icon, primary style), `settings_button.py` (gear icon, opens settings), `uied_button.py` (grid icon, triggers UI element detection with animations)
- Pattern: Each button is a thin QPushButton subclass extending BaseButton

**`qwen-desktop/qwen_desktop/core/`:**
- Purpose: All business logic, AI API clients, desktop automation, services
- Contains: 27 Python files covering API communication, vision capture, click execution, UI element detection, memory, task decomposition, behavior tracking
- Key files: `api_client.py` (primary API client), `zen_client.py` (OpenCode Zen client), `vision_capture.py` (screen capture service), `session_service.py` (chat persistence), `pyautogui_executor.py` (mouse automation), `tool_executor.py` (file/shell tools), `uied_service.py` (UI detection), `command_registry.py` (slash commands), `thinking_filter.py` (tag processing)
- Note: Contains multiple redundant clicker implementations (8 clicker variants in total)

**`qwen-desktop/qwen_desktop/auth/`:**
- Purpose: AI provider authentication and configuration
- Contains: `provider_config.py` (reads/writes provider settings, resolves provider info from defaults)
- Key files: `provider_config.py` (56 lines — ProviderConfig wrapping Settings + PROVIDERS dict)

**`qwen-desktop/qwen_desktop/config/`:**
- Purpose: Application configuration, defaults, and provider registry
- Contains: `settings.py` (JSON file-backed Settings with get/set/save/reset), `defaults.py` (PROVIDERS dict with 5+ providers, 50+ model entries, OS-specific config paths)
- Key files: `defaults.py` (148 lines — the authoritative provider + model registry)

**`qwen-desktop/qwen_desktop/attachments/`:**
- Purpose: File attachment handling
- Contains: `file_manager.py` (Attachment dataclass with file type detection, size formatting, supported extensions for code/images/configs)

**`qwen-desktop/qwen_desktop/utils/`:**
- Purpose: Cross-cutting utility functions
- Contains: `logger.py` (setup_logger — console + file), `error_handler.py` (ErrorType enum, classify_error, get_user_message, get_suggested_action), `file_encoder.py` (encode_file — base64 with size limit), `platform.py` (get_platform, is_windows, is_macos, is_linux)

**`qwen-desktop/qwen_desktop/resources/`:**
- Purpose: Static assets bundled with the application
- Contains: `icons/` directory with SVG files: `attach.svg`, `send.svg`, `settings.svg`, `vision.svg`

**`qwen-desktop/tests/`:**
- Purpose: Unit tests (pytest)
- Contains: 5 test files: `test_auth.py`, `test_attachments.py`, `test_conversation.py`, `test_error_handler.py`, `test_file_encoder.py`
- Coverage: Tests cover auth/credentials, file attachments, conversation models, error handling, and file encoding — does NOT cover UI, API clients, desktop automation, or core services

**`qwen-desktop/docs/`:**
- Purpose: Developer and user documentation
- Contains: 7 markdown documents covering user guide, developer setup, platform testing matrix, UIED feature spec, vision prompts, state machine design, and release notes

**`temp_make/`:**
- Purpose: Figma design exports for the Floating Button App mockup
- Contains: `meta.json`, `ai_chat.json`, `images/`, `canvas.fig`, `thumbnail.png`

**`graphify-out/`:**
- Purpose: Knowledge graph artifacts (auto-generated by graphify skill)
- Contains: `graph.json`, `graph.html`, `manifest.json`, `cache/`, `GRAPH_REPORT.md`
- Committed: Yes (generated artifacts checked in)

## Key File Locations

**Entry Points:**
- `qwen-desktop/run.py`: Quick-start runner script (adds project root to path, creates DesktopApp, calls run)
- `qwen-desktop/qwen_desktop/__main__.py`: Module entry point (`py -m qwen_desktop`)
- `qwen-desktop/qwen_desktop/app.py`: DesktopApp class (creates QApplication, Settings, FloatingAssistant)

**Configuration:**
- `qwen-desktop/pyproject.toml`: Build config, dependencies, tool configs (black, ruff, mypy, pytest)
- `qwen-desktop/requirements.txt`: Runtime dependencies (PyQt6, openai, httpx, opencv-python, pyautogui, etc.)
- `qwen-desktop/requirements-dev.txt`: Dev dependencies (pytest, pytest-cov, black, ruff, mypy)

**Core Logic:**
- `qwen-desktop/qwen_desktop/core/api_client.py`: OpenAI-compatible streaming API client (192 lines)
- `qwen-desktop/qwen_desktop/core/zen_client.py`: OpenCode Zen streaming API client (221 lines)
- `qwen-desktop/qwen_desktop/core/session_service.py`: Chat session CRUD + JSONL persistence (194 lines)
- `qwen-desktop/qwen_desktop/core/vision_capture.py`: Pynput-based screenshot service (214 lines)
- `qwen-desktop/qwen_desktop/core/pyautogui_executor.py`: Mouse action JSON parser + executor (352 lines)
- `qwen-desktop/qwen_desktop/core/uied_service.py`: OpenCV + LLM UI element detection (494 lines)
- `qwen-desktop/qwen_desktop/core/tool_executor.py`: File read/write + shell tool definitions (296 lines)
- `qwen-desktop/qwen_desktop/core/memory_manager.py`: Short-term, long-term memory, daily cache (159 lines)
- `qwen-desktop/qwen_desktop/core/behavior_tracker.py`: Session action logging + pattern learning (196 lines)
- `qwen-desktop/qwen_desktop/core/task_decomposer.py`: Multi-step task planner (188 lines)
- `qwen-desktop/qwen_desktop/core/default_prompt.py`: Desktop automation system prompt builder (106 lines)
- `qwen-desktop/qwen_desktop/core/thinking_filter.py`: Regex-based thinking tag extractor (69 lines)
- `qwen-desktop/qwen_desktop/core/command_registry.py`: Slash command register + dispatcher (223 lines)
- `qwen-desktop/qwen_desktop/core/models.py`: ModelInfo + TokenUsage dataclasses (56 lines)

**UI:**
- `qwen-desktop/qwen_desktop/ui/floating_assistant.py`: Main floating assistant widget, chat messages, input, automation triggers (1988 lines)
- `qwen-desktop/qwen_desktop/ui/settings_dialog.py`: AI provider settings dialog with test connection (298 lines)
- `qwen-desktop/qwen_desktop/ui/uied_overlay.py`: Figma-style UI element editor overlay with toolbar (971 lines)

**Testing:**
- `qwen-desktop/tests/test_auth.py`: Credentials/TokenManager unit tests (109 lines)
- `qwen-desktop/tests/test_conversation.py`: Message/Conversation model tests (185 lines)
- `qwen-desktop/tests/test_error_handler.py`: Error classification tests
- `qwen-desktop/tests/test_attachments.py`: File attachment tests
- `qwen-desktop/tests/test_file_encoder.py`: File encoding tests

## Naming Conventions

**Files:**
- `snake_case.py`: All Python source files (e.g., `floating_assistant.py`, `api_client.py`, `provider_config.py`)
- `test_snake_case.py`: Test files (e.g., `test_auth.py`, `test_conversation.py`)
- `UPPERCASE.md`: Documentation files (README.md, CHANGELOG.md, USER_GUIDE.md)
- `lowercase.md`: Most docs

**Directories:**
- `snake_case`: All source directories (e.g., `qwen_desktop/`, `ui/`, `core/`, `components/`)
- `kebab-case`: Top-level directories (e.g., `qwen-desktop/`, `temp_make/`, `graphify-out/`)
- `kebab-case`: Docs directory structure

**Classes:**
- `PascalCase`: All classes (e.g., `DesktopApp`, `FloatingAssistant`, `APIClient`, `Settings`, `BaseButton`, `SessionService`)
- `PascalCase`: QThread subclasses with Worker suffix (e.g., `APIServerWorker`, `TestWorker`, `UIEDDetectionWorker`)

**Functions/Methods:**
- `snake_case`: All functions and methods (e.g., `send_message()`, `setup_logger()`, `classify_error()`, `encode_file()`, `strip_thinking()`)
- `snake_case`: Module-level functions (e.g., `get_project_hash()`, `build_system_prompt()`, `detect_coordinate_range()`)

**Variables:**
- `snake_case`: All variables and parameters
- `UPPER_SNAKE_CASE`: Constants (e.g., `MAX_FILE_SIZE`, `MEMORY_DIR`, `BEHAVIOR_DIR`, `TEMPLATE_DIR`, `DESKTOP_ASSISTANT_SYSTEM_PROMPT`)
- Leading underscore for private members (e.g., `self._config`, `self._settings`, `self._is_detecting`)

**Types:**
- `PascalCase`: Type aliases using Literal (e.g., `Platform = Literal["windows", "macos", "linux", "other"]`)
- `PascalCase`: Enums (e.g., `ErrorType`, `class ErrorType(Enum)`)

## Where to Add New Code

**New Feature (e.g., new AI provider):**
- Provider config: Add to `qwen-desktop/qwen_desktop/config/defaults.py` in the PROVIDERS dict
- Auth handling: Update `qwen-desktop/qwen_desktop/auth/provider_config.py` if new auth scheme
- API client: Create new client in `qwen-desktop/qwen_desktop/core/` extending base pattern
- Tests: `qwen-desktop/tests/test_{feature}.py`
- Settings UI: Update `qwen-desktop/qwen_desktop/ui/settings_dialog.py`

**New UI Component:**
- Implementation: `qwen-desktop/qwen_desktop/ui/components/{name}_button.py` (extends BaseButton)
- Integration: Add to `qwen-desktop/qwen_desktop/ui/floating_assistant.py` (import + toolbar layout)
- Icon: Add SVG to `qwen-desktop/qwen_desktop/resources/icons/`

**New Service/Executor:**
- Implementation: `qwen-desktop/qwen_desktop/core/{name}.py`
- Tests: `qwen-desktop/tests/test_{name}.py`
- Integration: Wire into `FloatingAssistant` in `floating_assistant.py`

**New Slash Command:**
- Registration: Add to `CommandRegistry._register_defaults()` in `qwen-desktop/qwen_desktop/core/command_registry.py`
- Handler: Define handler method in the command module or in `FloatingAssistant`

**New Utility:**
- Implementation: `qwen-desktop/qwen_desktop/utils/{name}.py`
- Tests: `qwen-desktop/tests/test_{name}.py`

**New Test:**
- Test file: `qwen-desktop/tests/test_{subject}.py`
- Follow existing pattern: pytest classes with `Test{SubjectName}` naming, methods with `test_` prefix

## Special Directories

**`graphify-out/`:**
- Purpose: Auto-generated knowledge graph from the codebase analysis
- Source: Generated by the graphify skill
- Committed: Yes (checked in)
- Content: `graph.json`, `graph.html`, `cache/`, `manifest.json`, `GRAPH_REPORT.md`

**`temp_make/`:**
- Purpose: Figma design exports for UI mockup (Floating Button App)
- Source: Exported from Figma design tool
- Committed: Yes
- Content: `meta.json`, `ai_chat.json`, `canvas.fig`, `images/`, `thumbnail.png`

**`__pycache__/`:**
- Purpose: Python bytecode cache (auto-generated)
- Source: Python interpreter
- Committed: No (should be gitignored)
- Location: Multiple directories under `qwen_desktop/` (ui/, core/, auth/, config/, utils/)

---

*Structure analysis: 2026-06-06*
*Update when directory structure changes*
