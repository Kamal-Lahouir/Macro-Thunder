"""Tests for RecorderService — all callback and filter behaviors.

Tests call internal callback methods directly (no OS hooks required).
"""
from __future__ import annotations

import queue
import time
import types
import unittest
from unittest.mock import MagicMock, patch

# pynput is used in RecorderService; we need the real pynput.mouse.Button and
# pynput.keyboard.Key / KeyCode for realistic test data.
from pynput import keyboard, mouse

from macro_thunder.models.blocks import (
    KeyPressBlock,
    MouseClickBlock,
    MouseMoveBlock,
    MouseScrollBlock,
)
from macro_thunder.recorder import RecorderService


class TestRecorderServiceInit:
    """RecorderService initialises with correct defaults."""

    def test_default_threshold(self):
        q = queue.Queue()
        svc = RecorderService(q)
        assert svc._threshold == 3

    def test_custom_threshold(self):
        q = queue.Queue()
        svc = RecorderService(q, pixel_threshold=10)
        assert svc._threshold == 10


class TestOnMove:
    """on_move callback: first move queues, subsequent filtered by threshold."""

    def setup_method(self):
        self.q = queue.Queue()
        self.svc = RecorderService(self.q, pixel_threshold=5)
        self.svc._record_start = time.perf_counter()

    def test_first_move_is_always_queued(self):
        self.svc._on_move(100, 200)
        assert not self.q.empty()
        block = self.q.get_nowait()
        assert isinstance(block, MouseMoveBlock)
        assert block.x == 100
        assert block.y == 200
        assert block.timestamp >= 0.0

    def test_move_below_threshold_discarded(self):
        # first move establishes baseline
        self.svc._on_move(100, 200)
        self.q.get_nowait()  # consume
        # move only sqrt(9+4)=3.6 px — below threshold=5
        self.svc._on_move(103, 202)
        assert self.q.empty()

    def test_move_above_threshold_queued(self):
        self.svc._on_move(100, 200)
        self.q.get_nowait()  # consume
        # move sqrt(36+36)≈8.5 px — above threshold=5
        self.svc._on_move(106, 206)
        assert not self.q.empty()
        block = self.q.get_nowait()
        assert isinstance(block, MouseMoveBlock)
        assert block.x == 106
        assert block.y == 206

    def test_last_position_updated_after_discard(self):
        """Even discarded moves update the last position reference."""
        self.svc._on_move(100, 200)
        self.q.get_nowait()
        # sub-threshold — discarded but last pos stays at (100,200)?
        # Per spec: only update last pos on queued events.
        # Check: next move relative to (100,200) still applies threshold.
        self.svc._on_move(103, 202)  # discarded (3.6 < 5)
        assert self.q.empty()
        # Now 3 more px from (103,202) = hypot(3,2)≈3.6 < 5 → still discarded
        self.svc._on_move(106, 204)
        # total from original (100,200) = hypot(6,4)≈7.2 > 5 → queued
        # (last pos only updates on queue, so distance is from 100,200)
        assert not self.q.empty()

    def test_timestamp_is_non_negative(self):
        self.svc._on_move(50, 50)
        block = self.q.get_nowait()
        assert block.timestamp >= 0.0


class TestOnClick:
    """on_click callback produces correct MouseClickBlock."""

    def setup_method(self):
        self.q = queue.Queue()
        self.svc = RecorderService(self.q)
        self.svc._record_start = time.perf_counter()

    def test_left_button_down(self):
        self.svc._on_click(50, 60, mouse.Button.left, True)
        block = self.q.get_nowait()
        assert isinstance(block, MouseClickBlock)
        assert block.button == "left"
        assert block.direction == "down"
        assert block.x == 50
        assert block.y == 60

    def test_right_button_up(self):
        self.svc._on_click(50, 60, mouse.Button.right, False)
        block = self.q.get_nowait()
        assert isinstance(block, MouseClickBlock)
        assert block.button == "right"
        assert block.direction == "up"

    def test_middle_button(self):
        self.svc._on_click(10, 20, mouse.Button.middle, True)
        block = self.q.get_nowait()
        assert block.button == "middle"


class TestOnScroll:
    """on_scroll callback produces correct MouseScrollBlock."""

    def setup_method(self):
        self.q = queue.Queue()
        self.svc = RecorderService(self.q)
        self.svc._record_start = time.perf_counter()

    def test_scroll_down(self):
        self.svc._on_scroll(10, 20, 0, -3)
        block = self.q.get_nowait()
        assert isinstance(block, MouseScrollBlock)
        assert block.dx == 0
        assert block.dy == -3
        assert block.x == 10
        assert block.y == 20

    def test_scroll_up(self):
        self.svc._on_scroll(0, 0, 0, 1)
        block = self.q.get_nowait()
        assert block.dy == 1


