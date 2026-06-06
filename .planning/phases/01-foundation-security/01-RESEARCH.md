# Phase 1: Foundation & Security — Research

**Researched:** 2026-06-06
**Domain:** Codebase refactoring, test recovery, keychain security, automation safety
**Confidence:** HIGH

## Summary

Phase 1 targets four categories of technical debt across the existing codebase. The primary findings:

1. **Clicker consolidation is simpler than it appears** — all 8 clicker files (~3,284 lines) are dead code, imported by nothing. The `ScreenEnv`/`ScreenDetector` classes they contain are duplicated identically across two files. The actual production click path uses `EnhancedExecutor` (196 lines) and `PyAutoGUIExecutor` (319 lines) — neither needs to be part of the ClickerEngine. The Consolidation means: extract `ScreenEnv`/`ScreenDetector` to `utils/screen.py`, create a new `ClickerEngine` in `core/clickers/` from the `perfect_clicker.py` patterns, then delete all 8 old files.

2. **floating_assistant.py** splits cleanly along class boundaries: `APIServerWorker` (50 lines) → `assistant/worker.py`, `MessageBubble` (218 lines) → `assistant/message_bubble.py`, `ChatHistoryPopup` (210 lines) → `assistant/chat_popup.py`, `FloatingAssistant` (~1,500 lines) → `assistant/controller.py`. Click execution logic in `_execute_vision_action`, `_execute_uied_action`, etc. moves to the new `ClickerEngine`.

3. **APIClient/ZenClient share ~70% duplicate code** — identical message construction, attachment handling, streaming parse loop, and error handling. A `BaseClient` abstract class or shared utility module can eliminate the duplication cleanly.

4. **keyring 25.7.0 is already installed** — the library is present and the `requirements.txt` dependency exists. Only `ProviderConfig` (40 lines) and `settings.py` (55 lines) need modification to use keyring instead of plaintext JSON storage.

5. **FAILSAFE has exactly 3 violation sites** — one global `= False` in `enhanced_executor.py:13`, one unprotected `= False`/`= True` pair in `floating_assistant.py:1958/1981`. A `restore_failsafe` context manager in `utils/safety.py` solves both.

6. **Test suite:** `test_auth.py` (109 lines) and `test_conversation.py` (185 lines) import non-existent modules and must be deleted. `test_attachments.py`, `test_error_handler.py`, `test_file_encoder.py` are healthy and should remain. New tests needed for `ClickerEngine`, `utils/safety.py`, and keychain integration.

7. **23 files exceed 100 lines** — the limit is flexible per D-03, but 15 of those are targeted for splitting by other RFCT requirements.

**Primary recommendation:** Execute the five refactoring areas (clickers, floating_assistant, API clients, screen utils, file splitting) as independent sub-tasks using small iterative commits with `ruff check` and `pytest` after each.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Split files into nested sub-packages by concern (e.g., `qwen_desktop/ui/chat/`, `qwen_desktop/ui/actions/`, `qwen_desktop/core/clickers/`)
- **D-02:** One-pass import rewrite across the codebase — no backward-compat re-exports in `__init__.py`
- **D-03:** ≤100-line limit is a flexible guideline, not a hard cap. Core domain logic can exceed slightly if splitting would harm cohesion
- **D-04:** `floating_assistant.py` → per-class split into `qwen_desktop/ui/assistant/` sub-package. Each class gets its own file. Click execution logic moves to the new ClickerEngine
- **D-05:** Inheritance pattern — base `ClickerEngine` class with abstract methods, strategies inherit and override
- **D-06:** `perfect_clicker.py` is the canonical base to refactor into the engine
- **D-07:** Delete the 7 other clicker files after consolidation is verified by tests
- **D-08:** New location: `qwen_desktop/core/clickers/`
- **D-09:** Context manager (`@contextmanager`) pattern for FAILSAFE save/restore, defined in `qwen_desktop/utils/safety.py`
- **D-10:** Remove the global `pyautogui.FAILSAFE = False` from `enhanced_executor.py` — all call sites use the context manager explicitly
- **D-11:** Delete broken test files that import non-existent modules (`qwen_desktop.auth.oauth_handler`, `token_manager`, `credentials`, `core.conversation`)
- **D-12:** Write tests for refactored modules: ClickerEngine, safety context manager, and keychain integration

