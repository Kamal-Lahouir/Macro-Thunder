from __future__ import annotations
import queue
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from pynput import keyboard

from macro_thunder.settings import AppSettings


class HotkeyManager(QObject):
    """Registers global hotkeys via pynput and emits Qt signals on the main thread.

    Hotkey callbacks run on the pynput listener thread — they ONLY put a string
    into _hotkey_queue.  A QTimer on the main thread drains the queue and emits
    the corresponding Qt signal.  This satisfies the project threading rule:
    pynput callbacks MUST NEVER touch Qt objects directly.
    """

    start_record = pyqtSignal()
    stop_record = pyqtSignal()
    start_play = pyqtSignal()
    stop_play = pyqtSignal()
    record_here = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._hotkey_queue: queue.Queue[str] = queue.Queue()
        self._listener: Optional[keyboard.GlobalHotKeys] = None

        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(16)  # ~60 Hz drain
        self._drain_timer.timeout.connect(self._drain)
        self._drain_timer.start()

    def register(self, settings: AppSettings) -> None:
        """Stop any existing listener and start a new one with the given settings."""
        self.stop()

        q = self._hotkey_queue  # local alias so lambdas don't close over self

        hotkey_map = {
            settings.hotkey_start_record: lambda: q.put("start_record"),
            settings.hotkey_stop_record: lambda: q.put("stop_record"),
            settings.hotkey_start_play: lambda: q.put("start_play"),
            settings.hotkey_stop_play: lambda: q.put("stop_play"),
        }
        if settings.hotkey_record_here:
            hotkey_map[settings.hotkey_record_here] = lambda: q.put("record_here")

        listener = keyboard.GlobalHotKeys(hotkey_map)
        listener.daemon = True
        listener.start()
        self._listener = listener

    def stop(self) -> None:
        """Stop the current hotkey listener if one is running."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _drain(self) -> None:
        """Drain _hotkey_queue on the main thread and emit the matching signal."""
        while not self._hotkey_queue.empty():
            try:
                action = self._hotkey_queue.get_nowait()
            except queue.Empty:
                break
            if action == "start_record":
                self.start_record.emit()
            elif action == "stop_record":
                self.stop_record.emit()
            elif action == "start_play":
                self.start_play.emit()
            elif action == "stop_play":
                self.stop_play.emit()
            elif action == "record_here":
                self.record_here.emit()
