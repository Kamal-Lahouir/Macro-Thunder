"""BlockCardDelegate — paints each block row as a styled card."""
from __future__ import annotations

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QSize, QRect, QEvent, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QFontMetrics, QPainterPath

from macro_thunder.models.view_model import (
    BlockRow, GroupHeaderRow, GroupChildRow,
    LoopHeaderRow, LoopFooterRow, LoopChildRow,
    COL_ID, COL_TYPE, COL_VALUE, COL_TIMESTAMP,
)

_BG_CARD       = QColor("#0e1520")
_BG_SELECTED   = QColor("#1a3a50")
_BORDER        = QColor("#1e2d37")
_BORDER_SEL    = QColor("#25aff4")
_TEXT          = QColor("#e2e8f0")
_TEXT_MUTED    = QColor("#64748b")
_TEXT_DIM      = QColor("#2a3d4d")
_PRIMARY       = QColor("#25aff4")
_AMBER         = QColor("#f59e0b")
_AMBER_BG      = QColor(80, 55, 10)
_AMBER_BORDER  = QColor("#d97706")
_TEAL          = QColor("#0d9488")
_TEAL_BG       = QColor(13, 30, 28)

_CARD_H  = 70
_CHILD_H = 46
_LOOP_H  = 54
_R       = 8       # corner radius
_ICON_SZ = 32
_M       = 8       # outer horizontal margin

# block type → (hex_color, icon_char)
_TYPE_MAP: dict[str, tuple[str, str]] = {
    "mousemove":    ("#8b5cf6", "↗"),
    "mouseclick":   ("#3b82f6", "⊙"),
    "mousescroll":  ("#10b981", "⇅"),
    "keypress":     ("#25aff4", "⌨"),
    "delay":        ("#f59e0b", "⏱"),
    "windowfocus":  ("#ec4899", "⊞"),
    "label":        ("#6366f1", "⚑"),
    "goto":         ("#6366f1", "→"),
    "loopstart":    ("#0d9488", "↻"),
    "loopend":      ("#0d9488", "↲"),
    "group":        ("#8b5cf6", "↗"),
}


def _icon_for(type_text: str) -> tuple[str, str]:
    tl = type_text.lower().replace(" ", "").replace("▼", "").replace("▶", "").strip()
    for key, val in _TYPE_MAP.items():
        if key in tl:
            return val[1], val[0]
    return "•", "#64748b"


def _draw_rounded_rect(painter: QPainter, rect: QRect, radius: int,
                       fill: QColor, border: QColor) -> None:
    path = QPainterPath()
    path.addRoundedRect(float(rect.x()), float(rect.y()),
                        float(rect.width()), float(rect.height()),
                        radius, radius)
    painter.fillPath(path, fill)
    pen = QPen(border, 1)
    painter.setPen(pen)
    painter.drawPath(path)


