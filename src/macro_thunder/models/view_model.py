"""View-layer types and pure rescaling helpers for the visual block editor (Phase 3).

DisplayRow variants represent what is rendered in BlockTableModel:
- BlockRow: a single non-move block, or a lone move block outside any group
- GroupHeaderRow: the header row for a collapsed/expanded consecutive-move group
- GroupChildRow: one move block visible inside an expanded group

The rescaling functions (_rescale_group_duration, _rescale_group_coords) are
module-level pure functions so they can be imported and unit-tested without Qt.
They mutate blocks in-place and are called by BlockTableModel.setData().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, List, Tuple, Dict

from macro_thunder.models.blocks import (
    ActionBlock, MouseMoveBlock, MouseClickBlock, MouseScrollBlock,
    KeyPressBlock, DelayBlock, WindowFocusBlock, LabelBlock, GotoBlock,
)


@dataclass
class BlockRow:
    """A single non-move block, or a lone move block outside any group."""
    flat_index: int


@dataclass
class GroupHeaderRow:
    """Collapsed or expanded group header spanning flat_start..flat_end inclusive."""
    flat_start: int
    flat_end: int
    expanded: bool = False


@dataclass
class GroupChildRow:
    """One move block visible inside an expanded group."""
    flat_index: int
    group_flat_start: int


DisplayRow = Union[BlockRow, GroupHeaderRow, GroupChildRow]


def _rescale_group_duration(
    blocks: List[ActionBlock],
    flat_start: int,
    flat_end: int,
    new_duration: float,
) -> None:
    """Rescale timestamps of blocks[flat_start..flat_end] so total span == new_duration.

    Proportional rescaling: each block's offset from the group start is multiplied
    by (new_duration / old_duration).  Mutates timestamps in-place.

    No-op if flat_start == flat_end (single block) or old_duration <= 0.
    """
    if flat_start == flat_end:
        return

    old_start_t: float = blocks[flat_start].timestamp  # type: ignore[attr-defined]
    old_end_t: float = blocks[flat_end].timestamp  # type: ignore[attr-defined]
    old_duration = old_end_t - old_start_t

    if old_duration <= 0:
        return

    scale = new_duration / old_duration
    for block in blocks[flat_start : flat_end + 1]:
        block.timestamp = old_start_t + (block.timestamp - old_start_t) * scale  # type: ignore[attr-defined]


def _rescale_group_coords(
    blocks: List[ActionBlock],
    flat_start: int,
    flat_end: int,
    new_start: Tuple[int, int],
    new_end: Tuple[int, int],
) -> None:
    """Linearly interpolate x/y of each block in blocks[flat_start..flat_end].

    Interpolation parameter t = i / max(n-1, 1) where i is the block's position
    within the group and n is the group size.  Mutates x/y in-place.

    No-op if flat_start == flat_end (single block).
    """
    if flat_start == flat_end:
        return

    n = flat_end - flat_start + 1
    x0, y0 = new_start
    xN, yN = new_end

    for i, block in enumerate(blocks[flat_start : flat_end + 1]):
        t = i / max(n - 1, 1)
        block.x = round(x0 + t * (xN - x0))  # type: ignore[attr-defined]
        block.y = round(y0 + t * (yN - y0))  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Column indices
# ---------------------------------------------------------------------------
COL_TYPE = 0
COL_VALUE = 1
COL_TIMESTAMP = 2
COL_EXTRA = 3
_NUM_COLS = 4


def _block_value(block: ActionBlock) -> str:
    """Return human-readable value string for a block."""
    if isinstance(block, MouseMoveBlock):
        return f"({block.x}, {block.y})"
    if isinstance(block, MouseClickBlock):
        return f"{block.button} {block.direction} @ ({block.x},{block.y})"
    if isinstance(block, MouseScrollBlock):
        return f"scroll ({block.dx},{block.dy}) @ ({block.x},{block.y})"
    if isinstance(block, KeyPressBlock):
        return f"{block.key} {block.direction}"
    if isinstance(block, DelayBlock):
        return f"{block.duration:.3f}s"
    if isinstance(block, WindowFocusBlock):
        return f"{block.executable} — {block.title}"
    if isinstance(block, LabelBlock):
        return f":{block.name}"
    if isinstance(block, GotoBlock):
        return f"→ {block.target}"
    return ""


def _block_timestamp(block: ActionBlock) -> str:
    """Return timestamp string if the block has a timestamp attribute."""
    ts = getattr(block, "timestamp", None)
    if ts is None:
        return ""
    return f"{ts:.4f}"


# ---------------------------------------------------------------------------
# BlockTableModel
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtCore import (
        QAbstractTableModel, QMimeData, QModelIndex, Qt, pyqtSignal,
    )
    from PyQt6.QtCore import QByteArray
    _QT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _QT_AVAILABLE = False


if _QT_AVAILABLE:

    class BlockTableModel(QAbstractTableModel):
        """QAbstractTableModel presenting a flat MacroDocument as display rows.

        Consecutive MouseMoveBlock runs of 2+ blocks are collapsed into a
        single GroupHeaderRow.  toggle_group() expands/collapses inline.
        Drag-and-drop reorder operates on flat block indices.
        """

        document_modified = pyqtSignal()

        def __init__(self, doc, parent=None):
            super().__init__(parent)
            self._doc = doc
            # expanded state keyed by flat_start of group
            self._expanded: Dict[int, bool] = {}
            self._display_rows: List[DisplayRow] = []
            self._rebuild_display_rows()

        # ------------------------------------------------------------------
        # Internal helpers
        # ------------------------------------------------------------------

        def _rebuild_display_rows(self) -> None:
            """Recompute _display_rows from self._doc.blocks."""
            blocks = self._doc.blocks
            rows: List[DisplayRow] = []
            i = 0
            while i < len(blocks):
                block = blocks[i]
                if isinstance(block, MouseMoveBlock):
                    # Scan forward to find run length
                    j = i + 1
                    while j < len(blocks) and isinstance(blocks[j], MouseMoveBlock):
                        j += 1
                    run_end = j - 1  # inclusive
                    if run_end > i:
                        # Group of 2+ moves
                        flat_start = i
                        flat_end = run_end
                        expanded = self._expanded.get(flat_start, False)
                        hdr = GroupHeaderRow(flat_start=flat_start, flat_end=flat_end, expanded=expanded)
                        rows.append(hdr)
                        if expanded:
                            for k in range(flat_start, flat_end + 1):
                                rows.append(GroupChildRow(flat_index=k, group_flat_start=flat_start))
                        i = flat_end + 1
                    else:
                        # Lone move block
                        rows.append(BlockRow(flat_index=i))
                        i += 1
                else:
                    rows.append(BlockRow(flat_index=i))
                    i += 1
            self._display_rows = rows

        # ------------------------------------------------------------------
        # QAbstractTableModel interface
        # ------------------------------------------------------------------

        def rowCount(self, parent=QModelIndex()) -> int:
            if parent.isValid():
                return 0
            return len(self._display_rows)

        def columnCount(self, parent=QModelIndex()) -> int:
            if parent.isValid():
                return 0
            return _NUM_COLS

        def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
            if role != Qt.ItemDataRole.DisplayRole:
                return None
            if orientation == Qt.Orientation.Horizontal:
                return ["Type", "Value", "Timestamp", "Extra"][section]
            return str(section + 1)

        def data(self, index, role=Qt.ItemDataRole.DisplayRole):
            if not index.isValid():
                return None
            if role == Qt.ItemDataRole.UserRole:
                return self._display_rows[index.row()]
            if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                return None
            row_obj = self._display_rows[index.row()]
            col = index.column()
            blocks = self._doc.blocks

            if isinstance(row_obj, BlockRow):
                block = blocks[row_obj.flat_index]
                if col == COL_TYPE:
                    return block.type
                if col == COL_VALUE:
                    # EditRole: return raw numeric string for DelayBlock so the
                    # inline editor pre-fills with a bare number, not "0.500s"
                    if role == Qt.ItemDataRole.EditRole and isinstance(block, DelayBlock):
                        return f"{block.duration:.3f}"
                    return _block_value(block)
                if col == COL_TIMESTAMP:
                    return _block_timestamp(block)
                return ""

            if isinstance(row_obj, GroupHeaderRow):
                s, e = row_obj.flat_start, row_obj.flat_end
                count = e - s + 1
                first = blocks[s]
                last = blocks[e]
                if col == COL_TYPE:
                    arrow = "▼" if row_obj.expanded else "▶"
                    return f"{arrow} MouseMove Group"
                if col == COL_VALUE:
                    return f"{count} moves → ({last.x}, {last.y})"  # type: ignore[attr-defined]
                if col == COL_TIMESTAMP:
                    duration = blocks[e].timestamp - blocks[s].timestamp  # type: ignore[attr-defined]
                    return f"{duration:.3f}s"
                if col == COL_EXTRA:
                    return f"({first.x}, {first.y})"  # type: ignore[attr-defined]
                return ""

            if isinstance(row_obj, GroupChildRow):
                block = blocks[row_obj.flat_index]
                if col == COL_TYPE:
                    return "  MouseMove"
                if col == COL_VALUE:
                    return f"({block.x}, {block.y})"  # type: ignore[attr-defined]
                if col == COL_TIMESTAMP:
                    return f"{block.timestamp:.4f}"  # type: ignore[attr-defined]
                return ""

            return None

        def flags(self, index):
            base = (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
            )
            if not index.isValid():
                return Qt.ItemFlag.ItemIsDropEnabled
            row_obj = self._display_rows[index.row()]
            col = index.column()

            if isinstance(row_obj, GroupHeaderRow):
                if col in (COL_TIMESTAMP, COL_VALUE, COL_EXTRA):
                    base |= Qt.ItemFlag.ItemIsEditable
            elif isinstance(row_obj, BlockRow):
                if col in (COL_VALUE, COL_TIMESTAMP):
                    base |= Qt.ItemFlag.ItemIsEditable
            elif isinstance(row_obj, GroupChildRow):
                if col in (COL_VALUE, COL_TIMESTAMP):
                    base |= Qt.ItemFlag.ItemIsEditable

            return base

        def toggle_group(self, display_row_index: int) -> None:
            """Expand or collapse the group at the given display row index."""
            row_obj = self._display_rows[display_row_index]
            assert isinstance(row_obj, GroupHeaderRow)
            self.beginResetModel()
            new_expanded = not row_obj.expanded
            self._expanded[row_obj.flat_start] = new_expanded
            self._rebuild_display_rows()
            self.endResetModel()

        # ------------------------------------------------------------------
        # Drag-and-drop
        # ------------------------------------------------------------------

        def supportedDropActions(self):
            return Qt.DropAction.MoveAction

        def mimeTypes(self):
            return ["application/x-macroblock-rows"]

        def mimeData(self, indexes):
            seen_rows = set()
            parts = []
            for idx in indexes:
                if idx.column() != 0:
                    continue
                r = idx.row()
                if r in seen_rows:
                    continue
                seen_rows.add(r)
                row_obj = self._display_rows[r]
                if isinstance(row_obj, GroupHeaderRow):
                    parts.append(f"{row_obj.flat_start}:{row_obj.flat_end}")
                elif isinstance(row_obj, BlockRow):
                    parts.append(str(row_obj.flat_index))
                elif isinstance(row_obj, GroupChildRow):
                    parts.append(str(row_obj.flat_index))
            mime = QMimeData()
            mime.setData("application/x-macroblock-rows", QByteArray(",".join(parts).encode()))
            return mime

        def dropMimeData(self, data, action, row, column, parent):
            if not data.hasFormat("application/x-macroblock-rows"):
                return False
            raw = bytes(data.data("application/x-macroblock-rows")).decode()
            flat_indices: List[int] = []
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                if ":" in part:
                    s, e = part.split(":")
                    flat_indices.extend(range(int(s), int(e) + 1))
                else:
                    flat_indices.append(int(part))

            blocks = self._doc.blocks
            moving = [blocks[i] for i in flat_indices]
            flat_set = set(flat_indices)
            remaining = [b for i, b in enumerate(blocks) if i not in flat_set]

            # Compute insertion point in remaining list
            if row == -1:
                insert_at = len(remaining)
            else:
                # Map display row to flat index in remaining
                # Count how many flat indices before 'row'th display row were NOT moving
                count_before = 0
                for dr_idx in range(min(row, len(self._display_rows))):
                    dr = self._display_rows[dr_idx]
                    if isinstance(dr, BlockRow) and dr.flat_index not in flat_set:
                        count_before += 1
                    elif isinstance(dr, GroupHeaderRow):
                        for fi in range(dr.flat_start, dr.flat_end + 1):
                            if fi not in flat_set:
                                count_before += 1
                    elif isinstance(dr, GroupChildRow):
                        pass  # counted via group header
                insert_at = min(count_before, len(remaining))

            new_blocks = remaining[:insert_at] + moving + remaining[insert_at:]
            self.beginResetModel()
            self._doc.blocks[:] = new_blocks
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()
            return True

        # ------------------------------------------------------------------
        # Mutations
        # ------------------------------------------------------------------

        def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
            if role != Qt.ItemDataRole.EditRole or not index.isValid():
                return False
            row_obj = self._display_rows[index.row()]
            col = index.column()
            blocks = self._doc.blocks

            try:
                if isinstance(row_obj, GroupHeaderRow):
                    s, e = row_obj.flat_start, row_obj.flat_end
                    if col == COL_TIMESTAMP:
                        _rescale_group_duration(blocks, s, e, float(value))
                    elif col == COL_VALUE:
                        x, y = (int(v.strip()) for v in str(value).split(","))
                        cur_start = (blocks[s].x, blocks[s].y)  # type: ignore[attr-defined]
                        _rescale_group_coords(blocks, s, e, cur_start, (x, y))
                    elif col == COL_EXTRA:
                        x, y = (int(v.strip()) for v in str(value).split(","))
                        cur_end = (blocks[e].x, blocks[e].y)  # type: ignore[attr-defined]
                        _rescale_group_coords(blocks, s, e, (x, y), cur_end)
                    else:
                        return False

                elif isinstance(row_obj, BlockRow):
                    block = blocks[row_obj.flat_index]
                    if col == COL_TIMESTAMP:
                        block.timestamp = float(value)  # type: ignore[attr-defined]
                    elif col == COL_VALUE:
                        _set_block_value(block, str(value))
                    else:
                        return False

                elif isinstance(row_obj, GroupChildRow):
                    block = blocks[row_obj.flat_index]
                    if col == COL_TIMESTAMP:
                        block.timestamp = float(value)  # type: ignore[attr-defined]
                    elif col == COL_VALUE:
                        _set_block_value(block, str(value))
                    else:
                        return False
                else:
                    return False

            except (ValueError, AttributeError):
                return False

            self.beginResetModel()
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()
            return True

        def delete_rows(self, display_row_indices: list) -> None:
            """Delete blocks corresponding to the given display row indices."""
            flat_to_delete: set = set()
            for dr_idx in display_row_indices:
                row_obj = self._display_rows[dr_idx]
                if isinstance(row_obj, BlockRow):
                    flat_to_delete.add(row_obj.flat_index)
                elif isinstance(row_obj, GroupHeaderRow):
                    for fi in range(row_obj.flat_start, row_obj.flat_end + 1):
                        flat_to_delete.add(fi)
                    # Remove expanded state for deleted group
                    self._expanded.pop(row_obj.flat_start, None)
                elif isinstance(row_obj, GroupChildRow):
                    flat_to_delete.add(row_obj.flat_index)

            new_blocks = [b for i, b in enumerate(self._doc.blocks) if i not in flat_to_delete]
            self.beginResetModel()
            self._doc.blocks[:] = new_blocks
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()

        def display_row(self, display_row_index: int) -> "DisplayRow | None":
            """Return the DisplayRow object for a given display row index."""
            if 0 <= display_row_index < len(self._display_rows):
                return self._display_rows[display_row_index]
            return None

        def insert_blocks_at_flat(self, flat_index: int, blocks: list) -> None:
            """Insert a list of blocks after *flat_index* (-1 = append at end)."""
            if flat_index == -1 or flat_index >= len(self._doc.blocks):
                insert_at = len(self._doc.blocks)
            else:
                insert_at = flat_index + 1
            self.beginResetModel()
            self._doc.blocks[insert_at:insert_at] = blocks
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()

        def insert_block(self, after_display_row: int, block: ActionBlock) -> None:
            """Insert block after the given display row (-1 = prepend)."""
            if after_display_row == -1:
                flat_insert = 0
            else:
                row_obj = self._display_rows[after_display_row]
                if isinstance(row_obj, BlockRow):
                    flat_insert = row_obj.flat_index + 1
                elif isinstance(row_obj, GroupHeaderRow):
                    flat_insert = row_obj.flat_end + 1
                elif isinstance(row_obj, GroupChildRow):
                    flat_insert = row_obj.flat_index + 1
                else:
                    flat_insert = len(self._doc.blocks)

            self.beginResetModel()
            self._doc.blocks.insert(flat_insert, block)
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()

        def _display_row_to_flat_indices(self, dr_idx: int) -> List[int]:
            """Return all flat block indices for a given display row."""
            row_obj = self._display_rows[dr_idx]
            if isinstance(row_obj, BlockRow):
                return [row_obj.flat_index]
            if isinstance(row_obj, GroupHeaderRow):
                return list(range(row_obj.flat_start, row_obj.flat_end + 1))
            if isinstance(row_obj, GroupChildRow):
                return [row_obj.flat_index]
            return []

        def move_rows_up(self, display_row_indices: list) -> None:
            """Move selected display rows up by one position in flat block list."""
            if not display_row_indices:
                return
            min_dr = min(display_row_indices)
            if min_dr == 0:
                return

            # Collect flat indices to move
            flat_to_move: set = set()
            for dr_idx in display_row_indices:
                for fi in self._display_row_to_flat_indices(dr_idx):
                    flat_to_move.add(fi)

            # Find the block just above the lowest flat index to move
            min_flat = min(flat_to_move)
            if min_flat == 0:
                return
            pivot = min_flat - 1

            blocks = self._doc.blocks
            new_blocks = list(blocks)
            # Move pivot block after all moving blocks
            moving = [new_blocks[i] for i in sorted(flat_to_move)]
            pivot_block = new_blocks[pivot]
            rest = [b for i, b in enumerate(new_blocks) if i != pivot and i not in flat_to_move]
            insert_pos = pivot
            new_blocks = rest[:insert_pos] + moving + [pivot_block] + rest[insert_pos:]

            self.beginResetModel()
            self._doc.blocks[:] = new_blocks
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()

        def move_rows_down(self, display_row_indices: list) -> None:
            """Move selected display rows down by one position in flat block list."""
            if not display_row_indices:
                return
            max_dr = max(display_row_indices)
            if max_dr == len(self._display_rows) - 1:
                return

            flat_to_move: set = set()
            for dr_idx in display_row_indices:
                for fi in self._display_row_to_flat_indices(dr_idx):
                    flat_to_move.add(fi)

            max_flat = max(flat_to_move)
            blocks = self._doc.blocks
            if max_flat >= len(blocks) - 1:
                return

            pivot = max_flat + 1
            new_blocks = list(blocks)
            moving = [new_blocks[i] for i in sorted(flat_to_move)]
            pivot_block = new_blocks[pivot]
            rest = [b for i, b in enumerate(new_blocks) if i != pivot and i not in flat_to_move]
            # pivot block was after moving; insert moving after where pivot now sits
            # pivot in rest is at index (pivot - len(flat_to_move)) because moving blocks removed
            pivot_in_rest = pivot - len(flat_to_move)
            new_blocks = rest[:pivot_in_rest] + [pivot_block] + moving + rest[pivot_in_rest:]

            self.beginResetModel()
            self._doc.blocks[:] = new_blocks
            self._rebuild_display_rows()
            self.endResetModel()
            self.document_modified.emit()


def _set_block_value(block: ActionBlock, value: str) -> None:
    """Parse value string and update the block's primary value field."""
    if isinstance(block, (MouseMoveBlock, MouseClickBlock, MouseScrollBlock)):
        x, y = (int(v.strip()) for v in value.split(","))
        block.x = x  # type: ignore[attr-defined]
        block.y = y  # type: ignore[attr-defined]
    elif isinstance(block, KeyPressBlock):
        block.key = value
    elif isinstance(block, DelayBlock):
        block.duration = float(value.rstrip("s").strip())
    elif isinstance(block, LabelBlock):
        block.name = value
    elif isinstance(block, GotoBlock):
        block.target = value
