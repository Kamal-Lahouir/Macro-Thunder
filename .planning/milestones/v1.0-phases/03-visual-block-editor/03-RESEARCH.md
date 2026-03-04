# Phase 3: Visual Block Editor - Research

**Researched:** 2026-03-01
**Domain:** PyQt6 Model/View, QAbstractTableModel, QTreeView, QStyledItemDelegate, drag-and-drop, inline editing
**Confidence:** HIGH (core patterns), MEDIUM (group-row implementation approach)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Group row display:**
- Collapsed group row shows: move count + total duration + endpoint coordinates
- Format: e.g. "MouseMove Group — 47 moves, 1.2s → (1440, 900)"
- Visual distinction: indented with a collapse arrow (▶ collapsed, ▼ expanded)

**Inline editing:**
- Group duration cell is editable inline — click to edit
- Group start/end coordinates are also editable inline
- When start/end coords are changed, intermediate move coordinates are interpolated/scaled proportionally to fit the new anchors (path shape preserved)
- All block types support inline editing for their key fields (consistent behavior throughout the table)

**Expand/collapse:**
- Expanded group rows appear inline in the table — indented child rows below the group row
- Expand/collapse triggered by clicking the arrow icon on the group row
- Individual move rows inside an expanded group are fully editable (same inline edit behavior as other rows)
- When moves are deleted/reordered inside a group until only 1 remains, the group auto-ungroups — the single move becomes a regular block row

**Block editing controls:**
- Reorder: both up/down arrow buttons in toolbar AND drag-and-drop row reordering
- Multi-select: Shift+click and Ctrl+click for selecting multiple rows
- Bulk operations: delete and move work on multi-selection
- Insert: toolbar "Add Block" button opens block type picker, inserts after current selection
- Controls live in a toolbar above the block editor table (Delete, Move Up, Move Down, Add Block always visible)

**Library panel:**
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

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EDIT-01 | Recorded macro is displayed as a list of action blocks in the editor | QAbstractTableModel subclass populates rows from MacroDocument.blocks; view model computed from flat list |
| EDIT-02 | User can delete one or multiple selected blocks | Multi-select via model flags + toolbar Delete button; calls beginRemoveRows/endRemoveRows |
| EDIT-03 | User can reorder blocks via drag-and-drop or up/down controls | QAbstractItemModel.moveRows + InternalMove drag-drop mode; dropMimeData pattern |
| EDIT-04 | User can multi-select blocks (click, shift-click, ctrl-click) | QAbstractItemView.ExtendedSelection mode on the view |
| EDIT-05 | User can manually insert a new action block at any position | beginInsertRows/endInsertRows; block type picker dialog/menu |
| GROUP-01 | Consecutive MouseMove blocks between non-move actions are visually grouped | View-model computes "display rows" from flat blocks; group rows are synthetic display entities |
| GROUP-02 | User can select a movement group and edit its total duration — timestamps scale proportionally | setData on group row with EditRole triggers proportional timestamp rescaling on underlying blocks |
| GROUP-03 | User can expand a group to edit individual move lines within it | Toggle expand state → view-model recomputes display rows → model reset or insertRows/removeRows |
| GROUP-04 | User can select individual lines within an expanded group | Child rows have full ItemIsSelectable + ItemIsEditable flags |
| LIB-01 | User can save a macro to a named file | Existing serializer.save(); QLineEdit name prompt in library panel |
| LIB-02 | User can open/load a saved macro | Existing serializer.load(); unsaved-changes prompt before replacing buffer |
| LIB-03 | A macro library panel lists all saved macros in a designated folder | QListWidget or custom QListView fed by scanning MacroThunder/ dir; sorted by mtime |
</phase_requirements>

---

## Summary

