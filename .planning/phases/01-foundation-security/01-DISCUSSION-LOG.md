# Phase 1: Foundation & Security — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-06
**Phase:** 1 - Foundation & Security
**Areas discussed:** File structure after splitting, Clicker consolidation approach, FAILSAFE restoration pattern, Broken test recovery

---

## File structure after splitting

| Option | Description | Selected |
|--------|-------------|----------|
| Nested sub-packages (Recommended) | Each concern gets its own sub-package. Cleaner imports, easier navigation. | ✓ |
| Flat directory, more files | All files stay in the same package directory. Simpler, fewer directories. | |

**User's choice:** Nested sub-packages
**Notes:** User chose nested sub-packages for cleaner organization

| Option | Description | Selected |
|--------|-------------|----------|
| One-pass import rewrite (Recommended) | Update all imports across the codebase at once. | ✓ |
| Backward compat re-exports | Keep old paths via __init__.py re-exports, clean up later. | |

**User's choice:** One-pass import rewrite
**Notes:** User prefers clean break over backward compatibility

| Option | Description | Selected |
|--------|-------------|----------|
| Strict: hard 100-line cap | Any file >100 lines must split, no exceptions. | |
| Flexible: 100-line guideline (Recommended) | Core domain logic can exceed slightly if splitting harms readability. | ✓ |

**User's choice:** Flexible: 100-line guideline
**Notes:** Pragmatic approach — prioritizes module cohesion over strict rule

| Option | Description | Selected |
|--------|-------------|----------|
| Per-class split (Recommended) | Each class → own file in qwen_desktop/ui/assistant/ sub-package. | ✓ |
| Layer-based split | Separate files for API workers, chat widgets, actions, main controller. | |

**User's choice:** Per-class split
**Notes:** APIServerWorker, MessageBubble, ChatHistoryPopup, FloatingAssistant each get own file; click execution moves to ClickerEngine

---

## Clicker consolidation approach

| Option | Description | Selected |
|--------|-------------|----------|
| Inheritance (Recommended) | Base ClickerEngine class with abstract methods; strategies inherit. | ✓ |
| Strategy pattern (composition) | Single engine takes strategy via constructor; looser coupling. | |

**User's choice:** Inheritance
**Notes:** Clean polymorphism, shared init/cleanup in base class

| Option | Description | Selected |
|--------|-------------|----------|
| perfect_clicker.py (Recommended) | Most complete, best DPI handling, suggested keeper in CONCERNS.md | ✓ |
| New base from scratch | Create fresh ClickerEngine, copy patterns from existing ones. | |

**User's choice:** perfect_clicker.py
**Notes:** Use existing 638-line clicker as the canonical base

| Option | Description | Selected |
|--------|-------------|----------|
| Delete originals (Recommended) | Remove 7 other clickers after verification tests pass | ✓ |
| Deprecate in place | Keep with deprecation warnings for gradual migration | |

**User's choice:** Delete originals
**Notes:** Clean codebase, no dead code

| Option | Description | Selected |
|--------|-------------|----------|
| qwen_desktop/core/clickers/ (Recommended) | Dedicated sub-package with engine and strategy modules | ✓ |
| Single file in core/ | Simpler but likely exceeds 100 lines | |

**User's choice:** qwen_desktop/core/clickers/
**Notes:** Sub-package for clean separation

---

## FAILSAFE restoration pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Context manager (Recommended) | Reusable @contextmanager, save/restore FAILSAFE. Clean, exception-safe. | ✓ |
| try/finally at every site | Explicit, doesn't hide pattern, but easy to forget | |

**User's choice:** Context manager
**Notes:** Single point of change, exception-safe

| Option | Description | Selected |
|--------|-------------|----------|
| utils/safety.py (Recommended) | Dedicated utility module for safety helpers | ✓ |
| utils/screen.py | Alongside screen/detection utilities | |
| In ClickerEngine | Primarily used by clicker code | |

**User's choice:** utils/safety.py
**Notes:** Dedicated module for FAILSAFE, path validation, and other safety helpers

| Option | Description | Selected |
|--------|-------------|----------|
| Remove global set (Recommended) | No more global FAILSAFE=False; every operation uses context manager | ✓ |
| Keep + wrap call sites | Keep global but wrap in save/restore | |

**User's choice:** Remove global set
**Notes:** Cleaner, no side effects, no risk of leaked global state

---

## Broken test recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Delete broken tests (Recommended) | Remove test files importing non-existent modules | ✓ |
| Stub missing modules | Minimal implementations to make imports work | |
| Implement missing modules | Build auth handlers and conversation properly | |

**User's choice:** Delete broken tests
**Notes:** Old tests were for features that never shipped; write fresh tests for refactored code

| Option | Description | Selected |
|--------|-------------|----------|
| Refactored module tests (Recommended) | Tests for ClickerEngine, safety context manager, keychain | ✓ |
| Full coverage of changed files | Broader coverage including base API client and screen utils | |

**User's choice:** Refactored module tests
**Notes:** Focus on what was restructured — ClickerEngine, safety, keychain

---

## the agent's Discretion

- API client deduplication approach (base class vs. shared utilities)
- Specific boundary values for 100-line guideline per module
- Keychain migration strategy (lazy vs. eager)
- Import refactoring order (dependency order)

## Deferred Ideas

None
