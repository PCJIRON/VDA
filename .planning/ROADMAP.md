# VDA Roadmap — Voice-Driven Desktop Agent

**Generated:** 2026-06-06
**Mode:** mvp
**Granularity:** fine
**Total phases:** 8
**Total v1 requirements:** 48

## Core Value

VDA must reliably turn a user's spoken or typed command into correct desktop actions — clicking the right things, typing the right text, running the right commands — without destroying user data or getting stuck in loops.

## Phases

- [ ] **Phase 1: Foundation & Security** - Refactor codebase tech debt, fix tests, secure API key storage and FAILSAFE
- [ ] **Phase 2: Agent Core** - Agent manager with Antigravity loop, doom detection, sub-agent delegation, permission system, tool registry, session compaction
- [ ] **Phase 3: Web Tools** - Web search, page fetch, crawling with rate limiting
- [ ] **Phase 4: Terminal Tools** - PowerShell, CMD, cross-platform shell execution with approval dialog
- [ ] **Phase 5: File Tools** - File read/write, glob search, grep with path safety
- [ ] **Phase 6: Voice System** - Push-to-talk STT, multilingual TTS, voice UI indicators
- [ ] **Phase 7: GraphRAG Memory** - Local GraphRAG engine, short-term/long-term memory, behavior cache, mistake learning
- [ ] **Phase 8: GUI Redesign** - DESIGN.md tokens, modern UI, dark/light themes, tool execution visualization

## Phase Details

### Phase 1: Foundation & Security
**Mode:** mvp
**Goal:** Codebase is refactored into maintainable modules, tests pass, and security basics (keychain storage, FAILSAFE) are in place
**Depends on:** Nothing (brownfield — existing codebase)
**Requirements:** RFCT-01, RFCT-02, RFCT-03, RFCT-04, RFCT-05, SEC-02, SEC-03, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Eight clicker implementations consolidated into a single `ClickerEngine` with pluggable strategies — existing tests still pass
  2. `floating_assistant.py` (~1988 lines) split into controller module, chat widgets module, and action modules — no functionality lost
   3. `APIClient` and `ZenClient` share a common base client with zero duplicated request/response logic
   4. Every Python file in `qwen_desktop/` is ≤100 lines — files exceeding the limit are split into focused sub-modules with single responsibility
   5. API keys are stored in OS keychain via `keyring` library instead of plaintext JSON config file
   6. `pyautogui.FAILSAFE` is properly restored with `try/finally` guards in all automation code paths
   7. Test suite runs without import errors (previously broken imports fixed), and agent loop unit tests pass
**Plans:** 4 plans across 3 waves

```
Plans:
- [ ] 01-01-PLAN.md — Foundation: Screen utils + Safety + Test fix (Wave 1)
- [ ] 01-02-PLAN.md — API Client Deduplication (Wave 1)
- [ ] 01-03-PLAN.md — ClickerEngine + Keychain Integration (Wave 2)
- [ ] 01-04-PLAN.md — Floating Assistant Split + New Tests (Wave 3)
```

### Phase 2: Agent Core
**Mode:** mvp
**Goal:** Agent manager can plan, execute, verify, iterate autonomously on complex tasks, delegate to sub-agents, detect doom loops, and manage conversation context
**Depends on:** Phase 1 (refactored codebase)
**Requirements:** AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05, AGNT-06, GUI-06
**Success Criteria** (what must be TRUE):
  1. User issues a multi-step command ("find the Q3 report, update the chart, and email it") → agent creates spec → plans steps → executes each step → verifies result → iterates until done or max iterations hit
  2. Agent detects 3+ identical consecutive tool calls, immediately pauses execution, and notifies user via chat message
  3. Agent manager can spawn Web, Terminal, File, and Voice sub-agents, each with tools scoped to their domain; sub-agents execute autonomously and return results
  4. Agent asks for user permission before executing tools flagged as sensitive (configurable per agent type via permission system)
  5. Long conversations are automatically compacted (truncated/summarized) to avoid AI context window overflow
  6. Tools are loaded lazily — only initialized when first used in a session, keeping startup fast
  7. User can see agent's reasoning steps (plan → current step → verification result) in a dedicated UI section during task execution
**Plans:** TBD
**UI hint:** yes

### Phase 3: Web Tools
**Mode:** mvp
**Goal:** Agent can search the web, fetch page content, and crawl multi-page data with polite rate limiting
**Depends on:** Phase 2 (agent loop uses tools)
**Requirements:** WEB-01, WEB-02, WEB-03, WEB-04
**Success Criteria** (what must be TRUE):
  1. User asks "search the web for X" → agent returns structured results with title, URL, and snippet from configured search API (Google/Bing/DuckDuckGo)
  2. User asks "get content from URL" → agent fetches page and returns clean markdown-formatted content (stripped of ads/nav)
  3. User asks "collect data from these 5 pages" → agent scrolls and crawls multiple pages, returning combined content
  4. Agent respects configurable rate limits and polite delays between consecutive web requests
**Plans:** TBD

### Phase 4: Terminal Tools
**Mode:** mvp
**Goal:** Agent can execute shell commands in PowerShell, CMD, and cross-platform shells with working directory tracking and approval safety
**Depends on:** Phase 2 (agent loop uses tools)
**Requirements:** TERM-01, TERM-02, TERM-03, TERM-04, SEC-01
**Success Criteria** (what must be TRUE):
  1. User asks "run PowerShell command X" → agent executes and returns stdout and stderr output
  2. User asks "run cmd command X" → agent executes via Windows CMD and returns output
  3. Agent auto-detects platform and uses correct default shell (PowerShell on Windows, bash on Linux/macOS)
  4. Agent tracks working directory across consecutive shell commands (e.g., `cd dir` followed by `ls` works correctly)
  5. Every shell command execution triggers a modal PyQt6 approval dialog showing the exact command; user approves or denies before execution