Phase 3 is primarily a PyQt6 Model/View engineering problem. The core challenge is implementing a "virtual tree inside a flat table": consecutive MouseMove blocks are grouped in the display layer (never in the data model), and groups can expand/collapse inline. This is most cleanly solved with a custom QAbstractTableModel (not QTreeView) that maintains a computed list of "display rows" — each row is either a regular block row, a group header row, or a child move row. The flat `MacroDocument.blocks` list remains unchanged at all times per the locked data model rule.

Inline editing uses Qt's standard delegate pipeline: `flags()` returns `Qt.ItemIsEditable` for editable cells, `setData()` writes back to the flat list (with coordinate interpolation for group start/end edits). Drag-and-drop row reordering uses `setDragDropMode(InternalMove)` on the view and `moveRows()` / `dropMimeData()` on the model. Multi-select uses `ExtendedSelection` mode.

The library panel is a straightforward `QListWidget` reading `.json` files from the MacroThunder directory, sorted by modification time. Per-item context menu handles Load/Rename/Delete. The unsaved-changes guard checks `_macro_buffer` dirty state before loading a new file.

**Primary recommendation:** Use a single custom `BlockTableModel(QAbstractTableModel)` with a computed `_display_rows` list. Never use QTreeView — the table layout with indented group rows and inline expand is explicitly what the user decided. Delegate handles group row rendering (arrow icon, indentation, unified text); standard delegates handle editable cells.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | >=6.4 (already installed) | Model/View framework, table, delegates | Project stack — locked in Phase 1 |
| Python stdlib `pathlib` | 3.12 | File scanning for library panel | Already used in serializer |
| Python stdlib `dataclasses` | 3.12 | Block mutation helpers | Already used project-wide |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `QStyledItemDelegate` | Qt6 built-in | Custom cell rendering and editing widgets | Group row arrow, editable numeric cells |
| `QSortFilterProxyModel` | Qt6 built-in | Optional: filter library list | Only if library grows large — likely not needed Phase 3 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom `QAbstractTableModel` with `_display_rows` | `QTreeView` + `QAbstractItemModel` | QTreeView requires hierarchical `parent()`/`index()` — much more complex; user decided on flat table appearance |
| Custom `QAbstractTableModel` with `_display_rows` | `QStandardItemModel` with nested items | QStandardItemModel hides the flat-list constraint; harder to keep `MacroDocument.blocks` as source of truth |
| `QListWidget` for library | `QFileSystemModel` + `QListView` | QFileSystemModel shows filesystem live but can't sort by MRU; QListWidget with manual population is simpler and sufficient |

**Installation:** No new packages — all within existing PyQt6 + stdlib.

---

## Architecture Patterns

### Recommended Project Structure

```
src/macro_thunder/
├── models/
│   ├── blocks.py           # Existing — no changes
│   ├── document.py         # Existing — no changes
│   └── view_model.py       # NEW: DisplayRow types + BlockTableModel
├── ui/
│   ├── editor_panel.py     # Replace stub — EditorPanel with toolbar + table
│   ├── library_panel.py    # Replace stub — LibraryPanel with file list
│   ├── block_delegate.py   # NEW: QStyledItemDelegate for group rows + editing
│   └── block_type_dialog.py # NEW: block type picker (small dialog or menu)
└── persistence/
    └── serializer.py       # Existing — add rename/delete helpers if needed
```

### Pattern 1: Display Row Computed Model

**What:** `BlockTableModel` does NOT store data itself. It maintains `_display_rows: list[DisplayRow]` derived from `MacroDocument.blocks`. A `DisplayRow` is a tagged union:

```python
# src/macro_thunder/models/view_model.py
from dataclasses import dataclass
from typing import Union

@dataclass
class BlockRow:
    """A single non-move block, or a move block outside any group."""
    flat_index: int          # index into MacroDocument.blocks

@dataclass
class GroupHeaderRow:
    """Collapsed or expanded group header spanning flat_start..flat_end (inclusive)."""
    flat_start: int
    flat_end: int
    expanded: bool

@dataclass
class GroupChildRow:
    """One move block visible inside an expanded group."""
    flat_index: int
    group_flat_start: int   # backref to parent group

DisplayRow = Union[BlockRow, GroupHeaderRow, GroupChildRow]
```

