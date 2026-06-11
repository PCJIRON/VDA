---
phase: 2
slug: agent-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-06
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `qwen-desktop/pyproject.toml` |
| **Quick run command** | `cd qwen-desktop && py -m pytest tests/ -x -q` |
| **Full suite command** | `cd qwen-desktop && py -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd qwen-desktop && py -m pytest tests/test_{plan_module}.py -x -q`
- **After every plan wave:** Run `cd qwen-desktop && py -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {02-01-01} | 01 | 1 | AGNT-06 | T-02-02 / T-02-03 | Thread-safe lazy init prevents race conditions | unit | `py -m pytest tests/test_tool_registry.py -x -q` | ❌ W0 | ⬜ pending |
| {02-01-02} | 01 | 1 | AGNT-06 | — | N/A (stubs — no execution) | unit | `py -m pytest tests/test_tool_registry.py::test_registered_tools -x -q` | ❌ W0 | ⬜ pending |
| {02-01-03} | 01 | 1 | AGNT-06 | T-02-01 | Agent-type scope filtering prevents wrong tool exposure | unit | `py -m pytest tests/test_tool_registry.py -x -v` | ❌ W0 | ⬜ pending |
| {02-02-01} | 02 | 2 | AGNT-01 | T-02-04 / T-02-07 | Max iteration limit prevents infinite API spend | unit | `py -m pytest tests/test_agent_manager.py -x -q` | ❌ W0 | ⬜ pending |
| {02-02-02} | 02 | 2 | AGNT-02 | T-02-06 | Result-hash comparison prevents polling FPs | unit | `py -m pytest tests/test_doom_detector.py -x -q` | ❌ W0 | ⬜ pending |
| {02-02-03} | 02 | 2 | AGNT-01, AGNT-02, AGNT-04 | T-02-05 | Permission config from AGENT_TYPES (not mutable) | unit | `py -m pytest tests/test_permissions.py -x -q` | ❌ W0 | ⬜ pending |
| {02-03-01} | 03 | 3 | AGNT-03 | T-02-08 | Structured context prevents injection | unit | `py -m pytest tests/test_sub_agent.py -x -q` | ❌ W0 | ⬜ pending |
| {02-03-02} | 03 | 3 | AGNT-05 | T-02-09 / T-02-10 | One-time compaction prevents re-compaction loops | unit | `py -m pytest tests/test_compactor.py -x -q` | ❌ W0 | ⬜ pending |
| {02-03-03} | 03 | 3 | AGNT-03, AGNT-05 | — | N/A (test files) | unit | `py -m pytest tests/test_sub_agent.py tests/test_compactor.py -x -q` | ❌ W0 | ⬜ pending |
| {02-04-01} | 04 | 4 | GUI-06 | T-02-12 | Signal-based thread-safe communication | unit | `py -c "from qwen_desktop.core.agent_manager import AgentWorker; print('OK')"` | ❌ W0 | ⬜ pending |
| {02-04-02} | 04 | 4 | GUI-06 | — | N/A (UI widget — follow existing patterns) | manual | `py -m pytest tests/test_thinking_panel.py -x -v` | ❌ W0 | ⬜ pending |
| {02-04-03} | 04 | 4 | GUI-06 | T-02-13 / T-02-14 | Send button transitions to Stop during agent exec | unit | `py -m pytest tests/test_thinking_panel.py -x -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tool_registry.py` — covers AGNT-06 registration, lazy init, thread safety, scope filtering
- [ ] `tests/test_agent_manager.py` — covers AGNT-01 state machine, max iterations, pause/resume/abort
- [ ] `tests/test_doom_detector.py` — covers AGNT-02 loop detection, false positive prevention
- [ ] `tests/test_permissions.py` — covers AGNT-04 three-state logic, agent-type config, caching
- [ ] `tests/test_sub_agent.py` — covers AGNT-03 delegation, tool scoping, context passing
- [ ] `tests/test_compactor.py` — covers AGNT-05 threshold trigger, summarization, one-time flag
- [ ] `tests/test_thinking_panel.py` — covers GUI-06 step updates, status icons, doom loop UI

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ThinkingPanel expand/collapse animation | GUI-06 D-01 | QPropertyAnimation visual behavior | Launch app, click thinking toggle, verify smooth animation |
| Doom loop red badge + Resume/Abort buttons | GUI-06 D-04 | Needs agent loop running to trigger | Trigger doom loop (3 identical calls), verify badge appears and buttons work |
| Permission inline Allow/Deny bar | AGNT-04 | Needs agent loop + permission config | Send command that triggers ASK tool, verify bar appears |
| Agent vs single-query routing | AGNT-01 | Needs app running to observe routing | Send multi-step command → agent loop path; send short query → chat path |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
