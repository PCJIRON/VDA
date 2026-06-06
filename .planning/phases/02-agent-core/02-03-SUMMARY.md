---
phase: 02-agent-core
plan: 03
subsystem: agent_manager
tags: [sub-agent, delegation, session-compaction, context-management, supervisor-worker]

# Dependency graph
requires:
  - phase: 02-agent-core
    plan: 01
    provides: ToolRegistry with get_definitions(agent_type) for tool scoping
  - phase: 02-agent-core
    plan: 02
    provides: AgentManager state machine that consumes these services
provides:
  - SubAgentDelegator for spawning isolated sub-agents with scoped tool sets
  - SessionCompactor for automatic conversation compaction at token threshold
affects: [02-04 (AgentWorker + integration)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Full reasoning sub-agents (separate API call, own context window)
    - Structured SubAgentContext prevents context loss (research Pitfall 3)
    - One-time compaction guard prevents re-compaction loops
    - Structured summarization preserves critical details (research Pitfall 4)

key-files:
  created:
    - qwen-desktop/qwen_desktop/core/agent_manager/sub_agent_delegator.py
    - qwen-desktop/qwen_desktop/core/agent_manager/session_compactor.py
    - qwen-desktop/tests/test_sub_agent.py
    - qwen-desktop/tests/test_compactor.py
  modified:
    - qwen-desktop/qwen_desktop/core/agent_manager/__init__.py

key-decisions:
  - "Sub-agent delegation uses full reasoning model (separate API call per sub-agent) per CONTEXT.md discretion"
  - "Single registry with scope filtering — get_definitions(agent_type) returns only allowed tools"
  - "Auto-summarize at threshold (not truncate oldest or manual-only) per research recommendation"
  - "One-time per session compaction to avoid re-compaction loops"

requirements-completed: [AGNT-03, AGNT-05]

# Metrics
duration: 5 min
completed: 2026-06-07
---

# Phase 2 Plan 03: SubAgentDelegator + SessionCompactor Summary

**SubAgentDelegator for isolated sub-agents with scoped tool sets via ToolRegistry, and SessionCompactor for automatic conversation compaction at configurable token threshold**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-07T00:27:23Z
- **Completed:** 2026-06-07T00:32:22Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- SubAgentDelegator with hierarchical supervisor/worker pattern — spawns isolated sub-agents with scoped tool sets via `ToolRegistry.get_definitions(agent_type)`
- SubAgentContext dataclass carries (original_goal, preceding_work, subtask, constraints, agent_type) — prevents context loss per research Pitfall 3
- SubAgentResult dataclass returns structured output with success, output, tool_calls, error, token_usage
- Sub-agent prompt template includes goal, context, subtask, constraints, and tool definitions — tool calls execute within sub-agent's scope only
- SessionCompactor with estimate_tokens, needs_compaction, compact, and reset methods
- COMPACTION_PROMPT constant with structured fields for critical detail preservation (file paths, errors, decisions, pending items)
- One-time compaction guard prevents re-compaction loops; reset allows reuse across sessions
- compact() returns shortened message list with `[COMPACTED CONTEXT]` system message preserving last user message
- __init__.py exports SubAgentDelegator, SubAgentContext, SubAgentResult, and SessionCompactor

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SubAgentDelegator** — `fe9c14d` (feat)
2. **Task 2: Create SessionCompactor + update __init__.py** — `8dff7ff` (feat)
3. **Task 3: Write test files** — `32f0411` (test)

**Plan metadata:** (committed via docs commit after SUMMARY)

## Files Created/Modified

- `qwen-desktop/qwen_desktop/core/agent_manager/sub_agent_delegator.py` — SubAgentDelegator class, SubAgentContext and SubAgentResult dataclasses. Contains spawn_and_execute, _build_sub_agent_prompt, _execute_sub_agent_tool, get_available_agent_types. Created.
- `qwen-desktop/qwen_desktop/core/agent_manager/session_compactor.py` — SessionCompactor class with COMPACTION_PROMPT constant. Contains estimate_tokens, needs_compaction, compact, reset. Created.
- `qwen-desktop/qwen_desktop/core/agent_manager/__init__.py` — Updated exports to include SubAgentDelegator, SubAgentContext, SubAgentResult, SessionCompactor. Modified.
- `qwen-desktop/tests/test_sub_agent.py` — 15 tests: context dataclass, result dataclass, initialization, prompt building, agent type scoping, tool execution, error handling. Created.
- `qwen-desktop/tests/test_compactor.py` — 14 tests: token estimation, threshold trigger, one-time guard, message reduction, last message preservation, reset, prompt format. Created.

## Decisions Made

- **Full reasoning sub-agents**: Sub-agents get their own isolated API call with a separate context window (per CONTEXT.md discretion), not tool-group dispatching
- **Single registry with scope filtering**: The global ToolRegistry singleton provides `get_definitions(agent_type)` which returns only tools allowed for that agent type — avoids duplicate registries
- **Auto-summarize at threshold**: Compaction triggers automatically at configurable threshold (default 80%), not manual-only or truncation-based
- **One-time per session**: _compacted flag prevents re-compaction loops; reset() enables reuse across sessions
- **Structured summarization**: COMPACTION_PROMPT enforces structured output with specific fields for critical details (file paths, errors, decisions, pending)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed invalid field() usage on non-dataclass SubAgentDelegator**
- **Found during:** Task 3 (test execution)
- **Issue:** SubAgentDelegator used `field(default_factory=...)` for `available_agent_types`, but SubAgentDelegator is not a dataclass class — it has a custom `__init__`. `field()` only works inside `@dataclass`-decorated classes. Test `test_get_available_agent_types_default` failed with `TypeError: 'Field' object is not iterable`.
- **Fix:** Removed the `field()` class attribute and initialized `self._default_agent_types = [...]` in `__init__` instead. Updated `get_available_agent_types()` to reference `self._default_agent_types`.
- **Files modified:** `qwen-desktop/qwen_desktop/core/agent_manager/sub_agent_delegator.py`
- **Verification:** All 148 tests pass
- **Committed in:** `32f0411` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor — bug in field() usage on non-dataclass. Fixed inline during test execution. No scope creep.

## Issues Encountered

None — plan executed as specified with one minor auto-fix.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Ready for Plan 04 (AgentWorker QThread + ThinkingPanel + integration)
- SubAgentDelegator and SessionCompactor are both available for AgentWorker to use in the agent loop
- All tests pass (148 total, 29 in this plan)
- Threat model dispositions verified: T-02-08 (mitigated via structured context from parent), T-02-09 (accepted), T-02-10 (mitigated via original records preserved), T-02-11 (accepted), T-02-SC (mitigated — no packages installed)

---

*Phase: 02-agent-core*
*Completed: 2026-06-07*
