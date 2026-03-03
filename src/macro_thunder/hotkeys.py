from __future__ import annotations
import ctypes
import ctypes.wintypes
import queue
import sys
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from pynput import keyboard

from macro_thunder.settings import AppSettings

# ---------------------------------------------------------------------------
# Win32 RegisterHotKey support
# ---------------------------------------------------------------------------

_MOD_ALT      = 0x0001
_MOD_CONTROL  = 0x0002
_MOD_SHIFT    = 0x0004
_MOD_WIN      = 0x0008
_MOD_NOREPEAT = 0x4000  # don't re-fire while key is held

WM_HOTKEY = 0x0312  # exported so MainWindow can compare against it

_VK_MAP: dict[str, int] = {
    # Function keys
    "f1": 0x70, "f2": 0x71, "f3": 0x72,  "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76,  "f8": 0x77,
    "f9": 0x78, "f10": 0x79,"f11": 0x7A, "f12": 0x7B,
    # Navigation / editing
    "enter": 0x0D, "return": 0x0D,
    "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "tab": 0x09,
    "esc": 0x1B, "escape": 0x1B,
    "home": 0x24, "end": 0x23,
    "page_up": 0x21, "pageup": 0x21,
    "page_down": 0x22, "pagedown": 0x22,
    "insert": 0x2D,
    "left": 0x25, "right": 0x27, "up": 0x26, "down": 0x28,
    "space": 0x20,
    "print_screen": 0x2C,
    "scroll_lock": 0x91,
    "pause": 0x13,
    "num_lock": 0x90,
    "caps_lock": 0x14,
}


def _parse_hotkey_win32(hotkey_str: str) -> tuple[int, int] | None:
    """Parse a pynput-format hotkey string into (win32_modifiers, vk_code).

    Returns None if the string is empty or contains an unrecognised key.
    Examples:
        "<ctrl>+<f8>"  → (MOD_CONTROL | MOD_NOREPEAT, 0x77)
        "<alt>+a"      → (MOD_ALT | MOD_NOREPEAT, 0x41)
        "<f9>"         → (MOD_NOREPEAT, 0x78)
    """
    if not hotkey_str:
        return None

    mods = _MOD_NOREPEAT
    vk = 0

    for part in hotkey_str.lower().split("+"):
        token = part.strip().strip("<>")
        if token in ("ctrl", "control"):
            mods |= _MOD_CONTROL
        elif token == "alt":
            mods |= _MOD_ALT
        elif token == "shift":
            mods |= _MOD_SHIFT
        elif token in ("cmd", "win", "super", "meta"):
            mods |= _MOD_WIN
        elif token in _VK_MAP:
            vk = _VK_MAP[token]
        elif len(token) == 1 and token.isalpha():
            vk = ord(token.upper())
        elif len(token) == 1 and token.isdigit():
            vk = ord(token)
        else:
            return None  # unrecognised — don't register

    return (mods, vk) if vk else None


class Win32HotkeyService:
    """Wraps RegisterHotKey / UnregisterHotKey for a given HWND.

    IDs 1–5 are reserved for Macro Thunder actions:
        1 = start_record
        2 = stop_record
        3 = start_play
        4 = stop_play
        5 = record_here
    """

    _ID_MAP = {
        1: "start_record",
        2: "stop_record",
        3: "start_play",
        4: "stop_play",
        5: "record_here",
    }
    _ACTION_TO_ID = {v: k for k, v in _ID_MAP.items()}

    def __init__(self) -> None:
        self._hwnd: int = 0
        self._registered: set[int] = set()

    def set_hwnd(self, hwnd: int) -> None:
        self._hwnd = hwnd

    def register(self, settings: AppSettings) -> None:
        """Unregister all and re-register from current settings."""
        self.unregister_all()
        if not self._hwnd or sys.platform != "win32":
            return

        pairs = [
            ("start_record", settings.hotkey_start_record),
            ("stop_record",  settings.hotkey_stop_record),
            ("start_play",   settings.hotkey_start_play),
            ("stop_play",    settings.hotkey_stop_play),
            ("record_here",  settings.hotkey_record_here),
        ]
        for action, hotkey_str in pairs:
            if not hotkey_str:
                continue
            parsed = _parse_hotkey_win32(hotkey_str)
            if parsed is None:
                continue
            mods, vk = parsed
            hid = self._ACTION_TO_ID[action]
            ok = ctypes.windll.user32.RegisterHotKey(self._hwnd, hid, mods, vk)
            if ok:
                self._registered.add(hid)

    def unregister_all(self) -> None:
        if not self._hwnd or sys.platform != "win32":
            return
        for hid in list(self._registered):
            ctypes.windll.user32.UnregisterHotKey(self._hwnd, hid)
        self._registered.clear()

    def action_for_id(self, hid: int) -> str | None:
        """Return the action name for a WM_HOTKEY wParam, or None."""
        return self._ID_MAP.get(hid)


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
