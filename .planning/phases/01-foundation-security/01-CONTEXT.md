# Phase 1: Foundation & Security — Context

**Gathered:** 2026-06-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor existing codebase tech debt (consolidate 8 clickers into a single `ClickerEngine`, split `floating_assistant.py` god class, deduplicate `APIClient`/`ZenClient`, extract `ScreenEnv`/`ScreenDetector` into `utils/screen.py`, enforce ≤100 lines per file), fix broken test suite, secure API key storage via `keyring`, and fix `pyautogui.FAILSAFE` unsafe manipulation.

No new capabilities. No new features. Pure structural improvement and security hardening.
</domain>

<decisions>
## Implementation Decisions

### File Organization
- **D-01:** Split files into nested sub-packages by concern (e.g., `qwen_desktop/ui/chat/`, `qwen_desktop/ui/actions/`, `qwen_desktop/core/clickers/`)
- **D-02:** One-pass import rewrite across the codebase — no backward-compat re-exports in `__init__.py`
- **D-03:** ≤100-line limit is a flexible guideline, not a hard cap. Core domain logic can exceed slightly if splitting would harm cohesion
- **D-04:** `floating_assistant.py` → per-class split into `qwen_desktop/ui/assistant/` sub-package. Each class (APIServerWorker, MessageBubble, ChatHistoryPopup, FloatingAssistant) gets its own file. Click execution logic moves to the new ClickerEngine

### Clicker Consolidation
- **D-05:** Inheritance pattern — base `ClickerEngine` class with abstract methods, strategies inherit and override
- **D-06:** `perfect_clicker.py` is the canonical base to refactor into the engine
- **D-07:** Delete the 7 other clicker files after consolidation is verified by tests
- **D-08:** New location: `qwen_desktop/core/clickers/`

### FAILSAFE Safety
- **D-09:** Context manager (`@contextmanager`) pattern for FAILSAFE save/restore, defined in `qwen_desktop/utils/safety.py`
- **D-10:** Remove the global `pyautogui.FAILSAFE = False` from `enhanced_executor.py` — all call sites use the context manager explicitly

### Test Recovery
- **D-11:** Delete broken test files that import non-existent modules (`qwen_desktop.auth.oauth_handler`, `token_manager`, `credentials`, `core.conversation`)
- **D-12:** Write tests for refactored modules: ClickerEngine, safety context manager, and keychain integration

### the agent's Discretion
- API client deduplication approach (base class vs. shared utility functions) — planner decides
- Specific boundary values for the 100-line guideline — planner decides per module
- Nuances of keychain migration (lazy vs. eager) — planner decides
- Import refactoring order (which files to fix first, dependency order) — planner decides
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition
- `.planning/ROADMAP.md` §Phase 1 — Success criteria, requirement list, dependencies
- `.planning/REQUIREMENTS.md` — RFCT-01–RFCT-05, SEC-02, SEC-03, TEST-01, TEST-02

### Codebase Analysis
- `.planning/codebase/CONCERNS.md` — Detailed tech debt documentation (clicker duplication, god class, plaintext keys, broken tests, FAILSAFE bug)
- `.planning/codebase/ARCHITECTURE.md` — System architecture, layer diagram, data flows
- `.planning/codebase/CONVENTIONS.md` — Coding conventions to preserve during refactoring
- `.planning/codebase/STACK.md` — Technology stack, dependencies (keyring already listed)

### Design Decisions
- `.planning/STATE.md` — Active decisions, accumulated context
- `.planning/PROJECT.md` — Core value, constraints, key decisions
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `keyring>=24.0.0` already in `requirements.txt` — import and use, no new dependency needed
- `pyproject.toml` already has `black`, `ruff`, `mypy` config — run `ruff check .` after refactoring
- Existing `try/finally` pattern in `api_client.py:71` — reuse pattern for safety context manager
- `__init__.py` barrel exports pattern — replicate for new sub-packages

### Established Patterns
- Service classes initialized with `Settings` object, stateless methods
- `QThread`+`pyqtSignal` for async work without freezing GUI
- Full package-path imports (`from qwen_desktop.config.settings import Settings`)
- `snake_case` naming, `PascalCase` classes, module-level `logger = logging.getLogger(__name__)`
- Google-style docstrings on all public functions

### Integration Points
- `floating_assistant.py` imports ~15+ services directly — split points where each import connects
- `core/` directory is the clicker cluster — consolidate into `core/clickers/`
- `config/settings.py` stores API keys as plaintext — migration target for `keyring`
- `enhanced_executor.py` line 13 sets `FAILSAFE=False` globally — removal target
</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond decisions captured above — open to standard approaches for implementation details.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.
</deferred>

---

*Phase: 1-Foundation & Security*
*Context gathered: 2026-06-06*
