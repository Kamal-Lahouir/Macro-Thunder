# Phase 9: QA Pass — Bug Fixes and Polish - Research

**Researched:** 2026-03-04
**Domain:** Bug fixing — PyQt6 state machine, pynput recorder, block edit dialog verification
**Confidence:** HIGH (all findings sourced from direct code inspection)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Find bugs AND fix them inline (not document-then-fix separately)
- Each plan = one feature area: test it, find bugs, fix them, verify
- Plans are independent enough to execute sequentially without cross-dependencies
- Coverage areas in priority order:
  1. Playback state machine — amber cursor / hotkey resume
  2. Recording residue — stop-hotkey key-up leak
  3. Block edit dialog — Phase 8 verification of all block types + paired sync
  4. Flow control & loops — Label/Goto, LoopStart/LoopEnd execution correctness

### Claude's Discretion
- "Fix bugs and optimize if something is off" — fix correctness issues; optimize only if something is clearly wasteful
- Dirty flag, button states, and visual glitches count as bugs if they confuse the user

### Deferred Ideas (OUT OF SCOPE)
- Library/persistence QA — future pass
- Automated regression test suite — could be a Phase 10
- No new features added during this phase
- No UI redesign — polish only (button state mismatches, blink persistence)
</user_constraints>

---

## Summary

Phase 9 is a bug-fix-and-verify pass over four isolated feature areas. It is NOT a new-feature phase. All research is sourced from direct code inspection of the actual source files — no external libraries need to be introduced.

Two confirmed bugs are precisely located and have clear minimal fixes. The remaining two coverage areas (block edit dialog and flow control) need systematic manual verification with focused unit-test additions rather than large refactors.

The most impactful fix is the amber cursor stale-sentinel bug: a hotkey stop puts `(-1,-1)` into `_play_progress_queue` via `on_done`, which the 16ms `_update_status` timer later drains and routes to `_stop_play(clear_cursor=True)`, erasing the amber position the user needs to resume from. The correct fix is to check `self._state != AppState.PLAYING` before acting on the sentinel in the drain loop.

**Primary recommendation:** Fix each bug with the minimum surgical change. Do not refactor surrounding code. Verify with targeted pytest assertions where possible; use manual smoke-tests for UI-layer behavior.

---

## Standard Stack

No new libraries. All fixes use the existing stack.

### Core (already installed)
| Library | Version | Purpose | Relevant to Phase 9 |
|---------|---------|---------|----------------------|
| PyQt6 | existing | UI framework, QTimer drain pattern | `_update_status` bug fix |
| pynput | existing | Recorder callbacks, key events | stop-key suppression fix |
| pytest | existing | Unit tests | New test assertions for bugs |

---

## Architecture Patterns

### Pattern 1: Queue Drain Guard — Check State Before Acting on Sentinel

**What:** The `_update_status` drain loop receives `(-1,-1)` from the engine's `on_done` callback. It must only route this sentinel to `_stop_play(clear_cursor=True)` when the app is still in PLAYING state. If the hotkey already transitioned state to IDLE, the sentinel must be silently discarded.

**Current code (main_window.py lines 217-227):**
```python
while not self._play_progress_queue.empty():
    try:
        idx, total = self._play_progress_queue.get_nowait()
    except queue.Empty:
        break
    if idx == -1 and total == -1:
        self._stop_play(clear_cursor=True)  # BUG: called even after hotkey stop
        break
    else:
        self._toolbar_widget.set_playback_progress(idx + 1, total)
        self._editor_panel.set_playback_row(idx)
```

**Fixed code:**
```python
while not self._play_progress_queue.empty():
    try:
        idx, total = self._play_progress_queue.get_nowait()
    except queue.Empty:
        break
    if idx == -1 and total == -1:
        # Only act on natural completion sentinel when still playing.
        # If hotkey already stopped playback, discard the stale sentinel.
        if self._state == AppState.PLAYING:
            self._stop_play(clear_cursor=True)
        break
    else:
        self._toolbar_widget.set_playback_progress(idx + 1, total)
        self._editor_panel.set_playback_row(idx)
```

**Why this fix:** `_stop_play()` called by hotkey sets `self._state = AppState.IDLE` before the 16ms timer fires. The state check is the gate that distinguishes "natural completion" from "already stopped by user".

### Pattern 2: Stop-Key Consumed Flag — Suppress Release Event

**What:** `RecorderService._on_press` detects the stop hotkey and puts `STOP_SENTINEL`, returning early so the press is not recorded. But `_on_release` has no corresponding check, so the key-up event leaks into the block list as `KeyPressBlock(key="Key.f10", direction="up")`.

**Current code (recorder/__init__.py line 200-210):**
```python
def _on_release(self, key):
    if key in self._held_at_start:
        self._held_at_start.discard(key)
        return
    if self._click_mode == "combined":
        return
    ts = time.perf_counter() - self._record_start
    self._queue.put(KeyPressBlock(key=self._key_to_str(key), direction="up", timestamp=ts))
```

