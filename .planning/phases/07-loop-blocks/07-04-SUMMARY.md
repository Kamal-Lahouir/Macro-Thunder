---
phase: 07-loop-blocks
plan: 04
subsystem: ui
tags: [pyqt6, loop-blocks, context-menu, validation, bug-fix]

requires:
  - phase: 07-loop-blocks plan 03
    provides: LoopStartPanel, BlockDelegate loop row styling, BlockTypeDialog loop entries

provides:
  - LoopStartPanel shown in EditorPanel detail area when LoopStart row is selected
  - Right-click context menu "Wrap selection in Loop" on any table selection
  - BlockTableModel.wrap_in_loop(flat_indices) mutation method
  - validate_loops() called in _start_play before engine.start() — blocks unmatched loops
  - Bug fix: pair-delete of loop boundary removes only LoopStart+LoopEnd; children become ungrouped
  - Bug fix: LoopChildRow displays actual block type label (not "Loop body")

affects:
  - main_window: pre-play validation gate now checks both gotos and loops
  - editor_panel: context menu and LoopStart detail routing
  - view_model: new wrap_in_loop mutation

tech-stack:
  added: []
  patterns:
    - "Context menu via setContextMenuPolicy(CustomContextMenu) + customContextMenuRequested signal"
    - "wrap_in_loop inserts LoopEnd at hi+1 first, then LoopStart at lo — preserves index validity"
    - "validate_loops is a pre-flight gate matching validate_gotos pattern — both must pass before engine.start()"
    - "pair-delete removes only boundary rows; children become ungrouped plain blocks (unwrap semantics)"
    - "LoopChildRow COL_TYPE renders f'  {block.type}' — indented actual type for visual hierarchy"

key-files:
  created: []
  modified:
    - src/macro_thunder/models/view_model.py
    - src/macro_thunder/ui/editor_panel.py
    - src/macro_thunder/ui/main_window.py
    - tests/test_view_model.py

key-decisions:
  - "wrap_in_loop inserts LoopEnd first (hi+1) before LoopStart (lo) so the lo index remains valid"
  - "LoopFooterRow, LoopChildRow, GroupHeaderRow, GroupChildRow selections show no detail panel (no editable data)"
  - "validate_loops called after validate_gotos in _start_play — both validation errors block play with distinct QMessageBox messages"
  - "pair-delete of LoopStart/LoopEnd removes only the two boundary rows; children stay as plain blocks (not the full region)"
  - "LoopChildRow type label is block.type with two-space indent — not a separate 'Loop Body' label"

patterns-established:
  - "Context menu pattern: setContextMenuPolicy(CustomContextMenu) + slot reads selectedIndexes(), calls model mutation"
  - "Loop pair mutation: insert hi+1 first then lo — standard pattern for index-stable dual insert"

requirements-completed: [LOOP-08, LOOP-09, LOOP-10]

duration: 45min
completed: 2026-03-03
---

# Phase 7 Plan 04: Loop Blocks UI Wiring Summary

**Full end-to-end loop workflow: LoopStartPanel detail routing, right-click Wrap in Loop, validate_loops pre-play gate, plus pair-delete keeps children and loop child rows show actual block type**

## Performance

- **Duration:** 45 min (including bug fixes after human-verify)
- **Started:** 2026-03-03T00:00:00Z
- **Completed:** 2026-03-03T00:45:00Z
- **Tasks:** 2 original + 2 post-checkpoint bug fixes
- **Files modified:** 4

## Accomplishments
- Selecting a LoopStart row now shows LoopStartPanel (repeat count spinbox) in detail area
- Right-clicking selected rows shows "Wrap selection in Loop" context menu — inserts matching LoopStart/LoopEnd pair
- wrap_in_loop method added to BlockTableModel — inserts LoopEnd at hi+1 first, then LoopStart at lo
- validate_loops called in _start_play alongside validate_gotos — unmatched loop sentinels block playback with warning dialog
- Bug 1 fixed: pair-delete of a loop boundary row removes only LoopStart+LoopEnd; children remain as plain blocks
- Bug 2 fixed: LoopChildRow type column shows actual block type (e.g. "  delay") not "  Loop Body"
- 120 tests pass (17 view model loop row tests including 4 new regression tests)

## Task Commits

