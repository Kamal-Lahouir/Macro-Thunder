---
phase: 03-visual-block-editor
plan: 03
subsystem: ui
tags: [pyqt6, delegate, dialog, block-editor]

requires:
  - phase: 03-02
    provides: BlockTableModel with display row types (GroupHeaderRow, BlockRow, GroupChildRow)

provides:
  - BlockDelegate QStyledItemDelegate with toggle_group_requested signal for group expand/collapse
  - BlockTypeDialog modal picker returning default-constructed ActionBlock for all 8 types
  - UserRole data delivery from BlockTableModel.data() exposing DisplayRow objects

affects:
  - 03-05-editor-panel (consumes both BlockDelegate and BlockTypeDialog)

tech-stack:
  added: []
  patterns:
    - "Lightweight delegate — no paint() override; ▶/▼ arrows live in data() return value"
    - "UserRole used to pass structured DisplayRow objects from model to delegate"

key-files:
  created:
    - src/macro_thunder/ui/block_delegate.py
    - src/macro_thunder/ui/block_type_dialog.py
  modified:
    - src/macro_thunder/models/view_model.py

key-decisions:
  - "BlockDelegate skips paint() override — ▶/▼ prefix already returned by BlockTableModel.data(DisplayRole); delegate only overrides editorEvent"
  - "UserRole branch added to BlockTableModel.data() so delegate can isinstance-check the DisplayRow without coupling to model internals"
  - "BlockTypeDialog stores default block instances at module level in _BLOCK_TYPES list for O(1) lookup"

patterns-established:
  - "Delegate signals (toggle_group_requested) wired to model methods by EditorPanel — delegate stays unaware of model"

requirements-completed:
  - EDIT-05
  - GROUP-01

duration: 4min
completed: 2026-03-01
---

# Phase 3 Plan 03: BlockDelegate and BlockTypeDialog Summary

**QStyledItemDelegate with group-toggle signal and 8-type block picker dialog backed by default-constructed ActionBlock instances**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-01T21:01:00Z
- **Completed:** 2026-03-01T21:05:21Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created BlockDelegate with toggle_group_requested(int) pyqtSignal that fires when COL_TYPE cell clicked on a GroupHeaderRow
- Added Qt.ItemDataRole.UserRole branch to BlockTableModel.data() to expose raw DisplayRow objects
- Created BlockTypeDialog with QListWidget listing all 8 action block types; get_block() static method returns chosen default block or None

## Task Commits

1. **Task 1: BlockDelegate — group row rendering and toggle click detection** - `4979f40` (feat)
2. **Task 2: BlockTypeDialog — block type picker returning a default ActionBlock** - `e4d7803` (feat)

## Files Created/Modified
- `src/macro_thunder/ui/block_delegate.py` - QStyledItemDelegate subclass; editorEvent intercepts COL_TYPE clicks on GroupHeaderRow
- `src/macro_thunder/ui/block_type_dialog.py` - Modal dialog with 8-entry QListWidget; get_block() static factory
- `src/macro_thunder/models/view_model.py` - Added UserRole branch in BlockTableModel.data() returning DisplayRow object

## Decisions Made
- Skipped paint() override in BlockDelegate since ▶/▼ arrows are already embedded in DisplayRole text by BlockTableModel
- UserRole delivery added to view_model.py (small addition, no architectural change needed)
- Default block instances stored at module level in _BLOCK_TYPES to avoid re-construction on each dialog open

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added UserRole branch to BlockTableModel.data()**
- **Found during:** Task 1 (BlockDelegate implementation)
- **Issue:** Plan specified that BlockDelegate reads UserRole from model, but BlockTableModel.data() only handled DisplayRole
- **Fix:** Added `if role == Qt.ItemDataRole.UserRole: return self._display_rows[index.row()]` branch in data()
- **Files modified:** src/macro_thunder/models/view_model.py
- **Verification:** BlockDelegate import succeeds; 56 tests still pass
- **Committed in:** 4979f40 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (missing critical functionality)
**Impact on plan:** UserRole support was explicitly called out in the plan action — this was a planned addition, executed as part of Task 1.

## Issues Encountered
None - plan executed cleanly.

## Next Phase Readiness
- BlockDelegate and BlockTypeDialog are ready for wiring in EditorPanel (plan 03-05)
- toggle_group_requested signal connects to BlockTableModel.toggle_group()
- get_block() return value passes directly to BlockTableModel.insert_block()

---
*Phase: 03-visual-block-editor*
*Completed: 2026-03-01*
