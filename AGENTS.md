<!-- GSD:project-start source:PROJECT.md -->

## Project

**VDA — Voice-Driven Desktop Agent**

VDA is a desktop AI agent that controls computers like a human — seeing the screen, clicking, typing, and speaking. It combines vision-based desktop automation (already built) with an agentic loop (to build) that plans, executes tools, verifies results, and iterates until tasks are complete. Users interact via voice (push-to-talk STT with multilingual TTS response) or text chat in a floating PyQt6 assistant window.

**Core Value:** VDA must reliably turn a user's spoken or typed command into correct desktop actions — clicking the right things, typing the right text, running the right commands — without destroying user data or getting stuck in loops.

### Constraints

- **Tech Stack**: Python 3.9+ only. Keep everything in Python — no TypeScript/Node.js
- **Compatibility**: Must work on Windows (primary). macOS/Linux secondary
- **UI**: Keep PyQt6 floating assistant — replace internal widgets, don't change framework
- **API Provider**: Already implemented — do not modify APIClient/ZenClient architecture
- **Vision + Automation**: Already implemented — clean API exists for click/type/vision
- **Memory**: Local-only. No cloud storage for memory data
- **Agent Model**: Same AI provider as configured in VDA settings (user chooses provider/model)

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.9+ - Core application logic, all source code in `qwen-desktop/qwen_desktop/`
- Not detected

## Runtime

- CPython (standard Python runtime), requires >= 3.9
- pip (via `requirements.txt` and `requirements-dev.txt`)
- Build system: setuptools (configured in `qwen-desktop/pyproject.toml`)
- Lockfile: Not detected (no `poetry.lock`, `Pipfile.lock`, or `pdm.lock` present)

## Frameworks

- PyQt6 >= 6.4.0 - Desktop GUI framework used for the entire UI layer (`qwen-desktop/qwen_desktop/ui/`, `qwen_desktop/app.py`)
- httpx >= 0.25.0 - Async HTTP client for AI API communication (`qwen-desktop/qwen_desktop/core/api_client.py`, `core/zen_client.py`)
- `QApplication`, `QWidget`, `QLineEdit`, `QPushButton`, `QLabel`, `QVBoxLayout`, `QHBoxLayout`, `QScrollArea`, `QFrame` - Primary UI widget set
- `QPropertyAnimation`, `QVariantAnimation`, `QEasingCurve` - Animation framework for expand/collapse transitions
- `QThread`, `pyqtSignal` - Background threading for API streaming
- `QComboBox`, `QGroupBox`, `QFormLayout`, `QDialog` - Settings dialog components
- `QFileDialog`, `QGraphicsDropShadowEffect`, `QMenu`, `QTimer` - Utility components
- pytest >= 7.4.0 - Test runner (configured in `pyproject.toml` `[tool.pytest.ini_options]`)
- pytest-cov >= 4.1.0 - Coverage reporting
- pytest-qt >= 4.2.0 - Qt test helpers
- pytest-asyncio >= 0.21.0 - Async test support
- black >= 23.0.0 - Code formatter (line-length: 100, target-version: py39-py312)
- ruff >= 0.1.0 - Linter (select: E, F, W, I, N, D, UP; pydocstyle convention: google)
- mypy >= 1.5.0 - Static type checker (python_version: 3.9, warn_return_any: true)

## Key Dependencies

- `PyQt6>=6.4.0` - Entire GUI depends on it; no alternative
- `httpx>=0.25.0` - All AI API communication (streaming, async); cannot function without it
- `openai>=1.0.0` - OpenAI-compatible API client (listed in `requirements.txt` but `api_client.py` uses raw httpx, not the openai SDK)
- `pyautogui>=0.9.54` - Screen capture, mouse control, keyboard automation for vision mode
- `opencv-python>=4.8.0` - Template matching for UI element detection; pixel verification
- `Pillow>=10.0.0` - Image processing (screenshot resize, format conversion)
- `pynput>=1.7.6` - Global mouse/keyboard event listeners (vision trigger)
- `keyring>=24.0.0` - Secure credential storage for API keys
- `requests>=2.31.0` / `requests-oauthlib>=1.3.1` - OAuth flow support
- `flask>=3.0.0` - Local OAuth callback server (port 8080)
- `python-dotenv>=1.0.0` - Environment variable loading
- `pyyaml>=6.0.0` - YAML configuration parsing
- `markdown>=3.5.0` - Markdown rendering for AI responses
- `pygments>=2.17.0` - Syntax highlighting for code blocks
- `nest-asyncio>=1.6.0` - Async event loop integration with Qt event loop
- `aiofiles>=23.0.0` - Async file I/O
- `uiautomation>=2.0.18` - Windows UI Automation for 100% accurate element detection (Windows only)