**Fixed code:**
```python
def __init__(self, ...):
    ...
    self._stop_key_consumed: bool = False  # set True when stop-press fires

def _on_press(self, key):
    self._held_at_start.discard(key)
    if self._stop_hotkey_str and self._matches_stop_hotkey(key):
        self._stop_key_consumed = True       # mark it
        self._queue.put(self.STOP_SENTINEL)
        return
    ...

def _on_release(self, key):
    if key in self._held_at_start:
        self._held_at_start.discard(key)
        return
    # Suppress the release of the stop hotkey
    if self._stop_key_consumed and self._matches_stop_hotkey(key):
        self._stop_key_consumed = False
        return
    if self._click_mode == "combined":
        return
    ts = time.perf_counter() - self._record_start
    self._queue.put(KeyPressBlock(key=self._key_to_str(key), direction="up", timestamp=ts))
```

### Pattern 3: Block Edit Dialog Verification Checklist

The dialog system is implemented correctly:
- `open_edit_dialog()` dispatches to per-type dialog classes
- All dialogs write to block fields only in `accept()` (Cancel-safety verified in code)
- `_find_click_partner()` scans forward for "up" partner, backward for "down" partner, matching on `button` field
- `_on_double_click` in EditorPanel handles `BlockRow`, `LoopHeaderRow`, `LoopChildRow`, `GroupChildRow`; skips `GroupHeaderRow` and `LoopFooterRow`
- After `open_edit_dialog()` returns True, `beginResetModel/endResetModel` + `document_modified` signals are emitted correctly

**Verification actions needed (no code changes expected):**
1. Double-click each block type → correct dialog opens
2. Change a field, click Cancel → block unchanged
3. Change a field, click OK → block shows new value in editor; dirty flag set
4. For MouseClickBlock "down" paired with "up" → edit X on the "down" block → "up" block X also updated; direction NOT copied to partner

**Potential issue to verify:** `MouseClickEditDialog.accept()` copies `x`, `y`, `button` to partner but NOT `direction`. This is intentional (partner keeps its own direction). Confirm this is correct behavior.

### Pattern 4: Flow Control Verification Checklist

Engine code in `engine/__init__.py` handles Label, Goto, LoopStart, LoopEnd correctly per code inspection:
- Label: increment i and continue (no dispatch, no progress reset) — correct
- Goto: checks `progress_since_last_goto`, increments fire count, detects > 1000 → `on_loop_detected`
- LoopStart: pushes `(i, block.repeat - 1)` onto `loop_stack`; first pass already in progress so -1
- LoopEnd: pops and jumps to `start_idx + 1` if remaining > 0, else pops and continues

**Note — duplicate LoopStart/LoopEnd handlers detected:** Lines 180-201 and lines 233-255 in `engine/__init__.py` contain identical `LoopStart` and `LoopEnd` handling blocks. The second set (lines 233-255) is dead code because control never reaches it (the first set handles those block types and `continue`s). This is a code smell but does not cause incorrect behavior. Should be cleaned up during this phase.

**Verification actions needed:**
1. Label/Goto jump: macro with Label "loop_back" and Goto "loop_back" → loop detection fires after 1000 iterations → warning shown
2. Missing label: Goto targeting non-existent label → validate_gotos blocks play with error
3. LoopStart N=3 with body block: body executes exactly 3 times, not 2 or 4
4. Unmatched LoopStart (no LoopEnd): validate_loops blocks play with error

### Anti-Patterns to Avoid

- **Refactoring surrounding code during QA:** Each fix must be surgical. No method extractions, no renamed variables, no "while I'm in here" cleanups beyond the specific bug.
- **Flushing the entire queue in `_stop_play`:** The CONTEXT.md mentions this as an option, but it is worse than the state-check approach. Flushing in `_stop_play` would discard any legitimate progress updates that arrived before the stop was processed.
- **Adding sleep or delay to work around timing issues:** The timing system uses `perf_counter` targets; timing bugs should be fixed at the logic level.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread-to-UI communication | Custom event objects | Existing `queue.Queue` + QTimer drain | Pattern already in place; adding new mechanisms causes inconsistency |
| Key name conversion | New mapping table | Existing `_qt_key_to_pynput()` in block_edit_dialog.py | Already handles all common keys including F1-F12 |
| Dialog dirty tracking | New dirty tracking layer | Emit existing `document_modified` signal after `open_edit_dialog` returns True | Already wired in `_on_double_click` |

---

## Common Pitfalls

### Pitfall 1: State Check Ordering in Drain Loop

**What goes wrong:** Adding `if self._state == AppState.PLAYING` check after the sentinel drain loop exits — too late, the sentinel was already acted on.
**Why it happens:** The check must be INSIDE the `if idx == -1 and total == -1:` branch.
**How to avoid:** Place the guard immediately inside the sentinel branch, before calling `_stop_play`.

### Pitfall 2: Stop-Key Suppression Only Works for Single-Key Hotkeys

