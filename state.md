# Project State

## Completed Features

### 1. Core Application
- [x] PyQt6 floating assistant widget with expanding/collapsing UI
- [x] OAuth authentication with Qwen (device code flow + PKCE)
- [x] DashScope API client with streaming responses
- [x] Session management (QwenSessionService)
- [x] Rate limiting (1000 requests/day)
- [x] Settings management with JSON + QSettings persistence

### 2. Chat & AI
- [x] Chat history with session persistence
- [x] Vision mode (screenshot + AI analysis)
- [x] File/image attachments with staging area
- [x] Markdown rendering in chat

### 3. Voice Input
- [x] Mic button with toggle on/off state (user control, no auto-off)
- [x] Speech-to-text using SpeechRecognition (English: en-US, en-IN, en-GB)
- [x] Auto-send recognized text to Qwen
- [x] TTS speaker feedback when Qwen responds (while mic is on)
- [x] Duplicate recognition prevention (debounce)
- [x] Voice sending lock to prevent double messages

### 4. Desktop Automation
- [x] PyAutoGUI execution with ask_first/auto mode
- [x] UI Automation (Windows UIA) integration
- [x] OpenCV template matching cache
- [x] UIED element detection with manual box creation
- [x] Autonomous multi-step task execution
- [x] Figma-style toolbar overlay (move/box/delete tools)

### 5. Shell/Terminal Access (qwen-code style)
- [x] ShellTool with 3 permission modes:
  - `ask_first` - Ask before each command (default)
  - `auto_edit` - Auto-approve read-only, ask for write
  - `yolo` - Auto-approve everything
- [x] Read-only command detection (ls, dir, git status, ping, etc.)
- [x] Dangerous command detection (rm -rf, format, shutdown, etc.)
- [x] Permission confirmation dialog with 3 options: Deny, Run Once, Allow All
- [x] Shell result feedback loop to LLM for continuation
- [x] `[SHELL]...[/SHELL]` tag parsing in LLM responses
- [x] Computer expert system prompt (Windows/Linux/Unix/Networking/Cybersecurity)

### 6. Settings Dialog
- [x] Modern dark UI with sidebar navigation
- [x] Account page (login/logout, auth status)
- [x] MCP Servers page (add/remove, stdio/SSE/HTTP)
- [x] Extensions page (install from GitHub/local, view installed)
- [x] Agents page (create with YAML frontmatter, model/tools/prompt)
- [x] Skills page (create SKILL.md format, allowed tools)
- [x] Terminal page (execute commands, view output)
- [x] General page (API model, timeout, font size)

### 7. Configuration Files
- [x] MCP config: `~/.qwen/settings.json` (same as qwen-code)
- [x] Extensions: `~/.qwen/extensions/`
- [x] Agents: `~/.qwen/agents/*.md`
- [x] Skills: `~/.qwen/skills/*/SKILL.md`

## Pending Features

### High Priority
- [ ] MCP server connection testing (health check)
- [ ] Extension auto-loading on startup
- [ ] Agent execution from chat
- [ ] Skill loading and injection into system prompt
- [ ] Shell command output truncation for large results
- [ ] Background shell commands (long-running processes)
- [ ] Shell command history
- [ ] Permission rule persistence (remember user choices)

### Medium Priority
- [ ] Real-time terminal streaming (PTY mode)
- [ ] File editor integration (read/write files from chat)
- [ ] Git operations (status, diff, commit from chat)
- [ ] Web search/fetch tools
- [ ] Memory/context management
- [ ] Multi-model support with switching
- [ ] Export chat history
- [ ] Keyboard shortcuts

### Low Priority
- [ ] Light theme
- [ ] Custom CSS theming
- [ ] Plugin marketplace UI
- [ ] Collaborative features
- [ ] Voice output language selection
- [ ] Offline mode
- [ ] System tray integration
- [ ] Auto-start on boot

## Dependencies
- PyQt6, openai, requests, requests-oauthlib
- pyautogui, pynput, Pillow, opencv-python, uiautomation
- SpeechRecognition, PyAudio (voice input)
- pyyaml (agent/skill frontmatter)
- flask (OAuth callback server)
- easyocr (text detection)
- keyring (credential storage)

## Known Issues
- LSP import resolution errors (environment-specific, not runtime issues)
- API quota limits (free tier: 1000 requests/day)