`_rebuild_display_rows()` scans `blocks` sequentially: runs of `MouseMoveBlock` become `GroupHeaderRow` entries (with child rows injected after if `expanded`), everything else becomes `BlockRow`. Call this method after any mutation, then emit `modelReset()` or fine-grained `beginInsertRows`/`beginRemoveRows` signals.

**When to use:** Always — this is the central pattern for this phase.

### Pattern 2: Model Flags for Editable Cells

```python
# Source: https://doc.qt.io/qt-6/qabstractitemmodel.html#flags
def flags(self, index: QModelIndex) -> Qt.ItemFlag:
    base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    row = self._display_rows[index.row()]
    if isinstance(row, (BlockRow, GroupChildRow)):
        base |= Qt.ItemFlag.ItemIsDragEnabled
    if isinstance(row, GroupHeaderRow):
        base |= Qt.ItemFlag.ItemIsDragEnabled  # drag whole group
    # Make specific columns editable
    if self._is_editable_column(index):
        base |= Qt.ItemFlag.ItemIsEditable
    return base
```

**When to use:** Always implement `flags()` — without `ItemIsEditable` the delegate editor never appears.

### Pattern 3: Inline Editing via setData

```python
def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
    if role != Qt.ItemDataRole.EditRole:
        return False
    row = self._display_rows[index.row()]
    if isinstance(row, GroupHeaderRow) and index.column() == COL_DURATION:
        self._rescale_group_duration(row, float(value))
        self._rebuild_display_rows()
        self.dataChanged.emit(index, index, [role])
        return True
    # ... other column handlers
    return False
```

setData mutates `MacroDocument.blocks` directly, then rebuilds display rows. Always emit `dataChanged` after success.

### Pattern 4: Drag-and-Drop Row Reorder

```python
# View configuration (in EditorPanel.__init__)
view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
view.setDragDropOverwriteMode(False)
view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

# Model methods required
def supportedDropActions(self):
    return Qt.DropAction.MoveAction

def mimeTypes(self):
    return ["application/x-macroblock-rows"]

def mimeData(self, indexes):
    # encode source row indices (column 0 only, capture all)
    ...

def dropMimeData(self, data, action, row, column, parent):
    # always drop to column 0 to prevent column shifting
    # decode source rows, call self._move_blocks(src_rows, dest_row)
    # then _rebuild_display_rows() + modelReset
    ...
```

**Pitfall:** Always force `column = 0` inside `dropMimeData` regardless of what Qt passes — column shifting is the #1 drag-drop bug with multi-column tables.

### Pattern 5: Expand/Collapse via Toggle

```python
def toggle_group(self, display_row_index: int) -> None:
    row = self._display_rows[display_row_index]
    assert isinstance(row, GroupHeaderRow)
    row.expanded = not row.expanded
    self.beginResetModel()
    self._rebuild_display_rows()
    self.endResetModel()
```

The delegate's `editorEvent` or a custom `mousePressEvent` on the view detects clicks in the arrow-icon column and calls `toggle_group`. Using `beginResetModel`/`endResetModel` is safe and simple; fine-grained insert/remove signals are optional optimization.

### Pattern 6: Group Coordinate Interpolation

When the user edits group start `(x0, y0)` or end `(xN, yN)`, intermediate moves are rescaled:

```python
def _rescale_group_coords(self, group: GroupHeaderRow, new_start, new_end):
    moves = self._doc.blocks[group.flat_start : group.flat_end + 1]
    old_start = (moves[0].x, moves[0].y)
    old_end = (moves[-1].x, moves[-1].y)
    for i, block in enumerate(moves):
        t = i / max(len(moves) - 1, 1)   # 0.0 .. 1.0
        block.x = round(new_start[0] + t * (new_end[0] - new_start[0]))
        block.y = round(new_start[1] + t * (new_end[1] - new_start[1]))
```

