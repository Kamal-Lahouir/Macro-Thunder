"""LibraryPanel — redesigned left sidebar macro library."""
from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QPushButton, QInputDialog, QStyledItemDelegate, QStyle, QWidget,
)

_EXCLUDED = {"settings.json", "library_state.json"}

_PIN_COLOR = "#f0a500"
_PRIMARY   = "#25aff4"
_TEXT      = "#e2e8f0"
_MUTED     = "#64748b"
_BORDER    = "#1e2d37"
_HOVER     = "#1a2a34"
_SEL_BG    = "#1a3a50"
_SEL_BOR   = "#25aff4"


class _LibraryItemDelegate(QStyledItemDelegate):
    """Paints each library item as a mini card: icon + name + step count."""

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), 54)

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_sel = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)

        rect = option.rect.adjusted(4, 3, -4, -3)

        # Background
        if is_sel:
            bg, bord = QColor(_SEL_BG), QColor(_SEL_BOR)
        elif is_hover:
            bg, bord = QColor(_HOVER), QColor(_BORDER)
        else:
            bg, bord = QColor("#0e1520"), QColor(_BORDER)

        path = QPainterPath()
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                            float(rect.width()), float(rect.height()), 8, 8)
        painter.fillPath(path, bg)
        painter.setPen(QPen(bord, 1))
        painter.drawPath(path)

        # Folder icon circle
        icon_rect_x = rect.left() + 10
        icon_rect_y = rect.top() + (rect.height() - 28) // 2
        icon_r = QPainterPath()
        icon_r.addRoundedRect(float(icon_rect_x), float(icon_rect_y), 28.0, 28.0, 6, 6)
        ic_bg = QColor(_PRIMARY if is_sel else "#1e2d37")
        ic_bg.setAlpha(60 if is_sel else 180)
        painter.fillPath(icon_r, ic_bg)
        icon_font = QFont("Segoe UI", 13)
        painter.setFont(icon_font)
        painter.setPen(QColor(_PRIMARY if is_sel else _MUTED))
        painter.drawText(
            icon_rect_x, icon_rect_y, 28, 28,
            Qt.AlignmentFlag.AlignCenter, "▶"
        )

        cx = icon_rect_x + 36

        # Name
        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        name_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QColor(_TEXT if is_sel else _TEXT))
        painter.drawText(cx, rect.top() + 8, rect.right() - cx - 8, 18,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         name)

        # Sub-label (pinned or blank)
        is_pinned = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        sub = "Pinned" if is_pinned else ""
        sub_font = QFont("Segoe UI", 8)
        painter.setFont(sub_font)
        painter.setPen(QColor(_PIN_COLOR if is_pinned else _MUTED))
        painter.drawText(cx, rect.top() + 28, rect.right() - cx - 8, 14,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         sub)

        painter.restore()


