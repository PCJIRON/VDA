# Requirements: VDA — Voice-Driven Desktop Agent

**Defined:** 2026-06-06
**Core Value:** VDA must reliably turn a user's spoken or typed command into correct desktop actions — clicking the right things, typing the right text, running the right commands — without destroying user data or getting stuck in loops.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Agent System

- [ ] **AGNT-01**: Agent manager implements Antigravity-style loop (spec → plan → execute → verify → iterate) with max iteration limit
- [ ] **AGNT-02**: Doom loop detection — detect 3+ identical consecutive tool calls, trigger pause/user notification
- [ ] **AGNT-03**: Sub-agent delegation via task tool — manager spawns specialized agents with their own tool sets
- [ ] **AGNT-04**: Permission system — allow/deny/ask per tool, configurable by agent type
- [ ] **AGNT-05**: Session compaction — compress long conversation history to avoid context overflow
- [ ] **AGNT-06**: Tool registry with lazy initialization — tools loaded only when first used

### Web Tools

- [ ] **WEB-01**: Web search via API (Google/Bing/DuckDuckGo)
- [ ] **WEB-02**: Web page content fetch and markdown extraction
- [ ] **WEB-03**: Web scrolling and crawling for multi-page data collection
- [ ] **WEB-04**: Rate limiting and polite crawling (delay between requests)

### Terminal Tools

- [ ] **TERM-01**: PowerShell command execution with stdout/stderr capture
- [ ] **TERM-02**: Windows CMD support
- [ ] **TERM-03**: Cross-platform shell (bash on Linux/macOS)
- [ ] **TERM-04**: Working directory tracking per session

### File Tools

- [ ] **FILE-01**: File read with multiple format support (text, code, structured data)
- [ ] **FILE-02**: File write with safety checks (path validation, overwrite confirmation)
- [ ] **FILE-03**: Glob-based file search
- [ ] **FILE-04**: Grep-style content search across files

### Voice System

- [ ] **VOICE-01**: Push-to-talk microphone input capture (keyboard trigger in PyQt6)
- [ ] **VOICE-02**: Speech-to-text via API or local model
- [ ] **VOICE-03**: Multilingual text-to-speech response
- [ ] **VOICE-04**: Voice activation UI indicator (recording/speaking/idle states)
- [ ] **VOICE-05**: Interruptible TTS — new command stops current speech

### Memory & Learning

- [ ] **MEM-01**: Microsoft GraphRAG engine integration (local-only, file-based)
- [ ] **MEM-02**: Short-term memory — session chat history stored in GraphRAG
- [ ] **MEM-03**: Long-term memory — session data moved to persistent GraphRAG on session end
- [ ] **MEM-04**: Memory retrieval — prioritize short-term, fall back to long-term
- [ ] **MEM-05**: Daily user behavior cache — mouse/keyboard patterns stored as execution hints
- [ ] **MEM-06**: Mistake memory — failed tool calls stored with context, retrieved to inform future decisions

### Codebase Refactoring

- [ ] **RFCT-01**: Consolidate 8 clicker implementations into single ClickerEngine with pluggable strategies
- [ ] **RFCT-02**: Split `floating_assistant.py` (~1988 lines) into controller + chat widgets + action modules
- [ ] **RFCT-03**: Deduplicate APIClient/ZenClient into shared base client
- [ ] **RFCT-04**: Extract shared ScreenEnv/ScreenDetector into utils/screen.py

### Security

- [ ] **SEC-01**: Shell command approval dialog before execution (modal in PyQt6)
- [ ] **SEC-02**: API key storage via OS keychain (keyring library)
- [ ] **SEC-03**: Proper pyautogui.FAILSAFE restoration with try/finally guards
- [ ] **SEC-04**: Command whitelist and path traversal prevention in ToolExecutor

### GUI Redesign