This is linear interpolation — it preserves proportional spacing along the straight-line path. The original curved path shape is NOT preserved (only start/end anchors), which matches "path shape preserved" in context only approximately. This is in Claude's Discretion for algorithm choice.

### Pattern 7: Library Panel File List

```python
# src/macro_thunder/ui/library_panel.py
import pathlib, os

def _refresh_list(self):
    macro_dir = pathlib.Path.home() / "Documents" / "MacroThunder"
    files = sorted(macro_dir.glob("*.json"),
                   key=lambda f: f.stat().st_mtime, reverse=True)
    self._list_widget.clear()
    for f in files:
        item = QListWidgetItem(f.stem)
        item.setData(Qt.ItemDataRole.UserRole, str(f))
        self._list_widget.addItem(item)
```

Right-click context menu on items provides Load / Rename / Delete actions.

### Anti-Patterns to Avoid

- **Storing group information in `MacroDocument.blocks`:** The data model MUST stay as a flat list — grouping is computed at display time only. Violating this breaks the serializer, the playback engine, and the project data model rule.
- **Using `QTreeView` for group expand/collapse:** QTreeView requires implementing `parent()`, `index()`, and `hasChildren()` — substantial complexity for no benefit when the user wants table-style row layout.
- **Calling `modelReset()` without `beginResetModel()`/`endResetModel()`:** PyQt6 requires the begin/end pair; omitting them causes view corruption.
- **Accessing Qt objects from pynput threads:** Not relevant to this phase's core logic, but any future signal connections to the recorder must continue using the queue+timer pattern.
- **Using `time.sleep()` in group timestamp rescaling:** Not applicable, but timestamp arithmetic should use direct float math, not sleep.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-and-drop row reorder | Custom mouse event drag tracker | Qt's built-in `InternalMove` mode + `dropMimeData()` | Qt handles drag threshold, cursor, drop target highlighting |
| Inline cell editing | Custom floating QLineEdit popup | `QStyledItemDelegate.createEditor()` pipeline | Qt handles focus, commit-on-enter, escape-to-cancel, click-away |
| Multi-select | Track selected rows manually | `ExtendedSelection` mode on view | Qt handles Shift+click range, Ctrl+click toggle, keyboard navigation |
| File scanning / sort by mtime | Custom file watcher | `pathlib.Path.stat().st_mtime` + `sorted()` | No live-watch needed; refresh on panel open/save |

**Key insight:** Qt's model/view delegate pipeline handles >80% of editing UX complexity. The only custom code needed is `flags()`, `data()`, `setData()`, and `dropMimeData()` in the model.

---

## Common Pitfalls

### Pitfall 1: Column Shifting in Drag-and-Drop

**What goes wrong:** When user drops on a non-leftmost column, `dropMimeData(row, column, parent)` receives `column > 0`. Default `moveRows` implementation inserts at wrong position.

**Why it happens:** Qt passes the column of the drop target, not necessarily column 0.

**How to avoid:** In `dropMimeData`, always override `column` to `0` before computing the destination row index. Reference: Mount CREO article.

**Warning signs:** Rows appear shifted by one column after drop.

### Pitfall 2: beginResetModel / endResetModel Wrapping

**What goes wrong:** Calling `self.modelReset.emit()` directly (without begin/end) causes the view to hold stale persistent model indices, leading to selection corruption or crashes.

**Why it happens:** The begin/end pair tells the view to release all cached state before the reset.

**How to avoid:** Always use `self.beginResetModel()` / `self.endResetModel()` pair. Never call `modelReset` directly.

### Pitfall 3: flags() Missing ItemIsEditable

**What goes wrong:** Double-clicking a cell does nothing — the delegate's `createEditor()` is never called.

**Why it happens:** Qt checks `flags()` before invoking the delegate editor. If `ItemIsEditable` is absent, the click is ignored.

**How to avoid:** Return `Qt.ItemFlag.ItemIsEditable` from `flags()` for every cell/column that should be editable.

