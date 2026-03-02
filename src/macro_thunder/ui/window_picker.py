"""WindowPickerService — interactive click-to-pick-window for WindowFocus block editor.

Minimize Macro Thunder -> user clicks a window -> restore + emit (executable, title).
Threading: pynput listener callback calls _on_pick on its own thread.
pyqtSignal.emit() is thread-safe for cross-thread queued connections.
CLAUDE.md rule: pynput callbacks MUST NEVER touch Qt objects directly.
Only pyqtSignal.emit() is allowed in _on_pick(). Window restore is handled
in MainWindow slots connected to picked/cancelled signals (main thread).
"""
from __future__ import annotations
import ctypes
from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal

from macro_thunder.engine.window_utils import _hwnd_from_point, _get_window_info

IDC_CROSS = 32515


class WindowPickerService(QObject):
    """Encapsulates the minimize -> crosshair -> click -> restore -> fill cycle.

    Signals:
        picked(executable: str, title: str): emitted on successful pick
        cancelled(): emitted if no window resolved (click on desktop, etc.)

    Window restore (showNormal / activateWindow) is intentionally NOT called here.
    MainWindow must connect slots to picked and cancelled to restore itself on the
    main thread.
    """
    picked = pyqtSignal(str, str)   # (executable, title)
    cancelled = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._listener: mouse.Listener | None = None

    def start(self) -> None:
        """Minimize the app and begin waiting for a window click."""
        self.cancel()  # stop any in-progress pick
        self._main_window.showMinimized()
        # Best-effort crosshair cursor (resets on WM_SETCURSOR but provides UX hint)
        try:
            user32 = ctypes.windll.user32
            hcursor = user32.LoadCursorW(0, IDC_CROSS)
            user32.SetCursor(hcursor)
        except Exception:
            pass  # cosmetic only — failure is acceptable

        def on_click(x, y, button, pressed):
            if pressed:
                self._on_pick(x, y)
                return False  # stop listener

        self._listener = mouse.Listener(on_click=on_click)
        self._listener.start()

    def cancel(self) -> None:
        """Stop the listener if active (safe to call from closeEvent)."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_pick(self, x: int, y: int) -> None:
        """Called from pynput listener thread.

        ONLY pyqtSignal.emit() is allowed here — no Qt object calls.
        Window restore happens in MainWindow slots on the main thread.
        """
        hwnd = _hwnd_from_point(x, y)
        title, exe = _get_window_info(hwnd) if hwnd else ("", "")
        self._listener = None
        if exe or title:
            self.picked.emit(exe, title)
        else:
            self.cancelled.emit()
