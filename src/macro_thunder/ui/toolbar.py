from __future__ import annotations

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QWidget,
)


class ToolbarPanel(QWidget):
    """Full Phase 2 toolbar: recording controls, playback controls, and speed selector."""

    record_requested = pyqtSignal()
    stop_record_requested = pyqtSignal()
    play_requested = pyqtSignal(float, int)   # (speed, repeat)
    stop_play_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        # --- LEFT: recording controls ---
        self.btn_record = QPushButton("\u23fa Record")
        self.btn_record.setToolTip("Start recording (F9)")
        self.btn_record.clicked.connect(self.record_requested)

        self.btn_stop_record = QPushButton("\u23f9 Stop")
        self.btn_stop_record.setToolTip("Stop recording (F10)")
        self.btn_stop_record.setEnabled(False)
        self.btn_stop_record.clicked.connect(self.stop_record_requested)

        self._blink_indicator = QLabel("\u25cf")
        self._blink_indicator.setStyleSheet("color: red; font-size: 16px;")
        self._blink_indicator.setFixedWidth(20)
        self._blink_indicator.hide()

        self._block_count_label = QLabel("")
        self._block_count_label.hide()

        layout.addWidget(self.btn_record)
        layout.addWidget(self.btn_stop_record)
        layout.addWidget(self._blink_indicator)
        layout.addWidget(self._block_count_label)

        # --- SEPARATOR ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # --- CENTER: playback controls ---
        self.btn_play = QPushButton("\u25b6 Play")
        self.btn_play.setToolTip("Start playback (F6)")
        self.btn_play.clicked.connect(self._on_play_clicked)

        self.btn_stop_play = QPushButton("\u23f9 Stop")
        self.btn_stop_play.setToolTip("Stop playback (F8)")
        self.btn_stop_play.setEnabled(False)
        self.btn_stop_play.clicked.connect(self.stop_play_requested)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedWidth(120)
        self._progress_bar.hide()

        self._progress_label = QLabel("")
        self._progress_label.hide()

        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_stop_play)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._progress_label)

        layout.addStretch()

        # --- RIGHT: speed controls ---
        layout.addWidget(QLabel("Speed:"))

        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 5.0)
        self._speed_spin.setSingleStep(0.1)
        self._speed_spin.setValue(1.0)
        self._speed_spin.setDecimals(1)
        self._speed_spin.setMinimumWidth(64)
        layout.addWidget(self._speed_spin)

        btn_half = QPushButton("0.5\u00d7")
        btn_half.clicked.connect(lambda: self._speed_spin.setValue(0.5))
        layout.addWidget(btn_half)

        btn_one = QPushButton("1\u00d7")
        btn_one.clicked.connect(lambda: self._speed_spin.setValue(1.0))
        layout.addWidget(btn_one)

        btn_two = QPushButton("2\u00d7")
        btn_two.clicked.connect(lambda: self._speed_spin.setValue(2.0))
        layout.addWidget(btn_two)

        # --- SEPARATOR (before repeat controls) ---
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)

        # --- RIGHT: repeat controls ---
        layout.addWidget(QLabel("Repeat:"))

        self._spin_repeat = QSpinBox()
        self._spin_repeat.setRange(1, 9999)
        self._spin_repeat.setValue(1)
        self._spin_repeat.setMinimumWidth(60)
        self._spin_repeat.setToolTip("Number of times to play the macro")
        layout.addWidget(self._spin_repeat)

        self._chk_infinite = QCheckBox("\u221e")   # ∞ character
        self._chk_infinite.setToolTip("Loop infinitely until Stop is pressed")
        self._chk_infinite.toggled.connect(lambda on: self._spin_repeat.setEnabled(not on))
        layout.addWidget(self._chk_infinite)

        # --- Blink timer ---
        self._blink_visible: bool = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(500)
        self._blink_timer.timeout.connect(self._toggle_blink)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_play_clicked(self) -> None:
        repeat = -1 if self._chk_infinite.isChecked() else self._spin_repeat.value()
        self.play_requested.emit(self._speed_spin.value(), repeat)

    def _toggle_blink(self) -> None:
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self._blink_indicator.setStyleSheet("color: red; font-size: 16px;")
        else:
            self._blink_indicator.setStyleSheet("color: transparent; font-size: 16px;")

    # ------------------------------------------------------------------
    # Public API (called by MainWindow to reflect state changes)
    # ------------------------------------------------------------------

    def set_recording(self, active: bool, block_count: int = 0) -> None:
        """Switch toolbar into/out of recording state."""
        if active:
            self.btn_record.setEnabled(False)
            self.btn_stop_record.setEnabled(True)
            self._blink_visible = True
            self._blink_indicator.setStyleSheet("color: red; font-size: 16px;")
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
        """Update the live block count shown during recording."""
        self._block_count_label.setText(f"{count} blocks")

    def set_playback(self, active: bool) -> None:
        """Switch toolbar into/out of playback state."""
        if active:
            self.btn_play.setEnabled(False)
            self.btn_stop_play.setEnabled(True)
            self._progress_bar.show()
            self._progress_label.show()
        else:
            self.btn_play.setEnabled(True)
            self.btn_stop_play.setEnabled(False)
            self._progress_bar.hide()
            self._progress_label.hide()
            self._progress_bar.setValue(0)

    def set_playback_progress(self, index: int, total: int) -> None:
        """Update the progress bar and label during playback."""
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(index)
        self._progress_label.setText(f"Playing: {index} / {total}")
