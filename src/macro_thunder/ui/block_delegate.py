"""BlockDelegate — custom item delegate for the block editor table.

Responsibilities:
- Detect clicks in COL_TYPE column on GroupHeaderRow rows
- Emit toggle_group_requested(display_row_index) to trigger expand/collapse
- Paint amber background for the active playback row (overrides stylesheet)
"""
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QColor, QPainter

from macro_thunder.models.view_model import GroupHeaderRow, COL_TYPE

_AMBER = QColor(210, 160, 0)
_AMBER_TEXT = QColor(20, 20, 20)  # dark text on amber for readability


class BlockDelegate(QStyledItemDelegate):
    """Item delegate that intercepts toggle clicks on GroupHeaderRow cells."""

    toggle_group_requested = pyqtSignal(int)  # display_row_index

    def paint(self, painter: QPainter, option, index) -> None:
        bg = index.data(Qt.ItemDataRole.BackgroundRole)
        if bg is not None and bg.color() == _AMBER:
            # Fill the entire cell with amber, bypassing any stylesheet
            painter.fillRect(option.rect, _AMBER)
            # Draw selection indicator on top if selected
            if option.state & QStyle.StateFlag.State_Selected:
                highlight = QColor(_AMBER)
                highlight.setAlpha(80)
                painter.fillRect(option.rect, highlight)
            # Draw text in dark color for contrast
            text = index.data(Qt.ItemDataRole.DisplayRole)
            if text:
                old_pen = painter.pen()
                painter.setPen(_AMBER_TEXT)
                painter.drawText(
                    option.rect.adjusted(4, 0, -4, 0),
                    Qt.AlignmentFlag.AlignVCenter,
                    str(text),
                )
                painter.setPen(old_pen)
            return
        super().paint(painter, option, index)

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