**What goes wrong:** `_matches_stop_hotkey()` only checks the final non-modifier key token, not the full modifier combination. This is intentional (see comment in code) but means `_stop_key_consumed` must be a simple bool, not a key-set comparison.
**How to avoid:** Use `_stop_key_consumed = True/False` flag, not a key identity comparison in `_on_release`.

### Pitfall 3: Duplicate LoopStart/LoopEnd Handlers in Engine

**What goes wrong:** Editing the first set of handlers and forgetting the dead second set causes confusion in future maintenance.
**How to avoid:** Delete lines 233-255 (the second, dead set) during the flow control verification plan.
**Warning signs:** Lines 233-255 in `engine/__init__.py` have identical structure to lines 180-201.

### Pitfall 4: PyQt6 nativeEvent Return Values

**What goes wrong:** Returning `super().nativeEvent(...)` crashes (segfault on Windows in PyQt6).
**How to avoid:** Per CLAUDE.md, the correct "not handled" return is `return False, 0`.

### Pitfall 5: beginResetModel Must Be Paired

**What goes wrong:** Calling `beginResetModel()` without a matching `endResetModel()` (e.g. due to exception) leaves the view in a broken state.
**How to avoid:** No model mutations between `beginResetModel` and `endResetModel`. The current `_on_double_click` code is correct — no mutations happen between the two calls; `_rebuild_display_rows` only rebuilds internal lists.

---

## Code Examples

### Bug Fix 1: Sentinel State Guard
```python
# src/macro_thunder/ui/main_window.py — _update_status drain loop
# BEFORE (line 222):
if idx == -1 and total == -1:
    self._stop_play(clear_cursor=True)
    break

# AFTER:
if idx == -1 and total == -1:
    if self._state == AppState.PLAYING:
        self._stop_play(clear_cursor=True)
    break
```

### Bug Fix 2: Stop-Key Consumed Flag
```python
# src/macro_thunder/recorder/__init__.py

# In __init__:
self._stop_key_consumed: bool = False

# In _on_press (after held_at_start.discard, before recording):
if self._stop_hotkey_str and self._matches_stop_hotkey(key):
    self._stop_key_consumed = True
    self._queue.put(self.STOP_SENTINEL)
    return

# In _on_release (before click_mode check):
if self._stop_key_consumed and self._matches_stop_hotkey(key):
    self._stop_key_consumed = False
    return
```

### Dead Code Removal: Engine Duplicate Handlers
```python
# src/macro_thunder/engine/__init__.py
# DELETE lines 233-255 (second LoopStart/LoopEnd handler block, identical to 180-201)
# These are unreachable — the first handler already continues before reaching them.
```

---

## Open Questions

1. **MouseClickBlock direction sync in paired edit**
   - What we know: `accept()` syncs `x`, `y`, `button` but not `direction` to partner
   - What's unclear: Is it correct that changing direction on a "down" block does NOT update the partner to "up"? (User changing "down" to "click" would leave an orphaned "up" partner)
   - Recommendation: Verify during manual testing. If this causes confusion, add a note to the dialog — but do NOT auto-change direction on partners (would require more complex logic beyond phase scope).

2. **Infinite loop in `_update_status` when loop_detect_queue fires**
   - What we know: Lines 230-243 drain `_loop_detect_queue` and call `_stop_play(clear_cursor=True)` — but this also triggers `_run_post_playback_action()` which could shutdown/sleep the machine unexpectedly
   - What's unclear: Is post-playback action appropriate for loop-detection stops?
   - Recommendation: Verify this is correct (loop detection stop should probably NOT trigger post-playback action). If wrong, pass `clear_cursor=True` but skip post-action — requires a new param or separate helper.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/macro_thunder/ui/main_window.py` — lines 212-243 (`_update_status`), 428-434 (`_stop_play`)
- Direct code inspection: `src/macro_thunder/recorder/__init__.py` — lines 164-210 (`_on_press`, `_on_release`)
- Direct code inspection: `src/macro_thunder/ui/block_edit_dialog.py` — full file
- Direct code inspection: `src/macro_thunder/engine/__init__.py` — full file
- Direct code inspection: `src/macro_thunder/ui/editor_panel.py` — lines 123-152 (`_on_double_click`)
- `.planning/phases/09-qa-pass/09-CONTEXT.md` — locked decisions and code context

### Secondary (MEDIUM confidence)
- MEMORY.md entry: "Known Bug (unresolved) — Stop record hotkey release gets recorded as a block"
- STATE.md accumulated decisions log

---

## Metadata

**Confidence breakdown:**
- Bug identification: HIGH — confirmed by direct code inspection of exact lines
- Fix correctness: HIGH — minimal single-condition changes with no side effects
- Block edit dialog: HIGH — code shows correct Cancel/Accept pattern already in place; verification is manual
- Flow control: HIGH — engine logic verified correct; duplicate dead code identified as cleanup candidate
- Open question (direction sync): MEDIUM — behavior is deterministic but user intent unclear

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (codebase is stable; no external dependencies changing)