class TestOnKeyboard:
    """on_press / on_release produce correct KeyPressBlock."""

    def setup_method(self):
        self.q = queue.Queue()
        self.svc = RecorderService(self.q)
        self.svc._record_start = time.perf_counter()

    def test_key_press_special_key(self):
        self.svc._on_press(keyboard.Key.shift)
        block = self.q.get_nowait()
        assert isinstance(block, KeyPressBlock)
        assert block.key == "Key.shift"
        assert block.direction == "down"

    def test_key_press_char(self):
        self.svc._on_press(keyboard.KeyCode.from_char('a'))
        block = self.q.get_nowait()
        assert block.key == "a"
        assert block.direction == "down"

    def test_key_release(self):
        self.svc._on_release(keyboard.Key.f8)
        block = self.q.get_nowait()
        assert block.key == "Key.f8"
        assert block.direction == "up"

    def test_key_timestamp_non_negative(self):
        self.svc._on_press(keyboard.Key.ctrl_l)
        block = self.q.get_nowait()
        assert block.timestamp >= 0.0


class TestKeyToStr:
    """_key_to_str converts pynput key objects to strings."""

    def setup_method(self):
        self.svc = RecorderService(queue.Queue())

    def test_special_key(self):
        assert self.svc._key_to_str(keyboard.Key.shift) == "Key.shift"

    def test_char_keycode(self):
        assert self.svc._key_to_str(keyboard.KeyCode.from_char('z')) == "z"

    def test_unknown_key_falls_back_to_str(self):
        class _UnknownKey:
            def __str__(self):
                return "unknown_key"
        # No .char attribute, not a keyboard.Key → str(key) path
        result = self.svc._key_to_str(_UnknownKey())
        assert result == "unknown_key"


class TestInjectedEventFilters:
    """_mouse_filter and _kb_filter suppress injected OS events."""

    def setup_method(self):
        self.svc = RecorderService(queue.Queue())

    def test_mouse_filter_injected_blocked(self):
        data = types.SimpleNamespace(flags=0x00000001)  # LLMHF_INJECTED
        assert self.svc._mouse_filter(None, data) is False

    def test_mouse_filter_normal_passes(self):
        data = types.SimpleNamespace(flags=0x00000000)
        assert self.svc._mouse_filter(None, data) is True

    def test_kb_filter_injected_blocked(self):
        data = types.SimpleNamespace(flags=0x00000010)  # LLKHF_INJECTED bit 4
        assert self.svc._kb_filter(None, data) is False

    def test_kb_filter_normal_passes(self):
        data = types.SimpleNamespace(flags=0x00000000)
        assert self.svc._kb_filter(None, data) is True

    def test_mouse_filter_other_flags_pass(self):
        """Non-injected flags (e.g. 0x02) should pass."""
        data = types.SimpleNamespace(flags=0x00000002)
        assert self.svc._mouse_filter(None, data) is True


class TestStartStop:
    """start() and stop() lifecycle without real OS hooks."""

    def test_start_sets_record_start(self):
        svc = RecorderService(queue.Queue())
        with patch("macro_thunder.recorder.mouse.Listener") as MockML, \
             patch("macro_thunder.recorder.keyboard.Listener") as MockKL:
            mock_ml = MagicMock()
            mock_kl = MagicMock()
            MockML.return_value = mock_ml
            MockKL.return_value = mock_kl
            t_before = time.perf_counter()
            svc.start()
            t_after = time.perf_counter()
            assert t_before <= svc._record_start <= t_after

    def test_start_with_explicit_time(self):
        svc = RecorderService(queue.Queue())
        with patch("macro_thunder.recorder.mouse.Listener"), \
             patch("macro_thunder.recorder.keyboard.Listener"):
            svc.start(record_start_time=1234.5)
            assert svc._record_start == 1234.5

    def test_stop_is_idempotent(self):
        svc = RecorderService(queue.Queue())
        with patch("macro_thunder.recorder.mouse.Listener") as MockML, \
             patch("macro_thunder.recorder.keyboard.Listener") as MockKL:
            mock_ml = MagicMock()
            mock_kl = MagicMock()
            MockML.return_value = mock_ml
            MockKL.return_value = mock_kl
            svc.start()
            svc.stop()
            svc.stop()  # second call must not raise

    def test_stop_without_start_is_safe(self):
        svc = RecorderService(queue.Queue())
        svc.stop()  # must not raise