**Plans:** TBD
**UI hint:** yes

### Phase 5: File Tools
**Mode:** mvp
**Goal:** Agent can read, write, search, and glob files with path validation, safety checks, and complete test coverage
**Depends on:** Phase 2 (agent loop uses tools)
**Requirements:** FILE-01, FILE-02, FILE-03, FILE-04, SEC-04, TEST-03
**Success Criteria** (what must be TRUE):
  1. User asks "read file X" → agent reads with automatic format detection (text, code, JSON, YAML, CSV) and displays content
  2. User asks "write to file X" → agent writes content with path validation (prevents writes outside allowed directories) and requests confirmation before overwriting existing files
  3. User asks "find files matching *pattern*" → agent returns matching file paths with metadata
  4. User asks "search for 'text' in project files" → agent greps and returns matches with file paths and line numbers
  5. Path traversal attacks are prevented — all file paths validated against a configurable whitelist before any read/write operation
  6. Unit tests pass for web tools, terminal tools, and file tools
**Plans:** TBD

### Phase 6: Voice System
**Mode:** mvp
**Goal:** User can speak commands via push-to-talk and hear agent's spoken responses with full UI integration
**Depends on:** Phase 2 (agent core for processing spoken commands)
**Requirements:** VOICE-01, VOICE-02, VOICE-03, VOICE-04, VOICE-05, GUI-05
**Success Criteria** (what must be TRUE):
  1. User presses configured keyboard shortcut → microphone activates and captures audio (push-to-talk, no always-listening)
  2. Recorded speech is transcribed to text via API or local STT model and submitted to agent for processing
  3. Agent's text response is converted to spoken audio in the user's configured language (multilingual TTS)
  4. Voice indicator in the floating assistant UI shows three states: idle (mic icon), recording (pulsing red), speaking (waveform)
  5. New voice command or chat message immediately interrupts any ongoing TTS playback
**Plans:** TBD
**UI hint:** yes

### Phase 7: GraphRAG Memory
**Mode:** mvp
**Goal:** Agent remembers conversations across sessions, retrieves past context, learns from daily usage patterns, and avoids repeating past mistakes
**Depends on:** Phase 2 (agent queries memory during execution)
**Requirements:** MEM-01, MEM-02, MEM-03, MEM-04, MEM-05, MEM-06, TEST-04
**Success Criteria** (what must be TRUE):
  1. Microsoft GraphRAG engine runs locally with file-based storage (no cloud dependency) — all memory operations use the local GraphRAG index
  2. Session chat history is automatically stored in GraphRAG short-term memory during the session and accessible within the same session
  3. When a session ends, short-term data is persisted to long-term memory; in a new session, user can ask "what did we discuss yesterday?" and agent retrieves relevant context
  4. Memory retrieval prioritizes short-term results first; if no match found, falls back to long-term query with relevance scoring
  5. Daily user behavior patterns (frequent click targets, common keyboard sequences) are cached and served as execution hints to speed up routine tasks
  6. Failed tool calls are stored in mistake memory with full context (what was attempted, why it failed, timestamp); agent retrieves relevant mistakes before executing similar actions and avoids repeating them
  7. Unit tests pass for GraphRAG memory integration
**Plans:** TBD

### Phase 8: GUI Redesign
**Mode:** mvp
**Goal:** VDA's interface is modern, themeable, and informative — with DESIGN.md tokens, dark/light themes, and real-time tool execution visualization
**Depends on:** Phase 2 (visualizes agent activity), Phase 6 (voice controls in UI)
**Requirements:** GUI-01, GUI-02, GUI-03, GUI-04
**Success Criteria** (what must be TRUE):
  1. `DESIGN.md` exists at project root with YAML design tokens (colors, typography, spacing, border-radius, shadow, animation curves) and markdown rationale for each token — AI-readable and human-understandable
  2. Floating assistant UI features modern design: clean rounded chat bubbles with sender avatars, smooth scroll animations, and freely resizable window that remembers size
  3. User can toggle between dark and light themes from a toolbar button; themes derive values from DESIGN.md token system
  4. Tool execution calls appear inline in chat with real-time status badges: pending (⏳), running (🔄), done (✅), error (❌), and expandable detail on click
**Plans:** TBD
**UI hint:** yes

---

## Phase Dependency Graph

```text
Phase 1 (Foundation)
    │
    ▼
Phase 2 (Agent Core) ──────────────────────────────────────────┐
    │            │            │            │                   │
    ▼            ▼            ▼            ▼                   ▼
Phase 3    Phase 4    Phase 5    Phase 6              Phase 8 (GUI)
(Web)      (Term)     (File)     (Voice)             (needs Phase 2+6)
    │            │            │            │
    └────────────┴────────────┴────────────┘
                      │
                      ▼
              Phase 7 (Memory)
              (uses all tools + agent)
```

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Security | 0/4 | Not started (planned) | - |
| 2. Agent Core | 0/0 | Not started | - |
| 3. Web Tools | 0/0 | Not started | - |
| 4. Terminal Tools | 0/0 | Not started | - |
| 5. File Tools | 0/0 | Not started | - |
| 6. Voice System | 0/0 | Not started | - |
| 7. GraphRAG Memory | 0/0 | Not started | - |
| 8. GUI Redesign | 0/0 | Not started | - |

---

*Roadmap generated: 2026-06-06*
