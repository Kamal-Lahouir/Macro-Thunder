"""PlaybackEngine — perf_counter-based timing loop with pynput injection.

No Qt imports. Communicates progress via on_progress callback only.
Caller must bridge the callback to Qt via queue.Queue + QTimer.
"""
from __future__ import annotations

import time
import threading
from typing import Callable, List, Optional

from pynput import mouse, keyboard

from macro_thunder.models.blocks import (
    ActionBlock,
    MouseMoveBlock,
    MouseClickBlock,
    MouseScrollBlock,
    KeyPressBlock,
)


class PlaybackEngine:
    """Dispatches ActionBlocks to pynput controllers with perf_counter timing.

    Args:
        mouse_ctrl: pynput.mouse.Controller (or mock). Created if None.
        kb_ctrl: pynput.keyboard.Controller (or mock). Created if None.
        on_progress: callable(index: int, total: int) called after each block
            dispatch. Called from the playback thread — use a queue to bridge
            to Qt.
    """

    def __init__(
        self,
        mouse_ctrl=None,
        kb_ctrl=None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self._mouse_ctrl = mouse_ctrl if mouse_ctrl is not None else mouse.Controller()
        self._kb_ctrl = kb_ctrl if kb_ctrl is not None else keyboard.Controller()
        self._on_progress = on_progress
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(
        self,
        blocks: List[ActionBlock],
        speed: float = 1.0,
        repeat: int = 1,
    ) -> None:
        """Start playback in a daemon background thread. Returns immediately."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(blocks, speed, repeat),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the playback thread to exit. Safe to call at any time."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(
        self,
        blocks: List[ActionBlock],
        speed: float,
        repeat: int,
    ) -> None:
        """Main playback loop. Runs on background thread."""
        for _ in range(repeat):
            t0 = time.perf_counter()
            for i, block in enumerate(blocks):
                if self._stop_event.is_set():
                    return

                # Compute absolute target time for this block
                target = t0 + block.timestamp / speed  # type: ignore[union-attr]

                # Coarse sleep to avoid busy-waiting for most of the delay
                remaining = target - time.perf_counter()
                if remaining > 0.002:
                    time.sleep(remaining - 0.002)

                # Spin-wait for precision
                while time.perf_counter() < target:
                    pass

                self._dispatch(block)

                if self._on_progress is not None:
                    self._on_progress(i + 1, len(blocks))

    def _dispatch(self, block: object) -> None:
        """Dispatch a single block to the appropriate pynput controller."""
        if isinstance(block, MouseMoveBlock):
            self._mouse_ctrl.position = (block.x, block.y)

        elif isinstance(block, MouseClickBlock):
            btn = mouse.Button[block.button]
            if block.direction == "down":
                self._mouse_ctrl.press(btn)
            else:
                self._mouse_ctrl.release(btn)

        elif isinstance(block, MouseScrollBlock):
            self._mouse_ctrl.scroll(block.dx, block.dy)

        elif isinstance(block, KeyPressBlock):
            key = self._parse_key(block.key)
            if block.direction == "down":
                self._kb_ctrl.press(key)
            else:
                self._kb_ctrl.release(key)

        # DelayBlock, LabelBlock, GotoBlock, WindowFocusBlock: no-op (Phase 4)
        # Unknown / future block types: silently ignored

    @staticmethod
    def _parse_key(key_str: str):
        """Parse a key string into a pynput Key or KeyCode.

        'Key.shift' -> keyboard.Key.shift
        'a'         -> keyboard.KeyCode.from_char('a')
        """
        if key_str.startswith("Key."):
            return keyboard.Key[key_str[4:]]
        return keyboard.KeyCode.from_char(key_str)