### the agent's Discretion
- API client deduplication approach (base class vs. shared utility functions) — planner decides
- Specific boundary values for the 100-line guideline — planner decides per module
- Nuances of keychain migration (lazy vs. eager) — planner decides
- Import refactoring order (which files to fix first, dependency order) — planner decides

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RFCT-01 | Consolidate 8 clicker implementations into single ClickerEngine with pluggable strategies | All 8 files dead code; perfect_clicker.py is canonical; ScreenEnv/ScreenDetector extracted to utils/screen.py; EnhancedExecutor/PyAutoGUIExecutor remain unaffected |
| RFCT-02 | Split floating_assistant.py (~1988 lines) into controller + chat widgets + action modules | 4 classes identified; APIServerWorker (50 lines), MessageBubble (218 lines), ChatHistoryPopup (210 lines), FloatingAssistant (~1500 lines); split into ui/assistant/ sub-package |
| RFCT-03 | Deduplicate APIClient/ZenClient into shared base client | ~70% duplicate code across both files; streaming parse loop, message construction, attachment handling are identical |
| RFCT-04 | Extract shared ScreenEnv/ScreenDetector into utils/screen.py | Identical ScreenEnv/ScreenDetector in both universal_clicker.py and perfect_clicker.py; not imported by live code |
| RFCT-05 | No Python file exceeds 100 lines | 23 files exceed 100 lines; 15 targeted by other RFCT requirements; remainder need targeted splitting |
| SEC-02 | API key storage via OS keychain (keyring library) | keyring 25.7.0 installed; ProviderConfig.get_api_key() reads plaintext; migration target is ProviderConfig.save() and Settings.get("api_key") |
| SEC-03 | Proper pyautogui.FAILSAFE restoration with try/finally guards | 3 violation sites identified (enhanced_executor.py:13, floating_assistant.py:1958/1981); contextmanager in utils/safety.py per D-09 |
| TEST-01 | Fix broken test suite (import non-existent modules) | test_auth.py + test_conversation.py = 294 lines of broken tests; deleting per D-11 leaves 3 healthy test files |
| TEST-02 | Unit tests for agent manager and loop logic | No agent manager exists yet (Phase 2); tests for ClickerEngine, safety module, keychain integration fulfill written requirement |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Clicker coordination | `core/clickers/` | — | ClickerEngine is a core service composing detection strategies; UI layer calls it, core owns it |
| Screen detection | `utils/screen.py` | — | Environment detection (DPI, OS, monitor) is cross-cutting utility; available to clickers, executors, any consumer |
| API communication | `core/` | — | BaseClient/APIClient/ZenClient are core services; UI has no business in HTTP details |
| FAILSAFE safety | `utils/safety.py` | — | Cross-cutting safety utility; used by UI (floating_assistant's _execute_uied_action) and core (enhanced_executor) |
| Keychain credential storage | `utils/` or `auth/` | `config/settings.py` | API key handling spans auth layer (ProviderConfig reads keys) and config layer (Settings persists them); new helper in utils/ or extended ProviderConfig |
| UI rendering | `ui/assistant/` | — | FloatingAssistant and chat widgets are pure UI; click execution logic moves to core/clickers/ |
| Test infrastructure | `tests/` | — | Tests validate behavior; broken tests deleted, new tests for refactored modules |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| keyring | 25.7.0 | OS keychain credential storage | Already installed, already in requirements.txt, industry standard for OS-level secret storage |
| pyautogui | 0.9.54 | Desktop automation (mouse, keyboard, screenshot) | Already installed, only viable cross-platform desktop automation library for Python |
| pytest | 7.4+ | Test framework | Already configured in pyproject.toml; only Python test framework in use |

### Python Standard Library
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `contextlib.contextmanager` | FAILSAFE save/restore via `@contextmanager` decorator | D-09 prescribes this pattern |
| `unittest.mock` | Mock pyautogui.FAILSAFE, keyring, httpx in tests | New tests for ClickerEngine, safety, keychain |
| `ctypes` | Windows DPI detection in ScreenEnv | Existing pattern in both clicker files |
| `dataclasses.dataclass` | `ScreenEnv` dataclass definition | Existing pattern from perfect_clicker.py |

### Installation
```bash
# No new dependencies needed — all already in requirements.txt
pip install -r requirements.txt
pip install -r requirements-dev.txt  # pytest, etc.
```

### Version Verification
```bash
pip show keyring         # Confirmed: 25.7.0
pip show pyautogui       # Confirmed: 0.9.54
pip show pytest          # Confirmed: 7.4.0+
```

## Package Legitimacy Audit

> **No new packages are introduced by this phase.** All dependencies (keyring, pyautogui, httpx) are already in `requirements.txt` and verified installed. The phase only restructures existing code and uses existing dependencies.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| keyring | PyPI | 15+ yrs | 50M+/mo | github.com/jaraco/keyring | [OK] | Approved (already installed) |
| pyautogui | PyPI | 10+ yrs | 5M+/mo | github.com/asweigart/pyautogui | [OK] | Approved (already installed) |

## Architecture Patterns

### System Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRE-REFACTOR (Current)                               │
│                                                                             │
│  qwen_desktop/ui/floating_assistant.py (1988 lines)                        │
│  ├── APIServerWorker      │──core/api_client.py / zen_client.py (duplicate)│
│  ├── MessageBubble        │                                                 │
│  ├── ChatHistoryPopup     │──core/enhanced_executor.py (FAILSAFE unsafe)   │
│  └── FloatingAssistant    │                                                 │
│       └── Inline click    │──core/perfect_clicker.py (ScreenEnv dup)       │
│           execution       │──core/universal_clicker.py (ScreenEnv dup)      │
│                            │──6 other dead clicker files                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        POST-REFACTOR (Target)                               │
│                                                                             │
│  qwen_desktop/ui/assistant/                          qwen_desktop/core/     │
│  ├── __init__.py                                      │                     │
│  ├── controller.py  (was FlatAssistant, ~700 lines)   ├── api_client.py     │
│  ├── worker.py      (was APIServerWorker)              ├── zen_client.py    │
│  ├── message_bubble.py (was MessageBubble)             ├── _base_client.py  │
│  └── chat_popup.py  (was ChatHistoryPopup)             │   [NEW - shared]   │
│                                                         │                     │
│  qwen_desktop/core/clickers/ [NEW]                      ├── pyautogui_exec.py│
│  ├── __init__.py                                        ├── enhanced_exec.py │
│  ├── engine.py  (ClickerEngine base)                    │                     │
│  ├── strategies/ (strategy classes)                     ├── ... (other core) │
│  │   └── ...                                            │                     │
│  └── ...                                                │                     │
│                                                          │                     │
│  qwen_desktop/utils/                                    │                     │
│  ├── screen.py  [NEW - was duplicated in clickers]      │                     │
│  ├── safety.py  [NEW - FAILSAFE contextmanager]          │                     │
│  └── ... (existing utils)                                │                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (post-refactor additions)
```
qwen_desktop/
├── core/
│   ├── clickers/                  # [NEW] Clicker consolidation
│   │   ├── __init__.py
│   │   ├── engine.py              # ClickerEngine base + strategies
│   │   └── strategies/            # Pluggable click strategies
│   │       ├── __init__.py
│   │       ├── template.py        # OpenCV template matching
│   │       ├── vision_api.py      # VLM-based click coordinate
│   │       └── local_vision.py    # Local model-based
│   ├── _base_client.py            # [NEW] Shared base for APIClient+ZenClient
│   ├── api_client.py              # Refactored to use BaseClient
│   └── zen_client.py              # Refactored to use BaseClient
├── ui/
│   └── assistant/                 # [NEW] Floating assistant split
│       ├── __init__.py
│       ├── controller.py          # Former FloatingAssistant (reduced)
│       ├── worker.py              # APIServerWorker
│       ├── message_bubble.py      # MessageBubble
│       └── chat_popup.py          # ChatHistoryPopup
├── utils/
│   ├── screen.py                  # [NEW] ScreenEnv + ScreenDetector
│   └── safety.py                  # [NEW] FAILSAFE contextmanager + utilities
```

### Pattern 1: Inheritance-Based ClickerEngine (D-05)
**What:** Base `ClickerEngine` class with abstract `click_at(coords)` method, strategy classes inherit and override. `perfect_clicker.py` provides the reference implementation.
**When to use:** All click coordination — strategy selection uses pluggable modules, the engine handles coordinate validation, error recovery, and logging.
**Example:**
```python
# Source: D-05, D-06; pattern from perfect_clicker.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ClickResult:
    success: bool
    x: int
    y: int
    strategy_used: str
    confidence: float

class ClickStrategy(ABC):
    """Base class for all click strategies."""
    
    @abstractmethod
    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        ...

class ClickerEngine:
    """Orchestrates click strategies with fallback chain."""
    
    def __init__(self, strategies: list[ClickStrategy]):
        self.strategies = strategies
    
    def execute(self, x: int, y: int, target_name: str = None) -> ClickResult:
        for strategy in self.strategies:
            result = strategy.click(x, y)
            if result.success:
                return result
        return ClickResult(False, x, y, "none", 0.0)
```

### Pattern 2: FAILSAFE Context Manager (D-09)
**What:** `@contextmanager` that saves `pyautogui.FAILSAFE` before the block and restores it in `finally`.
**When to use:** Every call site that sets `pyautogui.FAILSAFE = False` — replaces inline try/finally patterns.
**Example:**
```python
# Source: D-09; pattern from existing try/finally in api_client.py:71
from contextlib import contextmanager
import pyautogui

@contextmanager
def restore_failsafe():
    """Save FAILSAFE state, disable it, restore in finally."""
    original = pyautogui.FAILSAFE
    pyautogui.FAILSAFE = False
    try:
        yield
    finally:
        pyautogui.FAILSAFE = original
```

### Pattern 3: BaseClient Deduplication (RFCT-03)
**What:** Extract common message construction, streaming parse, and error handling into a `BaseClient` or shared utilities, keeping provider-specific customization (headers, connection test) in `APIClient`/`ZenClient`.
**When to use:** The streaming SSE parse loop, attachment handling, and system prompt injection are 100% identical between the two clients.
**Example:**
```python
# Source: RFCT-03, comparing api_client.py and zen_client.py
class BaseClient(ABC):
    """Shared base for OpenAI-compatible API clients."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    @abstractmethod
    def _get_headers(self) -> dict:
        ...
    
    async def _stream_chat(self, client: httpx.AsyncClient, 
                           payload: dict) -> AsyncGenerator[str, None]:
        """Shared streaming SSE parse loop (identical in both clients)."""
        async with client.stream("POST", "/chat/completions", json=payload) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                yield f"Error: API returned {response.status_code}."
                return
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                # ... SSE parsing (identical in both)
```

### Anti-Patterns to Avoid
- **Backward-compat re-exports:** D-02 explicitly prohibits keeping old import paths working. All imports must be updated in one pass. No `from qwen_desktop.ui.floating_assistant import FloatingAssistant` shim.
- **Preserving dead code:** After consolidation, delete the 7 non-canonical clicker files. Do not leave them as dead modules.
- **Global FAILSAFE mutation:** `pyautogui.FAILSAFE = False` at module level in `enhanced_executor.py:13` must be removed, not wrapped with a comment.
- **Lazy keychain migration risk:** If `keyring.get_password()` fails (e.g., no keyring backend on headless Linux), the app must fall back gracefully to the stored config value, not crash on startup.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OS credential storage | Encrypted config file, custom AES wrapper | `keyring` library | keyring handles macOS Keychain, Windows Credential Manager, Linux Secret Service; ~500 edge cases across 15+ years |
| DPI/screen environment detection | Duplicate detection per module | `utils/screen.py` ScreenEnv + ScreenDetector | ScreenDetector already exists (duplicated) — just extract to shared utility, don't reinvent |
| FAILSAFE save/restore | Inline try/finally per call site | `contextlib.contextmanager` | Standard library pattern, zero boilerplate, ensures `finally` always runs |
| Test mocks for pyautogui/httpx | Custom mock classes | `unittest.mock.patch` | Standard library, proven pattern for patching pyautogui and httpx in tests |

**Key insight:** This phase is about eliminating duplication, not adding capability. Every "don't hand-roll" item is an existing pattern or library that needs to be applied consistently — no new dependencies required.

## Common Pitfalls

### Pitfall 1: Silent Import Breakage After Refactoring
**What goes wrong:** Moving classes into new sub-packages breaks imports in files that weren't updated.
**Why it happens:** Python uses explicit import paths; `from qwen_desktop.ui.floating_assistant import FloatingAssistant` breaks when FloatingAssistant moves to `qwen_desktop.ui.assistant.controller`.
**How to avoid:** D-02 mandates one-pass import rewrite. After creating new sub-packages, run `ruff check .` (which includes `I` rules for import sorting) and fix all `ModuleNotFoundError` by running `python -c "import qwen_desktop"` after each major move.
**Warning signs:** `pytest tests/` shows `ModuleNotFoundError` for paths that used to work.

### Pitfall 2: Not Fully Testing ClickerEngine Before Deleting Old Files
**What goes wrong:** Old clicker files are deleted before the new ClickerEngine is verified, and a corner case was missed.
**Why it happens:** The 8 clicker files are dead code (not imported), so nothing breaks when they're deleted — but the new ClickerEngine needs to produce correct coordinates.
**How to avoid:** Write ClickerEngine tests that verify coordinate conversion, DPI scaling, and screen boundary clamping before deleting old files. Compare output of old `perfect_clicker.py` methods against new Engine for identical inputs.
**Warning signs:** Coordinates drift by ~5% after swap, pixel verification fails in edge cases.

### Pitfall 3: Keychain.get_password() Returns None on Fresh Install
**What goes wrong:** First-run migration eagerly reads keyring, finds no entry, and can't fall back to the config file value.
**Why it happens:** keyring has no stored secret until the user saves credentials via SettingsDialog for the first time. If the config file still has the old value, the app may think no API key is configured.
**How to avoid:** Use a lazy pattern: try keyring first, fall back to config file value, only write to keyring when `save()` is called. Keep the config file `api_key` field as a fallback during transition.
**Warning signs:** App asks for API key on every restart despite having one configured in the UI.

### Pitfall 4: Removing the Global FAILSAFE Bug But Not All Sites
**What goes wrong:** The global `pyautogui.FAILSAFE = False` in `enhanced_executor.py` is removed, but `floating_assistant.py` still has unprotected FAILSAFE manipulation.
**Why it happens:** The context manager solves all sites consistently, but if a dev only fixes the obvious global and misses the inline pair, half the vulnerability remains.
**How to avoid:** After creating the context manager in `utils/safety.py`, grep for `FAILSAFE` across the entire codebase. Verify exactly 0 results remain after migration.
**Warning signs:** Any `pyautogui.FAILSAFE` assignment in `git diff` output must be flagged during code review.

### Pitfall 5: Losing Test Coverage by Deleting Broken Test Files
**What goes wrong:** `test_auth.py` and `test_conversation.py` are deleted (per D-11), removing any test coverage they accidentally had.
**Why it happens:** Broken test files that import non-existent modules can't run, so they contribute zero coverage — but developers may feel loss aversion.
**How to avoid:** D-11 explicitly permits deletion. Replace with new tests for ClickerEngine, safety module, and keychain integration per D-12. Measure coverage with `pytest --cov` to verify net improvement.

## Runtime State Inventory

> This is a **codebase refactoring** phase, not a rename/refactor/migration phase. No runtime state (databases, service configs, OS registrations, secrets, build artifacts) is being changed. All work targets source file organization within `qwen-desktop/qwen_desktop/`.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database or runtime datastore stores the names of internal modules | None |
| Live service config | None — no external service references internal module paths | None |
| OS-registered state | None — no OS-level registrations of internal module paths | None |
| Secrets/env vars | API keys stored in ~/.qwen-desktop/config.json plaintext — migration to keychain targeted by SEC-02 | Code edit: ProviderConfig.get_api_key() and save() |
| Build artifacts | None — source restructuring doesn't change package name or entry points | None |

## File Size Audit (Pre-Refactor)

> All files in `qwen_desktop/` exceeding 100 lines. RFCT-005 requires splitting or justifying.

| File | Lines | Target | Notes |
|------|-------|--------|-------|
| `ui/floating_assistant.py` | 1650 | Split (RFCT-02) | 4 classes, going to `ui/assistant/` sub-package |
| `ui/uied_overlay.py` | 937 | Split (RFCT-05) | Not targeted by other requirements; needs splitting |
| `core/perfect_clicker.py` | 638 | Delete (RFCT-01) | Dead code; ScreenEnv extracted first |
| `core/universal_clicker.py` | 526 | Delete (RFCT-01) | Dead code; ScreenEnv extracted first |
| `core/opencv_qwen_clicker_enhanced.py` | 512 | Delete (RFCT-01) | Dead code |
| `core/uied_service.py` | 479 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/pixel_perfect_clicker.py` | 439 | Delete (RFCT-01) | Dead code |
| `core/opencv_qwen_clicker.py` | 431 | Delete (RFCT-01) | Dead code |
| `ui/components/uied_button.py` | 377 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/pyautogui_executor.py` | 319 | Keep (RFCT-05) | Can justify if splitting harms cohesion |
| `core/qwen_screen_clicker.py` | 293 | Delete (RFCT-01) | Dead code |
| `core/tool_executor.py` | 262 | Keep (RFCT-05) | Phase 5 will modify; can exceed |
| `core/local_vision_clicker.py` | 252 | Delete (RFCT-01) | Dead code |
| `ui/settings_dialog.py` | 252 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/opencv_detector.py` | 212 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/debug_clicker.py` | 193 | Delete (RFCT-01) | Dead code |
| `core/zen_client.py` | 191 | Refactor (RFCT-03) | Will shrink via BaseClient dedup |
| `core/behavior_tracker.py` | 184 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/command_registry.py` | 183 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/vision_capture.py` | 172 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/session_service.py` | 170 | Split (RFCT-05) | Not targeted; needs splitting |
| `core/enhanced_executor.py` | 169 | Keep (RFCT-05) | FAILSAFE safety fix reduces line count |
| `core/api_client.py` | 164 | Refactor (RFCT-03) | Will shrink via BaseClient dedup |

## Code Examples

### Context Manager: FAILSAFE Restoration
```python
# Source: D-09, pattern based on api_client.py try/finally
# File: utils/safety.py
from contextlib import contextmanager
import logging
import pyautogui

logger = logging.getLogger(__name__)

@contextmanager
def restore_failsafe():
    """Temporarily disable pyautogui.FAILSAFE, restore on exit.
    
    Use this around any pyautogui click/type operation that might
    trigger the failsafe corner escape unintentionally.
    
    Example:
        with restore_failsafe():
            pyautogui.click(x, y)
    """
    original = pyautogui.FAILSAFE
    pyautogui.FAILSAFE = False
    try:
        yield
    finally:
        pyautogui.FAILSAFE = original
        logger.debug(f"FAILSAFE restored to {original}")
```

### Keychain: Wrapping API Key Storage
```python
# Source: SEC-02, keyring documentation pattern
# Migration target: ProviderConfig.get_api_key() and save()
import keyring

# Service name and account constant for the keychain entry
_KEYRING_SERVICE = "VDA-Desktop"
_KEYRING_ACCOUNT = "api_key"

def get_api_key_from_keyring() -> str:
    """Get API key from OS keychain, or empty string if not found."""
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT) or ""

