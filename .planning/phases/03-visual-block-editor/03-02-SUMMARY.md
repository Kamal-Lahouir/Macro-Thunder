---
phase: 03-visual-block-editor
plan: "02"
subsystem: models/view_model
tags: [qt, model, table-model, drag-drop, grouping]
dependency_graph:
  requires: [03-01]
  provides: [BlockTableModel]
  affects: [03-05-ui-wiring]
tech_stack:
  added: []
  patterns: [QAbstractTableModel, pyqtSignal, beginResetModel/endResetModel, QMimeData]
key_files:
  created: []
  modified:
    - src/macro_thunder/models/view_model.py
key_decisions:
  - "BlockTableModel uses beginResetModel/endResetModel for all mutations — simpler than fine-grained insertRows/removeRows given that _rebuild_display_rows recomputes entire display list"
  - "Expanded state is stored in a Dict[int, bool] keyed on flat_start so toggling survives _rebuild_display_rows calls (which create new GroupHeaderRow instances)"
  - "dropMimeData uses column=0 always to prevent column-shift bugs per plan spec"
  - "_set_block_value is a module-level helper (not a method) so it can be called from setData without Qt dependency"
metrics:
  duration: "2 min"
  completed: "2026-03-01"
  tasks: 2
  files_modified: 1
---

# Phase 3 Plan 02: BlockTableModel Implementation Summary

BlockTableModel QAbstractTableModel subclass with group-aware display rows, toggle_group expand/collapse, setData delegation to rescale helpers, and drag-and-drop InternalMove reorder.

## What Was Built

`BlockTableModel` was appended to `src/macro_thunder/models/view_model.py` (which already contained the DisplayRow dataclasses and rescaling helpers from plan 03-01).

### Task 1: Core — rowCount, data, flags, _rebuild_display_rows, toggle_group

- `_rebuild_display_rows()` scans `self._doc.blocks` sequentially, groups runs of 2+ consecutive `MouseMoveBlock` entries into `GroupHeaderRow` objects, lone move blocks become `BlockRow`, all other block types become `BlockRow`.
- Expanded state is preserved across rebuilds via `self._expanded: Dict[int, bool]` keyed on `flat_start`.
- `data()` returns formatted display strings for all three row types and all four columns.
- `flags()` marks editable cells: COL_TIMESTAMP/COL_VALUE/COL_EXTRA for group headers; COL_VALUE/COL_TIMESTAMP for block rows and child rows.
- `toggle_group()` flips expanded state in `_expanded` dict, then calls `beginResetModel / _rebuild_display_rows / endResetModel`.

Verification: `rowCount()` returned 2 (1 group + 1 keypress) and 5 after expand (header + 3 children + keypress).

### Task 2: Mutations — setData, delete_rows, insert_block, move_rows_up/down, drag-drop

- `setData()` dispatches to `_rescale_group_duration` / `_rescale_group_coords` for group header edits; parses and updates individual block fields for BlockRow/GroupChildRow edits.
- `delete_rows()` expands group headers to all their flat indices before deletion; uses `beginResetModel/endResetModel`.
- `insert_block()` resolves flat insertion index from the display row type.
- `move_rows_up/down()` move flat block slices up or down by one position.
- Drag-and-drop: `mimeData()` encodes flat index ranges as `"flat_start:flat_end"` or single `"flat_idx"` strings; `dropMimeData()` decodes and reorders `self._doc.blocks` in-place.
- `document_modified = pyqtSignal()` emitted on every mutation.

Verification: All 56 existing tests pass (5 rescale + 51 engine/recorder/serializer).

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- src/macro_thunder/models/view_model.py: FOUND
- Commit 3b3731d: FOUND
