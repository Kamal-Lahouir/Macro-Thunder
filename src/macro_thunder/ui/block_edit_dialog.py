"""Per-type block edit dialogs for the Macro Thunder block editor.

Public API:
  open_edit_dialog(block, doc_blocks, parent=None) -> bool
  KeyCaptureField
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from macro_thunder.models.blocks import (
    MouseClickBlock,
    MouseMoveBlock,
    MouseScrollBlock,
    KeyPressBlock,
    DelayBlock,
    LabelBlock,
    GotoBlock,
    WindowFocusBlock,
    LoopStartBlock,
)

# ---------------------------------------------------------------------------
# Internal key-conversion helper
# ---------------------------------------------------------------------------

def _qt_key_to_pynput(event: QKeyEvent) -> str:
    """Convert a QKeyEvent to a pynput key string (no modifiers)."""
    key = event.key()
    named = {
        Qt.Key.Key_Space: "Key.space",
        Qt.Key.Key_Return: "Key.enter",
        Qt.Key.Key_Enter: "Key.enter",
        Qt.Key.Key_Backspace: "Key.backspace",
        Qt.Key.Key_Delete: "Key.delete",
        Qt.Key.Key_Tab: "Key.tab",
        Qt.Key.Key_Escape: "Key.esc",
        Qt.Key.Key_Up: "Key.up",
        Qt.Key.Key_Down: "Key.down",
        Qt.Key.Key_Left: "Key.left",
        Qt.Key.Key_Right: "Key.right",
        Qt.Key.Key_Home: "Key.home",
        Qt.Key.Key_End: "Key.end",
        Qt.Key.Key_PageUp: "Key.page_up",
        Qt.Key.Key_PageDown: "Key.page_down",
        Qt.Key.Key_Insert: "Key.insert",
        Qt.Key.Key_F1: "Key.f1",
        Qt.Key.Key_F2: "Key.f2",
        Qt.Key.Key_F3: "Key.f3",
        Qt.Key.Key_F4: "Key.f4",
        Qt.Key.Key_F5: "Key.f5",
        Qt.Key.Key_F6: "Key.f6",
        Qt.Key.Key_F7: "Key.f7",
        Qt.Key.Key_F8: "Key.f8",
        Qt.Key.Key_F9: "Key.f9",
        Qt.Key.Key_F10: "Key.f10",
        Qt.Key.Key_F11: "Key.f11",
        Qt.Key.Key_F12: "Key.f12",
        Qt.Key.Key_CapsLock: "Key.caps_lock",
        Qt.Key.Key_NumLock: "Key.num_lock",
        Qt.Key.Key_ScrollLock: "Key.scroll_lock",
        Qt.Key.Key_Print: "Key.print_screen",
        Qt.Key.Key_Pause: "Key.pause",
    }
    if key in named:
        return named[key]
    text = event.text()
    if text and text.isprintable():
        return text.lower()
    return f"Key.{Qt.Key(key).name.replace('Key_', '').lower()}"


# ---------------------------------------------------------------------------
# KeyCaptureField widget
# ---------------------------------------------------------------------------

class KeyCaptureField(QWidget):
    """A widget that captures a single physical keypress and stores it in pynput format."""

    def __init__(self, initial_value: str = "", parent=None) -> None:
        super().__init__(parent)
        self._value = initial_value
        self._capturing = False

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        self._display = QLineEdit(initial_value)
        self._display.setReadOnly(True)
        self._display.setMinimumWidth(160)

        self._btn = QPushButton("Press a key...")
        self._btn.setFixedWidth(110)
        self._btn.clicked.connect(self._start_capture)

        row.addWidget(self._display)
        row.addWidget(self._btn)

    def value(self) -> str:
        return self._value

    def _start_capture(self) -> None:
        self._capturing = True
        self._display.setText("… press a key …")
        self._btn.setText("Cancel")
        try:
            self._btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._btn.clicked.connect(self._cancel_capture)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def _cancel_capture(self) -> None:
        self._capturing = False
        self._display.setText(self._value)
        self._btn.setText("Press a key...")
        try:
            self._btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._btn.clicked.connect(self._start_capture)
        self.clearFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifier_only = {
            Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt,
            Qt.Key.Key_Meta, Qt.Key.Key_AltGr,
        }
        if key in modifier_only:
            return

        if key == Qt.Key.Key_Escape:
            self._cancel_capture()
            return

        self._value = _qt_key_to_pynput(event)
        self._display.setText(self._value)
        self._capturing = False
        self._btn.setText("Press a key...")
        try:
            self._btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._btn.clicked.connect(self._start_capture)
        self.clearFocus()
        event.accept()


# ---------------------------------------------------------------------------
# Partner-finding helper
# ---------------------------------------------------------------------------

def _find_click_partner(
    block: MouseClickBlock, doc_blocks: list
) -> tuple[int, object]:
    """Find the paired down/up MouseClickBlock for the given block.

    Scans forward when block.direction == "down" (looking for "up"),
    backward when block.direction == "up" (looking for "down").
    Returns (index, block) on first match or (-1, None).
    """
    try:
        idx = doc_blocks.index(block)
    except ValueError:
        return (-1, None)

    if block.direction == "down":
        target_direction = "up"
        search_range = range(idx + 1, len(doc_blocks))
    else:
        target_direction = "down"
        search_range = range(idx - 1, -1, -1)

    for i in search_range:
        b = doc_blocks[i]
        if (
            isinstance(b, MouseClickBlock)
            and b.button == block.button
            and b.direction == target_direction
        ):
            return (i, b)

    return (-1, None)


# ---------------------------------------------------------------------------
# Shared dialog builder helpers
# ---------------------------------------------------------------------------

def _make_buttons(dialog: QDialog) -> QDialogButtonBox:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    return buttons


def _coord_spin() -> QSpinBox:
    s = QSpinBox()
    s.setRange(-9999, 9999)
    return s


# ---------------------------------------------------------------------------
# Per-type dialog classes
# ---------------------------------------------------------------------------

class MouseClickEditDialog(QDialog):
    def __init__(self, block: MouseClickBlock, partner, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._partner = partner
        self.setWindowTitle("Edit MouseClickBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._x = _coord_spin()
        self._x.setValue(block.x)
        form.addRow("X:", self._x)

        self._y = _coord_spin()
        self._y.setValue(block.y)
        form.addRow("Y:", self._y)

        self._button_combo = QComboBox()
        self._button_combo.addItems(["left", "right", "middle"])
        self._button_combo.setCurrentText(block.button)
        form.addRow("Button:", self._button_combo)

        self._dir_combo = QComboBox()
        self._dir_combo.addItems(["down", "up", "click"])
        self._dir_combo.setCurrentText(block.direction)
        form.addRow("Direction:", self._dir_combo)

        if partner is not None:
            lbl = QLabel("(editing paired down/up blocks)")
            lbl.setStyleSheet("color: gray; font-size: 11px;")
            layout.addWidget(lbl)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        x = self._x.value()
        y = self._y.value()
        button = self._button_combo.currentText()
        direction = self._dir_combo.currentText()
        self._block.x = x
        self._block.y = y
        self._block.button = button
        self._block.direction = direction
        if self._partner is not None:
            self._partner.x = x
            self._partner.y = y
            self._partner.button = button
        super().accept()


class MouseMoveEditDialog(QDialog):
    def __init__(self, block: MouseMoveBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit MouseMoveBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._x = _coord_spin()
        self._x.setValue(block.x)
        form.addRow("X:", self._x)

        self._y = _coord_spin()
        self._y.setValue(block.y)
        form.addRow("Y:", self._y)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.x = self._x.value()
        self._block.y = self._y.value()
        super().accept()


class MouseScrollEditDialog(QDialog):
    def __init__(self, block: MouseScrollBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit MouseScrollBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._x = _coord_spin()
        self._x.setValue(block.x)
        form.addRow("X:", self._x)

        self._y = _coord_spin()
        self._y.setValue(block.y)
        form.addRow("Y:", self._y)

        self._dx = QSpinBox()
        self._dx.setRange(-99, 99)
        self._dx.setValue(block.dx)
        form.addRow("DX:", self._dx)

        self._dy = QSpinBox()
        self._dy.setRange(-99, 99)
        self._dy.setValue(block.dy)
        form.addRow("DY:", self._dy)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.x = self._x.value()
        self._block.y = self._y.value()
        self._block.dx = self._dx.value()
        self._block.dy = self._dy.value()
        super().accept()


class KeyPressEditDialog(QDialog):
    def __init__(self, block: KeyPressBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit KeyPressBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._key_field = KeyCaptureField(block.key)
        form.addRow("Key:", self._key_field)

        self._dir_combo = QComboBox()
        self._dir_combo.addItems(["down", "up", "key"])
        self._dir_combo.setCurrentText(block.direction)
        form.addRow("Direction:", self._dir_combo)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.key = self._key_field.value()
        self._block.direction = self._dir_combo.currentText()
        super().accept()


class DelayEditDialog(QDialog):
    def __init__(self, block: DelayBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit DelayBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._duration = QDoubleSpinBox()
        self._duration.setRange(0.001, 3600.0)
        self._duration.setDecimals(3)
        self._duration.setSuffix(" s")
        self._duration.setValue(block.duration)
        form.addRow("Duration:", self._duration)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.duration = self._duration.value()
        super().accept()


class LabelEditDialog(QDialog):
    def __init__(self, block: LabelBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit LabelBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._name = QLineEdit(block.name)
        self._name.setPlaceholderText("Unique label name")
        form.addRow("Name:", self._name)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.name = self._name.text().strip()
        super().accept()


class GotoEditDialog(QDialog):
    def __init__(self, block: GotoBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit GotoBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._target = QLineEdit(block.target)
        self._target.setPlaceholderText("Label name to jump to")
        form.addRow("Target:", self._target)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.target = self._target.text().strip()
        super().accept()


class WindowFocusEditDialog(QDialog):
    def __init__(self, block: WindowFocusBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit WindowFocusBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._executable = QLineEdit(block.executable)
        form.addRow("Executable:", self._executable)

        self._title = QLineEdit(block.title)
        form.addRow("Title:", self._title)

        self._match_mode = QComboBox()
        self._match_mode.addItems(["Contains", "Exact", "Starts With"])
        self._match_mode.setCurrentText(block.match_mode)
        form.addRow("Match Mode:", self._match_mode)

        self._timeout = QDoubleSpinBox()
        self._timeout.setRange(0.0, 3600.0)
        self._timeout.setDecimals(1)
        self._timeout.setSuffix(" s")
        self._timeout.setValue(block.timeout)
        form.addRow("Timeout:", self._timeout)

        self._on_failure_label = QLineEdit(block.on_failure_label)
        form.addRow("On Failure Label:", self._on_failure_label)

        self._on_success_label = QLineEdit(block.on_success_label)
        form.addRow("On Success Label:", self._on_success_label)

        layout.addLayout(form)

        self._reposition_check = QCheckBox("Reposition window")
        self._reposition_check.setChecked(block.reposition)
        layout.addWidget(self._reposition_check)

        self._reposition_group = QGroupBox("Position/Size")
        group_form = QFormLayout(self._reposition_group)

        self._pos_x = _coord_spin()
        self._pos_x.setValue(block.x)
        group_form.addRow("X:", self._pos_x)

        self._pos_y = _coord_spin()
        self._pos_y.setValue(block.y)
        group_form.addRow("Y:", self._pos_y)

        self._pos_w = _coord_spin()
        self._pos_w.setValue(block.w)
        group_form.addRow("W:", self._pos_w)

        self._pos_h = _coord_spin()
        self._pos_h.setValue(block.h)
        group_form.addRow("H:", self._pos_h)

        layout.addWidget(self._reposition_group)
        self._reposition_group.setVisible(block.reposition)
        self._reposition_check.toggled.connect(self._reposition_group.setVisible)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.executable = self._executable.text()
        self._block.title = self._title.text()
        self._block.match_mode = self._match_mode.currentText()
        self._block.timeout = self._timeout.value()
        self._block.on_failure_label = self._on_failure_label.text()
        self._block.on_success_label = self._on_success_label.text()
        self._block.reposition = self._reposition_check.isChecked()
        self._block.x = self._pos_x.value()
        self._block.y = self._pos_y.value()
        self._block.w = self._pos_w.value()
        self._block.h = self._pos_h.value()
        super().accept()


class LoopStartEditDialog(QDialog):
    def __init__(self, block: LoopStartBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit LoopStartBlock")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._repeat = QSpinBox()
        self._repeat.setRange(1, 9999)
        self._repeat.setValue(block.repeat)
        form.addRow("Repeat:", self._repeat)

        layout.addWidget(_make_buttons(self))

    def accept(self) -> None:
        self._block.repeat = self._repeat.value()
        super().accept()


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def open_edit_dialog(block, doc_blocks: list, parent=None) -> bool:
    """Open the appropriate edit dialog for the given block.

    Returns True if the user confirmed the edit (Accept), False if cancelled
    or if the block type has no editable dialog (e.g. LoopEndBlock).
    """
    if isinstance(block, MouseClickBlock):
        _, partner = _find_click_partner(block, doc_blocks)
        dlg = MouseClickEditDialog(block, partner, parent)
    elif isinstance(block, MouseMoveBlock):
        dlg = MouseMoveEditDialog(block, parent)
    elif isinstance(block, MouseScrollBlock):
        dlg = MouseScrollEditDialog(block, parent)
    elif isinstance(block, KeyPressBlock):
        dlg = KeyPressEditDialog(block, parent)
    elif isinstance(block, DelayBlock):
        dlg = DelayEditDialog(block, parent)
    elif isinstance(block, LabelBlock):
        dlg = LabelEditDialog(block, parent)
    elif isinstance(block, GotoBlock):
        dlg = GotoEditDialog(block, parent)
    elif isinstance(block, WindowFocusBlock):
        dlg = WindowFocusEditDialog(block, parent)
    elif isinstance(block, LoopStartBlock):
        dlg = LoopStartEditDialog(block, parent)
    else:
        # LoopEndBlock or unknown — no dialog
        return False

    return dlg.exec() == QDialog.DialogCode.Accepted
