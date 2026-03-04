"""RecorderService — pynput-based input capture pipeline.

No Qt imports. Uses queue.Queue + callback pattern exclusively.
Caller is responsible for draining the queue (QTimer in UI layer).
"""
from __future__ import annotations

import math
import queue
import time
from typing import Optional

from pynput import keyboard, mouse

from macro_thunder.models.blocks import (
    KeyPressBlock,
    MouseClickBlock,
    MouseMoveBlock,
    MouseScrollBlock,
)


class RecorderService:
    """Captures mouse and keyboard events and puts ActionBlock instances into a queue.

    Parameters
    ----------
    event_queue:
        Caller-supplied queue.Queue. Blocks are put() from pynput listener threads.
    pixel_threshold:
        Minimum pixel distance (Euclidean) between consecutive mouse-move events.
        Moves smaller than this value are discarded. Default: 3.
    """

    # Sentinel value put into the event queue when the stop hotkey is pressed
    # inside the recording listener itself (bypasses GlobalHotKeys chain).
    STOP_SENTINEL = "__STOP__"

    def __init__(
        self,
        event_queue: queue.Queue,
        pixel_threshold: int = 3,
        click_mode: str = "separate",
        stop_hotkey: str = "",
    ) -> None:
        self._queue = event_queue
        self._threshold = pixel_threshold
        self._click_mode = click_mode
        self._stop_hotkey_str = stop_hotkey  # e.g. "<f8>" or "<ctrl>+a"
        self._record_start: float = 0.0
        self._last_move_x: Optional[int] = None
        self._last_move_y: Optional[int] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._kb_listener: Optional[keyboard.Listener] = None
        # Keys physically held at recording start (hotkey residue).
        # Their first release is silently skipped; they're recorded normally thereafter.
        self._held_at_start: set = set()
        # Set to True when the stop hotkey press fires STOP_SENTINEL so the
        # matching key-up can be suppressed in _on_release.
        self._stop_key_consumed: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, record_start_time: Optional[float] = None) -> None:
        """Begin capturing input events.

        Parameters
        ----------
        record_start_time:
            Override the recording start time (float from time.perf_counter()).
            If None, uses the current time.
        """
        self._record_start = record_start_time if record_start_time is not None else time.perf_counter()
        self._last_move_x = None
        self._last_move_y = None

        # Snapshot which keys are physically held right now so we can discard
        # their residue releases (e.g. hotkey modifiers still held when recording starts).
        try:
            self._held_at_start = set(keyboard.Controller().pressed_keys)
        except Exception:
            self._held_at_start = set()

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
            win32_event_filter=self._mouse_filter,
        )
        self._kb_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            win32_event_filter=self._kb_filter,
        )
        self._mouse_listener.start()
        self._kb_listener.start()

    def stop(self) -> None:
        """Stop capturing. Safe to call multiple times or before start()."""
        if self._mouse_listener is not None:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        if self._kb_listener is not None:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None

    # ------------------------------------------------------------------
    # Internal callbacks — MUST NOT touch Qt objects
    # ------------------------------------------------------------------

    def _on_move(self, x: int, y: int) -> None:
        ts = time.perf_counter() - self._record_start
        if self._last_move_x is None:
            # First move — always queue and establish baseline
            self._last_move_x = x
            self._last_move_y = y
            self._queue.put(MouseMoveBlock(x=x, y=y, timestamp=ts))
            return

        dist = math.hypot(x - self._last_move_x, y - self._last_move_y)
        if dist < self._threshold:
            return  # discard sub-threshold move; do NOT update last position

        self._last_move_x = x
        self._last_move_y = y
        self._queue.put(MouseMoveBlock(x=x, y=y, timestamp=ts))

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        ts = time.perf_counter() - self._record_start
        if self._click_mode == "combined":
            # In combined mode emit a single "click" block only on press;
            # suppress the release so the pair appears as one block.
            if pressed:
                self._queue.put(
                    MouseClickBlock(
                        x=x,
                        y=y,
                        button=button.name,
                        direction="click",
                        timestamp=ts,
                    )
                )
        else:
            self._queue.put(
                MouseClickBlock(
                    x=x,
                    y=y,
                    button=button.name,
                    direction="down" if pressed else "up",
                    timestamp=ts,
                )
            )

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        ts = time.perf_counter() - self._record_start
        self._queue.put(MouseScrollBlock(x=x, y=y, dx=dx, dy=dy, timestamp=ts))

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        # If this key was held before recording started (hotkey residue), it has
        # now been released and re-pressed — clear it from the held set and record
        # it as intentional from this point onward.
        self._held_at_start.discard(key)

        # Direct stop-hotkey fallback in case the GlobalHotKeys chain is broken.
        if self._stop_hotkey_str and self._matches_stop_hotkey(key):
            self._stop_key_consumed = True
            self._queue.put(self.STOP_SENTINEL)
            return  # don't record the stop key itself

        ts = time.perf_counter() - self._record_start
        if self._click_mode == "combined":
            self._queue.put(KeyPressBlock(key=self._key_to_str(key), direction="key", timestamp=ts))
        else:
            self._queue.put(KeyPressBlock(key=self._key_to_str(key), direction="down", timestamp=ts))

    def _matches_stop_hotkey(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        """Return True if *key* is the final (non-modifier) key of the stop hotkey.

        We only check the primary key here, not the full modifier combination,
        because pynput fires _on_press once per individual key. The correct
        multi-key check is handled by GlobalHotKeys; this is only a fallback
        for when that chain fails.
        """
        if not self._stop_hotkey_str:
            return False
        # Extract the last token after '+' stripping angle brackets
        last_token = self._stop_hotkey_str.split("+")[-1].strip("<>").lower()
        key_str = self._key_to_str(key).lower()
        # Map pynput key names to bare names for comparison
        # e.g. "Key.f8" -> "f8", "a" -> "a"
        if key_str.startswith("key."):
            key_str = key_str[4:]
        return key_str == last_token

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        # Silently drop the release of any key that was physically held when
        # recording started (hotkey modifier/trigger residue, not intentional input).
        if key in self._held_at_start:
            self._held_at_start.discard(key)
            return

        if self._stop_key_consumed and self._matches_stop_hotkey(key):
            self._stop_key_consumed = False
            return

        if self._click_mode == "combined":
            return  # suppress release — combined mode emits a single "key" block on press
        ts = time.perf_counter() - self._record_start
        self._queue.put(KeyPressBlock(key=self._key_to_str(key), direction="up", timestamp=ts))

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _key_to_str(key: keyboard.Key | keyboard.KeyCode) -> str:
        """Convert a pynput key object to a stable string representation."""
        if isinstance(key, keyboard.Key):
            return f"Key.{key.name}"
        if hasattr(key, "char") and key.char:
            return key.char
        return str(key)

    @staticmethod
    def _mouse_filter(msg, data) -> bool:
        """Return False to suppress injected mouse events (e.g. from playback)."""
        LLMHF_INJECTED = 0x00000001
        return not bool(data.flags & LLMHF_INJECTED)

    @staticmethod
    def _kb_filter(msg, data) -> bool:
        """Return False to suppress injected keyboard events."""
        LLKHF_INJECTED = 0x00000010  # bit 4
        return not bool(data.flags & LLKHF_INJECTED)
