---
phase: 02-agent-core
plan: 01
subsystem: core, config, testing
tags: tool-registry, decorator, lazy-init, base-tool, agent-types, pytest
requires:
  - phase: 01-foundation-security
    provides: refactored codebase, test patterns, module conventions
provides:
  - ToolRegistry class with register/get_tool/get_definitions methods
  - BaseTool abstract class for all tool implementations
  - @register_tool decorator for declarative tool registration
  - 8 tool skeleton classes for Phases 3-6
  - AGENT_TYPES config dict with main/web/terminal/file/voice agent types
  - Extended DEFAULT_SETTINGS with agent loop configuration keys
  - 14 unit tests covering registration, lazy init, threading, filtering
affects: phase 02-agent-core (plans 02-02, 02-03, 02-04), phases 3-6 tool implementations

tech-stack:
  added: []
  patterns:
    - Decorator-based tool registration (@register_tool)
    - Double-checked locking for thread-safe lazy initialization
    - OpenAI-compatible tool definition generation
    - Agent type scope filtering for sub-agent tool sets

key-files:
  created:
    - qwen_desktop/core/tool_registry/__init__.py
    - qwen_desktop/core/tool_registry/base_tool.py
    - qwen_desktop/core/tool_registry/registry.py
    - qwen_desktop/core/tool_registry/tools/__init__.py
    - qwen_desktop/core/tool_registry/tools/web_search.py
    - qwen_desktop/core/tool_registry/tools/web_fetch.py
    - qwen_desktop/core/tool_registry/tools/terminal.py
    - qwen_desktop/core/tool_registry/tools/file_tools.py
    - qwen_desktop/core/tool_registry/tools/voice_tools.py
    - tests/test_tool_registry.py
  modified:
    - qwen_desktop/config/defaults.py

key-decisions:
  - "Single registry with agent type scope filtering (not per-agent registries) — matches research recommendation R1"
  - "Auto-import tools package from registry __init__.py so @register_tool decorators fire at import time"
  - "Thread-safe lazy init via double-checked locking with per-tool Lock objects"
  - "Config-backed agent type tool filtering via optional settings dict on ToolRegistry constructor"

patterns-established:
  - "Tool skeleton pattern: @register_tool decorator + BaseTool subclass with name/description/parameters class attributes"
  - "Lazy init pattern: register stores class reference, get_tool instantiates on first access with lock"
  - "Tool import pattern: tools/__init__.py imports all modules to trigger decorator registration"

requirements-completed: [AGNT-06]

duration: 12 min
completed: 2026-06-07
---

# Phase 2 Plan 1: ToolRegistry with lazy init, skeletons, and config extension

**Decorator-based ToolRegistry with thread-safe lazy initialization, 8 tool skeleton classes for Phases 3-6, AGENT_TYPES config, and 14 passing tests**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-07T00:01:00Z
- **Completed:** 2026-06-07T00:13:00Z
- **Tasks:** 3
- **Files modified:** 10 created, 1 modified

## Accomplishments

- ToolRegistry sub-package with BaseTool abstract class, registry singleton, and @register_tool decorator
- 8 tool skeletons registered (web_search, web_fetch, terminal, file_read, file_write, file_glob, file_grep, voice) returning "not implemented" errors for Phases 3-6
- Thread-safe lazy initialization with double-checked locking — tools instantiated only on first get_tool() call
- Agent type scope filtering via get_definitions(agent_type) — only tools allowed for that agent type are returned
- AGENT_TYPES dict in defaults.py with 5 agent type configurations (main, web, terminal, file, voice)
- Extended DEFAULT_SETTINGS with agent loop config keys (max_iterations, compaction_threshold, doom_loop_threshold, etc.)
- 14 unit tests all passing: registration, lazy init, definitions, agent-type filtering, thread safety, BaseTool contract, singleton, decorator

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ToolRegistry package with BaseTool + Registry + decorator** - `4c30099` (feat)
2. **Task 2: Create tool skeleton modules for Phases 3-6** - `4ed4efc` (feat)
3. **Task 3: Extend config/defaults.py with agent type configuration + write tests** - `165b8e8` (feat)

