"""BlockTypeDialog — modal dialog for choosing and inserting a new block type.

Presents a list of all 8 action block types.  On acceptance returns a
default-constructed ActionBlock instance ready to be inserted into the document.
"""
from __future__ import annotations

import copy
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox,
)

from macro_thunder.models.blocks import (
    ActionBlock,
    MouseMoveBlock,
    MouseClickBlock,
    MouseScrollBlock,
    KeyPressBlock,
    DelayBlock,
    WindowFocusBlock,
    LabelBlock,
    GotoBlock,
)

# Ordered list of (label, default block factory)
_BLOCK_TYPES: list[tuple[str, ActionBlock]] = [
    ("Mouse Move",    MouseMoveBlock(x=0, y=0, timestamp=0.0)),
    ("Mouse Click",   MouseClickBlock(x=0, y=0, button="left", direction="down", timestamp=0.0)),
    ("Mouse Scroll",  MouseScrollBlock(x=0, y=0, dx=0, dy=1, timestamp=0.0)),
    ("Key Press",     KeyPressBlock(key="a", direction="down", timestamp=0.0)),
    ("Delay",         DelayBlock(duration=0.5)),
    ("Window Focus",  WindowFocusBlock(executable="", title="", match_mode="Contains")),
    ("Label",         LabelBlock(name="start")),
    ("Goto",          GotoBlock(target="start")),
]


class BlockTypeDialog(QDialog):
    """Dialog that lets the user choose a block type to insert."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Block")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)

        self._list = QListWidget()
        for label, _ in _BLOCK_TYPES:
            self._list.addItem(QListWidgetItem(label))
        self._list.setCurrentRow(0)
        self._list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _selected_block(self) -> ActionBlock:
        row = self._list.currentRow()
        if row < 0:
            row = 0
        _, block = _BLOCK_TYPES[row]
        return copy.copy(block)  # fresh instance so edits don't mutate the shared default

    @staticmethod
    def get_block(parent=None) -> Optional[ActionBlock]:
        """Show the dialog and return the chosen block, or None if cancelled."""
        dlg = BlockTypeDialog(parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg._selected_block()
        return None