## Configuration

- Settings stored as JSON at platform-specific paths:
- `python-dotenv` supports `.env` file loading (optional)
- API keys stored via `keyring` (OS-level credential manager) or in config file
- Logs written to `~/.qwen-desktop/app.log`
- Conversation history stored at `~/.qwen-desktop/sessions/{project_hash}/chats/`
- Memory/behavior data at `~/.qwen-desktop/memory/` and `~/.qwen-desktop/behavior/`
- UIED template images at `~/.qwen_desktop/uied_templates/`
- `pyproject.toml` at `qwen-desktop/pyproject.toml` - Project metadata, dependencies, tool configs
- `requirements.txt` at `qwen-desktop/requirements.txt` - Runtime dependencies (24 lines)
- `requirements-dev.txt` at `qwen-desktop/requirements-dev.txt` - Dev dependencies (14 lines)

## Platform Requirements

- Python 3.9+ installed
- pip install -r requirements.txt and requirements-dev.txt
- Windows recommended for full feature set (UI Automation, DPI scaling support)
- macOS/Linux supported but `uiautomation` is Windows-only
- Windows desktop (primary target, given `uiautomation`, `ctypes.windll`, DPI detection)
- No server deployment — this is a local desktop application
- Entry points: `py run.py` or `python -m qwen_desktop`

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- snake_case for all Python files (`file_manager.py`, `error_handler.py`, `api_client.py`)
- One module per file with focused responsibility
- `__init__.py` for barrel exports in each package directory
- snake_case for all functions and methods (`setup_logger`, `classify_error`, `get_user_message`)
- No special prefix for async functions (Python `async def` is its own marker)
- Private/helper methods use single underscore prefix: `_get_headers`, `_create_client`, `_load`, `_resolve_path`
- Class methods use `@classmethod` decorator: `from_api_response`, `get_default_models`, `get_provider_models`
- snake_case for module-level, local, and instance variables
- Module-level logger instance: `logger = logging.getLogger(__name__)` (`qwen_desktop/utils/error_handler.py`)
- No special prefix for instance variables (except `self._` for private/protected)
- UPPER_SNAKE_CASE for module-level constants: `MAX_FILE_SIZE`, `THINKING_PATTERNS`, `MEMORY_DIR`, `DEFAULT_SETTINGS`, `PROVIDERS` (`qwen_desktop/config/defaults.py`, `qwen_desktop/utils/file_encoder.py`)
- PascalCase for class names (`DesktopApp`, `Settings`, `APIClient`, `SessionService`, `ToolExecutor`) — `qwen_desktop/app.py`, `qwen_desktop/config/settings.py`
- PascalCase for dataclasses: `ModelInfo`, `TokenUsage`, `Attachment`, `SlashCommand` — `qwen_desktop/core/models.py`, `qwen_desktop/attachments/file_manager.py`, `qwen_desktop/core/command_registry.py`
- PascalCase for enums: `ErrorType` with UPPER_CASE values: `AUTH_ERROR`, `RATE_LIMIT` — `qwen_desktop/utils/error_handler.py`
- Type aliases use PascalCase: `Platform = Literal["windows", "macos", "linux", "other"]` — `qwen_desktop/utils/platform.py`

## Code Style

