# Debug: Auto-Mode Not Running Continuously

**Date:** 2026-03-31  
**Issue:** Phase execution stops after each task instead of running continuously until completion  
**Status:** ✅ Fixed

---

## Problem

When running `/gsd-execute-phase`, the execution would:
1. Complete one task/plan
2. Stop and wait for user input
3. Not continue automatically to the next task/plan

**Expected behavior:** Continuous execution until all plans in the phase are complete.

---

## Root Cause Analysis

### Issue 1: Missing `--auto` Flag Documentation

The `gsd-execute-phase` skill file (`.github/skills/gsd-execute-phase/SKILL.md`) did not document the `--auto` flag, even though the workflow (`.github/get-shit-done/workflows/execute-phase.md`) had full support for it.

**Impact:** Users didn't know they could use `--auto` to enable continuous execution.

### Issue 2: `auto_advance` Config Not Set

The `.planning/config.json` file had `workflow.auto_advance` missing, which defaults to `false` in the hardcoded defaults (`.github/get-shit-done/bin/lib/config.cjs` line 122).

**Impact:** Auto-mode was never activated unless explicitly enabled.

### Issue 3: Auto-Chain Flag Cleared on Init

The `execute-phase.md` workflow's `initialize` step (line 85-90) explicitly clears `_auto_chain_active` if `--auto` is NOT in arguments:

```bash
# REQUIRED: prevents stale auto-chain from previous --auto runs
if [[ ! "$ARGUMENTS" =~ --auto ]]; then
  node ".github/get-shit-done/bin/gsd-tools.cjs" config-set workflow._auto_chain_active false 2>/dev/null
fi
```

**Impact:** Even if auto-mode was previously active, it gets cleared unless `--auto` is passed every time.

---

## How Auto-Mode Works

### Auto-Mode Activation (any one enables it):

1. **`--auto` flag** passed to `/gsd-execute-phase`
2. **`workflow._auto_chain_active: true`** in config (ephemeral, set by `/gsd-discuss-phase --auto`)
3. **`workflow.auto_advance: true`** in `.planning/config.json` (persistent user preference)

### Auto-Mode Behavior:

When active, checkpoints are handled automatically:

| Checkpoint Type | Auto-Mode Behavior |
|-----------------|-------------------|
| `human-verify` | Auto-approve with `"approved"`, log `⚡ Auto-approved checkpoint` |
| `decision` | Auto-select first option, log `⚡ Auto-selected: [option]` |
| `human-action` | Still stops (auth gates cannot be automated) |

### Phase Completion:

When verification passes and auto-mode is active:
- Executes transition workflow inline
- Auto-advances to next phase (if `--auto` or config enabled)
- Otherwise presents options to user

---

## Fixes Applied

### Fix 1: Updated `gsd-execute-phase/SKILL.md`

Added `--auto` flag documentation:

```markdown
argument-hint: "<phase-number> [--wave N] [--gaps-only] [--interactive] [--auto]"

**Available optional flags:**
- `--auto` — Enable auto-advance mode: auto-approve checkpoints (human-verify/decision), auto-transition to next phase after verification. Use for continuous unattended execution.
```

### Fix 2: Updated `.planning/config.json`

Added `auto_advance: true` to workflow settings:

```json
{
  "workflow": {
    "mode": "interactive",
    "auto_research": false,
    "require_approvals": true,
    "auto_advance": true
  }
}
```

---

## Usage

### Option 1: Persistent Auto-Mode (Recommended)

Keep `auto_advance: true` in `.planning/config.json`.

**Pros:** 
- Always on by default
- No need to remember flags
- Consistent behavior across sessions

**Cons:**
- Less control over when it activates

### Option 2: Explicit `--auto` Flag

Run: `/gsd-execute-phase 1 --auto`

**Pros:**
- Explicit control per invocation
- Clear intent in command history

**Cons:**
- Must remember to add flag every time
- Easy to forget

### Option 3: Interactive Mode (Default)

Run: `/gsd-execute-phase 1` (no flags, `auto_advance: false`)

**Pros:**
- Full control over each task/plan
- Catch mistakes early
- Good for learning/debugging

**Cons:**
- Requires manual approval at each step
- Slower execution
- Higher token usage (more back-and-forth)

---

## Verification

To verify auto-mode is working:

1. Run `/gsd-execute-phase 1` (or with `--auto` flag)
2. Watch for checkpoint handling:
   - **Auto-mode active:** `⚡ Auto-approved checkpoint` or `⚡ Auto-selected: [option]`
   - **Auto-mode inactive:** Presents checkpoint details and waits for user input
3. Check if execution continues automatically after checkpoints
4. After phase complete, check if transition workflow runs automatically

---

## Related Files

- `.github/skills/gsd-execute-phase/SKILL.md` — Skill definition
- `.github/get-shit-done/workflows/execute-phase.md` — Execution workflow
- `.github/get-shit-done/workflows/execute-plan.md` — Plan execution
- `.github/get-shit-done/references/checkpoints.md` — Checkpoint protocol
- `.planning/config.json` — Project configuration
- `.github/get-shit-done/bin/lib/config.cjs` — Config defaults

---

## Future Improvements

1. **Add `--auto` to skill argument-hint in other skills:**
   - `/gsd-plan-phase --auto`
   - `/gsd-discuss-phase --auto` (already has it)

2. **Better error messages:**
   - When auto-mode is disabled, suggest using `--auto` or updating config
   - Show auto-mode status in phase execution output

3. **Config UI:**
   - Add interactive prompt in `/gsd-new-project` to set `auto_advance` preference
   - Document the setting in project README

---

## Summary

**Problem:** Execution stopped after each task instead of running continuously.

**Cause:** Auto-mode was not activated because:
1. `--auto` flag not documented in skill file
2. `auto_advance` config setting was `false` (default)

**Fix:**
1. ✅ Added `--auto` flag documentation to `gsd-execute-phase/SKILL.md`
2. ✅ Set `auto_advance: true` in `.planning/config.json`

**Result:** Phase execution now runs continuously until completion, auto-approving checkpoints and transitioning to next phase automatically.
