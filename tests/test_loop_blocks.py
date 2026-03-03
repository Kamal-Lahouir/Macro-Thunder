"""TDD tests for LoopStartBlock, LoopEndBlock, validate_loops, and engine dispatch."""
from __future__ import annotations

import dataclasses
import pytest

from macro_thunder.models.blocks import (
    LoopStartBlock,
    LoopEndBlock,
    DelayBlock,
    block_from_dict,
    _BLOCK_CLASSES,
    ActionBlock,
)
from macro_thunder.engine.validation import validate_loops
from macro_thunder.engine import PlaybackEngine


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------


class TestLoopBlockDataclasses:
    def test_loop_start_serializes(self):
        b = LoopStartBlock(repeat=3)
        d = dataclasses.asdict(b)
        assert d == {"type": "LoopStart", "repeat": 3}

    def test_loop_end_serializes(self):
        b = LoopEndBlock()
        d = dataclasses.asdict(b)
        assert d == {"type": "LoopEnd"}

    def test_loop_start_registered_in_block_classes(self):
        assert "LoopStart" in _BLOCK_CLASSES
        assert _BLOCK_CLASSES["LoopStart"] is LoopStartBlock

    def test_loop_end_registered_in_block_classes(self):
        assert "LoopEnd" in _BLOCK_CLASSES
        assert _BLOCK_CLASSES["LoopEnd"] is LoopEndBlock

    def test_block_from_dict_loop_start(self):
        b = block_from_dict({"type": "LoopStart", "repeat": 2})
        assert isinstance(b, LoopStartBlock)
        assert b.repeat == 2

    def test_block_from_dict_loop_end(self):
        b = block_from_dict({"type": "LoopEnd"})
        assert isinstance(b, LoopEndBlock)

    def test_loop_start_repeat_preserved(self):
        b = LoopStartBlock(repeat=99)
        assert b.repeat == 99

    def test_type_field_not_init(self):
        # type field should NOT be settable via constructor
        b = LoopStartBlock(repeat=1)
        assert b.type == "LoopStart"
        b2 = LoopEndBlock()
        assert b2.type == "LoopEnd"


# ---------------------------------------------------------------------------
# validate_loops tests
# ---------------------------------------------------------------------------


class TestValidateLoops:
    def test_balanced_no_errors(self):
        blocks = [LoopStartBlock(repeat=2), DelayBlock(0.01), LoopEndBlock()]
        assert validate_loops(blocks) == []

    def test_empty_blocks_no_errors(self):
        assert validate_loops([]) == []

    def test_orphaned_loop_end_error(self):
        blocks = [DelayBlock(0.01), LoopEndBlock()]
        errors = validate_loops(blocks)
        assert len(errors) >= 1
        assert any("LoopEnd" in e for e in errors)

    def test_unclosed_loop_start_error(self):
        blocks = [LoopStartBlock(repeat=2), DelayBlock(0.01)]
        errors = validate_loops(blocks)
        assert len(errors) >= 1
        assert any("LoopStart" in e for e in errors)

    def test_nested_loops_error(self):
        blocks = [
            LoopStartBlock(repeat=2),
            LoopStartBlock(repeat=3),
            DelayBlock(0.01),
            LoopEndBlock(),
            LoopEndBlock(),
        ]
        errors = validate_loops(blocks)
        assert len(errors) >= 1
        assert any("nested" in e.lower() or "LoopStart" in e for e in errors)

    def test_multiple_errors_returned(self):
        # Two orphaned LoopEnds
        blocks = [LoopEndBlock(), LoopEndBlock()]
        errors = validate_loops(blocks)
        assert len(errors) >= 2

    def test_non_loop_blocks_ignored(self):
        blocks = [DelayBlock(0.01), DelayBlock(0.02)]
        assert validate_loops(blocks) == []


# ---------------------------------------------------------------------------
# Engine dispatch tests — use mock controllers to avoid real input injection
# ---------------------------------------------------------------------------


class MockMouseCtrl:
    def __init__(self):
        self.calls = []

    @property
    def position(self):
        return (0, 0)

    @position.setter
    def position(self, v):
        self.calls.append(("move", v))

    def press(self, btn):
        self.calls.append(("press", btn))

    def release(self, btn):
        self.calls.append(("release", btn))

    def scroll(self, dx, dy):
        self.calls.append(("scroll", dx, dy))


class MockKbCtrl:
    def __init__(self):
        self.calls = []

    def press(self, key):
        self.calls.append(("press", key))

    def release(self, key):
        self.calls.append(("release", key))


def run_engine_sync(blocks, repeat=1):
    """Run the engine synchronously and return (delay_count, progress_events)."""
    delay_count = []
    progress_events = []
    done_flag = []

    def on_progress(idx, total):
        progress_events.append((idx, total))

    def on_done():
        done_flag.append(True)

    mouse_ctrl = MockMouseCtrl()
    kb_ctrl = MockKbCtrl()

    engine = PlaybackEngine(
        mouse_ctrl=mouse_ctrl,
        kb_ctrl=kb_ctrl,
        on_progress=on_progress,
        on_done=on_done,
    )
    engine.start(blocks, speed=1.0, repeat=repeat)
    engine._thread.join(timeout=10.0)
    return progress_events, done_flag


class TestEngineLoopDispatch:
    def test_loop_body_fires_repeat_times(self):
        """[LoopStart(3), Delay, LoopEnd] → Delay fires 3 times."""
        blocks = [LoopStartBlock(repeat=3), DelayBlock(0.0), LoopEndBlock()]
        progress_events, done_flag = run_engine_sync(blocks)
        # progress fires for DelayBlock (LoopStart/LoopEnd are flow control)
        assert len(progress_events) == 3
        assert done_flag

    def test_loop_repeat_1_fires_once(self):
        """[LoopStart(1), Delay, LoopEnd] → Delay fires 1 time."""
        blocks = [LoopStartBlock(repeat=1), DelayBlock(0.0), LoopEndBlock()]
        progress_events, _ = run_engine_sync(blocks)
        assert len(progress_events) == 1

    def test_blocks_after_loop_fire_once(self):
        """[LoopStart(2), A, LoopEnd, B] → A fires 2 times, B fires 1 time."""
        blocks = [
            LoopStartBlock(repeat=2),
            DelayBlock(0.0),
            LoopEndBlock(),
            DelayBlock(0.0),
        ]
        progress_events, _ = run_engine_sync(blocks)
        # A fires 2x, B fires 1x = 3 total progress events
        assert len(progress_events) == 3

    def test_orphaned_loop_end_skipped(self):
        """Orphaned LoopEnd: skip it and continue, no crash."""
        blocks = [DelayBlock(0.0), LoopEndBlock(), DelayBlock(0.0)]
        progress_events, done_flag = run_engine_sync(blocks)
        assert len(progress_events) == 2
        assert done_flag

    def test_loop_stack_resets_between_outer_repeats(self):
        """Outer repeat=2, inner loop repeat=3 → delay fires 3*2=6 times total."""
        blocks = [LoopStartBlock(repeat=3), DelayBlock(0.0), LoopEndBlock()]
        progress_events, done_flag = run_engine_sync(blocks, repeat=2)
        assert len(progress_events) == 6
        assert done_flag

    def test_on_done_fires_after_loop(self):
        blocks = [LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock()]
        _, done_flag = run_engine_sync(blocks)
        assert done_flag
