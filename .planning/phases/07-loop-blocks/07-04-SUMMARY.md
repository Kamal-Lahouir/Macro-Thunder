---
phase: 07-loop-blocks
plan: 04
subsystem: ui
tags: [pyqt6, loop-blocks, context-menu, validation]

requires:
  - phase: 07-loop-blocks plan 03
    provides: LoopStartPanel, BlockDelegate loop row styling, BlockTypeDialog loop entries

provides:
  - LoopStartPanel shown in EditorPanel detail area when LoopStart row is selected
  - Right-click context menu "Wrap selection in Loop" on any table selection
  - BlockTableModel.wrap_in_loop(flat_indices) mutation method
  - validate_loops() called in _start_play before engine.start() — blocks unmatched loops

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

key-files:
  created: []
  modified:
    - src/macro_thunder/models/view_model.py
    - src/macro_thunder/ui/editor_panel.py
    - src/macro_thunder/ui/main_window.py

key-decisions:
  - "wrap_in_loop inserts LoopEnd first (hi+1) before LoopStart (lo) so the lo index remains valid"
  - "LoopFooterRow, LoopChildRow, GroupHeaderRow, GroupChildRow selections show no detail panel (no editable data)"
  - "validate_loops called after validate_gotos in _start_play — both validation errors block play with distinct QMessageBox messages"

patterns-established:
  - "Context menu pattern: setContextMenuPolicy(CustomContextMenu) + slot reads selectedIndexes(), calls model mutation"
  - "Loop pair mutation: insert hi+1 first then lo — standard pattern for index-stable dual insert"

requirements-completed: [LOOP-08, LOOP-09, LOOP-10]

duration: 15min
completed: 2026-03-03
---

# Phase 7 Plan 04: Loop Blocks UI Wiring Summary

**Full end-to-end loop workflow: LoopStartPanel detail routing, right-click Wrap in Loop context menu, and validate_loops pre-play gate blocking unmatched sentinels**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-03T00:00:00Z
- **Completed:** 2026-03-03T00:15:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Selecting a LoopStart row now shows LoopStartPanel (repeat count spinbox) in detail area
- Right-clicking selected rows shows "Wrap selection in Loop" context menu — inserts matching LoopStart/LoopEnd pair
- wrap_in_loop method added to BlockTableModel — inserts LoopEnd at hi+1 first, then LoopStart at lo
- validate_loops called in _start_play alongside validate_gotos — unmatched loop sentinels block playback with warning dialog
- 118 tests pass (21 new loop block tests + 15 view model loop row tests)

## Task Commits

1. **Task 1: wrap_in_loop + EditorPanel context menu + selection routing** - `6df3ea6` (feat)
2. **Task 2: validate_loops pre-flight gate in MainWindow** - `6df3ea6` (feat, included in same commit)

## Files Created/Modified
- `src/macro_thunder/models/view_model.py` - Added wrap_in_loop method and amber highlight fix for loop rows
- `src/macro_thunder/ui/editor_panel.py` - Added context menu, _wrap_selection_in_loop, and LoopHeaderRow → LoopStartPanel routing
- `src/macro_thunder/ui/main_window.py` - Imported validate_loops and added call in _start_play

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

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Necessary correction for correct playback cursor display on loop rows. No scope creep.

## Issues Encountered
- Plans 07-01 through 07-03 were already fully implemented and committed in a prior session. This session only needed to implement Plan 07-04's two tasks.

## Self-Check

All required artifacts:
- [x] wrap_in_loop exists on BlockTableModel
- [x] EditorPanel has context menu connected
- [x] LoopStartPanel shown for LoopHeaderRow selection
- [x] validate_loops imported and called in _start_play
- [x] 118 tests pass

## Self-Check: PASSED

## Next Phase Readiness
- Full loop block workflow is complete and end-to-end testable in the running app
- Human verification checkpoint required to confirm full workflow in app
- Phase 7 complete pending human verify

---
*Phase: 07-loop-blocks*
*Completed: 2026-03-03*