class BlockCardDelegate(QStyledItemDelegate):
    """Paints each display row as a card with icon, title, and value pills."""

    toggle_group_requested = pyqtSignal(int)

    # ── Size hint ─────────────────────────────────────────────────────────

    def sizeHint(self, option, index) -> QSize:
        row_obj = index.data(Qt.ItemDataRole.UserRole)
        if isinstance(row_obj, GroupChildRow):
            h = _CHILD_H
        elif isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow)):
            h = _LOOP_H
        else:
            h = _CARD_H
        return QSize(option.rect.width(), h + 6)

    # ── Paint ─────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        row_obj  = index.data(Qt.ItemDataRole.UserRole)
        model    = index.model()
        r        = index.row()

        step_id  = model.data(model.index(r, COL_ID),        Qt.ItemDataRole.DisplayRole) or ""
        type_txt = model.data(model.index(r, COL_TYPE),      Qt.ItemDataRole.DisplayRole) or ""
        val_txt  = model.data(model.index(r, COL_VALUE),     Qt.ItemDataRole.DisplayRole) or ""
        ts_txt   = model.data(model.index(r, COL_TIMESTAMP), Qt.ItemDataRole.DisplayRole) or ""

        bg_brush    = model.data(index, Qt.ItemDataRole.BackgroundRole)
        is_amber    = bg_brush is not None and bg_brush.color() == _AMBER
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        full = option.rect
        card = QRect(full.left() + _M, full.top() + 3,
                     full.width() - 2 * _M, full.height() - 6)

        # ── Background ────────────────────────────────────────────────────
        is_loop = isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow))
        if is_amber:
            bg, border = _AMBER_BG, _AMBER_BORDER
        elif is_selected:
            bg, border = _BG_SELECTED, _BORDER_SEL
        elif is_loop:
            bg, border = _TEAL_BG, _TEAL
        else:
            bg, border = _BG_CARD, _BORDER

        _draw_rounded_rect(painter, card, _R, bg, border)

        # ── Left accent bar for playback ──────────────────────────────────
        if is_amber:
            accent = QRect(card.left(), card.top() + 10, 4, card.height() - 20)
            ap = QPainterPath()
            ap.addRoundedRect(float(accent.x()), float(accent.y()),
                              float(accent.width()), float(accent.height()), 2, 2)
            painter.fillPath(ap, _AMBER)

        # ── Content x cursor ─────────────────────────────────────────────
        cx = card.left() + 10

        # Step ID
        id_font = QFont("Segoe UI", 8, QFont.Weight.Medium)
        painter.setFont(id_font)
        painter.setPen(_TEXT_DIM if not is_amber else QColor("#a16207"))
        id_rect = QRect(cx, card.top(), 24, card.height())
        painter.drawText(id_rect,
                         Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                         step_id.zfill(2))
        cx += 30

        # Icon circle
        icon_char, icon_hex = _icon_for(type_txt)
        if is_loop:
            icon_hex = "#0d9488"
        icon_rect = QRect(cx,
                          card.top() + (card.height() - _ICON_SZ) // 2,
                          _ICON_SZ, _ICON_SZ)
        ic_bg = QColor(icon_hex)
        ic_bg.setAlpha(35)
        _draw_rounded_rect(painter, icon_rect, 8, ic_bg, QColor(0, 0, 0, 0))
        ic_font = QFont("Segoe UI", 14)
        painter.setFont(ic_font)
        painter.setPen(QColor(icon_hex))
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, icon_char)
        cx += _ICON_SZ + 10

        # Title
        title = _title(type_txt, row_obj)
        title_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(_TEXT if not is_amber else QColor("#fbbf24"))
        title_y = card.top() + 10 if val_txt else card.top() + (card.height() - 16) // 2
        title_rect = QRect(cx, title_y, card.right() - 28 - cx, 18)
        painter.drawText(title_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         title)

        # Value pills
        if val_txt:
            pills = _make_pills(val_txt, ts_txt)
            _draw_pills(painter, cx, card.top() + 32, card.right() - 28, pills)

        # Group expand/collapse arrow
        if isinstance(row_obj, GroupHeaderRow):
            arrow = "▼" if row_obj.expanded else "▶"
            af = QFont("Segoe UI", 9)
            painter.setFont(af)
            painter.setPen(_TEXT_MUTED)
            painter.drawText(
                QRect(card.right() - 28, card.top(), 24, card.height()),
                Qt.AlignmentFlag.AlignCenter, arrow,
            )

        painter.restore()

    # ── Editor events ─────────────────────────────────────────────────────

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            row_obj = index.data(Qt.ItemDataRole.UserRole)
            if isinstance(row_obj, GroupHeaderRow):
                self.toggle_group_requested.emit(index.row())
                return True
        return super().editorEvent(event, model, option, index)


# ── Module helpers ────────────────────────────────────────────────────────

def _title(type_txt: str, row_obj) -> str:
    if isinstance(row_obj, GroupHeaderRow):
        return "Mouse Move Group"
    if isinstance(row_obj, GroupChildRow):
        return "  Move"
    return type_txt.lstrip("▼▶ ").strip()


def _make_pills(val_txt: str, ts_txt: str) -> list[str]:
    pills = []
    if val_txt:
        pills.append(val_txt)
    if ts_txt:
        pills.append(f"⏱ {ts_txt}s")
    return pills


def _draw_pills(painter: QPainter, x: int, y: int, max_x: int, pills: list[str]) -> None:
    pill_font = QFont("Segoe UI", 8)
    painter.setFont(pill_font)
    fm = QFontMetrics(pill_font)
    for pill in pills:
        pw = fm.horizontalAdvance(pill) + 14
        if x + pw > max_x:
            break
        pr = QRect(x, y, pw, 16)
        pp = QPainterPath()
        pp.addRoundedRect(float(pr.x()), float(pr.y()),
                          float(pr.width()), float(pr.height()), 4, 4)
        painter.fillPath(pp, QColor("#0c141a"))
        painter.setPen(QPen(QColor("#1e2d37"), 1))
        painter.drawPath(pp)
        painter.setPen(_TEXT_MUTED)
        painter.drawText(pr, Qt.AlignmentFlag.AlignCenter, pill)
        x += pw + 4
