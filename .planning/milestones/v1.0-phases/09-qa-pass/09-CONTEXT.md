# Phase 9: QA Pass — Bug Fixes and Polish - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Systematically test every implemented feature (playback, recording, block editor, flow control/loops),
find bugs, and fix them inline. No new features. Ends when all success criteria pass.

</domain>

<decisions>
## Implementation Decisions

### QA Approach
- Find bugs AND fix them inline (not document-then-fix separately)
- Each plan = one feature area: test it, find bugs, fix them, verify
- Plans are independent enough to execute sequentially without cross-dependencies

### Coverage Areas (in priority order)
1. **Playback state machine** — amber cursor / hotkey resume (confirmed bug found in code review)
2. **Recording residue** — stop-hotkey key-up leak (known bug from memory/session notes)
3. **Block edit dialog** — Phase 8 work, needs verification of all block types + paired sync
4. **Flow control & loops** — Label/Goto, LoopStart/LoopEnd execution correctness

### Out of Scope
- Library/persistence (save/load, file management) — deferred
- No new features added during this phase
- No UI redesign — polish only (button state mismatches, blink persistence)

### Fix Style
- Minimal targeted fixes — don't refactor surrounding code
- Each fix should have a clear before/after behavior statement
- Dirty flag, button states, and visual glitches count as bugs if they confuse the user

</decisions>

<code_context>
## Existing Code Insights

### Confirmed Bug: Amber Cursor Wiped by Stale Sentinel
- `_stop_play(clear_cursor=False)` called by hotkey → amber stays
- Engine thread puts `(-1, -1)` into `_play_progress_queue`
- Next `_update_status` tick drains queue → sees `(-1, -1)` → calls `_stop_play(clear_cursor=True)` → **wipes amber**
- Fix: flush the queue in `_stop_play()` before returning, OR check `_state != PLAYING` before processing sentinel in drain loop
- Files: `src/macro_thunder/ui/main_window.py` lines 213-228 (`_update_status` drain) and 422-434 (`_stop_play`)

### Known Bug: Stop-Record Hotkey Key-Up Leaks into Blocks
- `_on_press` puts STOP_SENTINEL and returns (press not recorded ✓)
- `_on_release` has no matching suppression → records `KeyPressBlock(key="Key.f10", direction="up")` ✗
- Fix: add `_stop_key_consumed` set to `RecorderService`; suppress matching release
- Noted in memory/session-ui-recording-fixes.md and MEMORY.md

### Block Edit Dialog (Phase 8 — just implemented)
- `block_edit_dialog.py` with all per-type dialogs exists (08-01 plan)
- EditorPanel double-click wiring exists (08-02 plan)
- Needs end-to-end verification: each block type, paired MouseClick sync, dirty flag, Cancel behavior

### Playback State Machine
- `AppState`: IDLE / RECORDING / PLAYING
- `_start_play` reads `get_playback_row()` → starts from amber if >= 0
- `_on_selection_changed` in EditorPanel calls `clear_playback_row()` on any row click — intentional (user explicitly picks new start)
- `get_playback_row()` returns `_model._playback_flat_index` or -1

### Integration Points
- `main_window.py` orchestrates all state transitions
- `engine/__init__.py` runs playback in a thread, communicates via `_play_progress_queue`
- `editor_panel.py` owns amber cursor display
- `recorder_service.py` owns stop-key suppression logic

</code_context>

<specifics>
## Specific Ideas

- User noticed: pressing play hotkey after stop doesn't resume from yellow step — traced to stale sentinel drain
- "Fix bugs and optimize if something is off" — fix correctness issues; optimize only if something is clearly wasteful

</specifics>

<deferred>
## Deferred Ideas

- Library/persistence QA — future pass
- Automated regression test suite — could be a Phase 10

</deferred>

---

*Phase: 09-qa-pass*
*Context gathered: 2026-03-04*
