---
phase: 1
slug: foundation-security
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-06
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `qwen-desktop/pyproject.toml` |
| **Quick run command** | `cd qwen-desktop && pytest tests/ -x -q` |
| **Full suite command** | `cd qwen-desktop && pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd qwen-desktop && pytest tests/ -x -q`
- **After every plan wave:** Run `cd qwen-desktop && pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {01-01-01} | 01 | 1 | RFCT-01 | T-01-01 / — | N/A | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-02} | 01 | 1 | RFCT-02 | T-01-02 / — | N/A | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-03} | 01 | 1 | RFCT-03 | T-01-03 / — | N/A | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-04} | 01 | 1 | RFCT-04 | T-01-04 / — | N/A | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-05} | 01 | 1 | RFCT-05 | T-01-05 / — | N/A | unit | `ruff check .` | ❌ W0 | ⬜ pending |
| {01-01-06} | 01 | 1 | SEC-02 | T-01-06 | key exposure | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-07} | 01 | 1 | SEC-03 | T-01-07 | mouse safety | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| {01-01-08} | 01 | 1 | TEST-01 | — | N/A | n/a | `cd qwen-desktop && pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `qwen-desktop/tests/test_clicker_engine.py` — stubs for RFCT-01
- [ ] `qwen-desktop/tests/test_safety.py` — stubs for SEC-03
- [ ] `qwen-desktop/tests/test_keychain.py` — stubs for SEC-02

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| keyring integration works end-to-end | SEC-02 | Needs OS keychain access | Run app, save API key, restart, verify key is retrieved |
| FAILSAFE restoration on exception | SEC-03 | Needs pyautogui mouse simulation | Trigger click action, raise exception, verify FAILSAFE is restored |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
