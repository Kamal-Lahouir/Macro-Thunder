"""EditorPanel — block editor panel with QTableView + card-style delegate."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout,
    QTableView, QAbstractItemView, QWidget, QMenu, QHeaderView, QProgressBar,
)
from PyQt6.QtCore import pyqtSignal, Qt

from macro_thunder.models.view_model import (
    BlockTableModel, BlockRow, GroupHeaderRow, GroupChildRow,
    LoopHeaderRow, LoopFooterRow, LoopChildRow,
)
from macro_thunder.models.document import MacroDocument
from macro_thunder.models.blocks import LabelBlock, GotoBlock, WindowFocusBlock, LoopStartBlock
from macro_thunder.ui.block_delegate import BlockDelegate
from macro_thunder.ui.block_type_dialog import BlockTypeDialog
from macro_thunder.ui.block_panels import LabelPanel, GotoPanel, WindowFocusPanel, LoopStartPanel


class EditorPanel(QFrame):
    """Central block-editor panel: table view + toolbar."""

    document_modified     = pyqtSignal()
    record_here_requested = pyqtSignal(int)

    def __init__(self, picker_service=None, parent=None):
        super().__init__(parent)
        self._model: BlockTableModel | None = None
        self._picker_service = picker_service
        self._detail_widget: QWidget | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Table view ────────────────────────────────────────────────────
        self._table = QTableView()
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._table.setDragDropOverwriteMode(False)
        self._table.setDropIndicatorShown(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(False)
        # Compact rows so many are visible at once
        self._table.verticalHeader().setDefaultSectionSize(26)
        self._table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )

        self._delegate = BlockDelegate()
        self._table.setItemDelegate(self._delegate)
        self._delegate.toggle_group_requested.connect(self._on_toggle_group)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

        # ── Detail panel container ────────────────────────────────────────
        self._detail_container = QWidget()
        self._detail_container.setMaximumHeight(360)
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(12, 0, 12, 0)
        self._detail_container.hide()

        # ── Progress bar ──────────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("Step %v / %m")
        self._progress_bar.setFixedHeight(18)
        self._progress_bar.hide()

        layout.addWidget(self._table, stretch=1)
        layout.addWidget(self._detail_container)
        layout.addWidget(self._progress_bar)

        self._update_button_state()

    # ── Public API ────────────────────────────────────────────────────────

    def load_document(self, doc: MacroDocument) -> None:
        self._clear_detail_panel()
        self._model = BlockTableModel(doc)
        self._model.document_modified.connect(self.document_modified)
        self._table.setModel(self._model)
        self._table.setColumnWidth(0, 40)    # ID
        self._table.setColumnWidth(1, 190)   # Type
        self._table.setColumnWidth(2, 240)   # Value
        self._table.setColumnWidth(3, 90)    # Timestamp
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._update_button_state()

    # ── Public action API (called from ribbon) ────────────────────────────

    def delete_selected(self) -> None:
        self._on_delete()

    def move_up(self) -> None:
        self._on_move_up()

    def move_down(self) -> None:
        self._on_move_down()

    def add_block(self) -> None:
        self._on_add_block()

    def edit_selected(self) -> None:
        rows = self._selected_display_rows()
        if not rows or self._model is None:
            return
        row_obj = self._model.display_row(rows[0])
        if isinstance(row_obj, (GroupHeaderRow, LoopFooterRow)):
            return
        if isinstance(row_obj, BlockRow):
            flat_index = row_obj.flat_index
        elif isinstance(row_obj, (LoopHeaderRow, LoopChildRow, GroupChildRow)):
            flat_index = row_obj.flat_index
        else:
            return
        block = self._model._doc.blocks[flat_index]
        from macro_thunder.ui.block_edit_dialog import open_edit_dialog
        confirmed = open_edit_dialog(block, self._model._doc.blocks, self)
        if confirmed:
            self._model.beginResetModel()
            self._model._rebuild_display_rows()
            self._model.endResetModel()
            self._model.document_modified.emit()
            self.document_modified.emit()

    def record_here(self) -> None:
        self._on_record_here()

    def get_selected_flat_index(self) -> int:
        return self._selected_flat_end_index()

    def select_flat_index(self, flat_index: int) -> None:
        if self._model is None:
            return
        for display_row in range(self._model.rowCount()):
            row_obj = self._model.display_row(display_row)
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                self._table.selectRow(display_row)
                self._table.scrollTo(self._model.index(display_row, 0))
                return

    def get_playback_row(self) -> int:
        if self._model is None:
            return -1
        return self._model._playback_flat_index

    def set_playback_row(self, flat_index: int) -> None:
        if self._model is None:
            return
        self._model.set_playback_flat_index(flat_index)
        for display_row in range(self._model.rowCount()):
            row_obj = self._model.display_row(display_row)
            match = False
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                match = True
            elif (isinstance(row_obj, GroupHeaderRow)
                  and row_obj.flat_start <= flat_index <= row_obj.flat_end):
                match = True
            elif isinstance(row_obj, (GroupChildRow, LoopChildRow,
                                       LoopHeaderRow, LoopFooterRow)):
                if row_obj.flat_index == flat_index:
                    match = True
            if match:
                self._table.scrollTo(self._model.index(display_row, 0))
                return

    def clear_playback_row(self) -> None:
        if self._model is not None:
            self._model.clear_playback_flat_index()
        self._progress_bar.hide()

    def set_progress(self, index: int, total: int) -> None:
        if total > 0:
            self._progress_bar.setRange(0, total)
            self._progress_bar.setValue(index)
            self._progress_bar.show()
        else:
            self._progress_bar.hide()

    def insert_blocks_at(self, flat_index: int, blocks: list) -> None:
        if self._model is None:
            return
        self._model.insert_blocks_at_flat(flat_index, blocks)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _selected_display_rows(self) -> list[int]:
        indexes = self._table.selectionModel().selectedRows()
        return sorted({idx.row() for idx in indexes})

    def _selected_flat_end_index(self) -> int:
        if self._model is None:
            return -1
        rows = self._selected_display_rows()
        if not rows:
            return -1
        row_obj = self._model.display_row(rows[-1])
        if row_obj is None:
            return -1
        if isinstance(row_obj, BlockRow):
            return row_obj.flat_index
        if isinstance(row_obj, GroupHeaderRow):
            return row_obj.flat_end
        if isinstance(row_obj, GroupChildRow):
            return row_obj.flat_index
        if isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow)):
            return row_obj.flat_index
        return -1

    def _on_double_click(self, index) -> None:
        if self._model is None:
            return
        row_obj = self._model.display_row(index.row())
        if row_obj is None:
            return
        if isinstance(row_obj, (GroupHeaderRow, LoopFooterRow)):
            return
        if isinstance(row_obj, BlockRow):
            flat_index = row_obj.flat_index
        elif isinstance(row_obj, (LoopHeaderRow, LoopChildRow, GroupChildRow)):
            flat_index = row_obj.flat_index
        else:
            return
        block = self._model._doc.blocks[flat_index]
        from macro_thunder.ui.block_edit_dialog import open_edit_dialog
        confirmed = open_edit_dialog(block, self._model._doc.blocks, self)
        if confirmed:
            self._model.beginResetModel()
            self._model._rebuild_display_rows()
            self._model.endResetModel()
            self._model.document_modified.emit()
            self.document_modified.emit()

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
        flat_index = self._selected_flat_end_index()
        self.record_here_requested.emit(flat_index)

    def _on_context_menu(self, pos) -> None:
        menu = QMenu(self)
        index = self._table.indexAt(pos)
        toggle_action = None
        if index.isValid() and self._model is not None:
            row_obj = self._model.display_row(index.row())
            if isinstance(row_obj, GroupHeaderRow):
                label = "Collapse group" if row_obj.expanded else "Expand group"
                toggle_action = menu.addAction(label)
                menu.addSeparator()
        wrap_action = menu.addAction("Wrap selection in Loop")
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == toggle_action and toggle_action is not None:
            self._on_toggle_group(index.row())
        elif action == wrap_action:
            self._wrap_selection_in_loop()

    def _wrap_selection_in_loop(self) -> None:
        if self._model is None:
            return
        selected_rows = [idx.row() for idx in self._table.selectedIndexes()
                         if idx.column() == 0]
        if not selected_rows:
            return
        flat_indices: list[int] = []
        for dr_idx in selected_rows:
            flat_indices.extend(self._model._display_row_to_flat_indices(dr_idx))
        if flat_indices:
            self._model.wrap_in_loop(flat_indices)

    def _on_selection_changed(self, *_):
        self.clear_playback_row()
        self._clear_detail_panel()
        if self._model is None:
            return
        rows = self._selected_display_rows()
        if len(rows) != 1:
            return
        row_obj = self._model.display_row(rows[0])
        if row_obj is None:
            return
        panel = None
        if isinstance(row_obj, LoopHeaderRow):
            block = self._model._doc.blocks[row_obj.flat_index]
            panel = LoopStartPanel(block, self._emit_modified)
        elif isinstance(row_obj, (LoopFooterRow, LoopChildRow, GroupHeaderRow, GroupChildRow)):
            return
        elif isinstance(row_obj, BlockRow):
            block = self._model._doc.blocks[row_obj.flat_index]
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
        self.document_modified.emit()

    def _clear_detail_panel(self):
        if self._detail_widget is not None:
            self._detail_layout.removeWidget(self._detail_widget)
            self._detail_widget.deleteLater()
            self._detail_widget = None
        self._detail_container.hide()

    def _update_button_state(self) -> None:
        pass  # buttons now live in the ribbon
