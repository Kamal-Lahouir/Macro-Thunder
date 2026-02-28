"""Tests for PlaybackEngine — dispatch, timing, stop, progress, repeat, speed."""
import time
import threading
from unittest.mock import MagicMock, call

import pytest
from pynput.mouse import Button
from pynput.keyboard import Key, KeyCode

from macro_thunder.models.blocks import (
    MouseMoveBlock,
    MouseClickBlock,
    MouseScrollBlock,
    KeyPressBlock,
    DelayBlock,
    LabelBlock,
    GotoBlock,
)
from macro_thunder.engine import PlaybackEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_engine():
    mock_mouse = MagicMock()
    mock_kb = MagicMock()
    engine = PlaybackEngine(mouse_ctrl=mock_mouse, kb_ctrl=mock_kb)
    return engine, mock_mouse, mock_kb


# ---------------------------------------------------------------------------
# DISPATCH tests (call _dispatch() directly, no timing involved)
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_mouse_move(self):
        engine, mock_mouse, _ = make_engine()
        block = MouseMoveBlock(x=100, y=200, timestamp=0.0)
        engine._dispatch(block)
        assert mock_mouse.position == (100, 200)

    def test_mouse_click_down(self):
        engine, mock_mouse, _ = make_engine()
        block = MouseClickBlock(x=0, y=0, button="left", direction="down", timestamp=0.0)
        engine._dispatch(block)
        mock_mouse.press.assert_called_once_with(Button.left)

    def test_mouse_click_up(self):
        engine, mock_mouse, _ = make_engine()
        block = MouseClickBlock(x=0, y=0, button="right", direction="up", timestamp=0.0)
        engine._dispatch(block)
        mock_mouse.release.assert_called_once_with(Button.right)

    def test_mouse_scroll(self):
        engine, mock_mouse, _ = make_engine()
        block = MouseScrollBlock(x=0, y=0, dx=0, dy=-3, timestamp=0.0)
        engine._dispatch(block)
        mock_mouse.scroll.assert_called_once_with(0, -3)

    def test_key_press_special(self):
        engine, _, mock_kb = make_engine()
        block = KeyPressBlock(key="Key.shift", direction="down", timestamp=0.0)
        engine._dispatch(block)
        mock_kb.press.assert_called_once_with(Key.shift)

    def test_key_release_char(self):
        engine, _, mock_kb = make_engine()
        block = KeyPressBlock(key="a", direction="up", timestamp=0.0)
        engine._dispatch(block)
        mock_kb.release.assert_called_once_with(KeyCode.from_char("a"))

    def test_delay_block_noop(self):
        """DelayBlock is a no-op in Phase 2 — must not raise."""
        engine, mock_mouse, mock_kb = make_engine()
        block = DelayBlock(duration=1.0)
        engine._dispatch(block)  # should not raise

    def test_label_block_noop(self):
        """LabelBlock is a no-op — must not raise."""
        engine, mock_mouse, mock_kb = make_engine()
        block = LabelBlock(name="start")
        engine._dispatch(block)

    def test_goto_block_noop(self):
        """GotoBlock is a no-op — must not raise."""
        engine, _, _ = make_engine()
        block = GotoBlock(target="start")
        engine._dispatch(block)

    def test_unknown_block_noop(self):
        """Completely unknown object should be silently ignored."""
        engine, _, _ = make_engine()
        engine._dispatch(object())  # should not raise


# ---------------------------------------------------------------------------
# STOP test
# ---------------------------------------------------------------------------

class TestStop:
    def test_stop_halts_playback(self):
        engine, mock_mouse, _ = make_engine()

        # 3 blocks all at t=0.0 (tight timing — will dispatch as fast as possible)
        blocks = [
            MouseMoveBlock(x=i, y=i, timestamp=0.0)
            for i in range(3)
        ]

        dispatch_count = [0]
        original_dispatch = engine._dispatch
        def counting_dispatch(block):
            dispatch_count[0] += 1
            time.sleep(0.002)  # 2ms per block so 300 blocks takes ~0.6s
            original_dispatch(block)
        engine._dispatch = counting_dispatch

        engine.start(blocks, speed=1.0, repeat=100)
        time.sleep(0.05)  # stop after ~25 dispatches
        engine.stop()

        # Retrieve the thread before it clears (engine keeps reference)
        thread = engine._thread
        if thread:
            thread.join(timeout=2.0)
            assert not thread.is_alive(), "Playback thread did not exit within 2 seconds"

        assert dispatch_count[0] < 300, (
            f"Expected fewer than 300 dispatches (not all repeats), got {dispatch_count[0]}"
        )


# ---------------------------------------------------------------------------
# PROGRESS callback test
# ---------------------------------------------------------------------------

class TestProgress:
    def test_progress_tuples_emitted_in_order(self):
        progress_calls = []

        def on_progress(index, total):
            progress_calls.append((index, total))

        mock_mouse = MagicMock()
        mock_kb = MagicMock()
        engine = PlaybackEngine(
            mouse_ctrl=mock_mouse,
            kb_ctrl=mock_kb,
            on_progress=on_progress,
        )

        blocks = [
            MouseMoveBlock(x=0, y=0, timestamp=0.0),
            MouseMoveBlock(x=1, y=1, timestamp=0.0),
        ]

        engine.start(blocks, speed=1.0, repeat=1)
        thread = engine._thread
        thread.join(timeout=2.0)

        assert progress_calls == [(1, 2), (2, 2)]


# ---------------------------------------------------------------------------
# REPEAT test
# ---------------------------------------------------------------------------

class TestRepeat:
    def test_repeat_calls_progress_n_times(self):
        progress_calls = []

        def on_progress(index, total):
            progress_calls.append((index, total))

        mock_mouse = MagicMock()
        mock_kb = MagicMock()
        engine = PlaybackEngine(
            mouse_ctrl=mock_mouse,
            kb_ctrl=mock_kb,
            on_progress=on_progress,
        )

        blocks = [
            MouseMoveBlock(x=0, y=0, timestamp=0.0),
            MouseMoveBlock(x=1, y=1, timestamp=0.0),
        ]

        engine.start(blocks, speed=1.0, repeat=3)
        thread = engine._thread
        thread.join(timeout=5.0)

        # 2 blocks × 3 repeats = 6 progress calls
        assert len(progress_calls) == 6


# ---------------------------------------------------------------------------
# SPEED test (structural)
# ---------------------------------------------------------------------------

class TestSpeed:
    def test_high_speed_dispatches_all_blocks(self):
        """At speed=10x all blocks (even with timestamps) should dispatch quickly."""
        progress_calls = []

        def on_progress(index, total):
            progress_calls.append((index, total))

        mock_mouse = MagicMock()
        mock_kb = MagicMock()
        engine = PlaybackEngine(
            mouse_ctrl=mock_mouse,
            kb_ctrl=mock_kb,
            on_progress=on_progress,
        )

        # blocks spread over 1 second — at speed=10x should finish in ~0.1s
        blocks = [
            MouseMoveBlock(x=0, y=0, timestamp=0.0),
            MouseMoveBlock(x=1, y=1, timestamp=0.5),
            MouseMoveBlock(x=2, y=2, timestamp=1.0),
        ]

        engine.start(blocks, speed=10.0, repeat=1)
        thread = engine._thread
        thread.join(timeout=2.0)

        assert not thread.is_alive()
        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)
