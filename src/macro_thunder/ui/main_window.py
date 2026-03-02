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
from macro_thunder.ui.window_picker import WindowPickerService
from macro_thunder.recorder import RecorderService
from macro_thunder.engine import PlaybackEngine
from macro_thunder.engine.validation import validate_gotos
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
        self._picker_service = WindowPickerService(self, parent=self)
        self._editor_panel = EditorPanel(picker_service=self._picker_service)

        self._splitter.addWidget(self._library_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        # Dirty flag (unsaved-changes guard)
        self._is_dirty: bool = False

        # Connect editor dirty signal
        self._editor_panel.document_modified.connect(self._on_document_modified)

        # Connect library panel signals
        self._library_panel.load_requested.connect(self._on_library_load)
        self._library_panel.save_requested.connect(self._save_macro)

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
        self._macro_buffer: Optional[MacroDocument] = None
        self._state: AppState = AppState.IDLE
        self._rec_blocks: list = []
        self._append_after_flat: int = -2  # -2 = replace mode; >= -1 = append after that index

        # Progress queue for thread-safe playback progress updates
        self._play_progress_queue: queue.Queue = queue.Queue()

        # Loop detection queue for thread-safe loop detection notifications
        self._loop_detect_queue: queue.Queue = queue.Queue()

        self._engine = PlaybackEngine(
            on_progress=self._on_play_progress,
            on_loop_detected=self._on_loop_detected_callback,
        )

        # Hotkey manager
        self._hotkeys = HotkeyManager(self)
        try:
            self._hotkeys.register(self._settings)
        except Exception as e:
            QMessageBox.warning(self, "Hotkey Error", str(e))

        # Connect picker signals (picker_service created in __init__ above the splitter)
        self._picker_service.picked.connect(self._on_picker_picked)
        self._picker_service.cancelled.connect(self._on_picker_cancelled)

        # Connect editor "Record Here" button
        self._editor_panel.record_here_requested.connect(self._start_record_here)

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

        # Drain loop detection notifications
        while not self._loop_detect_queue.empty():
            try:
                flat_index, label_name = self._loop_detect_queue.get_nowait()
            except queue.Empty:
                break
            self._stop_play()
            # Select first so the row is visible when the dialog closes
            self._editor_panel.select_flat_index(flat_index)
            QMessageBox.warning(
                self,
                "Infinite Loop Detected",
                f"Infinite loop detected at '{label_name}' — execution stopped.\n"
                "Check your Goto blocks."
            )

    # ------------------------------------------------------------------
    # Recording slots
    # ------------------------------------------------------------------

    def _start_record(self) -> None:
        if self._state != AppState.IDLE:
            return
        self._append_after_flat = -2  # replace mode
        self._state = AppState.RECORDING
        self._rec_blocks = []
        self._recorder.start()
        self._rec_drain_timer.start()
        self._toolbar_widget.set_recording(True, 0)

    def _start_record_here(self, flat_index: int) -> None:
        """Start recording in append mode — new blocks inserted after flat_index."""
        if self._state != AppState.IDLE:
            return
        self._append_after_flat = flat_index  # >= -1: append mode
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
        self._state = AppState.IDLE
        self._toolbar_widget.set_recording(False)
        if self._append_after_flat >= -1 and self._macro_buffer is not None:
            # Append mode: insert new blocks into existing document
            self._editor_panel.insert_blocks_at(self._append_after_flat, self._rec_blocks)
            self._macro_buffer.blocks = list(self._macro_buffer.blocks)  # ensure list
            self._toolbar_widget.update_block_count(len(self._macro_buffer.blocks))
            self.statusBar().showMessage(f"Appended {len(self._rec_blocks)} blocks", 3000)
        else:
            # Replace mode: load as new document
            doc = MacroDocument(blocks=self._rec_blocks)
            self._load_document(doc)
        self._append_after_flat = -2

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
        missing = validate_gotos(self._macro_buffer.blocks)
        if missing:
            QMessageBox.critical(
                self,
                "Missing Labels",
                "Cannot play: the following label names are not defined:\n"
                + "\n".join(f"  \u2022 {m}" for m in missing),
            )
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

    def _on_loop_detected_callback(self, flat_index: int, label_name: str) -> None:
        """Called from playback thread — put into queue, drain on main thread."""
        self._loop_detect_queue.put((flat_index, label_name))

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
            p = pathlib.Path(path)
            if p.stem != self._macro_buffer.name:
                self._macro_buffer.name = p.stem
            save_macro(self._macro_buffer, p)
            self._is_dirty = False
            self._library_panel.set_dirty(False)
            self._library_panel.refresh()

    def _open_macro(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Macro", str(SETTINGS_DIR), "Macro Files (*.json)"
        )
        if path:
            doc = load_macro(pathlib.Path(path))
            self._load_document(doc)

    # ------------------------------------------------------------------
    # Integration helpers
    # ------------------------------------------------------------------

    def _load_document(self, doc: MacroDocument) -> None:
        """Central load helper: wire buffer, clear dirty, update editor."""
        self._macro_buffer = doc
        self._is_dirty = False
        self._library_panel.set_dirty(False)
        self._editor_panel.load_document(doc)
        self._toolbar_widget.update_block_count(len(doc.blocks))
        self.statusBar().showMessage(f"Loaded: {doc.name}", 3000)

    def _on_document_modified(self) -> None:
        self._is_dirty = True
        self._library_panel.set_dirty(True)

    def _on_library_load(self, path: str) -> None:
        doc = load_macro(pathlib.Path(path))
        self._load_document(doc)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._settings = dlg.get_settings()
            try:
                self._hotkeys.register(self._settings)
            except Exception as e:
                QMessageBox.warning(self, "Hotkey Error", str(e))

    # ------------------------------------------------------------------
    # Window picker slots (main thread — safe to call Qt methods here)
    # ------------------------------------------------------------------

    def _on_picker_picked(self, exe: str, title: str) -> None:
        """Runs on main thread via queued signal connection."""
        self.showNormal()
        self.activateWindow()
        # Subclasses or future block panels can override or connect to _picker.picked
        # directly to consume (exe, title) and populate a form field.

    def _on_picker_cancelled(self) -> None:
        """Runs on main thread via queued signal connection."""
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        self._picker_service.cancel()
        super().closeEvent(event)
