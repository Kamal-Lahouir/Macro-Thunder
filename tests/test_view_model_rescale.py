"""Tests for rescaling functions in view_model.py (GROUP-02).

These tests are written RED-first: view_model.py does not exist yet,
so the import will fail until Task 2 creates the implementation.
"""
import pytest
from macro_thunder.models.view_model import (
    _rescale_group_duration,
    _rescale_group_coords,
)
from macro_thunder.models.blocks import MouseMoveBlock


def _make_moves(coords_and_times):
    """Helper: create a list of MouseMoveBlock from [(x, y, t), ...]."""
    return [MouseMoveBlock(x=x, y=y, timestamp=t) for x, y, t in coords_and_times]


def test_rescale_duration_proportional():
    """3 moves at t=[0.0, 0.5, 1.0], rescaled to new_duration=2.0 → t=[0.0, 1.0, 2.0]."""
    blocks = _make_moves([(0, 0, 0.0), (50, 50, 0.5), (100, 100, 1.0)])
    _rescale_group_duration(blocks, 0, 2, 2.0)
    assert blocks[0].timestamp == pytest.approx(0.0)
    assert blocks[1].timestamp == pytest.approx(1.0)
    assert blocks[2].timestamp == pytest.approx(2.0)


def test_rescale_duration_single_move():
    """Single move: _rescale_group_duration is a no-op (flat_start == flat_end)."""
    blocks = _make_moves([(0, 0, 0.5)])
    _rescale_group_duration(blocks, 0, 0, 2.0)
    assert blocks[0].timestamp == pytest.approx(0.5)


def test_rescale_duration_zero_old():
    """3 blocks all at t=0.5 (old_duration == 0): no-op, timestamps unchanged."""
    blocks = _make_moves([(0, 0, 0.5), (10, 10, 0.5), (20, 20, 0.5)])
    _rescale_group_duration(blocks, 0, 2, 2.0)
    assert blocks[0].timestamp == pytest.approx(0.5)
    assert blocks[1].timestamp == pytest.approx(0.5)
    assert blocks[2].timestamp == pytest.approx(0.5)


def test_rescale_coords_linear():
    """3 moves: original (0,0)→(50,50)→(100,100).
    Rescale to new_start=(0,0), new_end=(100,200).
    Intermediate block (i=1) → t=0.5 → (50, 100).
    """
    blocks = _make_moves([(0, 0, 0.0), (50, 50, 0.5), (100, 100, 1.0)])
    _rescale_group_coords(blocks, 0, 2, (0, 0), (100, 200))
    assert blocks[0].x == 0
    assert blocks[0].y == 0
    assert blocks[1].x == 50
    assert blocks[1].y == 100
    assert blocks[2].x == 100
    assert blocks[2].y == 200


def test_rescale_coords_single_move():
    """Single move: no crash, start coords applied."""
    blocks = _make_moves([(10, 20, 0.0)])
    _rescale_group_coords(blocks, 0, 0, (5, 5), (5, 5))
    # No crash is the primary assertion; single move is a no-op per spec
    assert blocks[0].x == 10
    assert blocks[0].y == 20
