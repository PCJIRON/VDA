# Architecture

**Analysis Date:** 2026-06-06

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                                │
│          `run.py` / `qwen_desktop/__main__.py`                      │
│                        `qwen_desktop/app.py`                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        UI LAYER (PyQt6)                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  FloatingAssistant (main window)                             │   │
│  │  `qwen_desktop/ui/floating_assistant.py`                     │   │
│  │  ├── MessageBubble (chat messages)                           │   │
│  │  ├── APIServerWorker (async API thread)                      │   │
│  │  └── UI components (buttons, toolbar)                        │   │
│  └───────────┬──────────────────────────────────────────────────┘   │
│              │                                                       │
│  ┌───────────┴───────────────┐  ┌───────────────┐                  │
│  │ SettingsDialog            │  │ UIEDOverlay   │                  │
│  │ `settings_dialog.py`      │  │ `uied_overlay.py`               │
│  └───────────────────────────┘  └───────────────┘                  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      CORE SERVICE LAYER                              │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐         │
│  │ APIClient   │ │ ZenClient    │ │ SessionService       │         │
│  │ `api_client`│ │ `zen_client` │ │ `session_service.py` │         │
│  └──────┬──────┘ └──────┬───────┘ └──────────────────────┘         │
│         │               │                                           │
│  ┌──────┴──────────────────┴──────────────────────────────────┐    │
│  │              DESKTOP AUTOMATION                              │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐       │   │
│  │  │ VisionCapture│ │ PyAutoGUI    │ │ EnhancedExecutor │       │   │
│  │  │`vision_capture`│`pyautogui_exec`│`enhanced_executor`    │   │
│  │  └─────────────┘ └──────────────┘ └────────────────┘       │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐       │   │
│  │  │ UIEDService │ │ OpenCVDetect │ │ UniversalClick  │       │   │
│  │  │`uied_service`│`opencv_detect`│ │`universal_click`│       │   │
│  │  └─────────────┘ └──────────────┘ └────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐              │
│  │ MemoryMgr   │ │ BehaviorTrack│ │ TaskDecomposer  │              │
│  │`memory_mgr` │ │`behavior_track`│`task_decomposer`│              │
│  └─────────────┘ └──────────────┘ └────────────────┘              │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  SUPPORT LAYERS                                       │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐         │
│  │ Auth       │ │ Config    │ │ Attach   │ │ Utils       │         │
│  │`auth/`     │ │`config/`  │ │`attach/` │ │`utils/`     │         │
│  │ ProviderCfg│ │ Settings  │ │FileMgr   │ │ Logger, Err │         │
│  │            │ │ Defaults  │ │          │ │ Platform    │         │
│  └────────────┘ └───────────┘ └──────────┘ └─────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

## Pattern Overview

**Overall:** PyQt6 Desktop Application with Event-Driven UI and Multi-Layer Service Architecture

**Key Characteristics:**
- Single-window floating assistant GUI (PyQt6 QWidget)
- Event-driven UI with QThread workers for async API calls
- Multi-provider AI API support (OpenCode Zen, DeepSeek, OpenRouter, Gemini)
- Desktop automation stack (vision capture → element detection → click execution)
- File-based state persistence (JSON/JSONL in `~/.qwen-desktop/`)
- Template-matching for pixel-perfect UI automation

## Layers

**Entry Layer:**
- Purpose: Bootstrap the application, parse CLI args, create main app instance
- Location: `qwen-desktop/run.py`, `qwen_desktop/__main__.py`, `qwen_desktop/app.py`
- Contains: DesktopApp class, QApplication setup, logger init
- Depends on: Config layer (Settings), Utils (logger)
- Used by: CLI invocation (`py run.py` or `py -m qwen_desktop`)

**UI Layer:**
- Purpose: Render the floating assistant window and all interactive widgets
- Location: `qwen_desktop/ui/`
- Contains: `floating_assistant.py` (main widget, chat bubbles, input), `settings_dialog.py`, `uied_overlay.py`, `components/` (VisionButton, AttachButton, SendButton, SettingsButton, UIEDButton)
- Depends on: Core layer (API clients, vision, executors), Auth layer, Config layer
- Used by: Entry layer (DesktopApp creates FloatingAssistant)