class LibraryPanel(QFrame):
    """Left-sidebar macro library panel — redesigned."""

    load_requested = pyqtSignal(str)
    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dirty: bool = False
        self._pinned: list[str] = []
        self._order: list[str] = []

        self.setMinimumWidth(200)
        self.setMaximumWidth(320)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top section ───────────────────────────────────────────────────
        top = QWidget()
        top.setStyleSheet("background-color: #0a1218; border-bottom: 1px solid #1e2d37;")
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.setSpacing(8)

        # App icon + name row
        brand_row = QHBoxLayout()
        brand_lbl = QLabel("⚡  Macro Engine")
        brand_lbl.setStyleSheet(
            "color: #25aff4; font-weight: 700; font-size: 13px; background: transparent;"
        )
        brand_row.addWidget(brand_lbl)
        brand_row.addStretch()
        top_layout.addLayout(brand_row)

        # New Macro button
        self._btn_new = QPushButton("＋  New Macro")
        self._btn_new.setProperty("role", "new_macro")
        self._btn_new.setFixedHeight(36)
        self._btn_new.clicked.connect(self._on_new_macro)
        top_layout.addWidget(self._btn_new)

        # Search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search library...")
        self._search_box.setStyleSheet(
            "background-color: #0c141a; border: 1px solid #1e2d37; border-radius: 8px;"
            "color: #e2e8f0; padding: 6px 10px; font-size: 12px;"
        )
        self._search_box.textChanged.connect(self._on_search)
        top_layout.addWidget(self._search_box)

        root.addWidget(top)

        # ── Library list ──────────────────────────────────────────────────
        mid = QWidget()
        mid_layout = QVBoxLayout(mid)
        mid_layout.setContentsMargins(8, 8, 8, 0)
        mid_layout.setSpacing(4)

        section_lbl = QLabel("LIBRARY")
        section_lbl.setStyleSheet(
            "color: #64748b; font-size: 10px; font-weight: 700; "
            "letter-spacing: 1.5px; background: transparent; padding-left: 4px;"
        )
        mid_layout.addWidget(section_lbl)

        self._list_widget = QListWidget()
        self._list_widget.setObjectName("SidebarList")
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self._list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list_widget.model().rowsMoved.connect(self._on_rows_moved)
        self._list_widget.doubleClicked.connect(lambda _: self._on_load())
        self._list_widget.setItemDelegate(_LibraryItemDelegate())
        self._list_widget.setStyleSheet(
            "QListWidget { background: transparent; border: none; outline: none; }"
            "QListWidget::item { border: none; padding: 0; margin: 0; }"
        )
        mid_layout.addWidget(self._list_widget)
        root.addWidget(mid, stretch=1)

        # ── Save button at bottom ─────────────────────────────────────────
        bottom = QWidget()
        bottom.setStyleSheet("background-color: #0a1218; border-top: 1px solid #1e2d37;")
        bot_layout = QVBoxLayout(bottom)
        bot_layout.setContentsMargins(12, 10, 12, 12)
        save_btn = QPushButton("💾  Save Current Macro")
        save_btn.setProperty("role", "save")
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self.save_requested.emit)
        bot_layout.addWidget(save_btn)
        root.addWidget(bottom)

        self._load_state()
        self._refresh_list()

    # ── Public API ────────────────────────────────────────────────────────

    def set_dirty(self, dirty: bool) -> None:
        self._is_dirty = dirty

    def refresh(self) -> None:
        self._refresh_list()

    # ── State persistence ─────────────────────────────────────────────────

    def _state_file(self) -> Path:
        from macro_thunder.persistence.serializer import default_macro_dir
        return default_macro_dir() / "library_state.json"

    def _load_state(self) -> None:
        p = self._state_file()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self._pinned = data.get("pinned", [])
                self._order  = data.get("order", [])
            except Exception:
                self._pinned = []
                self._order  = []

    def _save_state(self) -> None:
        p = self._state_file()
        p.write_text(
            json.dumps({"pinned": self._pinned, "order": self._order}, indent=2),
            encoding="utf-8",
        )

    # ── List management ───────────────────────────────────────────────────

    def _macro_files(self) -> dict[str, Path]:
        from macro_thunder.persistence.serializer import default_macro_dir
        macro_dir = default_macro_dir()
        return {
            f.stem: f
            for f in macro_dir.glob("*.json")
            if f.name not in _EXCLUDED
        }

    def _refresh_list(self) -> None:
        files = self._macro_files()
        known    = [s for s in self._order if s in files]
        new_stems = [s for s in files if s not in self._order]
        new_stems.sort(key=lambda s: files[s].stat().st_mtime, reverse=True)
        all_stems = known + new_stems
        pinned    = [s for s in self._pinned if s in files]
        unpinned  = [s for s in all_stems if s not in pinned]
        self._order  = pinned + unpinned
        self._pinned = pinned

        query = self._search_box.text().lower().strip() if hasattr(self, "_search_box") else ""

        self._list_widget.clear()
        for stem in self._order:
            if query and query not in stem.lower():
                continue
            item = QListWidgetItem(stem)
            item.setData(Qt.ItemDataRole.UserRole, str(files[stem]))
            item.setData(Qt.ItemDataRole.UserRole + 1, stem in self._pinned)
            item.setSizeHint(QSize(0, 54))
            self._list_widget.addItem(item)

        self._save_state()

    def _on_search(self, _text: str) -> None:
        self._refresh_list()

    def _on_rows_moved(self) -> None:
        new_order = []
        for i in range(self._list_widget.count()):
            new_order.append(self._list_widget.item(i).text())
        self._order = new_order
        self._save_state()

    def _on_new_macro(self) -> None:
        """Emit load_requested with empty string as sentinel for new macro."""
        self.load_requested.emit("")

    # ── Helpers ───────────────────────────────────────────────────────────

    def _current_path(self) -> str | None:
        item = self._list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _current_stem(self) -> str | None:
        item = self._list_widget.currentItem()
        return item.text() if item else None

    def _on_load(self) -> None:
        path = self._current_path()
        if path is None:
            return
        if self._is_dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes", "Save changes before loading?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.save_requested.emit()
        self.load_requested.emit(path)

    def _on_rename(self) -> None:
        path = self._current_path()
        stem = self._current_stem()
        if path is None:
            return
        old_path = Path(path)
        new_name, ok = QInputDialog.getText(
            self, "Rename Macro", "New name:", text=old_path.stem
        )
        if ok and new_name.strip():
            from macro_thunder.persistence.serializer import rename_macro
            new_stem = new_name.strip()
            rename_macro(old_path, new_stem)
            self._order  = [new_stem if s == stem else s for s in self._order]
            self._pinned = [new_stem if s == stem else s for s in self._pinned]
            self._refresh_list()

    def _on_delete(self) -> None:
        path = self._current_path()
        stem = self._current_stem()
        if path is None:
            return
        p = Path(path)
        reply = QMessageBox.question(
            self, "Delete Macro", f"Delete '{p.stem}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            p.unlink(missing_ok=True)
            self._order  = [s for s in self._order if s != stem]
            self._pinned = [s for s in self._pinned if s != stem]
            self._refresh_list()

    def _on_pin(self) -> None:
        stem = self._current_stem()
        if stem and stem not in self._pinned:
            self._pinned.insert(0, stem)
        self._refresh_list()

    def _on_unpin(self) -> None:
        stem = self._current_stem()
        if stem:
            self._pinned = [s for s in self._pinned if s != stem]
        self._refresh_list()

    def _show_context_menu(self, pos) -> None:
        stem = self._current_stem()
        menu = QMenu(self)
        menu.addAction("Load").triggered.connect(self._on_load)
        menu.addSeparator()
        if stem and stem in self._pinned:
            menu.addAction("Unpin").triggered.connect(self._on_unpin)
        else:
            menu.addAction("Pin to top").triggered.connect(self._on_pin)
        menu.addSeparator()
        menu.addAction("Rename...").triggered.connect(self._on_rename)
        menu.addAction("Delete").triggered.connect(self._on_delete)
        menu.exec(self._list_widget.mapToGlobal(pos))