### Pitfall 4: Group Row Count Changes Breaking Drag-and-Drop

**What goes wrong:** User drags a group header row; drop target row index is computed against the pre-drag `_display_rows`, but after dropping the row count changes (children may now be visible/hidden), causing off-by-one in the destination.

**Why it happens:** `_display_rows` is the source of truth for row indices during D&D, but `_rebuild_display_rows()` changes row count when expand state changes.

**How to avoid:** Never toggle expand state during a drag operation. Only rebuild after `dropMimeData` completes. Store source row flat_indices in mimeData, not display row indices, and recompute destination after rebuild.

### Pitfall 5: Auto-Ungroup Race When Deleting Child Rows

**What goes wrong:** User deletes last child of a group; auto-ungroup fires, triggering a model reset mid-selection, leaving stale selection state.

**Why it happens:** Delete operation mutates blocks, then rebuild fires before the view clears selection.

**How to avoid:** Clear the view's selection before calling `_rebuild_display_rows()` in the delete handler. Sequence: (1) compute new blocks list, (2) `beginResetModel()`, (3) update `self._doc.blocks`, (4) rebuild display rows, (5) `endResetModel()`.

### Pitfall 6: Library Panel Refresh Timing

**What goes wrong:** Library panel shows stale file list after save (new file not visible) or after delete (deleted file still shows).

**Why it happens:** `_refresh_list()` is only called on panel open, not after file operations.

**How to avoid:** Call `_refresh_list()` explicitly after every save and delete operation that the library panel initiates. Expose a `refresh()` method and call it from `MainWindow` after File > Save Macro.

---

## Code Examples

Verified patterns from Qt6 official docs and Python GUIs resources:

### QAbstractTableModel Minimum Interface

```python
# Source: https://doc.qt.io/qt-6/qabstracttablemodel.html
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

class BlockTableModel(QAbstractTableModel):
    def rowCount(self, parent=QModelIndex()):
        return len(self._display_rows)

    def columnCount(self, parent=QModelIndex()):
        return 4  # Type | Value | Timestamp | Duration (context-dependent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._display_rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_text(row, index.column())
        return None

    def flags(self, index):
        f = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self._is_editable(index):
            f |= Qt.ItemFlag.ItemIsEditable
        f |= Qt.ItemFlag.ItemIsDragEnabled
        return f

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return False
        # ... mutate self._doc.blocks ...
        self.dataChanged.emit(index, index, [role])
        return True
```

### Drag-and-Drop View Setup

```python
# Source: https://www.pythonguis.com/faq/qtableview-drag-and-drop-drop-prohibited-icon/
from PyQt6.QtWidgets import QAbstractItemView

view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
view.setDragDropOverwriteMode(False)
view.setDropIndicatorShown(True)
```

### Library Panel File Load with Unsaved-Changes Guard

```python
def _on_load_clicked(self, path: str) -> None:
    if self._has_unsaved_changes():
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "Save changes before loading?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return
        if reply == QMessageBox.StandardButton.Yes:
            self.save_requested.emit()  # signal to MainWindow
    self.load_requested.emit(path)
```

### Group Timestamp Rescaling