**Plan metadata:** (committed in final commit)

## Files Created/Modified

- `qwen_desktop/core/tool_registry/__init__.py` — Package barrel exports
- `qwen_desktop/core/tool_registry/base_tool.py` — BaseTool abstract class
- `qwen_desktop/core/tool_registry/registry.py` — ToolRegistry + decorator + singleton
- `qwen_desktop/core/tool_registry/tools/__init__.py` — Auto-imports all tool modules for registration
- `qwen_desktop/core/tool_registry/tools/web_search.py` — WebSearchTool skeleton
- `qwen_desktop/core/tool_registry/tools/web_fetch.py` — WebFetchTool skeleton
- `qwen_desktop/core/tool_registry/tools/terminal.py` — TerminalTool skeleton
- `qwen_desktop/core/tool_registry/tools/file_tools.py` — FileReadTool, FileWriteTool, FileGlobTool, FileGrepTool skeletons
- `qwen_desktop/core/tool_registry/tools/voice_tools.py` — VoiceTool skeleton
- `qwen_desktop/config/defaults.py` — Extended with AGENT_TYPES dict + new DEFAULT_SETTINGS keys
- `tests/test_tool_registry.py` — 14 comprehensive tests

## Decisions Made

- **Single registry with scope filtering** (not per-agent registries): ToolRegistry accepts optional `settings` dict for config-backed agent type tool filtering. `get_definitions(agent_type="web")` returns only web-scoped tools. Simpler than maintaining duplicate registries.
- **Auto-import at package init**: tools/`__init__.py` imports all tool modules so that `@register_tool` decorators fire automatically when the tool_registry package is imported.
- **Direct sub-module imports in tools**: Tool skeletons import `BaseTool` and `register_tool` from their specific sub-modules (`base_tool.py`, `registry.py`) rather than from the barrel, avoiding circular import issues during package initialization.
- **Config-backed filtering**: ToolRegistry constructor accepts optional `settings` dict. Agent type tool lists are read from `settings["agent_types"][agent_type]["tools"]`, matching the structure of the new `AGENT_TYPES` constant in `defaults.py`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Circular import on tool auto-registration**: Initial attempt to import tools from the parent `__init__.py` using barrel imports (`from qwen_desktop.core.tool_registry import BaseTool`) caused circular import during package init. Fixed by using direct sub-module imports in tool skeletons and relative imports (`from . import tools`) in the parent `__init__.py`.
- **Thread safety test barrier bug**: Test used two separate `threading.Barrier` objects per thread instead of one shared barrier, causing deadlock. Fixed by using a single `Barrier(2)` that both threads wait on.
- **Test mock tool names**: Initial test used `_MockTool` with `name = "mock_tool"` registered under different registry keys, causing definition output to use `cls.name` (mock_tool) instead of the expected registry key. Fixed by creating separate tool classes with matching names for each test scenario.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ToolRegistry foundation complete, ready for AgentManager integration (02-02)
- Tool skeletons ready for full implementation in Phases 3-6
- Agent type config ready for permission system integration
- 14 tests pass, providing regression protection for future tool work

## Self-Check: PASSED

- [x] All 11 created files exist on disk
- [x] 4 commits exist (3 task commits + 1 metadata commit)
- [x] 14 tests pass
- [x] ToolRegistry.registered_count == 8
- [x] AGENT_TYPES keys match expected: main, web, terminal, file, voice
- [x] Lazy init confirmed: no tools initialized before first get_tool()
- [x] Thread safety test passes with double-checked locking
- [x] Agent type scope filtering works correctly

---

*Phase: 02-agent-core*
*Completed: 2026-06-07*