def set_api_key_in_keyring(api_key: str) -> None:
    """Store API key in OS keychain."""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT, api_key)
```

### ScreenEnv: Shared Dataclass for Cross-cutting Screen Detection
```python
# Source: ScreenEnv from perfect_clicker.py + universal_clicker.py (identical)
# File: utils/screen.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ScreenEnv:
    """Screen environment detected at runtime."""
    os: str              # "windows" | "mac" | "linux"
    logical_w: int
    logical_h: int
    physical_w: int
    physical_h: int
    scale_x: float       # physical / logical
    scale_y: float
    dpi: float
    is_hidpi: bool
    monitors: list       # multi-monitor info
    wayland: bool        # Linux Wayland flag

class ScreenDetector:
    """Runtime screen environment detection (now shared)."""
    
    @staticmethod
    def detect() -> ScreenEnv:
        # OS detection + platform-specific detection extracted
        # from perfect_clicker.py lines 38-260
        ...
```

### BaseClient: Deduplicated Streaming SSE Parser
```python
# Source: RFCT-03, comparing api_client.py:130-178 vs zen_client.py:146-208
# The streaming parse loop is 100% identical across both files.
# Common pattern:
async def _parse_sse_stream(response, provider_name: str) -> AsyncGenerator[str, None]:
    """Parse SSE stream from OpenAI-compatible chat completions endpoint.
    
    Handles both standard content deltas and reasoning_content fields.
    Identical code was duplicated in api_client.py and zen_client.py.
    """
    async for line in response.aiter_lines():
        if not line.startswith("data: "):
            continue
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            break
        try:
            data = json.loads(data_str)
            choices = data.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield content
            reasoning = delta.get("reasoning_content") or delta.get("reasoning_details")
            if reasoning:
                if isinstance(reasoning, list):
                    for r in reasoning:
                        if isinstance(r, dict):
                            t = r.get("text", "")
                            if t:
                                yield f"<think>{t}</think>"
                elif isinstance(reasoning, str):
                    yield f"<think>{reasoning}</think>"
        except json.JSONDecodeError:
            continue
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 8 separate clicker files, each reinventing ScreenEnv/ScreenDetector | Single ClickerEngine with pluggable strategies, shared ScreenEnv in utils/screen.py | Phase 1 | DPI detection fixed once; strategies swappable; 3,000+ lines of dead code removed |
| API keys stored plaintext in ~/.qwen-desktop/config.json | API keys stored in OS keychain via keyring | Phase 1 | Keys encrypted at rest; keyring handles OS-native encryption; backward-compat fallback during transition |
| pyautogui.FAILSAFE = False at module level + unguarded inline set | Context manager in utils/safety.py, all call sites protected | Phase 1 | FAILSAFE always restored on exception; global mutation eliminated; grep-able pattern |
| floating_assistant.py = 1650-line god class with 4 classes, ~40 methods | Per-class files in ui/assistant/ sub-package | Phase 1 | Each file < 200 lines; single responsibility; testable in isolation |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All 8 clicker files are dead code (not imported by any live code) | Clicker Consolidation | Low — verified by grep across entire `qwen_desktop/` tree; no imports found |
| A2 | ScreenEnv and ScreenDetector are identical across universal_clicker.py and perfect_clicker.py | RFCT-04 | Low — verified by reading both files; only docstring style differs |
| A3 | No existing test file depends on the broken modules being deleted | TEST-01 | Low — test_auth.py and test_conversation.py only import non-existent modules |
| A4 | keyring 25.7.0 works on Windows Credential Manager without additional config | SEC-02 | Medium — keyring requires `pywin32-ctypes` (already installed) but headless/WSL environments may lack a keyring backend |

