# State: VDA — Voice-Driven Desktop Agent

**Last Updated:** 2026-06-06
**Current Phase:** Phase 1 (Foundation & Security)
**Current Status:** Not started — awaiting roadmap approval

---

## Project Reference

| Field | Value |
|-------|-------|
| Core Value | Turn user commands into correct desktop actions without data loss or loops |
| Repository | VDA (Voice-Driven Desktop Agent) |
| Stack | Python 3.9+, PyQt6, httpx, opencv-python, pyautogui, pynput, Microsoft GraphRAG |
| Platform | Windows (primary), macOS/Linux secondary |
| Mode | mvp |
| Granularity | fine |

---

## Current Position

| Phase | Goal | Status |
|-------|------|--------|
| 1. Foundation & Security | Refactor codebase, fix tests, secure key storage and FAILSAFE | Not started |
| 2. Agent Core | Agent manager with loop, sub-agents, doom detection, permissions | Not started |
| 3. Web Tools | Web search, fetch, crawl | Not started |
| 4. Terminal Tools | PowerSHell, CMD, cross-platform shell with approval | Not started |
| 5. File Tools | File read/write, glob, grep with path safety | Not started |
| 6. Voice System | Push-to-talk STT, multilingual TTS, voice UI | Not started |
| 7. GraphRAG Memory | Local memory engine, short-term, long-term, mistake learning | Not started |
| 8. GUI Redesign | DESIGN.md, modern UI, themes, tool visualization | Not started |

```
Phase 1 [    ] 0% — Not started
```

---

## Performance Metrics

*No metrics tracked yet. First phase will establish baseline.*

---

## Accumulated Context

### Active Decisions

| ID | Decision | Status |
|----|----------|--------|
| D01 | Antigravity-style agent loop (plan → execute → verify → iterate) | Pending implementation |
| D02 | Manager + sub-agents architecture (OpenCode-style delegation) | Pending implementation |
| D03 | Python same stack (no TypeScript/Node.js) | ✓ Confirmed |
| D04 | Microsoft GraphRAG for local memory | Pending implementation |
| D05 | Push-to-talk + local TTS (no always-listening) | Pending implementation |
| D06 | Memory-based learning v1 (mistake storage + retrieval; RL deferred) | Pending implementation |
| D07 | DESIGN.md for AI-readable design tokens | Pending implementation |
| D08 | Keep PyQt6 floating assistant (replace internals) | ✓ Confirmed |

### TODOs

- [ ] ⬜ Phase 1: Create plans for Foundation & Security
- [ ] ⬜ Phase 2: Create plans for Agent Core
- [ ] ⬜ Phase 3: Create plans for Web Tools
- [ ] ⬜ Phase 4: Create plans for Terminal Tools
- [ ] ⬜ Phase 5: Create plans for File Tools
- [ ] ⬜ Phase 6: Create plans for Voice System
- [ ] ⬜ Phase 7: Create plans for GraphRAG Memory
- [ ] ⬜ Phase 8: Create plans for GUI Redesign

### Blockers

*None currently.*

---

## Session Continuity

| Session | Date | Phase Worked | Notes |
|---------|------|-------------|-------|
| Initial | 2026-06-06 | Roadmap creation | 8 phases defined from 47 v1 requirements |

---

## Key Files

| File | Purpose |
|------|---------|
| `.planning/ROADMAP.md` | Phase structure, success criteria, dependencies |
| `.planning/REQUIREMENTS.md` | All v1/v2 requirements with phase traceability |
| `.planning/PROJECT.md` | Core value, context, constraints, key decisions |
| `.planning/STATE.md` | (this file) — project state and session context |
| `.planning/config.json` | Configuration (mode, granularity, workflows) |
| `.planning/codebase/ARCHITECTURE.md` | Existing codebase architecture analysis |

---

*State last updated: 2026-06-06*