- [ ] **GUI-01**: Create DESIGN.md for VDA with YAML tokens (colors, typography, spacing, components) + markdown rationale
- [ ] **GUI-02**: Modern floating assistant UI — clean chat bubbles, smooth animations, resizeable window
- [ ] **GUI-03**: Dark/light theme toggle matching DESIGN.md token system
- [ ] **GUI-04**: Tool execution visualization — show tool calls with real-time status (pending/running/done/error)
- [ ] **GUI-05**: Voice controls — mic button, speaking indicator, voice activation status bar
- [ ] **GUI-06**: Agent thinking visualization — show reasoning steps during complex tasks

### Testing

- [ ] **TEST-01**: Fix broken test suite (import non-existent modules)
- [ ] **TEST-02**: Unit tests for agent manager and loop logic
- [ ] **TEST-03**: Unit tests for web/terminal/file tools
- [ ] **TEST-04**: Unit tests for GraphRAG memory integration

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Machine Learning

- **ML-01**: Full reinforcement learning pipeline (reward modeling, policy training)
- **ML-02**: Fine-tuned behavior predictions from daily usage patterns

### Advanced Features

- **ADV-01**: MCP protocol support for third-party tool integration
- **ADV-02**: Wake-word activation (always-listening mode)
- **ADV-03**: Multi-monitor DPI-aware automation improvements
- **ADV-04**: Screen recording for replay/debugging

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full RL training pipeline | Too complex for v1; memory-based learning first |
| Web dashboard / API server | Desktop-only application |
| Mobile app | Windows desktop primary target |
| Cloud deployment | Fully local — no server infrastructure |
| Third-party MCP protocol | Use native Python tools instead |
| Browser extension | Desktop agent handles browser natively via vision |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGNT-01 | Phase 1 | Pending |
| AGNT-02 | Phase 1 | Pending |
| AGNT-03 | Phase 2 | Pending |
| AGNT-04 | Phase 1 | Pending |
| AGNT-05 | Phase 2 | Pending |
| AGNT-06 | Phase 1 | Pending |
| WEB-01 | Phase 2 | Pending |
| WEB-02 | Phase 2 | Pending |
| WEB-03 | Phase 3 | Pending |
| WEB-04 | Phase 2 | Pending |
| TERM-01 | Phase 3 | Pending |
| TERM-02 | Phase 3 | Pending |
| TERM-03 | Phase 3 | Pending |
| TERM-04 | Phase 3 | Pending |
| FILE-01 | Phase 2 | Pending |
| FILE-02 | Phase 2 | Pending |
| FILE-03 | Phase 2 | Pending |
| FILE-04 | Phase 2 | Pending |
| VOICE-01 | Phase 4 | Pending |
| VOICE-02 | Phase 4 | Pending |
| VOICE-03 | Phase 4 | Pending |
| VOICE-04 | Phase 4 | Pending |
| VOICE-05 | Phase 4 | Pending |
| MEM-01 | Phase 5 | Pending |
| MEM-02 | Phase 5 | Pending |
| MEM-03 | Phase 5 | Pending |
| MEM-04 | Phase 5 | Pending |
| MEM-05 | Phase 5 | Pending |
| MEM-06 | Phase 5 | Pending |
| RFCT-01 | Phase 1 | Pending |
| RFCT-02 | Phase 1 | Pending |
| RFCT-03 | Phase 1 | Pending |
| RFCT-04 | Phase 1 | Pending |
| SEC-01 | Phase 3 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 1 | Pending |
| SEC-04 | Phase 2 | Pending |
| GUI-01 | Phase 6 | Pending |
| GUI-02 | Phase 6 | Pending |
| GUI-03 | Phase 6 | Pending |
| GUI-04 | Phase 6 | Pending |
| GUI-05 | Phase 4 | Pending |
| GUI-06 | Phase 1 | Pending |
| TEST-01 | Phase 1 | Pending |
| TEST-02 | Phase 1 | Pending |
| TEST-03 | Phase 2 | Pending |
| TEST-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 45 total
- Mapped to phases: 45
- Unmapped: 0 ✓

---

*Requirements defined: 2026-06-06*
*Last updated: 2026-06-06 after initial definition*
