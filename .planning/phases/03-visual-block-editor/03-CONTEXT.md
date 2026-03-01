# Phase 3: Visual Block Editor - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

A visual block editor where users view, edit, and reorder recorded macros. Consecutive MouseMove events are collapsed into group rows. Users can edit group durations, start/end coordinates, and individual block fields. A library panel allows loading, renaming, and deleting saved macros.

Playback, undo/redo, and flow control are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Group row display
- Collapsed group row shows: move count + total duration + endpoint coordinates
- Format: e.g. "MouseMove Group — 47 moves, 1.2s → (1440, 900)"
- Visual distinction: indented with a collapse arrow (▶ collapsed, ▼ expanded)

### Inline editing
- Group duration cell is editable inline — click to edit
- Group start/end coordinates are also editable inline
- When start/end coords are changed, intermediate move coordinates are interpolated/scaled proportionally to fit the new anchors (path shape preserved)
- All block types support inline editing for their key fields (consistent behavior throughout the table)

### Expand/collapse
- Expanded group rows appear inline in the table — indented child rows below the group row
- Expand/collapse triggered by clicking the arrow icon on the group row
- Individual move rows inside an expanded group are fully editable (same inline edit behavior as other rows)
- When moves are deleted/reordered inside a group until only 1 remains, the group auto-ungroups — the single move becomes a regular block row

### Block editing controls
- Reorder: both up/down arrow buttons in toolbar AND drag-and-drop row reordering
- Multi-select: Shift+click and Ctrl+click for selecting multiple rows
- Bulk operations: delete and move work on multi-selection
- Insert: toolbar "Add Block" button opens block type picker, inserts after current selection
- Controls live in a toolbar above the block editor table (Delete, Move Up, Move Down, Add Block always visible)

### Library panel
- Lives in the left sidebar (consistent with 3-panel app layout)
- Sorted by most recently used at top
- Per-macro actions: Load, Rename, Delete
- Unsaved edits: prompt "Save changes before loading?" with Yes / No / Cancel options

### Claude's Discretion
- Exact drag-and-drop handle visual (gripper icon vs. full-row drag)
- Block type picker UI (dropdown vs. small dialog)
- Exact toolbar icon choices and keyboard shortcuts
- How group rows visually render inside the QAbstractTableModel (delegate implementation details)
- Interpolation algorithm for coordinate scaling

</decisions>

<specifics>
## Specific Ideas

- Group row format explicitly shows endpoint coordinates so users know where the cursor ends up without expanding
- Coordinate editing on groups should feel like editing a start/end field, not require expanding the group

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-visual-block-editor*
*Context gathered: 2026-03-01*