- Black formatter configured in `pyproject.toml` with `line-length = 100` and `target-version = ["py39", "py310", "py311", "py312"]`
- Ruff linter configured with `line-length = 100`, `target-version = "py39"`
- 100 character line length maximum
- Double quotes not enforced (mixed usage observed — single and double quotes both appear)
- 4-space indentation (Python standard)
- Ruff: `select = ["E", "F", "W", "I", "N", "D", "UP"]`, `ignore = ["D100", "D104"]` — `pyproject.toml`
- MyPy configured: `python_version = "3.9"`, `warn_return_any = true`, `disallow_untyped_defs = false`, `check_untyped_defs = true` — `pyproject.toml`
- Not enforced in CI (added as dev dependency only)
- Run: `ruff check .`, `mypy qwen_desktop`, `black --check .`

## Import Organization

- Blank line between standard library and third-party imports, and between third-party and local imports
- Alphabetical within groups
- `from` imports before simple `import` statements within groups
- No path aliases; all local imports use full package path: `from qwen_desktop.config.settings import Settings`
- Examples: `from qwen_desktop.utils.logger import setup_logger` (`qwen_desktop/app.py`), `from qwen_desktop.auth.provider_config import ProviderConfig` (`qwen_desktop/core/api_client.py`)

## Type Hints

- Type hints required for all function parameters and return types
- Module-level: `from typing import Optional, List, Dict, Any, Tuple`
- Modern syntax (`list[str]`, `dict[str, Any]`) used in many files (Python 3.9+ compatible)
- `Optional[X]` used for nullable values
- Return types always annotated, including `-> None` for void functions

## Error Handling

- Custom exception classes defined when needed: `class AuthenticationError(Exception):` (`qwen_desktop/core/api_client.py:15`)
- Try/except with specific exception types; broad `except Exception` only at top-level boundaries
- Centralized error classification via `classify_error()` — `qwen_desktop/utils/error_handler.py`
- Service methods often return error message strings rather than raising exceptions (e.g., `ToolExecutor.execute_tool` returns `f"Error: ..."` — `qwen_desktop/core/tool_executor.py:149`)
- Async generators yield error messages as strings: `yield f"Error: API returned {response.status_code}."` (`qwen_desktop/core/api_client.py:142`)
- Use `exc_info=True` with `logger.error()` to capture stack traces (`qwen_desktop/app.py:46`, `qwen_desktop/core/session_service.py:36`)
- Bare `except:` or `except Exception` used in some session deserialization as short-circuit (`qwen_desktop/core/session_service.py:62`)
- `try/finally` pattern for cleanup (e.g., `client.aclose()` in finally blocks — `qwen_desktop/core/api_client.py:71`)

## Logging

- Module-level logger: `logger = logging.getLogger(__name__)` (every module)
- Structured format: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- Log at service boundaries and external API calls
- Include error context: `logger.error(f"Application error: {e}", exc_info=True)` (`qwen_desktop/app.py:46`)
- Custom prefixes in log messages: `"[STM] Task started: ..."` (`qwen_desktop/core/memory_manager.py:31`), `"[UIA] UI Automation loaded successfully"` (`qwen_desktop/ui/floating_assistant.py:39`)
- No `print()` statements in production code (only `print()` found in `file_encoder.py` line 49 in an error path; should use logger)

## Comments

- Module-level docstring explaining purpose at top of every `.py` file
- Docstrings for all public functions and methods (Google-style)
- Inline comments for non-obvious logic, regular expressions, workarounds
- Class docstrings explaining purpose

## Function Design

- Most functions under 50-60 lines
- Complex operations extracted into helper methods
- One level of abstraction per function
- Max 4-5 parameters before using an options/settings object
- Default parameter values for optional arguments
- Type hints on all parameters
- Explicit return statements with annotated return types
- Return early for guard clauses (`if not path.exists(): return None` in `qwen_desktop/utils/file_encoder.py:28`)
- Return `None` for expected error states (not exceptions) in utility functions
- `Tuple[bool, str]` for validation results (`is_valid, error = manager.validate_file(...)`) — `qwen_desktop/attachments/file_manager.py:104`

## Module Design

- Each package has an `__init__.py` that imports and re-exports the public API
- `__all__` lists defined in `__init__.py`:
- `__init__.py` used as barrel files for package re-exports
- Internal helpers kept private (not exported from `__init__.py`)

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Pattern Overview

