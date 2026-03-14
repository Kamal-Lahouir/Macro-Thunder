"""RibbonBar — tab-based ribbon replacing the flat HeaderBar."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QFrame, QStackedWidget, QTabBar,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class RibbonBar(QWidget):
    """Tab strip (Record | Playback | Settings) + swappable content pane."""

    new_macro_requested   = pyqtSignal()
    open_macro_requested  = pyqtSignal()
    save_macro_requested  = pyqtSignal()
    record_requested      = pyqtSignal()
    stop_record_requested = pyqtSignal()
    record_here_requested = pyqtSignal()
    play_requested        = pyqtSignal(float, int)   # (speed, repeat)
    stop_play_requested   = pyqtSignal()
    edit_requested        = pyqtSignal()
    move_up_requested     = pyqtSignal()
    move_down_requested   = pyqtSignal()
    delete_requested      = pyqtSignal()
    add_block_requested   = pyqtSignal()
    undo_requested        = pyqtSignal()
    redo_requested        = pyqtSignal()
    duplicate_requested   = pyqtSignal()
    settings_requested    = pyqtSignal()
    theme_toggled         = pyqtSignal(bool)          # True = dark, False = light

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("RibbonBar")
        self.setFixedHeight(80)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Tab strip row ─────────────────────────────────────────────────
        self._tab_bar = QTabBar()
        self._tab_bar.setObjectName("RibbonTabs")
        self._tab_bar.setDrawBase(False)
        self._tab_bar.setExpanding(False)
        self._tab_bar.addTab("Files")
        self._tab_bar.addTab("Record")
        self._tab_bar.addTab("Edit")
        self._tab_bar.addTab("Playback")
        self._tab_bar.addTab("Settings")
        self._prev_tab = 0

        self._btn_theme = QPushButton("Light mode")
        self._btn_theme.setObjectName("ThemeToggle")
        self._btn_theme.setFixedHeight(26)
        self._btn_theme.setMinimumWidth(80)
        self._btn_theme.setToolTip("Switch to light mode")
        self._btn_theme.clicked.connect(self._on_theme_clicked)
        self._is_dark = True

        tab_row = QWidget()
        tab_row_hl = QHBoxLayout(tab_row)
        tab_row_hl.setContentsMargins(0, 0, 6, 0)
        tab_row_hl.setSpacing(0)
        tab_row_hl.addWidget(self._tab_bar, alignment=Qt.AlignmentFlag.AlignVCenter)
        tab_row_hl.addStretch()
        tab_row_hl.addWidget(self._btn_theme, alignment=Qt.AlignmentFlag.AlignVCenter)

        # ── Stacked panes ─────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setFixedHeight(48)

        self._files_pane    = self._build_files_pane()
        self._record_pane   = self._build_record_pane()
        self._edit_pane     = self._build_edit_pane()
        self._playback_pane = self._build_playback_pane()
        self._settings_pane = QWidget()   # never visible; tab click opens dialog

        self._stack.addWidget(self._files_pane)
        self._stack.addWidget(self._record_pane)
        self._stack.addWidget(self._edit_pane)
        self._stack.addWidget(self._playback_pane)
        self._stack.addWidget(self._settings_pane)

        root.addWidget(tab_row)
        root.addWidget(self._stack)

        # ── Tab wiring ────────────────────────────────────────────────────
        self._tab_bar.tabBarClicked.connect(self._on_tab_clicked)

        # ── Blink timer ───────────────────────────────────────────────────
        self._blink_visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(500)
        self._blink_timer.timeout.connect(self._toggle_blink)

    # ── Pane builders ─────────────────────────────────────────────────────

    def _build_files_pane(self) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(6)

        btn_new = QPushButton("New")
        btn_new.setFixedHeight(32)
        btn_new.setToolTip("New macro (Ctrl+N)")
        btn_new.clicked.connect(self.new_macro_requested)

        btn_open = QPushButton("Open")
        btn_open.setFixedHeight(32)
        btn_open.setToolTip("Open macro (Ctrl+O)")
        btn_open.clicked.connect(self.open_macro_requested)

        btn_save = QPushButton("Save")
        btn_save.setFixedHeight(32)
        btn_save.setToolTip("Save macro (Ctrl+S)")
        btn_save.clicked.connect(self.save_macro_requested)

        hl.addWidget(btn_new)
        hl.addWidget(_vsep())
        hl.addWidget(btn_open)
        hl.addWidget(_vsep())
        hl.addWidget(btn_save)
        hl.addStretch()
        return w

    def _build_record_pane(self) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(6)

        self.btn_record = QPushButton("Record")
        self.btn_record.setProperty("role", "record")
        self.btn_record.setFixedHeight(32)
        self.btn_record.setToolTip("Start recording (F9)")
        self.btn_record.clicked.connect(self.record_requested)

        self.btn_stop_record = QPushButton("Stop")
        self.btn_stop_record.setFixedHeight(32)
        self.btn_stop_record.setToolTip("Stop recording (F10)")
        self.btn_stop_record.setEnabled(False)
        self.btn_stop_record.clicked.connect(self.stop_record_requested)

        self._blink_indicator = QLabel("●")
        self._blink_indicator.setStyleSheet(
            "color:#ef4444;font-size:14px;background:transparent;"
        )
        self._blink_indicator.setFixedWidth(18)
        self._blink_indicator.hide()

        self._block_count_label = QLabel("")
        self._block_count_label.setStyleSheet(
            "color:#64748b;font-size:11px;min-width:58px;background:transparent;"
        )
        self._block_count_label.hide()

        btn_record_here = QPushButton("Record Here")
        btn_record_here.setProperty("role", "record")
        btn_record_here.setFixedHeight(32)
        btn_record_here.setToolTip("Insert recording after selected row")
        btn_record_here.clicked.connect(self.record_here_requested)

        hotkey_hint = QLabel("F9 Start  ·  F10 Stop")
        hotkey_hint.setStyleSheet("color:#374151;font-size:10px;background:transparent;")

        hl.addWidget(self.btn_record)
        hl.addWidget(_vsep())
        hl.addWidget(self.btn_stop_record)
        hl.addWidget(self._blink_indicator)
        hl.addWidget(self._block_count_label)
        hl.addWidget(_vsep())
        hl.addWidget(btn_record_here)
        hl.addStretch()
        hl.addWidget(hotkey_hint)
        return w

    def _build_edit_pane(self) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(6)

        btn_edit = QPushButton("Edit")
        btn_edit.setFixedHeight(32)
        btn_edit.setToolTip("Edit selected block")
        btn_edit.clicked.connect(self.edit_requested)

        btn_up = QPushButton("Move Up")
        btn_up.setFixedHeight(32)
        btn_up.setToolTip("Move selected block up")
        btn_up.clicked.connect(self.move_up_requested)

        btn_down = QPushButton("Move Down")
        btn_down.setFixedHeight(32)
        btn_down.setToolTip("Move selected block down")
        btn_down.clicked.connect(self.move_down_requested)

        btn_delete = QPushButton("Delete")
        btn_delete.setFixedHeight(32)
        btn_delete.setToolTip("Delete selected block(s)")
        btn_delete.clicked.connect(self.delete_requested)

        btn_dup = QPushButton("Duplicate")
        btn_dup.setFixedHeight(32)
        btn_dup.setToolTip("Duplicate selected block(s)")
        btn_dup.clicked.connect(self.duplicate_requested)

        btn_add = QPushButton("Add Block")
        btn_add.setFixedHeight(32)
        btn_add.setToolTip("Insert a new block after selection")
        btn_add.clicked.connect(self.add_block_requested)

        btn_undo = QPushButton("Undo")
        btn_undo.setFixedHeight(32)
        btn_undo.setToolTip("Undo last edit (Ctrl+Z)")
        btn_undo.clicked.connect(self.undo_requested)

        btn_redo = QPushButton("Redo")
        btn_redo.setFixedHeight(32)
        btn_redo.setToolTip("Redo (Ctrl+Y)")
        btn_redo.clicked.connect(self.redo_requested)

        hl.addWidget(btn_edit)
        hl.addWidget(_vsep())
        hl.addWidget(btn_up)
        hl.addWidget(btn_down)
        hl.addWidget(_vsep())
        hl.addWidget(btn_delete)
        hl.addWidget(btn_dup)
        hl.addWidget(_vsep())
        hl.addWidget(btn_add)
        hl.addWidget(_vsep())
        hl.addWidget(btn_undo)
        hl.addWidget(btn_redo)
        hl.addStretch()
        return w

    def _build_playback_pane(self) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(12, 0, 0, 0)
        hl.setSpacing(6)

        self.btn_play = QPushButton("Play")
        self.btn_play.setProperty("role", "play")
        self.btn_play.setFixedHeight(32)
        self.btn_play.setToolTip("Play macro (F6)")
        self.btn_play.clicked.connect(self._on_play_clicked)

        self.btn_stop_play = QPushButton("Stop")
        self.btn_stop_play.setFixedHeight(32)
        self.btn_stop_play.setToolTip("Stop playback (F8)")
        self.btn_stop_play.setEnabled(False)
        self.btn_stop_play.clicked.connect(self.stop_play_requested)

        speed_lbl = QLabel("Speed")
        speed_lbl.setStyleSheet("color:#64748b;font-size:11px;background:transparent;")

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(1, 50)
        self._speed_slider.setValue(10)
        self._speed_slider.setFixedWidth(80)
        self._speed_slider.setToolTip("Playback speed")
        self._speed_slider.valueChanged.connect(self._on_slider_speed_changed)

        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 5.0)
        self._speed_spin.setSingleStep(0.1)
        self._speed_spin.setValue(1.0)
        self._speed_spin.setDecimals(1)
        self._speed_spin.setFixedWidth(66)
        self._speed_spin.setFixedHeight(28)
        self._speed_spin.setSuffix("x")
        self._speed_spin.valueChanged.connect(self._on_spinbox_speed_changed)

        rep_lbl = QLabel("Repeat")
        rep_lbl.setStyleSheet("color:#64748b;font-size:11px;background:transparent;")

        self._spin_repeat = QSpinBox()
        self._spin_repeat.setRange(1, 9999)
        self._spin_repeat.setValue(1)
        self._spin_repeat.setFixedWidth(62)
        self._spin_repeat.setFixedHeight(28)
        self._spin_repeat.setToolTip("Repeat count")

        self._chk_infinite = QPushButton("Loop")
        self._chk_infinite.setProperty("role", "toggle")
        self._chk_infinite.setCheckable(True)
        self._chk_infinite.setFixedHeight(28)
        self._chk_infinite.setToolTip("Loop infinitely until Stop is pressed")
        self._chk_infinite.toggled.connect(lambda on: self._spin_repeat.setEnabled(not on))

        btn_half = QPushButton("0.5x")
        btn_half.setFixedHeight(28)
        btn_half.setMinimumWidth(52)
        btn_half.setToolTip("Set speed to 0.5x")
        btn_half.clicked.connect(lambda: self._set_speed(0.5))

        btn_1x = QPushButton("1x")
        btn_1x.setFixedHeight(28)
        btn_1x.setMinimumWidth(44)
        btn_1x.setToolTip("Set speed to 1x")
        btn_1x.clicked.connect(lambda: self._set_speed(1.0))

        btn_2x = QPushButton("2x")
        btn_2x.setFixedHeight(28)
        btn_2x.setMinimumWidth(44)
        btn_2x.setToolTip("Set speed to 2x")
        btn_2x.clicked.connect(lambda: self._set_speed(2.0))

        hl.addWidget(self.btn_play)
        hl.addWidget(_vsep())
        hl.addWidget(self.btn_stop_play)
        hl.addWidget(_vsep())
        hl.addWidget(speed_lbl)
        hl.addWidget(self._speed_slider)
        hl.addWidget(self._speed_spin)
        hl.addWidget(btn_half)
        hl.addWidget(btn_1x)
        hl.addWidget(btn_2x)
        hl.addWidget(_vsep())
        hl.addWidget(rep_lbl)
        hl.addWidget(self._spin_repeat)
        hl.addWidget(self._chk_infinite)
        hl.addStretch()
        return w

    def _set_speed(self, speed: float) -> None:
        self._speed_spin.setValue(speed)

    # ── Theme toggle ──────────────────────────────────────────────────────

    def _on_theme_clicked(self) -> None:
        self._is_dark = not self._is_dark
        if self._is_dark:
            self._btn_theme.setText("Light mode")
            self._btn_theme.setToolTip("Switch to light mode")
        else:
            self._btn_theme.setText("Dark mode")
            self._btn_theme.setToolTip("Switch to dark mode")
        self.theme_toggled.emit(self._is_dark)

    # ── Tab click handler ─────────────────────────────────────────────────

    def _on_tab_clicked(self, index: int) -> None:
        if index == 4:
            self.settings_requested.emit()
            self._tab_bar.setCurrentIndex(self._prev_tab)
        else:
            self._prev_tab = index
            self._stack.setCurrentIndex(index)

    # ── Speed sync ────────────────────────────────────────────────────────

    def _on_play_clicked(self) -> None:
        repeat = -1 if self._chk_infinite.isChecked() else self._spin_repeat.value()
        self.play_requested.emit(self._speed_spin.value(), repeat)

    def _on_slider_speed_changed(self, val: int) -> None:
        self._speed_spin.blockSignals(True)
        self._speed_spin.setValue(val / 10.0)
        self._speed_spin.blockSignals(False)

    def _on_spinbox_speed_changed(self, val: float) -> None:
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(round(val * 10))
        self._speed_slider.blockSignals(False)

    # ── Blink ─────────────────────────────────────────────────────────────

    def _toggle_blink(self) -> None:
        self._blink_visible = not self._blink_visible
        color = "#ef4444" if self._blink_visible else "transparent"
        self._blink_indicator.setStyleSheet(
            f"color:{color};font-size:14px;background:transparent;"
        )

    # ── Public API ────────────────────────────────────────────────────────

    def set_recording(self, active: bool, block_count: int = 0) -> None:
        if active:
            self.btn_record.setEnabled(False)
            self.btn_stop_record.setEnabled(True)
            self._blink_visible = True
            self._blink_indicator.setStyleSheet(
                "color:#ef4444;font-size:14px;background:transparent;"
            )
            self._blink_indicator.show()
            self._blink_timer.start()
            self._block_count_label.setText(f"{block_count} blocks")
            self._block_count_label.show()
        else:
            self.btn_record.setEnabled(True)
            self.btn_stop_record.setEnabled(False)
            self._blink_indicator.hide()
            self._blink_timer.stop()
            self._block_count_label.hide()

    def update_block_count(self, count: int) -> None:
        self._block_count_label.setText(f"{count} blocks")

    def set_playback(self, active: bool) -> None:
        if active:
            self.btn_play.setEnabled(False)
            self.btn_stop_play.setEnabled(True)
        else:
            self.btn_play.setEnabled(True)
            self.btn_stop_play.setEnabled(False)

    def set_playback_progress(self, index: int, total: int) -> None:
        pass  # Progress shown in EditorPanel's progress bar


# ── Helpers ───────────────────────────────────────────────────────────────

def _vsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFrameShadow(QFrame.Shadow.Plain)
    f.setStyleSheet("color:#1e2d37;")
    f.setFixedHeight(28)
    return f