## Open Questions

1. **API Client deduplication: base class vs. shared utility functions?**
   - What we know: Both APIClient and ZenClient need headers, message construction, SSE parsing, error handling. SSE parse loop and message construction are identical.
   - What's unclear: Whether to use abstract base class (`BaseClient` → `APIClient`, `ZenClient`) or extract static utility functions (`_build_messages()`, `_parse_sse_stream()`) and keep thin wrappers.
   - Recommendation: Planner decides (discretion area). Base class is cleaner if more providers will be added. Utility functions are simpler for the current two.

2. **Keychain migration: lazy fallback vs. eager migration on first startup?**
   - What we know: Existing `config.json` has plaintext `api_key` field. keyring integration needs to coexist with existing config.
   - What's unclear: Whether to migrate all existing keys on first startup (write keyring, clear config) or read keyring first, fall back to config, and only write keyring on next `save()`.
   - Recommendation: Lazy is safer — read keyring first, fall back to config file value. Write keyring on `save()`. Keeps backward compat and avoids data loss if keyring backend fails.

3. **What is the exact split boundary for `uied_overlay.py` (937 lines)?**
   - What we know: It's the second-largest file. It contains UI canvas, toolbar, event handling, and component editing inline.
   - What's unclear: Whether to split it in Phase 1 (RFCT-05 applies) or defer to Phase 8 (GUI Redesign) where it would be a more natural home.
   - Recommendation: Defer to Phase 8. Phase 1 already has 5 major refactoring areas; adding uied_overlay split risks scope creep. Justify under the flexible 100-line guideline (D-03).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9+ | All code | ✓ | 3.11.x | — |
