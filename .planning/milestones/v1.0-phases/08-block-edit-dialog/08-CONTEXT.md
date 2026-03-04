# Phase 8: Block Edit Dialog - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Double-clicking a block row in the editor opens a modal form dialog to edit that block's fields in-place. All logically editable block types are covered. Paired press/release MouseClick blocks are edited atomically. This phase does not add new block types or change the recording pipeline.

</domain>

<decisions>
## Implementation Decisions

### Dialog trigger
- Double-click on a block row opens the edit dialog
- LoopEnd blocks have no editable fields — do not open a dialog

### Dialog style
- Simple modal form dialog (QDialog) with labeled fields, OK and Cancel buttons
- Not inline editing, not a side panel

### Block type coverage — all logically editable types
- `MouseClickBlock`: x, y, button (left/right/middle), direction (down/up/click)
- `MouseMoveBlock`: x, y
- `MouseScrollBlock`: x, y, dx, dy
- `KeyPressBlock`: key (press-to-capture), direction (down/up/key)
- `DelayBlock`: duration (float seconds)
- `LabelBlock`: name
- `GotoBlock`: target label name
- `WindowFocusBlock`: all fields (executable, title, match_mode, timeout, on_failure_label, on_success_label, reposition, x, y, w, h)
- `LoopStartBlock`: repeat count
- `LoopEndBlock`: no dialog

### Paired MouseClick sync
- A click in Mode 2 produces two blocks: direction="down" and direction="up" with the same button
- When editing either block of a pair, the edit dialog edits both atomically
- Pairing rule: from the edited block, find the nearest sibling with matching button and the complementary direction (down↔up)
- Both button AND x/y are synced — down and up happen at the same coordinates
- If no pair is found (e.g. orphaned block), edit only the single block

### Key capture for KeyPress
- Uses press-to-capture: a button labeled "Press a key..." that captures the next physical keypress
- Same interaction pattern as the hotkey capture UI in Settings (Phase 6)

### Dirty flag
- Confirming edits (OK) marks the macro as unsaved, same as delete/reorder/insert
- Cancelling leaves the block unchanged and does not dirty the document

</decisions>

<specifics>
## Specific Ideas

- User's primary motivation: change left click to right click without re-recording
- The paired block sync is the most important correctness requirement — a mismatch between down/up buttons would produce broken playback

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BlockTypeDialog` (ui/block_type_dialog.py): existing modal dialog pattern for block selection — same QDialog structure can be reused for edit dialogs
- Hotkey capture button pattern from Phase 6 Settings UI — reuse for KeyPress key field
- `block_from_dict` / dataclass fields: each block's fields are discoverable from the dataclass, useful for building per-type forms

### Established Patterns
- Mutations go through `BlockTableModel` methods (delete_rows, insert_block, move_rows_*) — edit should follow same pattern with a new `edit_block(flat_index, new_block)` method
- Dirty flag set via `MacroDocument` mutation path — already wired in MainWindow
- Double-click: connect `QTableView.doubleClicked` signal in `EditorPanel`

### Integration Points
- `EditorPanel.doubleClicked` signal → new `_on_double_click(index)` slot
- `BlockTableModel.edit_block(flat_index, new_block)` — new mutation method
- For paired sync: `BlockTableModel` has access to `MacroDocument.blocks` flat list — scan for partner from flat_index

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-block-edit-dialog*
*Context gathered: 2026-03-04*
