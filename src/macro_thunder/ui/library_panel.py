from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

# Excluded filenames (not macros)
_EXCLUDED = {"settings.json", "library_state.json"}


def _pin_icon() -> QIcon:
    """Small colored square used as the pin indicator."""
    px = QPixmap(10, 10)
    px.fill(QColor("#f0a500"))
    return QIcon(px)


class LibraryPanel(QFrame):
    """Left-sidebar macro library panel."""

    load_requested = pyqtSignal(str)   # file path
    save_requested = pyqtSignal()      # tell MainWindow to save current macro

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dirty: bool = False
        self._pinned: list[str] = []   # stems of pinned macros, in pin order
        self._order: list[str] = []    # stems of all macros, in display order

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        layout.addWidget(QLabel("Macro Library"))

        save_btn = QPushButton("Save Macro")
        save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(save_btn)

        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)

        # Drag-and-drop reordering
        self._list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list_widget.model().rowsMoved.connect(self._on_rows_moved)

        layout.addWidget(self._list_widget)

        load_btn = QPushButton("Load Selected")
        load_btn.clicked.connect(self._on_load)
        layout.addWidget(load_btn)

        self.setMinimumWidth(180)
        self.setMaximumWidth(320)

        self._load_state()
        self._refresh_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_dirty(self, dirty: bool) -> None:
        self._is_dirty = dirty

    def refresh(self) -> None:
        self._refresh_list()

    # ------------------------------------------------------------------
    # State persistence (pinned + order)
    # ------------------------------------------------------------------

    def _state_file(self) -> Path:
        from macro_thunder.persistence.serializer import default_macro_dir
        return default_macro_dir() / "library_state.json"

    def _load_state(self) -> None:
        p = self._state_file()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self._pinned = data.get("pinned", [])
                self._order = data.get("order", [])
            except Exception:
                self._pinned = []
                self._order = []

    def _save_state(self) -> None:
        p = self._state_file()
        p.write_text(
            json.dumps({"pinned": self._pinned, "order": self._order}, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    def _macro_files(self) -> dict[str, Path]:
        """Return {stem: path} for all macro files, excluding non-macros."""
        from macro_thunder.persistence.serializer import default_macro_dir
        macro_dir = default_macro_dir()
        return {
            f.stem: f
            for f in macro_dir.glob("*.json")
            if f.name not in _EXCLUDED
        }

    def _refresh_list(self) -> None:
        files = self._macro_files()

        # Merge saved order with actual files on disk
        known = [s for s in self._order if s in files]
        new_stems = [s for s in files if s not in self._order]
        # New files go after pinned section, sorted by mtime descending
        new_stems.sort(key=lambda s: files[s].stat().st_mtime, reverse=True)
        all_stems = known + new_stems

        # Pinned first, then the rest (preserving relative order within each group)
        pinned = [s for s in self._pinned if s in files]
        unpinned = [s for s in all_stems if s not in pinned]
        self._order = pinned + unpinned
        self._pinned = pinned  # drop stale pins

        self._list_widget.clear()
        icon = _pin_icon()
        for stem in self._order:
            item = QListWidgetItem(stem)
            item.setData(Qt.ItemDataRole.UserRole, str(files[stem]))
            if stem in self._pinned:
                item.setIcon(icon)
                item.setToolTip("Pinned")
            self._list_widget.addItem(item)

        self._save_state()

    def _on_rows_moved(self) -> None:
        """Persist new order after a drag-and-drop reorder."""
        new_order = []
        for i in range(self._list_widget.count()):
            new_order.append(self._list_widget.item(i).text())
        self._order = new_order
        self._save_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
                self,
                "Unsaved Changes",
                "Save changes before loading?",
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
            # Update order/pinned lists to use the new name
            self._order = [new_stem if s == stem else s for s in self._order]
            self._pinned = [new_stem if s == stem else s for s in self._pinned]
            self._refresh_list()

    def _on_delete(self) -> None:
        path = self._current_path()
        stem = self._current_stem()
        if path is None:
            return
        p = Path(path)
        reply = QMessageBox.question(
            self,
            "Delete Macro",
            f"Delete '{p.stem}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            p.unlink(missing_ok=True)
            self._order = [s for s in self._order if s != stem]
            self._pinned = [s for s in self._pinned if s != stem]
            self._refresh_list()

    def _on_pin(self) -> None:
        stem = self._current_stem()
        if stem is None:
            return
        if stem not in self._pinned:
            self._pinned.insert(0, stem)
        self._refresh_list()

    def _on_unpin(self) -> None:
        stem = self._current_stem()
        if stem is None:
            return
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
