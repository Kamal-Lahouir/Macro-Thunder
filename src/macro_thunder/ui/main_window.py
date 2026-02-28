from __future__ import annotations

import enum
import pathlib
import queue
from typing import Optional

from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QLabel,
    QToolBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QCursor

from macro_thunder.ui.library_panel import LibraryPanel
from macro_thunder.ui.editor_panel import EditorPanel
from macro_thunder.ui.toolbar import ToolbarPanel
from macro_thunder.ui.settings_dialog import SettingsDialog
from macro_thunder.recorder import RecorderService
from macro_thunder.engine import PlaybackEngine
from macro_thunder.hotkeys import HotkeyManager
from macro_thunder.settings import AppSettings, SETTINGS_DIR
from macro_thunder.models.document import MacroDocument
from macro_thunder.persistence import save_macro, load_macro


class AppState(enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PLAYING = "playing"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Thunder")
        self.resize(1200, 700)

        # Load settings
        self._settings = AppSettings.load()

        # Toolbar row at top
        self._toolbar_widget = ToolbarPanel()
        toolbar = QToolBar("Main Toolbar")
        toolbar.addWidget(self._toolbar_widget)
        self.addToolBar(toolbar)

        # Central area: horizontal splitter (library | editor)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._library_panel = LibraryPanel()
        self._editor_panel = EditorPanel()

        self._splitter.addWidget(self._library_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self._splitter)

        # Status bar with live coordinate readout
        self._coord_label = QLabel("X: 0  Y: 0")
        self.statusBar().addPermanentWidget(self._coord_label)

        # File menu
        file_menu = self.menuBar().addMenu("&File")

        save_action = QAction("&Save Macro...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_macro)
        file_menu.addAction(save_action)

        open_action = QAction("&Open Macro...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_macro)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        # Services
        self._rec_queue: queue.Queue = queue.Queue()
        self._recorder = RecorderService(self._rec_queue, self._settings.mouse_threshold_px)
        self._engine = PlaybackEngine(on_progress=self._on_play_progress)
        self._macro_buffer: Optional[MacroDocument] = None
        self._state: AppState = AppState.IDLE
        self._rec_blocks: list = []

        # Progress queue for thread-safe playback progress updates
        self._play_progress_queue: queue.Queue = queue.Queue()

        # Hotkey manager
        self._hotkeys = HotkeyManager(self)
        try:
            self._hotkeys.register(self._settings)
        except Exception as e:
            QMessageBox.warning(self, "Hotkey Error", str(e))

        # Connect toolbar signals
        self._toolbar_widget.record_requested.connect(self._start_record)
        self._toolbar_widget.stop_record_requested.connect(self._stop_record)
        self._toolbar_widget.play_requested.connect(self._start_play)
        self._toolbar_widget.stop_play_requested.connect(self._stop_play)

        # Connect hotkey signals
        self._hotkeys.start_record.connect(self._start_record)
        self._hotkeys.stop_record.connect(self._stop_record)
        self._hotkeys.start_play.connect(
            lambda: self._start_play(self._toolbar_widget._speed_spin.value(), 1)
        )
        self._hotkeys.stop_play.connect(self._stop_play)

        # Recording drain timer (50ms / 20 Hz)
        self._rec_drain_timer = QTimer(self)
        self._rec_drain_timer.setInterval(50)
        self._rec_drain_timer.timeout.connect(self._drain_recorder)

        # Poll QCursor.pos() at ~60 Hz and drain play progress queue
        self._coord_timer = QTimer(self)
        self._coord_timer.setInterval(16)  # ~60 Hz
        self._coord_timer.timeout.connect(self._update_status)
        self._coord_timer.start()

    # ------------------------------------------------------------------
    # Status bar timer (coordinates + play progress drain)
    # ------------------------------------------------------------------

    def _update_status(self) -> None:
        pos = QCursor.pos()  # screen-absolute, DPI-correct
        self._coord_label.setText(f"X: {pos.x()}  Y: {pos.y()}")

        # Drain playback progress queue
        while not self._play_progress_queue.empty():
            try:
                idx, total = self._play_progress_queue.get_nowait()
            except queue.Empty:
                break
            self._toolbar_widget.set_playback_progress(idx, total)
            if idx >= total:
                self._stop_play()  # auto-reset when playback finishes

    # ------------------------------------------------------------------
    # Recording slots
    # ------------------------------------------------------------------

    def _start_record(self) -> None:
        if self._state != AppState.IDLE:
            return
        self._state = AppState.RECORDING
        self._rec_blocks = []
        self._recorder.start()
        self._rec_drain_timer.start()
        self._toolbar_widget.set_recording(True, 0)

    def _stop_record(self) -> None:
        if self._state != AppState.RECORDING:
            return
        self._recorder.stop()
        self._rec_drain_timer.stop()
        self._drain_recorder()  # drain remaining events
        self._macro_buffer = MacroDocument(blocks=self._rec_blocks)
        self._state = AppState.IDLE
        self._toolbar_widget.set_recording(False)
        self._toolbar_widget.update_block_count(0)

    def _drain_recorder(self) -> None:
        while not self._rec_queue.empty():
            try:
                block = self._rec_queue.get_nowait()
            except queue.Empty:
                break
            self._rec_blocks.append(block)
            self._toolbar_widget.update_block_count(len(self._rec_blocks))

    # ------------------------------------------------------------------
    # Playback slots
    # ------------------------------------------------------------------

    def _start_play(self, speed: float = 1.0, repeat: int = 1) -> None:
        if self._state != AppState.IDLE:
            return
        if self._macro_buffer is None or not self._macro_buffer.blocks:
            QMessageBox.information(self, "No Macro", "Record or load a macro first.")
            return
        self._state = AppState.PLAYING
        self._toolbar_widget.set_playback(True)
        self._engine.start(self._macro_buffer.blocks, speed=speed, repeat=repeat)

    def _stop_play(self) -> None:
        self._engine.stop()
        self._state = AppState.IDLE
        self._toolbar_widget.set_playback(False)

    def _on_play_progress(self, index: int, total: int) -> None:
        """Called from playback thread — put into queue, drain on main thread."""
        self._play_progress_queue.put((index, total))

    # ------------------------------------------------------------------
    # File menu slots
    # ------------------------------------------------------------------

    def _save_macro(self) -> None:
        if self._macro_buffer is None:
            QMessageBox.information(self, "Nothing to Save", "No macro in memory.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Macro", str(SETTINGS_DIR), "Macro Files (*.json)"
        )
        if path:
            save_macro(self._macro_buffer, pathlib.Path(path))

    def _open_macro(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Macro", str(SETTINGS_DIR), "Macro Files (*.json)"
        )
        if path:
            self._macro_buffer = load_macro(pathlib.Path(path))
            self.statusBar().showMessage(f"Loaded: {pathlib.Path(path).name}", 3000)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._settings = dlg.get_settings()
            try:
                self._hotkeys.register(self._settings)
            except Exception as e:
                QMessageBox.warning(self, "Hotkey Error", str(e))