**Core Service Layer:**
- Purpose: All business logic, API communication, desktop automation, and AI orchestration
- Location: `qwen_desktop/core/`
- Contains: APIClient, ZenClient, SessionService, VisionCapture, PyAutoGUIExecutor, EnhancedExecutor, ToolExecutor, UIEDService, OpenCVDetector, AutoTemplateExtractor, MemoryManager, BehaviorTracker, TaskDecomposer, ThinkingFilter, CommandRegistry, Models, DefaultPrompt, and multiple clicker variants (UniversalClicker, PerfectClicker, PixelPerfectClicker, QwenScreenClicker, OpencvQwenClicker, DebugClicker, LocalVisionClicker)
- Depends on: Auth layer (ProviderConfig), Config layer (Settings), Utils, external dependencies (httpx, opencv, pyautogui, pytesseract, uiautomation)
- Used by: UI layer (called from FloatingAssistant)

**Auth Layer:**
- Purpose: Manage AI provider credentials and configuration
- Location: `qwen_desktop/auth/provider_config.py`
- Contains: ProviderConfig class (reads/writes provider, API key, model, base URL)
- Depends on: Config layer (Settings, defaults.py for PROVIDERS registry)
- Used by: Core layer (APIClient, ZenClient), UI layer (SettingsDialog)

**Config Layer:**
- Purpose: Application settings persistence and defaults
- Location: `qwen_desktop/config/`
- Contains: `settings.py` (Settings class, JSON file persistence), `defaults.py` (PROVIDERS dict with all AI provider configs, DEFAULT_SETTINGS)
- Depends on: Utils (platform.py for OS-specific config paths)
- Used by: All layers

**Attachments Layer:**
- Purpose: File attachment management (validation, preview, encoding)
- Location: `qwen_desktop/attachments/file_manager.py`
- Contains: Attachment dataclass, file type detection, size formatting
- Depends on: Nothing internal (pathlib, dataclasses)
- Used by: UI layer (FloatingAssistant for file picker)

**Utilities Layer:**
- Purpose: Shared cross-cutting helpers
- Location: `qwen_desktop/utils/`
- Contains: `logger.py` (centralized logging setup), `error_handler.py` (error classification, user messages, suggested actions), `file_encoder.py` (base64 file encoding for API), `platform.py` (OS detection)
- Depends on: External libraries only
- Used by: All layers

## Data Flow

### Primary Request Path (Chat)

1. User types message in FloatingAssistant input field and clicks Send
2. `FloatingAssistant.send_message()` creates `APIServerWorker` (QThread), starts it
3. Worker calls `APIClient.send_message()` or `ZenClient.send_message()` with message + conversation history
4. API client sends POST to `/chat/completions` with streaming enabled
5. Response chunks arrive via `AsyncGenerator[str, None]`
6. Worker emits `chunk_received(str)` PyQt signal with visible content
7. `FloatingAssistant` updates `MessageBubble` in the chat scroll area
8. Worker emits `thinking_changed(str)` signal for invisible thinking tags
9. Worker emits `finished_response(str)` when stream completes
10. Full response appended to session history, persisted to JSONL

**State Management:**
- Session history stored as JSONL files in `~/.qwen-desktop/sessions/{project_hash}/chats/`
- Application settings stored as JSON in platform-specific config dir (e.g., `AppData/Local/QwenDesktop/config.json`)
- No in-memory cache between restarts (stateless on shutdown)
- Short/Long-term memory (in `memory_manager.py`) persists across in-session tasks

### Desktop Automation Flow

1. User enables Vision mode via VisionButton
2. `VisionCaptureService` starts listening for mouse/keyboard via `pynput`
3. On user interaction, screenshot captured via `pyautogui.screenshot()`
4. Screenshot encoded as base64, sent via `screenshot_ready` PyQt signal
5. FloatingAssistant appends vision data to next API call
6. AI response may include JSON actions (click, type, scroll at coordinates)
7. `PyAutoGUIExecutor` parses JSON, executes mouse actions via pyautogui
8. Click validation via `ClickValidator.capture_region()` + `verify_pixel_change()`
9. `BehaviorTracker` records all actions for learning

### UI Element Detection Flow (UIED)

1. User clicks UIEDButton → captures full-screen screenshot
2. `UIEDDetectionWorker` (QThread) runs:
   a. OpenCV contour analysis on screenshot → detects UI components
   b. Each component: x, y, width, height, type (button/input/icon/text)
   c. Components sent to Qwen Vision LLM for labeling
   d. LLM returns structured labels for each component
3. Components cached as templates in `~/.qwen-desktop/templates/`
4. Components displayed in `UIEDResultsPanel` (QMenu)
5. `UIEDOverlayWidget` shows bounding boxes on screen
6. Clicking a component triggers `PyAutoGUIExecutor` at exact coordinates

## Key Abstractions

**DesktopApp:**
- Purpose: Top-level application singleton, owns QApplication and FloatingAssistant
- Location: `qwen_desktop/app.py`
- Pattern: Singleton (single instance), composition root

