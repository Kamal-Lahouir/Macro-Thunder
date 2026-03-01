"""BlockDelegate — custom item delegate for the block editor table.

Responsibilities:
- Detect clicks in COL_TYPE column on GroupHeaderRow rows
- Emit toggle_group_requested(display_row_index) to trigger expand/collapse
- No custom paint override: ▶/▼ arrows are already returned by BlockTableModel.data()
"""
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QEvent, pyqtSignal

from macro_thunder.models.view_model import GroupHeaderRow, COL_TYPE


class BlockDelegate(QStyledItemDelegate):
    """Item delegate that intercepts toggle clicks on GroupHeaderRow cells."""

    toggle_group_requested = pyqtSignal(int)  # display_row_index

    def editorEvent(self, event, model, option, index):
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and index.column() == COL_TYPE
        ):
            row_data = model.data(index, Qt.ItemDataRole.UserRole)
            if isinstance(row_data, GroupHeaderRow):
                self.toggle_group_requested.emit(index.row())
                return True  # consume event, don't start editor
        return super().editorEvent(event, model, option, index)