```python
def _rescale_group_duration(self, group: GroupHeaderRow, new_duration: float) -> None:
    """Rescale timestamps of moves in group so total duration = new_duration."""
    moves = self._doc.blocks[group.flat_start : group.flat_end + 1]
    if len(moves) < 2:
        return
    old_start_t = moves[0].timestamp
    old_end_t = moves[-1].timestamp
    old_duration = old_end_t - old_start_t
    if old_duration <= 0:
        return
    scale = new_duration / old_duration
    for block in moves:
        block.timestamp = old_start_t + (block.timestamp - old_start_t) * scale
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `QTableWidget` (convenience class) | `QAbstractTableModel` + `QTableView` | Qt4 → Qt5 best practice | Must use model/view split; QTableWidget bakes data into widgets |
| `event.pos()` | `event.position()` | Qt5 → Qt6 | Already noted in CLAUDE.md — use `position()` in any delegate event handlers |
| `QAction` from `QtWidgets` | `QAction` from `PyQt6.QtGui` | Qt5 → Qt6 | Already noted in STATE.md — same rule applies to toolbar actions in EditorPanel |

**Deprecated/outdated:**
- `Qt.AA_EnableHighDpiScaling`: Removed in Qt6 — do not use (already in CLAUDE.md).
- `event.pos()` / `event.globalPos()`: Use `event.position()` / `event.globalPosition()` — already in CLAUDE.md.

---

## Open Questions

1. **Dirty-state tracking for unsaved-changes guard**
   - What we know: `MainWindow._macro_buffer` holds the current document; no dirty flag currently exists
   - What's unclear: Is a boolean `_is_dirty` flag on `MainWindow` sufficient, or should `BlockTableModel` emit a `documentModified` signal?
   - Recommendation: Add a simple `_is_dirty: bool` on `MainWindow`, set to `True` on any `setData` call or block mutation, reset to `False` after save. The model emits a `document_modified` signal that MainWindow connects to.

2. **Group drag-and-drop unit semantics**
   - What we know: User can drag rows; groups are display entities spanning multiple flat blocks
   - What's unclear: When user drags a collapsed group header, do ALL underlying flat blocks move as a unit?
   - Recommendation: Yes — dragging a collapsed group header moves `flat_end - flat_start + 1` consecutive blocks as a unit. Encode `(flat_start, flat_end, row_type)` in mimeData to handle this.

3. **Rename in library panel**
   - What we know: Per-macro Rename action needed (LIB-03 context)
   - What's unclear: Rename = rename filename only, or also rename `doc.name` field inside the JSON?
   - Recommendation: Rename the file on disk AND reload/update `doc.name` if the current buffer matches that file. Use `QInputDialog.getText()` for the new name.

---

## Sources

### Primary (HIGH confidence)

- Qt6 official docs: https://doc.qt.io/qt-6/qabstracttablemodel.html — rowCount, columnCount, data, flags, setData, beginResetModel API
- Qt6 official docs: https://doc.qt.io/qt-6/qabstractitemview.html — setDragDropMode, SelectionBehavior, SelectionMode
- Qt6 official docs: https://doc.qt.io/qt-6/qstyleditemdelegate.html — createEditor, setEditorData, setModelData
- Existing codebase: `src/macro_thunder/models/blocks.py`, `models/document.py`, `persistence/serializer.py` — block types, flat list rule, serialization

### Secondary (MEDIUM confidence)

- https://www.pythonguis.com/faq/qtableview-cell-edit/ — setData + flags() pattern, verified against Qt6 docs
- https://mountcreo.com/article/pyqtpyside-drag-and-drop-qtableview-reordering-rows/ — column-0 dropMimeData pitfall, hidden column mimeData pattern
- https://www.pythonguis.com/faq/qtableview-drag-and-drop-drop-prohibited-icon/ — view configuration flags for InternalMove

### Tertiary (LOW confidence)

- WebSearch results on MRU file sorting — no dedicated source; using `pathlib.stat().st_mtime` is stdlib standard, HIGH confidence in the approach itself

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all within existing PyQt6 + stdlib; no new packages
- Architecture (DisplayRow pattern): MEDIUM — well-established pattern for flat-table-with-groups, but no single canonical PyQt6 tutorial verified; pattern derived from Qt model/view principles + existing project constraints
- Drag-and-drop specifics: MEDIUM — column-0 pitfall verified via two sources; full flow not end-to-end verified in PyQt6 6.4+
- Inline editing: HIGH — flags() + setData() pattern is canonical Qt model/view
- Library panel: HIGH — simple QListWidget + pathlib; no novel patterns

**Research date:** 2026-03-01
**Valid until:** 2026-06-01 (PyQt6 stable API; 90 days)
