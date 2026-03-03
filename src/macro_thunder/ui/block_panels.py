"""Per-block-type detail panels shown below the block table in EditorPanel.

Each panel takes a block reference and a modified_callback (callable, no args)
that it calls whenever a field changes. The block is mutated in-place; the
MacroDocument flat list is not rebuilt.
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpinBox, QLabel,
)
from PyQt6.QtCore import Qt
from macro_thunder.models.blocks import LabelBlock, GotoBlock, WindowFocusBlock, LoopStartBlock


class LabelPanel(QWidget):
    """Edit panel for LabelBlock: single 'Name' text field."""

    def __init__(self, block: LabelBlock, modified_cb, parent=None):
        super().__init__(parent)
        self._block = block
        self._cb = modified_cb
        layout = QFormLayout(self)
        self._name_edit = QLineEdit(block.name)
        self._name_edit.setPlaceholderText("Label name (unique)")
        layout.addRow("Label Name:", self._name_edit)
        self._name_edit.textChanged.connect(self._on_name_changed)

    def _on_name_changed(self, text: str) -> None:
        self._block.name = text
        self._cb()


class GotoPanel(QWidget):
    """Edit panel for GotoBlock: single 'Target Label' text field."""

    def __init__(self, block: GotoBlock, modified_cb, parent=None):
        super().__init__(parent)
        self._block = block
        self._cb = modified_cb
        layout = QFormLayout(self)
        self._target_edit = QLineEdit(block.target)
        self._target_edit.setPlaceholderText("Target label name")
        layout.addRow("Jump To Label:", self._target_edit)
        self._target_edit.textChanged.connect(self._on_target_changed)

    def _on_target_changed(self, text: str) -> None:
        self._block.target = text
        self._cb()


class LoopStartPanel(QWidget):
    """Edit panel for LoopStartBlock: spinbox for repeat count."""

    def __init__(self, block: LoopStartBlock, modified_cb, parent=None):
        super().__init__(parent)
        self._block = block
        self._cb = modified_cb
        layout = QFormLayout(self)
        self._spin = QSpinBox()
        self._spin.setMinimum(1)
        self._spin.setMaximum(9999)
        self._spin.setValue(block.repeat)
        self._spin.setToolTip("Number of times to repeat the loop body (minimum 1)")
        layout.addRow("Repeat Count:", self._spin)
        self._spin.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value: int) -> None:
        self._block.repeat = value
        self._cb()


class WindowFocusPanel(QWidget):
    """Edit panel for WindowFocusBlock with all Phase 4 fields + window picker."""

    def __init__(self, block: WindowFocusBlock, modified_cb, picker_service, parent=None):
        super().__init__(parent)
        self._block = block
        self._cb = modified_cb
        self._picker = picker_service

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        form = QFormLayout()

        # Executable + title
        self._exe_edit = QLineEdit(block.executable)
        self._exe_edit.setPlaceholderText("e.g. game.exe")
        form.addRow("Executable:", self._exe_edit)

        self._title_edit = QLineEdit(block.title)
        self._title_edit.setPlaceholderText("Window title (or part of it)")
        form.addRow("Window Title:", self._title_edit)

        # Match mode
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Contains", "Exact", "Starts With"])
        idx = self._mode_combo.findText(block.match_mode)
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)
        form.addRow("Match Mode:", self._mode_combo)

        # Timeout
        self._timeout_spin = QDoubleSpinBox()
        self._timeout_spin.setRange(0.0, 300.0)
        self._timeout_spin.setSuffix(" s")
        self._timeout_spin.setValue(block.timeout)
        form.addRow("Timeout:", self._timeout_spin)

        # Success / Failure labels
        self._success_edit = QLineEdit(block.on_success_label)
        self._success_edit.setPlaceholderText("empty = Next")
        form.addRow("On Success: Go To:", self._success_edit)

        self._failure_edit = QLineEdit(block.on_failure_label)
        self._failure_edit.setPlaceholderText("empty = Next")
        form.addRow("On Failure: Go To:", self._failure_edit)

        outer.addLayout(form)

        # Reposition checkbox + hidden group
        self._reposition_check = QCheckBox("Reposition window on success")
        self._reposition_check.setChecked(block.reposition)
        outer.addWidget(self._reposition_check)

        self._reposition_group = QGroupBox()
        repos_form = QFormLayout(self._reposition_group)
        self._x_spin = QSpinBox(); self._x_spin.setRange(-9999, 9999); self._x_spin.setValue(block.x)
        self._y_spin = QSpinBox(); self._y_spin.setRange(-9999, 9999); self._y_spin.setValue(block.y)
        self._w_spin = QSpinBox(); self._w_spin.setRange(0, 9999); self._w_spin.setValue(block.w)
        self._h_spin = QSpinBox(); self._h_spin.setRange(0, 9999); self._h_spin.setValue(block.h)
        repos_form.addRow("X:", self._x_spin)
        repos_form.addRow("Y:", self._y_spin)
        repos_form.addRow("W:", self._w_spin)
        repos_form.addRow("H:", self._h_spin)
        self._reposition_group.setVisible(block.reposition)
        outer.addWidget(self._reposition_group)

        # Select Window button
        self._pick_btn = QPushButton("Select Window...")
        outer.addWidget(self._pick_btn)

        # Wire signals
        self._exe_edit.textChanged.connect(self._on_exe_changed)
        self._title_edit.textChanged.connect(self._on_title_changed)
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self._timeout_spin.valueChanged.connect(self._on_timeout_changed)
        self._success_edit.textChanged.connect(self._on_success_changed)
        self._failure_edit.textChanged.connect(self._on_failure_changed)
        self._reposition_check.toggled.connect(self._on_reposition_toggled)
        self._x_spin.valueChanged.connect(self._on_rect_changed)
        self._y_spin.valueChanged.connect(self._on_rect_changed)
        self._w_spin.valueChanged.connect(self._on_rect_changed)
        self._h_spin.valueChanged.connect(self._on_rect_changed)
        self._pick_btn.clicked.connect(self._on_pick_clicked)

        if self._picker is not None:
            self._picker.picked.connect(self._on_picker_result)

    def _on_exe_changed(self, t): self._block.executable = t; self._cb()
    def _on_title_changed(self, t): self._block.title = t; self._cb()
    def _on_mode_changed(self, t): self._block.match_mode = t; self._cb()
    def _on_timeout_changed(self, v): self._block.timeout = v; self._cb()
    def _on_success_changed(self, t): self._block.on_success_label = t; self._cb()
    def _on_failure_changed(self, t): self._block.on_failure_label = t; self._cb()

    def _on_reposition_toggled(self, checked: bool):
        self._block.reposition = checked
        self._reposition_group.setVisible(checked)
        self._cb()

    def _on_rect_changed(self):
        self._block.x = self._x_spin.value()
        self._block.y = self._y_spin.value()
        self._block.w = self._w_spin.value()
        self._block.h = self._h_spin.value()
        self._cb()

    def _on_pick_clicked(self):
        if self._picker is not None:
            self._picker.start()

    def _on_picker_result(self, exe: str, title: str):
        """Auto-fill fields from picker result. match_mode defaults to Contains."""
        self._exe_edit.setText(exe)
        self._title_edit.setText(title)
        idx = self._mode_combo.findText("Contains")
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)