1. **Task 1: wrap_in_loop + EditorPanel context menu + selection routing** - `6df3ea6` (feat)
2. **Task 2: validate_loops pre-flight gate in MainWindow** - `6df3ea6` (feat, included in same commit)
3. **Bug fixes: pair-delete keeps children + loop child type label** - `131d001` (fix)

## Files Created/Modified
- `src/macro_thunder/models/view_model.py` - Added wrap_in_loop method, amber highlight fix, pair-delete bug fix, LoopChildRow type label bug fix
- `src/macro_thunder/ui/editor_panel.py` - Added context menu, _wrap_selection_in_loop, and LoopHeaderRow → LoopStartPanel routing
- `src/macro_thunder/ui/main_window.py` - Imported validate_loops and added call in _start_play
- `tests/test_view_model.py` - Added 4 regression tests (2 pair-delete + 2 type label); replaced 2 stale tests

## Decisions Made
- wrap_in_loop inserts LoopEnd first (at hi+1) then LoopStart (at lo) to keep flat indices valid during dual insertion
- LoopFooterRow/LoopChildRow selections show no detail panel — LoopEndBlock has no editable data
- validate_loops uses QMessageBox.warning (vs validate_gotos uses QMessageBox.critical) to match severity difference

## Deviations from Plan

**1. [Rule 1 - Bug] Fixed amber highlight not showing on loop rows during playback**
- **Found during:** Task 1 (view_model.py inspection)
- **Issue:** BackgroundRole for loop rows always returned teal, even during active playback (amber should take precedence)
- **Fix:** Added elif branch inside the `if pi >= 0` block to check LoopHeaderRow/LoopFooterRow/LoopChildRow flat_index == pi before returning teal
- **Files modified:** src/macro_thunder/models/view_model.py
- **Verification:** Logic confirmed; amber check now correctly precedes teal fallback for loop rows
- **Committed in:** cd1e194 (included in view model loop row commit)

**2. [Rule 1 - Bug] pair-delete removed loop children instead of keeping them**
- **Found during:** Human-verify checkpoint (user-reported)
- **Issue:** LoopHeaderRow and LoopFooterRow branches in delete_rows added all k-indexed blocks in the inner scanning loop to flat_to_delete, including children between boundaries
- **Fix:** Removed `flat_to_delete.add(k)` from inner loop body in both branches; only add k when it is the matching boundary
- **Files modified:** src/macro_thunder/models/view_model.py, tests/test_view_model.py
- **Verification:** 2 regression tests pass; children remain as BlockRows after pair-delete
- **Committed in:** 131d001

**3. [Rule 1 - Bug] LoopChildRow always displayed "Loop Body" instead of actual block type**
- **Found during:** Human-verify checkpoint (user-reported)
- **Issue:** data() for LoopChildRow returned hard-coded string "  Loop Body" for COL_TYPE
- **Fix:** Changed to `return f"  {block.type}"` to show indented actual type
- **Files modified:** src/macro_thunder/models/view_model.py, tests/test_view_model.py
- **Verification:** 2 regression tests pass; Delay inside loop shows "  delay", KeyPress shows "  key_press"
- **Committed in:** 131d001

---

**Total deviations:** 3 auto-fixed (all Rule 1 bugs)
**Impact on plan:** All corrections necessary for correct UX and display. No scope creep.

## Issues Encountered
- Plans 07-01 through 07-03 were already fully implemented and committed in a prior session. This session only needed to implement Plan 07-04's two tasks.

## Self-Check

All required artifacts:
- [x] wrap_in_loop exists on BlockTableModel
- [x] EditorPanel has context menu connected
- [x] LoopStartPanel shown for LoopHeaderRow selection
- [x] validate_loops imported and called in _start_play
- [x] Bug 1 fixed: pair-delete removes only boundaries, children survive
- [x] Bug 2 fixed: LoopChildRow shows actual block type
- [x] 120 tests pass (17 view model loop row tests, all passing)
- [x] Commit 131d001 exists

## Self-Check: PASSED

## Next Phase Readiness
- Phase 7 (Loop Blocks) fully complete — all 4 plans executed and human-verified
- Loop workflow end-to-end: insert, wrap, edit repeat count, play with validation gate
- Pair-delete and type display bugs fixed post-checkpoint

---
*Phase: 07-loop-blocks*
*Completed: 2026-03-03*
