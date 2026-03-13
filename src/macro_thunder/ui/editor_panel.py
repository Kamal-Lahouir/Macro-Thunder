"""EditorPanel — block editor panel using card-based QListView (Phase 3 rework)."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
    QListView, QAbstractItemView, QWidget, QMenu, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QModelIndex

from macro_thunder.models.view_model import (
    BlockTableModel, BlockRow, GroupHeaderRow, GroupChildRow,
    LoopHeaderRow, LoopFooterRow, LoopChildRow,
)
from macro_thunder.models.document import MacroDocument
from macro_thunder.models.blocks import LabelBlock, GotoBlock, WindowFocusBlock, LoopStartBlock
from macro_thunder.ui.block_card_delegate import BlockCardDelegate
from macro_thunder.ui.block_type_dialog import BlockTypeDialog
from macro_thunder.ui.block_panels import LabelPanel, GotoPanel, WindowFocusPanel, LoopStartPanel


class EditorPanel(QFrame):
    """Central block-editor panel: card list view + action toolbar."""

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

        # ── Top editor toolbar ────────────────────────────────────────────
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        toolbar_layout.setSpacing(6)

        self._btn_delete = QPushButton("✕ Delete")
        self._btn_up     = QPushButton("▲ Up")
        self._btn_down   = QPushButton("▼ Down")
        self._btn_record_here = QPushButton("⏺ Record Here")
        self._btn_record_here.setToolTip(
            "Start recording and insert new blocks after the selected row"
        )

        for btn in [self._btn_delete, self._btn_up, self._btn_down]:
            btn.setFixedHeight(30)
        self._btn_record_here.setFixedHeight(30)
        self._btn_record_here.setProperty("role", "record")

        toolbar_layout.addWidget(self._btn_delete)
        toolbar_layout.addWidget(self._btn_up)
        toolbar_layout.addWidget(self._btn_down)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._btn_record_here)

        # ── List view (card-based) ────────────────────────────────────────
        self._table = QListView()          # named _table for API compat
        self._table.setObjectName("StepList")
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._table.setDragDropOverwriteMode(False)
        self._table.setDropIndicatorShown(True)
        self._table.setUniformItemSizes(False)
        self._table.setSpacing(0)

        # Give the scroll area a dark background that matches cards
        self._table.setStyleSheet(
            "QListView { background-color: #0c141a; }"
            "QListView::item { background: transparent; }"
        )

        self._delegate = BlockCardDelegate()
        self._table.setItemDelegate(self._delegate)
        self._delegate.toggle_group_requested.connect(self._on_toggle_group)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

        # ── "Insert Step" button at bottom ────────────────────────────────
        self._btn_add = QPushButton("＋  INSERT STEP")
        self._btn_add.setProperty("role", "add_step")
        self._btn_add.setFixedHeight(52)
        self._btn_add.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Detail panel container ────────────────────────────────────────
        self._detail_container = QWidget()
        self._detail_container.setMaximumHeight(360)
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(12, 0, 12, 0)
        self._detail_container.hide()

        layout.addLayout(toolbar_layout)
        layout.addWidget(self._table, stretch=1)

        # Bottom area: add button + detail panel with padding
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 12)
        bottom_layout.setSpacing(8)
        bottom_layout.addWidget(self._btn_add)
        bottom_layout.addWidget(self._detail_container)
        layout.addWidget(bottom)

        # ── Connections ───────────────────────────────────────────────────
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_up.clicked.connect(self._on_move_up)
        self._btn_down.clicked.connect(self._on_move_down)
        self._btn_add.clicked.connect(self._on_add_block)
        self._btn_record_here.clicked.connect(self._on_record_here)

        self._update_button_state()

    # ── Public API ────────────────────────────────────────────────────────

    def load_document(self, doc: MacroDocument) -> None:
        self._clear_detail_panel()
        self._model = BlockTableModel(doc)
        self._model.document_modified.connect(self.document_modified)
        self._table.setModel(self._model)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._update_button_state()

    def get_selected_flat_index(self) -> int:
        return self._selected_flat_end_index()

    def select_flat_index(self, flat_index: int) -> None:
        if self._model is None:
            return
        for dr in range(self._model.rowCount()):
            row_obj = self._model.display_row(dr)
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                idx = self._model.index(dr, 0)
                self._table.setCurrentIndex(idx)
                self._table.scrollTo(idx)
                return

    def get_playback_row(self) -> int:
        if self._model is None:
            return -1
        return self._model._playback_flat_index

    def set_playback_row(self, flat_index: int) -> None:
        if self._model is None:
            return
        self._model.set_playback_flat_index(flat_index)
        for dr in range(self._model.rowCount()):
            row_obj = self._model.display_row(dr)
            match = False
            if isinstance(row_obj, BlockRow) and row_obj.flat_index == flat_index:
                match = True
            elif isinstance(row_obj, GroupHeaderRow) and row_obj.flat_start <= flat_index <= row_obj.flat_end:
                match = True
            elif isinstance(row_obj, (GroupChildRow, LoopChildRow, LoopHeaderRow, LoopFooterRow)):
                if row_obj.flat_index == flat_index:
                    match = True
            if match:
                self._table.scrollTo(self._model.index(dr, 0))
                return

    def clear_playback_row(self) -> None:
        if self._model is not None:
            self._model.clear_playback_flat_index()

    def insert_blocks_at(self, flat_index: int, blocks: list) -> None:
        if self._model is None:
            return
        self._model.insert_blocks_at_flat(flat_index, blocks)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _selected_display_rows(self) -> list[int]:
        sm = self._table.selectionModel()
        if sm is None:
            return []
        return sorted({idx.row() for idx in sm.selectedIndexes()})

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

    def _on_double_click(self, index: QModelIndex) -> None:
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
        wrap_action = menu.addAction("Wrap selection in Loop")
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == wrap_action:
            self._wrap_selection_in_loop()

    def _wrap_selection_in_loop(self) -> None:
        if self._model is None:
            return
        selected_rows = self._selected_display_rows()
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
        enabled = self._model is not None
        for btn in [self._btn_delete, self._btn_up, self._btn_down, self._btn_add]:
            btn.setEnabled(enabled)
        self._btn_record_here.setEnabled(True)