- Single-window floating assistant GUI (PyQt6 QWidget)
- Event-driven UI with QThread workers for async API calls
- Multi-provider AI API support (OpenCode Zen, DeepSeek, OpenRouter, Gemini)
- Desktop automation stack (vision capture → element detection → click execution)
- File-based state persistence (JSON/JSONL in `~/.qwen-desktop/`)
- Template-matching for pixel-perfect UI automation

## Layers

- Purpose: Bootstrap the application, parse CLI args, create main app instance
- Location: `qwen-desktop/run.py`, `qwen_desktop/__main__.py`, `qwen_desktop/app.py`
- Contains: DesktopApp class, QApplication setup, logger init
- Depends on: Config layer (Settings), Utils (logger)
- Used by: CLI invocation (`py run.py` or `py -m qwen_desktop`)
- Purpose: Render the floating assistant window and all interactive widgets
- Location: `qwen_desktop/ui/`
- Contains: `floating_assistant.py` (main widget, chat bubbles, input), `settings_dialog.py`, `uied_overlay.py`, `components/` (VisionButton, AttachButton, SendButton, SettingsButton, UIEDButton)
- Depends on: Core layer (API clients, vision, executors), Auth layer, Config layer
- Used by: Entry layer (DesktopApp creates FloatingAssistant)
- Purpose: All business logic, API communication, desktop automation, and AI orchestration
- Location: `qwen_desktop/core/`
- Contains: APIClient, ZenClient, SessionService, VisionCapture, PyAutoGUIExecutor, EnhancedExecutor, ToolExecutor, UIEDService, OpenCVDetector, AutoTemplateExtractor, MemoryManager, BehaviorTracker, TaskDecomposer, ThinkingFilter, CommandRegistry, Models, DefaultPrompt, and multiple clicker variants (UniversalClicker, PerfectClicker, PixelPerfectClicker, QwenScreenClicker, OpencvQwenClicker, DebugClicker, LocalVisionClicker)
- Depends on: Auth layer (ProviderConfig), Config layer (Settings), Utils, external dependencies (httpx, opencv, pyautogui, pytesseract, uiautomation)
- Used by: UI layer (called from FloatingAssistant)
- Purpose: Manage AI provider credentials and configuration
- Location: `qwen_desktop/auth/provider_config.py`
- Contains: ProviderConfig class (reads/writes provider, API key, model, base URL)
- Depends on: Config layer (Settings, defaults.py for PROVIDERS registry)
- Used by: Core layer (APIClient, ZenClient), UI layer (SettingsDialog)
- Purpose: Application settings persistence and defaults
- Location: `qwen_desktop/config/`
- Contains: `settings.py` (Settings class, JSON file persistence), `defaults.py` (PROVIDERS dict with all AI provider configs, DEFAULT_SETTINGS)
- Depends on: Utils (platform.py for OS-specific config paths)
- Used by: All layers
- Purpose: File attachment management (validation, preview, encoding)
- Location: `qwen_desktop/attachments/file_manager.py`
- Contains: Attachment dataclass, file type detection, size formatting
- Depends on: Nothing internal (pathlib, dataclasses)
- Used by: UI layer (FloatingAssistant for file picker)
- Purpose: Shared cross-cutting helpers
- Location: `qwen_desktop/utils/`
- Contains: `logger.py` (centralized logging setup), `error_handler.py` (error classification, user messages, suggested actions), `file_encoder.py` (base64 file encoding for API), `platform.py` (OS detection)
- Depends on: External libraries only
- Used by: All layers

## Data Flow

### Primary Request Path (Chat)

- Session history stored as JSONL files in `~/.qwen-desktop/sessions/{project_hash}/chats/`
- Application settings stored as JSON in platform-specific config dir (e.g., `AppData/Local/QwenDesktop/config.json`)
- No in-memory cache between restarts (stateless on shutdown)
- Short/Long-term memory (in `memory_manager.py`) persists across in-session tasks

### Desktop Automation Flow

### UI Element Detection Flow (UIED)

## Key Abstractions

