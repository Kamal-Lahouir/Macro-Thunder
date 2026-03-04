---
phase: 08-block-edit-dialog
plan: 01
subsystem: ui
tags: [pyqt6, dialogs, block-edit, key-capture]

requires:
  - phase: 07-loop-blocks
    provides: LoopStartBlock and LoopEndBlock definitions used in dialog dispatch

provides:
  - block_edit_dialog.py with open_edit_dialog() dispatcher
  - KeyCaptureField widget for pynput-format key capture
  - _find_click_partner() helper for paired MouseClick editing
  - 9 QDialog subclasses (one per editable block type)

affects:
  - 08-02 (wiring open_edit_dialog into editor double-click / toolbar button)

tech-stack:
  added: []
  patterns:
    - "Per-type dialog dispatch via isinstance chain in open_edit_dialog()"
    - "Cancel-safe editing: all field writes happen only inside accept(), never in __init__"
    - "KeyCaptureField: QPushButton capture mode + keyPressEvent with modifier filter"

key-files:
  created:
    - src/macro_thunder/ui/block_edit_dialog.py
  modified: []

key-decisions:
  - "KeyCaptureField stores pynput single-key format (no modifiers) — distinct from HotkeyField which supports modifier combos"
  - "_find_click_partner scans forward for 'up' partner when editing 'down' block, backward when editing 'up'"
  - "WindowFocusEditDialog reposition group visibility toggled by QCheckBox.toggled signal"

patterns-established:
  - "Dialog pattern: QVBoxLayout > QFormLayout + QDialogButtonBox; writes to block only in accept()"

requirements-completed:
  - EDIT-06
  - EDIT-07
  - EDIT-08

duration: 4min
completed: 2026-03-04
---

# Phase 8 Plan 1: Block Edit Dialog Summary

**Modal QDialog forms for all 9 editable block types with KeyCaptureField (pynput format), paired MouseClick editing, and Cancel-safe field writes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-04T01:31:27Z
- **Completed:** 2026-03-04T01:35:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `block_edit_dialog.py` with complete per-type dialog system
- `open_edit_dialog()` dispatcher handles all block types; returns False for LoopEndBlock without opening a dialog
- `KeyCaptureField` captures physical keypresses and converts to pynput format (e.g. "a", "Key.space", "Key.f10")
- `_find_click_partner()` finds paired down/up MouseClickBlock for synchronized coordinate editing
- All 9 dialog classes pre-fill from block values and write only on Accept — Cancel leaves blocks untouched

## Task Commits

1. **Task 1: Create block_edit_dialog.py with KeyCaptureField and _find_click_partner** - `1932cf3` (feat)

## Files Created/Modified
- `src/macro_thunder/ui/block_edit_dialog.py` - Complete per-type edit dialog module (584 lines)

## Decisions Made
- `KeyCaptureField` uses single-key pynput format (no modifier combos), unlike `HotkeyField` in settings which supports `<ctrl>+a` style
- `_find_click_partner` scans forward for matching "up" when block is "down", backward for "down" when block is "up", matching on button field
- `WindowFocusEditDialog` uses a `QGroupBox` for the reposition section, toggled visible by the checkbox signal

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `open_edit_dialog` and `KeyCaptureField` are importable and ready for wiring into the editor panel (double-click row, toolbar Edit button)
- No blockers

---
*Phase: 08-block-edit-dialog*
*Completed: 2026-03-04*
