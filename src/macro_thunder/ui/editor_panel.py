"""EditorPanel — full block editor panel for Phase 3.

Provides a QTableView backed by BlockTableModel with a toolbar containing
Delete, Move Up, Move Down, and Add Block buttons.  BlockDelegate handles
group row expand/collapse.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QAbstractItemView, QWidget,
)
from PyQt6.QtCore import pyqtSignal

from macro_thunder.models.view_model import BlockTableModel, BlockRow, GroupHeaderRow, GroupChildRow
from macro_thunder.models.document import MacroDocument
from macro_thunder.models.blocks import LabelBlock, GotoBlock, WindowFocusBlock
from macro_thunder.ui.block_delegate import BlockDelegate
from macro_thunder.ui.block_type_dialog import BlockTypeDialog
from macro_thunder.ui.block_panels import LabelPanel, GotoPanel, WindowFocusPanel


class EditorPanel(QFrame):
    """Central block-editor panel: table view + toolbar."""

    document_modified = pyqtSignal()  # forwarded from BlockTableModel
    record_here_requested = pyqtSignal(int)  # flat block index to insert after (-1 = end)

    def __init__(self, picker_service=None, parent=None):
        super().__init__(parent)
        self._model: BlockTableModel | None = None
        self._picker_service = picker_service
        self._detail_widget: QWidget | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Toolbar row ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(4, 4, 4, 0)

        self._btn_delete = QPushButton("Delete")
        self._btn_up = QPushButton("\u25b2 Up")
        self._btn_down = QPushButton("\u25bc Down")
        self._btn_add = QPushButton("+ Add Block")
        self._btn_record_here = QPushButton("\u23fa Record Here")
        self._btn_record_here.setToolTip("Start recording and insert new blocks after the selected row")

        toolbar_layout.addWidget(self._btn_delete)
        toolbar_layout.addWidget(self._btn_up)
        toolbar_layout.addWidget(self._btn_down)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._btn_record_here)
        toolbar_layout.addWidget(self._btn_add)

        # --- Table view ---
        self._table = QTableView()
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._table.setDragDropOverwriteMode(False)
        self._table.setDropIndicatorShown(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        self._delegate = BlockDelegate()
        self._table.setItemDelegate(self._delegate)
        self._delegate.toggle_group_requested.connect(self._on_toggle_group)

        layout.addLayout(toolbar_layout)
        layout.addWidget(self._table)

        # --- Detail panel container (shown below table on single block selection) ---
        self._detail_container = QWidget()
        self._detail_container.setMaximumHeight(360)
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_container.hide()
        layout.addWidget(self._detail_container)

        # --- Button connections ---
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_up.clicked.connect(self._on_move_up)
        self._btn_down.clicked.connect(self._on_move_down)
        self._btn_add.clicked.connect(self._on_add_block)
        self._btn_record_here.clicked.connect(self._on_record_here)

        self._update_button_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_document(self, doc: MacroDocument) -> None:
        """Replace the current model with one built from *doc*."""
        self._clear_detail_panel()
        self._model = BlockTableModel(doc)
        self._model.document_modified.connect(self.document_modified)
        self._table.setModel(self._model)
        self._table.setColumnWidth(0, 200)
        self._table.setColumnWidth(1, 250)
        self._table.setColumnWidth(2, 100)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._update_button_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _selected_display_rows(self) -> list[int]:
        indexes = self._table.selectionModel().selectedRows()
        return sorted({idx.row() for idx in indexes})

    def _on_toggle_group(self, display_row_index: int) -> None:
        if self._model:
            self._model.toggle_group(display_row_index)

    def _on_delete(self) -> None:
        if self._model is None:
            return
        rows = self._selected_display_rows()
        if not rows:
            return
        self._clear_detail_panel()
        self._table.clearSelection()
        self._model.delete_rows(rows)

    def _on_move_up(self) -> None:
        if self._model is None:
            return
        rows = self._selected_display_rows()
        if not rows:
            return
        self._clear_detail_panel()
        self._model.move_rows_up(rows)

    def _on_move_down(self) -> None:
        if self._model is None:
            return
        rows = self._selected_display_rows()
        if not rows:
            return
        self._clear_detail_panel()
        self._model.move_rows_down(rows)

    def _on_add_block(self) -> None:
        if self._model is None:
            return
        block = BlockTypeDialog.get_block(self)
        if block is None:
            return
        self._clear_detail_panel()
        rows = self._selected_display_rows()
        after = rows[-1] if rows else (self._model.rowCount() - 1)
        self._model.insert_block(after, block)

    def _on_record_here(self) -> None:
        """Emit record_here_requested with the flat index after current selection."""
        flat_index = self._selected_flat_end_index()
        self.record_here_requested.emit(flat_index)

    def get_selected_flat_index(self) -> int:
        """Return flat block index of the last selected row, or -1 (append at end).

        Public API used by MainWindow for Record Here hotkey.
        """
        return self._selected_flat_end_index()

    def _selected_flat_end_index(self) -> int:
        """Return flat block index of the last selected row, or -1 (append at end)."""
        if self._model is None:
            return -1
        rows = self._selected_display_rows()
        if not rows:
            return -1
        last_display = rows[-1]
        row_obj = self._model.display_row(last_display)
        if row_obj is None:
            return -1
        if isinstance(row_obj, BlockRow):
            return row_obj.flat_index
        if isinstance(row_obj, GroupHeaderRow):
            return row_obj.flat_end
        if isinstance(row_obj, GroupChildRow):
            return row_obj.flat_index
        return -1

    def select_flat_index(self, flat_index: int) -> None:
        """Select the display row corresponding to flat_index."""
        if self._model is None:
            return
        for display_row in range(self._model.rowCount()):
            row_obj = self._model.display_row(display_row)
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                self._table.selectRow(display_row)
                self._table.scrollTo(self._model.index(display_row, 0))
                return

    def get_playback_row(self) -> int:
        """Return the current amber playback cursor flat index, or -1 if none."""
        if self._model is None:
            return -1
        return self._model._playback_flat_index

    def set_playback_row(self, flat_index: int) -> None:
        """Highlight flat_index with the amber playback cursor and scroll to it."""
        if self._model is None:
            return
        self._model.set_playback_flat_index(flat_index)
        for display_row in range(self._model.rowCount()):
            from macro_thunder.models.view_model import BlockRow
            row_obj = self._model.display_row(display_row)
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                self._table.scrollTo(self._model.index(display_row, 0))
                return

    def clear_playback_row(self) -> None:
        """Remove the amber playback cursor highlight."""
        if self._model is not None:
            self._model.clear_playback_flat_index()

    def insert_blocks_at(self, flat_index: int, blocks: list) -> None:
        """Insert *blocks* after *flat_index* in the current model.

        flat_index == -1 means append at end.
        No-op if no document is loaded.
        """
        if self._model is None:
            return
        self._model.insert_blocks_at_flat(flat_index, blocks)

    def _on_selection_changed(self, *_):
        """Show/hide detail panel based on selected block type."""
        # User explicitly picked a row — clear amber so play starts from here
        self.clear_playback_row()
        self._clear_detail_panel()
        if self._model is None:
            return
        rows = self._selected_display_rows()
        if len(rows) != 1:
            return  # only show panel for single selection
        row_obj = self._model.display_row(rows[0])
        if row_obj is None or not isinstance(row_obj, BlockRow):
            return  # groups/headers: no detail panel
        block = self._model._doc.blocks[row_obj.flat_index]
        panel = None
        if isinstance(block, LabelBlock):
            panel = LabelPanel(block, self._emit_modified)
        elif isinstance(block, GotoBlock):
            panel = GotoPanel(block, self._emit_modified)
        elif isinstance(block, WindowFocusBlock):
            panel = WindowFocusPanel(block, self._emit_modified, self._picker_service)
        if panel is not None:
            self._detail_layout.addWidget(panel)
            self._detail_widget = panel
            self._detail_container.show()

    def _emit_modified(self):
        """Called by panels when a block field changes."""
        self.document_modified.emit()

    def _clear_detail_panel(self):
        if self._detail_widget is not None:
            self._detail_layout.removeWidget(self._detail_widget)
            self._detail_widget.deleteLater()
            self._detail_widget = None
        self._detail_container.hide()

    def _update_button_state(self) -> None:
        enabled = self._model is not None
        for btn in [self._btn_delete, self._btn_up, self._btn_down, self._btn_add]:
            btn.setEnabled(enabled)
        # Record Here is always available (inserts at end when nothing loaded too)
        self._btn_record_here.setEnabled(True)
