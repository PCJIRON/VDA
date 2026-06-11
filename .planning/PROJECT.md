# VDA — Voice-Driven Desktop Agent

## What This Is

VDA is a desktop AI agent that controls computers like a human — seeing the screen, clicking, typing, and speaking. It combines vision-based desktop automation (already built) with an agentic loop (to build) that plans, executes tools, verifies results, and iterates until tasks are complete. Users interact via voice (push-to-talk STT with multilingual TTS response) or text chat in a floating PyQt6 assistant window.

## Core Value

VDA must reliably turn a user's spoken or typed command into correct desktop actions — clicking the right things, typing the right text, running the right commands — without destroying user data or getting stuck in loops.

## Requirements

### Validated

- ✓ **Vision capture**: Full-screen screenshot on user interaction, base64 encoding for AI API — existing
- ✓ **Mouse/keyboard control**: 8 clicker implementations with coordinate detection, DPI scaling, pixel verification — existing
- ✓ **AI API integration**: Dual clients (APIClient + ZenClient) communicating with OpenAI-compatible and OpenCode Zen providers — existing
- ✓ **Chat UI**: PyQt6 floating assistant window with message bubbles, input field, toolbar buttons — existing
- ✓ **Settings**: JSON-file-backed settings with multiple provider configuration — existing
- ✓ **Session management**: Chat history persistence as JSONL files — existing
- ✓ **Basic tool execution**: File read/write and shell command execution — existing
- ✓ **Basic memory**: Short-term and long-term memory with daily task cache — existing
- ✓ **Behavior tracking**: Records mouse/keyboard actions for learning — existing
- ✓ **Task decomposition**: Basic TaskDecomposer — existing
- ✓ **File attachments**: Upload images/text files as context — existing
- ✓ **UI element detection**: OpenCV contour analysis + vision-LLM labeling — existing

### Active

- [ ] **VDA-AGENT-01**: Agent manager with Antigravity-style plan→execute→verify→iterate loop
- [ ] **VDA-AGENT-02**: Specialized sub-agents (Web, Terminal, File, Voice) managed by orchestrator
- [ ] **VDA-WEB-01**: Web search tool (Google/Bing search via API)
- [ ] **VDA-WEB-02**: Web page fetch and content extraction
- [ ] **VDA-WEB-03**: Web scrolling and crawling for multi-page data
- [ ] **VDA-TERM-01**: PowerShell terminal access with command execution
- [ ] **VDA-TERM-02**: Windows CMD and cross-platform shell support
- [ ] **VDA-FILE-01**: File read/write with path validation and safety checks
- [ ] **VDA-VOICE-01**: Push-to-talk microphone input capture
- [ ] **VDA-VOICE-02**: Speech-to-text (STT) processing
- [ ] **VDA-VOICE-03**: Multilingual text-to-speech (TTS) response
- [ ] **VDA-VOICE-04**: Voice activation indicator in PyQt6 UI
- [ ] **VDA-MEM-01**: Microsoft GraphRAG integration for local memory
- [ ] **VDA-MEM-02**: Short-term memory (session chat history in GraphRAG)
- [ ] **VDA-MEM-03**: Long-term memory (cross-session persistence in GraphRAG)
- [ ] **VDA-MEM-04**: Priority query — short-term first, fall back to long-term
- [ ] **VDA-MEM-05**: Daily user behavior caching for faster execution
- [ ] **VDA-MEM-06**: Mistake memory — store failures, retrieve to improve decisions
- [ ] **VDA-GUI-01**: Modern PyQt6 UI redesign (inspired by DESIGN.md principles, market-leading agents)
- [ ] **VDA-GUI-02**: DESIGN.md file for VDA's design system tokens
- [ ] **VDA-DRIFT-01**: Codebase refactoring — consolidate 8 clickers into one engine
- [ ] **VDA-DRIFT-02**: Codebase refactoring — split 1988-line floating_assistant.py
- [ ] **VDA-DRIFT-03**: Codebase refactoring — deduplicate APIClient/ZenClient
- [ ] **VDA-SEC-01**: Shell command approval dialog before execution
- [ ] **VDA-SEC-02**: API key storage via OS keychain (keyring)
- [ ] **VDA-SEC-03**: Proper FAILSAFE restoration in automation
- [ ] **VDA-TEST-01**: Fix test suite (broken imports) and add tests for agent loop

### Out of Scope

- Full reinforcement learning training pipeline — deferred to v2 (memory-based learning first)
- Web interface / dashboard — desktop-only, keep PyQt6
- Mobile app — Windows desktop primary target
- Cloud deployment — fully local, no server
- Third-party MCP protocol support — use native Python tools instead

## Context

**Existing codebase** (`qwen-desktop/`): A fully functional PyQt6 desktop assistant with screen vision, mouse/keyboard automation, dual AI API clients, file tools, session management, basic memory, behavior tracking, and task decomposition. Major tech debt includes 8 competing clicker implementations (~3300 lines), a 1988-line god class (`floating_assistant.py`), duplicate API clients, and zero working tests.

**Research references:**
- **OpenCode architecture**: 6-agent system, 22+ tools, doom-loop detection, permission-based tool access, event bus, sub-agent delegation via `task` tool
- **Claude Computer Use**: Agent loop pattern (tool request → execute → return → repeat), fail-safe iteration limits
- **Antigravity (Google)**: Managed agent with sandboxed code execution, web search, file tools
- **DESIGN.md (Google Stitch)**: YAML tokens + markdown rationale for AI-readable design systems

**Python 3.9+**, PyQt6, httpx, opencv-python, pyautogui, pynput, Microsoft GraphRAG (planned).

## Constraints

- **Tech Stack**: Python 3.9+ only. Keep everything in Python — no TypeScript/Node.js
- **Compatibility**: Must work on Windows (primary). macOS/Linux secondary
- **UI**: Keep PyQt6 floating assistant — replace internal widgets, don't change framework
- **API Provider**: Already implemented — do not modify APIClient/ZenClient architecture
- **Vision + Automation**: Already implemented — clean API exists for click/type/vision
- **Memory**: Local-only. No cloud storage for memory data
- **Agent Model**: Same AI provider as configured in VDA settings (user chooses provider/model)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Antigravity-style agent loop | Most robust for desktop automation; plan→execute→verify→iterate catches failures | — Pending |
| Manager + sub-agents | OpenCode-style delegation; keeps context focused, each agent has specialized tools | — Pending |
| Python (same stack) | Existing codebase is Python; mixing languages adds complexity | ✓ Good |
| Microsoft GraphRAG | Robust open-source RAG over knowledge graphs; community standard | — Pending |
| Push-to-talk + local TTS | Simple activation model, no always-listening complexity | — Pending |
| Memory-based learning v1 | Pragmatic — store failures in GraphRAG, retrieve to avoid repeats; RL deferred | — Pending |
| DESIGN.md for UI tokens | Google Stitch format gives AI agents structured understanding of design decisions | — Pending |
| Keep PyQt6 floating assistant | Existing UI works; replace internals, keep the window/chrome | ✓ Good |

---

*Last updated: 2026-06-06 after initialization*
