"""Regression tests: stop-hotkey key-up must NOT leak into recorded blocks.

After the stop hotkey press fires STOP_SENTINEL, the matching key-up event
must be silently dropped. A different key's release must still be recorded.
_stop_key_consumed must reset to False after the suppressed release so the
next recording session starts clean.
"""
from __future__ import annotations

import queue
import time

from pynput import keyboard

from macro_thunder.models.blocks import KeyPressBlock
from macro_thunder.recorder import RecorderService


def _make_fkey(name: str) -> keyboard.Key:
    """Return the pynput Key object for a function key by name (e.g. 'f8')."""
    return getattr(keyboard.Key, name)


class TestStopKeyResidue:
    """Stop-hotkey release must not enqueue a KeyPressBlock."""

    def setup_method(self):
        self.q: queue.Queue = queue.Queue()
        # Use F8 as stop hotkey (pynput format: "<f8>")
        self.svc = RecorderService(self.q, stop_hotkey="<f8>")
        self.svc._record_start = time.perf_counter()
        self.svc._held_at_start = set()  # clean start

    def _drain(self) -> list:
        items = []
        while not self.q.empty():
            items.append(self.q.get_nowait())
        return items

    def test_stop_key_press_emits_sentinel(self):
        """Pressing the stop key must put STOP_SENTINEL (not a KeyPressBlock)."""
        self.svc._on_press(_make_fkey("f8"))
        items = self._drain()
        assert items == [RecorderService.STOP_SENTINEL], (
            f"Expected only STOP_SENTINEL, got {items}"
        )

    def test_stop_key_release_does_not_enqueue_block(self):
        """After stop-key press, the matching release must be silently dropped."""
        self.svc._on_press(_make_fkey("f8"))
        self._drain()  # clear sentinel

        self.svc._on_release(_make_fkey("f8"))
        items = self._drain()

        assert items == [], (
            f"Stop key release leaked into queue: {items}"
        )

    def test_other_key_release_still_recorded_after_stop_key(self):
        """A different key's release is still queued normally after stop press+release."""
        self.svc._on_press(_make_fkey("f8"))
        self._drain()  # clear sentinel

        self.svc._on_release(_make_fkey("f8"))  # suppress stop release
        self.svc._on_release(_make_fkey("f9"))   # different key — must be recorded
        items = self._drain()

        assert len(items) == 1, f"Expected exactly 1 item, got {items}"
        assert isinstance(items[0], KeyPressBlock)
        assert items[0].direction == "up"

    def test_stop_key_consumed_resets_after_suppressed_release(self):
        """_stop_key_consumed is False after the release is suppressed."""
        self.svc._on_press(_make_fkey("f8"))
        self._drain()
        assert self.svc._stop_key_consumed is True  # set after press

        self.svc._on_release(_make_fkey("f8"))
        assert self.svc._stop_key_consumed is False  # reset after release

    def test_stop_key_consumed_false_at_init(self):
        """_stop_key_consumed initialises to False on a fresh RecorderService."""
        fresh = RecorderService(queue.Queue(), stop_hotkey="<f8>")
        assert fresh._stop_key_consumed is False
