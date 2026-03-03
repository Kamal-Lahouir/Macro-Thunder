---
phase: 07-loop-blocks
plan: 03
subsystem: ui
tags: [PyQt6, QStyledItemDelegate, QSpinBox, loop-blocks, visual-editor]

requires:
  - phase: 07-02
    provides: LoopHeaderRow, LoopFooterRow, LoopChildRow display row types in view_model
  - phase: 07-01
    provides: LoopStartBlock, LoopEndBlock data model types

provides:
  - 4px teal left-border stripe in block_delegate for LoopHeaderRow/LoopFooterRow/LoopChildRow
  - LoopStartPanel with QSpinBox (min=1, max=9999) that mutates block.repeat on change
  - "Loop Start" and "Loop End" entries in BlockTypeDialog _BLOCK_TYPES

affects: [07-04, editor-panel-selection-routing]

tech-stack:
  added: []
  patterns:
    - "Loop row stripe: painter.save/fillRect(4px)/restore then super().paint() so text still renders"
    - "Detail panel pattern: QFormLayout with mutating spinbox, same as LabelPanel/GotoPanel"

key-files:
  created: []
  modified:
    - src/macro_thunder/ui/block_delegate.py
    - src/macro_thunder/ui/block_panels.py
    - src/macro_thunder/ui/block_type_dialog.py
    - src/macro_thunder/models/view_model.py

key-decisions:
  - "Teal stripe (0,160,140) painted before super().paint() so delegate text renders on top of stripe"
  - "LoopStartPanel follows LabelPanel/GotoPanel pattern: QFormLayout with single control, inline mutation"
  - "Loop rows completed in view_model: BackgroundRole teal, DisplayRole data, pair-delete in delete_rows"

patterns-established:
  - "Loop visual identity: teal background (0,60,55) from BackgroundRole + 4px teal stripe (0,160,140) from delegate"
  - "Loop boundary deletion is always pair-wise: deleting header auto-deletes footer+children, and vice versa"

requirements-completed: [LOOP-06, LOOP-07]

duration: 15min
completed: 2026-03-03
---

# Phase 7 Plan 3: Loop Blocks UI Styling Summary

**Teal left-border stripe in BlockDelegate, LoopStartPanel with repeat-count spinbox, and Loop Start/End entries in BlockTypeDialog — loop regions are now visually distinct and editable**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-03T09:42:00Z
- **Completed:** 2026-03-03T09:57:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- BlockDelegate.paint() draws a 4px teal stripe on the left edge of every LoopHeaderRow, LoopFooterRow, and LoopChildRow — makes loop region brackets immediately visible
- LoopStartPanel added to block_panels.py with QSpinBox (min=1, max=9999) wired to mutate block.repeat and call modified_cb on every change
- BlockTypeDialog extended with "Loop Start" and "Loop End" entries so users can insert loop blocks via the + Add Block button
- view_model.py completed: BackgroundRole dark teal (0,60,55) for loop rows, DisplayRole data for all three loop row types, pair-delete logic in delete_rows, insert_block extended for loop rows

## Task Commits

Each task was committed atomically:

1. **07-02 prerequisite (view_model completion)** - `cd1e194` (feat)
2. **Task 1: block_delegate teal stripe** - `dd52769` (feat)
3. **Task 2: LoopStartPanel + BlockTypeDialog** - `bd89d74` (feat)

## Files Created/Modified
- `src/macro_thunder/ui/block_delegate.py` - Imports loop row types, paints 4px teal stripe in paint()
- `src/macro_thunder/ui/block_panels.py` - Adds LoopStartPanel with repeat-count QSpinBox
- `src/macro_thunder/ui/block_type_dialog.py` - Adds Loop Start and Loop End to _BLOCK_TYPES
- `src/macro_thunder/models/view_model.py` - Completed loop row BackgroundRole, DisplayRole, delete_rows pair-delete

## Decisions Made
- Teal stripe is drawn BEFORE super().paint() so the base renderer draws text/selection on top; no return early (unlike amber which returns early to avoid Qt selection artifacts)
- LoopStartPanel uses the same QFormLayout + single control + inline mutation pattern as LabelPanel and GotoPanel
- view_model.py completion (07-02 remaining work) treated as a Rule 3 blocking deviation and done atomically

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Completed 07-02 view_model work that was partially missing**
- **Found during:** Task 1 (pre-execution verification)
- **Issue:** view_model.py was missing BackgroundRole for loop rows, DisplayRole data for LoopHeaderRow/LoopFooterRow/LoopChildRow, pair-delete in delete_rows, and insert_block handling for loop rows
- **Fix:** Added all missing view_model.py pieces: teal BackgroundRole, full DisplayRole data branches, pair-wise delete_rows logic, loop row handling in insert_block and _display_row_to_flat_indices
- **Files modified:** src/macro_thunder/models/view_model.py
- **Verification:** 118 tests pass including all loop block tests
- **Committed in:** cd1e194

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking prerequisite)
**Impact on plan:** Necessary to unblock Tasks 1 and 2. No scope creep.

## Issues Encountered
None during planned tasks.

## Next Phase Readiness
- Loop blocks now fully visible in the table with teal stripe + teal background
- LoopStartPanel ready for EditorPanel routing (Plan 07-04)
- BlockTypeDialog can insert loop blocks via + Add Block
- Plan 07-04 should wire EditorPanel._on_selection_changed to route LoopStartBlock selections to LoopStartPanel

---
*Phase: 07-loop-blocks*
*Completed: 2026-03-03*
