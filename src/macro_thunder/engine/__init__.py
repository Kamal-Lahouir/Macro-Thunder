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
    DelayBlock,
    LabelBlock,
    GotoBlock,
    WindowFocusBlock,
)
from macro_thunder.engine.window_utils import (
    _find_window,
    _activate_window,
    _set_window_rect,
)


class PlaybackEngine:
    """Dispatches ActionBlocks to pynput controllers with perf_counter timing.

    Args:
        mouse_ctrl: pynput.mouse.Controller (or mock). Created if None.
        kb_ctrl: pynput.keyboard.Controller (or mock). Created if None.
        on_progress: callable(index: int, total: int) called after each block
            dispatch. Called from the playback thread — use a queue to bridge
            to Qt.
        on_loop_detected: callable(flat_index: int, label_name: str) called when
            a GotoBlock fires more than 1000 times without non-flow progress.
            Called from the playback thread — use a queue to bridge to Qt.
    """

    def __init__(
        self,
        mouse_ctrl=None,
        kb_ctrl=None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_loop_detected: Optional[Callable[[int, str], None]] = None,
        on_done: Optional[Callable[[], None]] = None,
    ) -> None:
        self._mouse_ctrl = mouse_ctrl if mouse_ctrl is not None else mouse.Controller()
        self._kb_ctrl = kb_ctrl if kb_ctrl is not None else keyboard.Controller()
        self._on_progress = on_progress
        self._on_loop_detected = on_loop_detected
        self._on_done = on_done
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
        start_index: int = 0,
    ) -> None:
        """Start playback in a daemon background thread. Returns immediately."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(blocks, speed, repeat, start_index),
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
        start_index: int = 0,
    ) -> None:
        """Main playback loop. Runs on background thread."""
        # Build label index once per _run call (outside repeat loop)
        label_index: dict[str, int] = {
            b.name: idx
            for idx, b in enumerate(blocks)
            if isinstance(b, LabelBlock)
        }

        iteration = 0
        while True:
            # Check if we've hit the repeat limit (repeat=-1 means infinite)
            if repeat != -1 and iteration >= repeat:
                break
            if self._stop_event.is_set():
                return  # immediate stop, no on_done

            t0 = time.perf_counter()
            # virtual_time: monotonically-increasing playback clock (recording seconds).
            # Advances by each block's recorded gap from the previous block, plus any
            # DelayBlock durations. Using gaps (not raw timestamps) means manually
            # inserted blocks (timestamp=0) or appended recordings (timestamps restart
            # from 0) fire immediately after the previous block rather than jumping
            # back in time.
            virtual_time = 0.0
            prev_ts = 0.0  # recording timestamp of the last real block seen

            # start_index only applies to the first iteration; subsequent repeats
            # always play the full macro from the beginning.
            i = max(0, min(start_index, len(blocks) - 1)) if iteration == 0 else 0
            goto_fire_count: dict[int, int] = {}
            progress_since_last_goto = False

            while i < len(blocks):
                if self._stop_event.is_set():
                    return

                block = blocks[i]

                # --- Flow control: Label ---
                if isinstance(block, LabelBlock):
                    # Labels are jump targets only — do NOT count as progress.
                    # Only real action blocks reset the loop-detection counter.
                    i += 1
                    continue

                # --- Flow control: Goto ---
                if isinstance(block, GotoBlock):
                    if progress_since_last_goto:
                        goto_fire_count.clear()
                    count = goto_fire_count.get(i, 0) + 1
                    goto_fire_count[i] = count
                    progress_since_last_goto = False

                    if count > 1000:
                        if self._on_loop_detected:
                            self._on_loop_detected(i, block.target)
                        return

                    target_idx = label_index.get(block.target)
                    if target_idx is None:
                        return  # unresolved label (should be caught by pre-flight)
                    i = target_idx
                    continue

                # --- WindowFocus ---
                if isinstance(block, WindowFocusBlock):
                    deadline = time.perf_counter() + block.timeout
                    found_hwnd = None
                    while time.perf_counter() < deadline:
                        found_hwnd = _find_window(
                            block.executable, block.title, block.match_mode
                        )
                        if found_hwnd:
                            break
                        if self._stop_event.wait(timeout=0.5):  # returns True if set
                            return
                    if found_hwnd:
                        _activate_window(found_hwnd)
                        if block.reposition and block.w > 0 and block.h > 0:
                            _set_window_rect(found_hwnd, block.x, block.y, block.w, block.h)
                        if block.on_success_label and block.on_success_label in label_index:
                            i = label_index[block.on_success_label]
                        else:
                            i += 1
                    else:
                        if block.on_failure_label and block.on_failure_label in label_index:
                            i = label_index[block.on_failure_label]
                        else:
                            i += 1
                    progress_since_last_goto = True
                    goto_fire_count.clear()
                    continue

                # --- Normal action blocks (timing + dispatch) ---
                progress_since_last_goto = True
                goto_fire_count.clear()

                if isinstance(block, DelayBlock):
                    virtual_time += block.duration
                    target = t0 + virtual_time / speed
                else:
                    ts = block.timestamp  # type: ignore[union-attr]
                    if ts > prev_ts:
                        virtual_time += ts - prev_ts
                    # else: out-of-order / manually inserted block — fire immediately
                    # after the previous one (no gap added)
                    prev_ts = ts
                    target = t0 + virtual_time / speed

                remaining = target - time.perf_counter()
                if remaining > 0.002:
                    time.sleep(remaining - 0.002)
                while time.perf_counter() < target:
                    pass

                self._dispatch(block)

                if self._on_progress is not None:
                    self._on_progress(i, len(blocks))

                i += 1

            iteration += 1

        # All passes complete — signal done
        if self._on_done is not None:
            self._on_done()

    def _dispatch(self, block: object) -> None:
        """Dispatch a single block to the appropriate pynput controller."""
        if isinstance(block, MouseMoveBlock):
            self._mouse_ctrl.position = (block.x, block.y)

        elif isinstance(block, MouseClickBlock):
            btn = mouse.Button[block.button]
            if block.direction == "down":
                self._mouse_ctrl.press(btn)
            elif block.direction == "up":
                self._mouse_ctrl.release(btn)
            elif block.direction == "click":
                self._mouse_ctrl.press(btn)
                self._mouse_ctrl.release(btn)

        elif isinstance(block, MouseScrollBlock):
            self._mouse_ctrl.scroll(block.dx, block.dy)

        elif isinstance(block, KeyPressBlock):
            key = self._parse_key(block.key)
            if block.direction == "down":
                self._kb_ctrl.press(key)
            elif block.direction == "up":
                self._kb_ctrl.release(key)
            elif block.direction == "key":
                self._kb_ctrl.press(key)
                self._kb_ctrl.release(key)

        # LabelBlock, GotoBlock, WindowFocusBlock: handled in _run before dispatch
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