**Service Classes:**
- Purpose: Encapsulate domain-specific business logic with settings-driven construction
- Examples: `APIClient` (`core/api_client.py`), `ZenClient` (`core/zen_client.py`), `SessionService` (`core/session_service.py`), `VisionCaptureService` (`core/vision_capture.py`), `UIEDService` (`core/uied_service.py`)
- Pattern: Service classes initialized with `Settings` object, stateless methods, async-ready

**QThread Workers:**
- Purpose: Run blocking/async operations without freezing the GUI
- Examples: `APIServerWorker` (`ui/floating_assistant.py`), `TestWorker` (`ui/settings_dialog.py`), `UIEDDetectionWorker` (`core/uied_service.py`)
- Pattern: QThread subclass with PyQt signals (`pyqtSignal`) for data emission back to main thread

**BaseButton Hierarchy:**
- Purpose: Reusable floating toolbar buttons with translucent hover, Fluent Icons font
- Location: `qwen_desktop/ui/components/base_button.py`
- Subclasses: `VisionButton`, `AttachButton`, `SendButton`, `SettingsButton`, `UIEDButton`
- Pattern: PyQt QPushButton subclass, custom `paintEvent` for hover effects, Segoe Fluent Icons font

**ProviderConfig:**
- Purpose: Abstracts multiple AI providers into a unified configuration interface
- Location: `qwen_desktop/auth/provider_config.py`
- Pattern: Facade over `defaults.py` PROVIDERS dict and `Settings` object

**Settings:**
- Purpose: JSON-file-backed key-value settings with default values
- Location: `qwen_desktop/config/settings.py`
- Pattern: Dictionary wrapper, lazy file loading, save on write

**ThinkingFilter:**
- Purpose: Strip/extract model thinking/reasoning tags from AI responses
- Location: `qwen_desktop/core/thinking_filter.py`
- Pattern: Regex-based text processing with multiple tag format support

## Entry Points

**Main Entry (module):**
- Location: `qwen_desktop/__main__.py`
- Triggers: `py -m qwen_desktop`
- Responsibilities: Create DesktopApp, call app.run(), exit with return code

**Main Entry (script):**
- Location: `run.py`
- Triggers: `py run.py`
- Responsibilities: Add project root to sys.path, create DesktopApp, call app.run()

**Console Script:**
- Location: Defined in `pyproject.toml` as `qwen-desktop = "qwen_desktop.__main__:main"`
- Triggers: `qwen-desktop` (after pip install)

## Error Handling

**Strategy:** Multi-layered — classification at utility level, user-facing messages at UI level, detailed logging throughout

**Patterns:**
- `utils/error_handler.py`: `classify_error()` maps status codes/exceptions to `ErrorType` enum (AUTH_ERROR, RATE_LIMIT, NETWORK_ERROR, SERVER_ERROR, FILE_ERROR, UNKNOWN)
- `get_user_message()` returns user-friendly error strings
- `get_suggested_action()` returns actionable recovery steps
- API clients raise `AuthenticationError` for auth failures
- QThread workers emit `error_occurred(str)` PyQt signal for GUI-level error display
- Top-level `try/except` in `DesktopApp.run()` catches unhandled exceptions, logs them
- Graceful import guards for optional dependencies (pyautogui, pynput, PIL, uiautomation)

## Cross-Cutting Concerns

**Logging:**
- Centralized `setup_logger()` in `qwen_desktop/utils/logger.py`
- Logs to console + file (`~/.qwen-desktop/app.log`)
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Logger name: `qwen_desktop` root, per-module loggers via `logging.getLogger(__name__)`

**Validation:**
- File attachment size limits (10MB max in `file_encoder.py`, `MAX_FILE_SIZE`)
- Provider connection validation via `test_connection()` methods on both API clients
- Optional dependency availability checked via try/except import guards
- Coordinate bounds clamping in click executors (`convert_to_screen()` clamps to screen dimensions)

**Authentication:**
- API key-based auth (Bearer tokens) for most providers
- OpenCode Zen supports anonymous access with `allow_anonymous=True`
- Provider selection and key storage via `Settings` JSON config file
- OAuth flow mentioned in docs but not in current codebase (older/auth module referenced in tests but not actively used)

**Desktop Automation Safety:**
- `pyautogui.FAILSAFE = False` (disabled — user should be cautious)
- Execution modes: `ask_first` (default), `auto_trusted`, `full_auto` in `PyAutoGUIExecutor`
- Coordinate validation: bounds checking, pixel change verification after clicks

---

*Architecture analysis: 2026-06-06*
*Update when major patterns change*
