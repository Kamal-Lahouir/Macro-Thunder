"""HeaderBar — top-of-window controls bar replacing ToolbarPanel."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class HeaderBar(QWidget):
    """Top header: logo + record/play controls + speed + repeats + settings."""

    record_requested      = pyqtSignal()
    stop_record_requested = pyqtSignal()
    play_requested        = pyqtSignal(float, int)   # (speed, repeat)
    stop_play_requested   = pyqtSignal()
    settings_requested    = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(56)

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 0, 16, 0)
        root.setSpacing(6)

        # ── Logo ──────────────────────────────────────────────────────────
        logo = QLabel("⚡")
        logo.setStyleSheet("color:#25aff4;font-size:22px;background:transparent;")
        title = QLabel("Macro Engine")
        title.setStyleSheet(
            "color:#25aff4;font-weight:700;font-size:14px;"
            "letter-spacing:0.5px;background:transparent;"
        )
        root.addWidget(logo)
        root.addWidget(title)
        root.addWidget(_vsep())

        # ── Record controls ───────────────────────────────────────────────
        self.btn_record = QPushButton("⏺  Record")
        self.btn_record.setProperty("role", "record")
        self.btn_record.setFixedHeight(32)
        self.btn_record.setToolTip("Start recording (F9)")
        self.btn_record.clicked.connect(self.record_requested)

        self.btn_stop_record = QPushButton("⏹")
        self.btn_stop_record.setFixedSize(32, 32)
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

        root.addWidget(self.btn_record)
        root.addWidget(self.btn_stop_record)
        root.addWidget(self._blink_indicator)
        root.addWidget(self._block_count_label)
        root.addWidget(_vsep())

        # ── Playback controls ─────────────────────────────────────────────
        self.btn_play = QPushButton("▶  Play")
        self.btn_play.setProperty("role", "play")
        self.btn_play.setFixedHeight(32)
        self.btn_play.setToolTip("Play macro (F6)")
        self.btn_play.clicked.connect(self._on_play_clicked)

        self.btn_stop_play = QPushButton("⏹")
        self.btn_stop_play.setFixedSize(32, 32)
        self.btn_stop_play.setToolTip("Stop playback (F8)")
        self.btn_stop_play.setEnabled(False)
        self.btn_stop_play.clicked.connect(self.stop_play_requested)

        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet(
            "color:#25aff4;font-size:11px;font-weight:600;"
            "min-width:80px;background:transparent;"
        )
        self._progress_label.hide()

        root.addWidget(self.btn_play)
        root.addWidget(self.btn_stop_play)
        root.addWidget(self._progress_label)

        root.addStretch()

        # ── Speed slider ──────────────────────────────────────────────────
        root.addWidget(self._make_speed_col())
        root.addSpacing(8)

        # ── Repeats ───────────────────────────────────────────────────────
        rep_col = _labeled_col("REPEATS")
        self._spin_repeat = QSpinBox()
        self._spin_repeat.setRange(1, 9999)
        self._spin_repeat.setValue(1)
        self._spin_repeat.setFixedWidth(62)
        rep_col.layout().addWidget(self._spin_repeat)
        root.addWidget(rep_col)
        root.addSpacing(8)

        # ── Loop toggle ───────────────────────────────────────────────────
        loop_col = _labeled_col("")
        self._chk_infinite = QPushButton("∞  Loop")
        self._chk_infinite.setProperty("role", "toggle")
        self._chk_infinite.setCheckable(True)
        self._chk_infinite.setFixedHeight(28)
        self._chk_infinite.setToolTip("Loop infinitely until Stop is pressed")
        self._chk_infinite.toggled.connect(lambda on: self._spin_repeat.setEnabled(not on))
        loop_col.layout().addWidget(self._chk_infinite)
        root.addWidget(loop_col)

        root.addWidget(_vsep())

        # ── Settings ──────────────────────────────────────────────────────
        self._btn_settings = QPushButton("⚙")
        self._btn_settings.setProperty("role", "icon_btn")
        self._btn_settings.setFixedSize(32, 32)
        self._btn_settings.setToolTip("Settings")
        self._btn_settings.clicked.connect(self.settings_requested)
        root.addWidget(self._btn_settings)

        # ── Blink timer ───────────────────────────────────────────────────
        self._blink_visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(500)
        self._blink_timer.timeout.connect(self._toggle_blink)

    # ── Private ───────────────────────────────────────────────────────────

    def _make_speed_col(self) -> QWidget:
        col = _labeled_col("PLAYBACK SPEED")
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(1, 50)   # ÷10 → 0.1x … 5.0x
        self._speed_slider.setValue(10)
        self._speed_slider.setFixedWidth(80)
        self._speed_slider.setToolTip("Playback speed")
        self._speed_slider.valueChanged.connect(self._on_slider_speed_changed)

        # Direct numeric input — bidirectionally synced with the slider
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 5.0)
        self._speed_spin.setSingleStep(0.1)
        self._speed_spin.setValue(1.0)
        self._speed_spin.setDecimals(1)
        self._speed_spin.setFixedWidth(58)
        self._speed_spin.setSuffix("×")
        self._speed_spin.valueChanged.connect(self._on_spinbox_speed_changed)

        hl.addWidget(self._speed_slider)
        hl.addWidget(self._speed_spin)
        col.layout().addWidget(row)
        return col

    def _on_play_clicked(self) -> None:
        repeat = -1 if self._chk_infinite.isChecked() else self._spin_repeat.value()
        self.play_requested.emit(self._speed_spin.value(), repeat)

    def _on_slider_speed_changed(self, val: int) -> None:
        # Slider → spinbox (block spinbox signal to avoid loop)
        self._speed_spin.blockSignals(True)
        self._speed_spin.setValue(val / 10.0)
        self._speed_spin.blockSignals(False)

    def _on_spinbox_speed_changed(self, val: float) -> None:
        # Spinbox → slider (block slider signal to avoid loop)
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(round(val * 10))
        self._speed_slider.blockSignals(False)

    def _toggle_blink(self) -> None:
        self._blink_visible = not self._blink_visible
        color = "#ef4444" if self._blink_visible else "transparent"
        self._blink_indicator.setStyleSheet(
            f"color:{color};font-size:14px;background:transparent;"
        )

    # ── Public API (mirrors ToolbarPanel) ─────────────────────────────────

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
            self._progress_label.show()
        else:
            self.btn_play.setEnabled(True)
            self.btn_stop_play.setEnabled(False)
            self._progress_label.hide()

    def set_playback_progress(self, index: int, total: int) -> None:
        self._progress_label.setText(f"Step {index} / {total}")


# ── Module-level helpers ──────────────────────────────────────────────────

def _vsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFrameShadow(QFrame.Shadow.Plain)
    f.setStyleSheet("color:#1e2d37;")
    f.setFixedHeight(28)
    return f


def _labeled_col(label_text: str) -> QWidget:
    w = QWidget()
    vl = QVBoxLayout(w)
    vl.setContentsMargins(0, 2, 0, 2)
    vl.setSpacing(2)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(
        "color:#64748b;font-size:9px;font-weight:700;"
        "letter-spacing:0.5px;background:transparent;"
    )
    vl.addWidget(lbl)
    return w
