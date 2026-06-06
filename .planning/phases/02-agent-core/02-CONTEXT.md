# Phase 2: Agent Core — Context

**Gathered:** 2026-06-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the agentic loop that makes VDA autonomous. The user gives a multi-step command — the agent manager plans, executes, verifies, and iterates until done. Includes doom loop detection, sub-agent delegation, a permission system, session compaction, lazy tool loading, and a thinking-visualization UI panel.

This phase does NOT build individual tools (Web, Terminal, File, Voice) — those get their own phases (3–6). It builds the loop infrastructure that those tools will plug into.

</domain>

<decisions>
## Implementation Decisions

### Thinking Visualization (GUI-06)
- **D-01:** Expandable panel below the chat input area — collapsible section in the floating assistant, reusing existing animation patterns
- **D-02:** Medium detail per step — step label, status icon (spinner/checkmark/X), and one-line tool detail. Full tool output stays available in chat history
- **D-03:** Step-by-step updates — UI reflects each completed step (not real-time streaming partial output)
- **D-04:** Doom loop detection triggers pause + red warning badge in the panel. User sees "Doom loop detected" and must click Resume or Abort to proceed

### the agent's Discretion
The following areas were not discussed. Planner/researcher has discretion:

- **Agent loop threading** — QThread worker vs. synchronous per-message. The existing APIServerWorker pattern (QThread + pyqtSignal) is the precedent for non-blocking API work
- **Sub-agent delegation model** — Full reasoning sub-agents (separate API call, own context window) vs. tool-group dispatching (manager routes to scoped tool sets without new API call). Either approach is acceptable
- **Permission system UX** — Modal PyQt6 dialog vs. inline chat question for allow/deny/ask. Both patterns exist in the codebase (modals in settings_dialog.py, inline in chat flow)
- **Session compaction** — Auto-summarize at token threshold vs. truncate oldest vs. manual trigger. Existing MemoryManager (short-term + long-term) should be considered for integration

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition
- `.planning/ROADMAP.md` §Phase 2 — Success criteria, requirement list, dependencies
- `.planning/REQUIREMENTS.md` — AGNT-01 through AGNT-06, GUI-06

### Codebase Analysis
- `.planning/codebase/ARCHITECTURE.md` — System architecture, layer diagram, data flows
- `.planning/codebase/STACK.md` — Technology stack, dependencies
- `.planning/codebase/CONVENTIONS.md` — Coding conventions
- `.planning/codebase/INTEGRATIONS.md` — External integrations, provider architecture

### Design Decisions
- `.planning/STATE.md` — Active decisions, accumulated context
- `.planning/phases/01-foundation-security/01-CONTEXT.md` — Phase 1 decisions (file org, patterns)

### Relevant Existing Code
- `qwen_desktop/core/task_decomposer.py` — Existing task decomposition (may inform agent loop)
- `qwen_desktop/core/memory_manager.py` — Short/long-term memory (relevant to session compaction)
- `qwen_desktop/core/command_registry.py` — Existing command registration pattern
- `qwen_desktop/core/tool_executor/` — Existing tool execution (POC for tool registry interface)
- `qwen_desktop/ui/assistant/controller.py` — FloatingAssistant class (thinking panel integration target)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TaskDecomposer` (`core/task_decomposer.py`): Existing planning/decomposition logic that the agent loop can call
- `MemoryManager` (`core/memory_manager.py`): Short-term (in-memory, 4096 token limit) + long-term (JSON file) — base for session compaction
- `CommandRegistry` (`core/command_registry.py`): Existing command registration — similar pattern to tool registry
- `ToolExecutor` (`core/tool_executor/executor.py`): Existing tool call interface — tools follow a function-based pattern
- `QPropertyAnimation` / `QVariantAnimation` (PyQt6): Existing animation framework for the expandable thinking panel
- `QThread` + `pyqtSignal` pattern in `APIServerWorker` (`ui/assistant/worker.py`): Established async pattern the agent loop should follow

### Established Patterns
- Service classes initialized with `Settings` object, stateless methods
- `QThread` + `pyqtSignal` for background work without freezing GUI
- Full package-path imports (`from qwen_desktop.core.xxx import Yyy`)
- Nested sub-packages by concern (established in Phase 1)
- `snake_case` naming, `PascalCase` classes, module-level `logger = logging.getLogger(__name__)`

### Integration Points
- `FloatingAssistant` (`ui/assistant/controller.py`): The thinking panel must integrate here — it owns the UI layout
- `SessionService` (`core/session_service.py`): Session compaction writes back to the conversation store
- `APIClient`/`ZenClient` (`core/api_client.py`, `core/zen_client.py`): Agent loop calls the AI for planning, execution, and verification
- `Settings` (`config/settings.py`): Permission configuration storage

</code_context>

<specifics>
## Specific Ideas

- Thinking panel: expandable section below input area, collapsible, with step label + status icon + one-line detail
- Doom loop: red badge, pause execution, require user action (Resume/Abort)
- Agent loop should follow the existing QThread+pyqtSignal async pattern

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Agent Core*
*Context gathered: 2026-06-06*