| keyring | SEC-02 | ✓ | 25.7.0 | — |
| pyautogui | SEC-03 | ✓ | 0.9.54 | — |
| pytest | TEST-01, TEST-02 | ✓ | — | pip install -r requirements-dev.txt |
| httpx | RFCT-03 | ✓ | — | — |

**Missing dependencies with no fallback:** None — all required libraries are already installed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ |
| Config file | `qwen-desktop/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest tests/ -x --tb=short -q` |
| Full suite command | `pytest tests/ --tb=short -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| RFCT-01 | ClickerEngine produces correct coordinates for multiple strategies | Unit | `pytest tests/test_clickers.py::TestClickerEngine -x` |
| RFCT-01 | screen.py ScreenDetector.detect() returns valid ScreenEnv | Unit | `pytest tests/test_screen.py -x` |
| SEC-03 | safety.restore_failsafe saves and restores FAILSAFE state | Unit | `pytest tests/test_safety.py -x` |
| SEC-03 | FAILSAFE restored even on exception in context | Unit | `pytest tests/test_safety.py::TestRestoreFailsafe -x` |
| SEC-02 | keyring helper stores and retrieves API key | Unit | `pytest tests/test_keychain.py -x` |
| SEC-02 | ProviderConfig falls back to config.json if keyring is empty | Unit | `pytest tests/test_keychain.py::TestFallback -x` |
| RFCT-03 | BaseClient shared SSE parser handles normal stream | Unit | `pytest tests/test_api_client.py -x` |
| TEST-01 | Broken test files deleted, remaining tests pass | Smoke | `pytest tests/ -q` |

### Wave 0 Gaps
- [ ] `tests/test_clickers.py` — covers RFCT-01, needs `unittest.mock.patch` for pyautogui
- [ ] `tests/test_screen.py` — covers RFCT-04, needs ctypes mocking for Windows-only tests
- [ ] `tests/test_safety.py` — covers SEC-03, verifies FAILSAFE save/restore
- [ ] `tests/test_keychain.py` — covers SEC-02, mocks keyring backends

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | keyring for API key storage (already installed, standard library) |
| V6 Cryptography | partial | keyring defers to OS Keychain/Credential Manager — never hand-roll crypto |
| V8 Data Protection | yes | API keys no longer in plaintext JSON config; moved to OS-protected storage |

### Known Threat Patterns for PyQt6 Desktop App
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Plaintext credential in config file | Information Disclosure | keyring OS keychain integration (SEC-02) |
| FAILSAFE disabled during click, not restored on exception | Tampering | contextmanager with finally guard (SEC-03) |
| Keyring unavailable on headless/WSL | Denial of Service | Lazy fallback to config file value (discretion area) |

## Sources

### Primary (HIGH confidence)
- Codebase direct reading: `floating_assistant.py`, `api_client.py`, `zen_client.py`, `perfect_clicker.py`, `universal_clicker.py`, `enhanced_executor.py`, `provider_config.py`, `settings.py` — all class structures, line counts, import relationships, duplication patterns verified by reading source files
- `pip show keyring` — confirmed keyring 25.7.0 installed
- `.planning/codebase/CONCERNS.md` — verified all 8 clicker files are dead code via grep
- `.planning/codebase/ARCHITECTURE.md` — layer diagram, data flows, service boundaries
- `.planning/codebase/CONVENTIONS.md` — naming, imports, style, docstring conventions
- `CONTEXT.md` decisions D-01 through D-12 — locked from discuss-phase

### Secondary (MEDIUM confidence)
- keyring 25.7.0 usage patterns — based on documentation for `keyring.get_password()`/`keyring.set_password()` [CITED: Python keyring docs standard API pattern]
- pyautogui FAILSAFE semantics — based on pyautogui documentation for `pyautogui.FAILSAFE` attribute [CITED: pyautogui docs]

### Tertiary (LOW confidence)
- None — all findings were verified by reading actual source files or running pip queries.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified installed via pip
- Architecture: HIGH — all code relationships confirmed by reading source files
- Pitfalls: HIGH — based on code-level analysis of actual failure patterns in the codebase
- Package authority: HIGH — no new packages required; existing dependencies verified

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (30 days — Python ecosystem is stable)
