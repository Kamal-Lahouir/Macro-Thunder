from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
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


class LibraryPanel(QFrame):
    """Left-sidebar macro library panel."""

    load_requested = pyqtSignal(str)   # file path
    save_requested = pyqtSignal()      # tell MainWindow to save current macro

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dirty: bool = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        layout.addWidget(QLabel("Macro Library"))

        # Save button
        save_btn = QPushButton("Save Macro")
        save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(save_btn)

        # File list
        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list_widget)

        # Load button
        load_btn = QPushButton("Load Selected")
        load_btn.clicked.connect(self._on_load)
        layout.addWidget(load_btn)

        self.setMinimumWidth(180)
        self.setMaximumWidth(320)

        self._refresh_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_dirty(self, dirty: bool) -> None:
        """Called by MainWindow to track unsaved-changes state."""
        self._is_dirty = dirty

    def refresh(self) -> None:
        """Called by MainWindow after save/delete to update the list."""
        self._refresh_list()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_list(self) -> None:
        from macro_thunder.persistence.serializer import default_macro_dir

        macro_dir = default_macro_dir()
        files = sorted(macro_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        self._list_widget.clear()
        for f in files:
            item = QListWidgetItem(f.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._list_widget.addItem(item)

    def _current_path(self) -> str | None:
        item = self._list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

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
        if path is None:
            return
        old_path = Path(path)
        new_name, ok = QInputDialog.getText(
            self, "Rename Macro", "New name:", text=old_path.stem
        )
        if ok and new_name.strip():
            from macro_thunder.persistence.serializer import rename_macro

            rename_macro(old_path, new_name.strip())
            self._refresh_list()

    def _on_delete(self) -> None:
        path = self._current_path()
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
            self._refresh_list()

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Load").triggered.connect(self._on_load)
        menu.addAction("Rename...").triggered.connect(self._on_rename)
        menu.addAction("Delete").triggered.connect(self._on_delete)
        menu.exec(self._list_widget.mapToGlobal(pos))