- Purpose: Top-level application singleton, owns QApplication and FloatingAssistant
- Location: `qwen_desktop/app.py`
- Pattern: Singleton (single instance), composition root
- Purpose: Encapsulate domain-specific business logic with settings-driven construction
- Examples: `APIClient` (`core/api_client.py`), `ZenClient` (`core/zen_client.py`), `SessionService` (`core/session_service.py`), `VisionCaptureService` (`core/vision_capture.py`), `UIEDService` (`core/uied_service.py`)
- Pattern: Service classes initialized with `Settings` object, stateless methods, async-ready
- Purpose: Run blocking/async operations without freezing the GUI
- Examples: `APIServerWorker` (`ui/floating_assistant.py`), `TestWorker` (`ui/settings_dialog.py`), `UIEDDetectionWorker` (`core/uied_service.py`)
- Pattern: QThread subclass with PyQt signals (`pyqtSignal`) for data emission back to main thread
- Purpose: Reusable floating toolbar buttons with translucent hover, Fluent Icons font
- Location: `qwen_desktop/ui/components/base_button.py`
- Subclasses: `VisionButton`, `AttachButton`, `SendButton`, `SettingsButton`, `UIEDButton`
- Pattern: PyQt QPushButton subclass, custom `paintEvent` for hover effects, Segoe Fluent Icons font
- Purpose: Abstracts multiple AI providers into a unified configuration interface
- Location: `qwen_desktop/auth/provider_config.py`
- Pattern: Facade over `defaults.py` PROVIDERS dict and `Settings` object
- Purpose: JSON-file-backed key-value settings with default values
- Location: `qwen_desktop/config/settings.py`
- Pattern: Dictionary wrapper, lazy file loading, save on write
- Purpose: Strip/extract model thinking/reasoning tags from AI responses
- Location: `qwen_desktop/core/thinking_filter.py`
- Pattern: Regex-based text processing with multiple tag format support

## Entry Points

- Location: `qwen_desktop/__main__.py`
- Triggers: `py -m qwen_desktop`
- Responsibilities: Create DesktopApp, call app.run(), exit with return code
- Location: `run.py`
- Triggers: `py run.py`
- Responsibilities: Add project root to sys.path, create DesktopApp, call app.run()
- Location: Defined in `pyproject.toml` as `qwen-desktop = "qwen_desktop.__main__:main"`
- Triggers: `qwen-desktop` (after pip install)

## Error Handling

- `utils/error_handler.py`: `classify_error()` maps status codes/exceptions to `ErrorType` enum (AUTH_ERROR, RATE_LIMIT, NETWORK_ERROR, SERVER_ERROR, FILE_ERROR, UNKNOWN)
- `get_user_message()` returns user-friendly error strings
- `get_suggested_action()` returns actionable recovery steps
- API clients raise `AuthenticationError` for auth failures
- QThread workers emit `error_occurred(str)` PyQt signal for GUI-level error display
- Top-level `try/except` in `DesktopApp.run()` catches unhandled exceptions, logs them
- Graceful import guards for optional dependencies (pyautogui, pynput, PIL, uiautomation)

## Cross-Cutting Concerns

- Centralized `setup_logger()` in `qwen_desktop/utils/logger.py`
- Logs to console + file (`~/.qwen-desktop/app.log`)
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Logger name: `qwen_desktop` root, per-module loggers via `logging.getLogger(__name__)`
- File attachment size limits (10MB max in `file_encoder.py`, `MAX_FILE_SIZE`)
- Provider connection validation via `test_connection()` methods on both API clients
- Optional dependency availability checked via try/except import guards
- Coordinate bounds clamping in click executors (`convert_to_screen()` clamps to screen dimensions)
- API key-based auth (Bearer tokens) for most providers
- OpenCode Zen supports anonymous access with `allow_anonymous=True`
- Provider selection and key storage via `Settings` JSON config file
- OAuth flow mentioned in docs but not in current codebase (older/auth module referenced in tests but not actively used)
- `pyautogui.FAILSAFE = False` (disabled — user should be cautious)
- Execution modes: `ask_first` (default), `auto_trusted`, `full_auto` in `PyAutoGUIExecutor`
- Coordinate validation: bounds checking, pixel change verification after clicks

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
