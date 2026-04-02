# Project Understanding - Qwen Desktop

## What is Qwen Desktop?

Qwen Desktop is a PyQt6-based desktop AI assistant application that provides:
- Floating widget interface (expandable button)
- Chat with Qwen AI (via DashScope API)
- Voice input/output
- Desktop automation (PyAutoGUI + UI Automation)
- Shell/terminal access with permission controls
- Vision mode (screenshot analysis)
- MCP server integration
- Extensions, agents, and skills management

## Architecture

### Entry Point
- `qwen-desktop/run.py` - Application bootstrap
- `qwen-desktop/qwen_desktop/app.py` - Creates QApplication, launches FloatingAssistant

### Core Modules

#### `qwen_desktop/ui/floating_assistant.py` (Main UI)
- `FloatingAssistant` - Main widget (frameless, always-on-top, translucent)
- Collapsed: 70x70 glowing orb
- Expanded: 450x450 chat interface
- Contains: input field, send/stop, mic, vision, uied, attach, settings buttons
- Chat history popup with session management
- PyAutoGUI execution flow
- Shell command handling
- Voice input/output

#### `qwen_desktop/core/api_client.py` (API)
- `APIClient` - OpenAI SDK wrapper for DashScope/Qwen API
- OAuth token authentication
- Streaming responses
- Vision mode support
- Rate limiting (1000 req/day)
- System prompts: VISION_SYSTEM_PROMPT, COMPUTER_EXPERT_PROMPT

#### `qwen_desktop/core/shell_tool.py` (Shell)
- `ShellTool` - Shell execution with permission modes
- Modes: ask_first, auto_edit, yolo
- Read-only command detection
- Dangerous command detection
- Result formatting for LLM and user

#### `qwen_desktop/core/voice_service.py` (Voice)
- `VoiceService` - Background speech recognition
- Multi-language: en-US, en-IN, en-GB
- Continuous listening until stopped
- Debounce for duplicate prevention
- Signals: text_recognized, error_occurred, state_changed

#### `qwen_desktop/auth/` (Authentication)
- OAuth device code flow with PKCE
- Qwen OAuth endpoints (chat.qwen.ai)
- Token management and refresh
- Credential storage (keyring)

#### `qwen_desktop/config/settings.py` (Settings)
- JSON + QSettings persistence
- Default settings from `defaults.py`
- Platform-specific config paths

#### `qwen_desktop/ui/settings_dialog.py` (Settings UI)
- Modern dark theme with sidebar
- Pages: Account, MCP Servers, Extensions, Agents, Skills, Terminal, General
- MCP config: `~/.qwen/settings.json`
- Extensions: `~/.qwen/extensions/`
- Agents: `~/.qwen/agents/*.md`
- Skills: `~/.qwen/skills/*/SKILL.md`

### UI Components
- `BaseButton` - Circular button with icon (Segoe MDL2 Assets)
- `SendButton`, `VisionButton`, `AttachButton`, `SettingsButton`, `MicButton`, `UIEDButton`
- `ChatHistoryPopup` - Scrollable chat area with message bubbles
- `UIEDOverlayWidget` - Full-screen overlay for UI element detection

### Desktop Automation
- `PyAutoGUIExecutor` - Mouse/keyboard automation
- `VisionCaptureService` - Screenshot capture
- UI Automation (Windows) - Accurate element coordinates
- OpenCV template matching cache
- UIED element detection with manual box creation

## Dependencies
```
PyQt6, openai, requests, requests-oauthlib
pyautogui, pynput, Pillow, opencv-python, uiautomation
SpeechRecognition, PyAudio
pyyaml, flask, easyocr, keyring
```

## Key Patterns

### Message Flow
1. User types/speaks → input_field
2. Submit → `_handle_api()` → APIServerWorker (QThread)
3. Stream chunks → `_on_api_chunk()` → update UI
4. Complete → `_on_api_finished()` → save to session
5. If `[SHELL]` detected → permission dialog → execute → send result back
6. If `[PYAUTOGUI]` detected → execute automation
7. If JSON action detected → UIED template matching

### Permission Model (Shell)
```
Command received
  → YOLO mode? → Auto-execute
  → Read-only? → Auto-execute
  → Dangerous? → Warn user
  → Otherwise → Ask user (Deny/Run Once/Allow All)
```

### Session Management
- Sessions stored in `~/.qwen/tmp/<device-id>/chats/`
- Each session: JSON with messages, timestamps, parent_uuid chain
- Session switching via history popup

### OAuth Flow
1. User clicks Login → QwenAuthDialog
2. Request device code from `chat.qwen.ai/api/v1/oauth2/device/code`
3. Open browser for user authorization
4. Poll `chat.qwen.ai/api/v1/oauth2/token` for access token
5. Save credentials to keyring
6. Use token for DashScope API calls

## qwen-code Integration Points

### MCP Servers
- Config format matches qwen-code exactly
- Same file: `~/.qwen/settings.json`
- Supports stdio, SSE, HTTP transports
- OAuth for MCP servers

### Extensions
- Format: `qwen-extension.json`
- Can bundle MCP servers, skills, agents, hooks
- Install from GitHub or local path

### Agents
- Format: `.md` files with YAML frontmatter
- Same fields: name, description, tools, modelConfig, runConfig
- Stored in `~/.qwen/agents/`

### Skills
- Format: `SKILL.md` with YAML frontmatter
- Same fields: name, description, allowedTools
- Stored in `~/.qwen/skills/`

### Shell Tool
- Permission modes match qwen-code (ask_first, auto_edit, yolo)
- Read-only command detection
- Dangerous command detection
- Result formatting for LLM

## Current State
- Application runs successfully
- Chat with Qwen AI works
- Voice input works (English)
- Shell tool integrated with permission dialog
- Settings dialog with all management pages
- Computer expert system prompt injected
- Some API quota limits (free tier)

## File Structure
```
qwen-desktop/
├── run.py                          # Entry point
├── requirements.txt                # Dependencies
├── pyproject.toml                  # Package config
├── qwen_desktop/
│   ├── app.py                      # App bootstrap
│   ├── core/
│   │   ├── api_client.py           # DashScope API
│   │   ├── shell_tool.py           # Shell execution
│   │   ├── voice_service.py        # Speech recognition
│   │   ├── models.py               # Data models
│   │   ├── qwen_session_service.py # Session management
│   │   ├── pyautogui_executor.py   # Desktop automation
│   │   └── vision_capture.py       # Screenshot service
│   ├── ui/
│   │   ├── floating_assistant.py   # Main UI widget
│   │   ├── settings_dialog.py      # Settings dialog
│   │   ├── uied_overlay.py         # UI element overlay
│   │   └── components/             # Button components
│   ├── auth/
│   │   ├── oauth_handler.py        # OAuth flow
│   │   ├── qwen_auth_gui.py        # Auth dialog
│   │   ├── credentials.py          # Credential storage
│   │   └── token_manager.py        # Token management
│   ├── config/
│   │   ├── settings.py             # Settings manager
│   │   └── defaults.py             # Default settings
│   ├── utils/                      # Utilities
│   └── attachments/                # File handling
```
