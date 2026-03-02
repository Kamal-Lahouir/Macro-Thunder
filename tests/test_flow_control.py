"""Tests for validate_gotos (engine/validation.py) and loop detection counter logic."""
from __future__ import annotations

import pytest

from macro_thunder.models.blocks import LabelBlock, GotoBlock
from macro_thunder.engine.validation import validate_gotos


# ---------------------------------------------------------------------------
# validate_gotos tests
# ---------------------------------------------------------------------------

def test_validate_gotos_empty_blocks():
    """Empty block list returns no missing labels."""
    assert validate_gotos([]) == []


def test_validate_gotos_matching_label():
    """Goto whose target exists in the block list returns empty list."""
    blocks = [LabelBlock("start"), GotoBlock("start")]
    assert validate_gotos(blocks) == []


def test_validate_gotos_single_missing():
    """Goto whose target is absent returns that name."""
    blocks = [GotoBlock("missing")]
    assert validate_gotos(blocks) == ["missing"]


def test_validate_gotos_deduplicates_same_missing_label():
    """Two Gotos to the same missing label return a single entry."""
    blocks = [GotoBlock("loop"), GotoBlock("loop")]
    result = validate_gotos(blocks)
    assert result == ["loop"]


def test_validate_gotos_multiple_distinct_missing():
    """Multiple distinct missing labels are returned in the order first seen."""
    blocks = [GotoBlock("alpha"), GotoBlock("beta"), GotoBlock("alpha")]
    result = validate_gotos(blocks)
    assert result == ["alpha", "beta"]


def test_validate_gotos_only_labels_no_gotos():
    """Labels without any Goto return empty list."""
    from macro_thunder.models.blocks import DelayBlock
    blocks = [LabelBlock("x"), DelayBlock(1.0), LabelBlock("y")]
    assert validate_gotos(blocks) == []


def test_validate_gotos_mixed_blocks():
    """Mixed block list: only missing Goto targets appear."""
    from macro_thunder.models.blocks import DelayBlock, MouseMoveBlock
    blocks = [
        LabelBlock("start"),
        MouseMoveBlock(0, 0, 0.0),
        GotoBlock("start"),      # resolves
        GotoBlock("nowhere"),    # missing
        DelayBlock(0.5),
        GotoBlock("also_gone"),  # missing distinct
    ]
    assert validate_gotos(blocks) == ["nowhere", "also_gone"]


# ---------------------------------------------------------------------------
# Loop detection counter logic
# (The actual counter lives in the engine _run() loop — these tests document
#  the contract via direct dict manipulation so it is clear before Plan 02.)
# ---------------------------------------------------------------------------

def _simulate_loop_counter(
    fire_sequence: list[tuple[int, bool]],
    threshold: int = 1000,
) -> tuple[dict[int, int], bool]:
    """
    Simulate the goto_fire_count dict logic.

    fire_sequence: list of (flat_index, progress_since_last_goto)
        Each entry represents one Goto firing at flat_index.
        progress=True means a non-flow-control block ran since the last Goto.

    Returns (final_counter_state, loop_detected).
    """
    goto_fire_count: dict[int, int] = {}
    loop_detected = False

    for flat_index, progress in fire_sequence:
        count = goto_fire_count.get(flat_index, 0) + 1
        if progress:
            goto_fire_count.clear()
            count = 1
        goto_fire_count[flat_index] = count

        if count > threshold:
            loop_detected = True
            break

    return goto_fire_count, loop_detected


def test_loop_counter_increments_per_goto_index():
    """Counter increments each time same Goto index fires."""
    seq = [(3, False)] * 5
    state, detected = _simulate_loop_counter(seq)
    assert state[3] == 5
    assert not detected


def test_loop_counter_resets_on_progress():
    """Counter resets to 1 when progress_since_last_goto is True."""
    seq = [(3, False)] * 10 + [(3, True)] + [(3, False)] * 3
    state, detected = _simulate_loop_counter(seq)
    # After reset at index 10, count should be 1+3 = 4
    assert state[3] == 4
    assert not detected


def test_loop_detection_triggers_at_threshold():
    """Loop detected when same index fires > 1000 times consecutively."""
    seq = [(0, False)] * 1001
    _, detected = _simulate_loop_counter(seq, threshold=1000)
    assert detected


def test_loop_detection_not_triggered_at_exactly_threshold():
    """1000 fires is on threshold — NOT detected (> 1000 required)."""
    seq = [(0, False)] * 1000
    _, detected = _simulate_loop_counter(seq, threshold=1000)
    assert not detected


def test_loop_counter_different_indices_independent():
    """Two different Goto indices track independently; no cross-contamination."""
    seq = [(0, False)] * 5 + [(1, False)] * 3
    state, detected = _simulate_loop_counter(seq)
    assert state[0] == 5
    assert state[1] == 3
    assert not detected


def test_loop_counter_progress_clears_all_indices():
    """Progress clears the ENTIRE counter dict, not just the firing index."""
    seq = [(0, False)] * 5 + [(1, False)] * 3 + [(2, True)]
    state, detected = _simulate_loop_counter(seq)
    # Index 2 fires with progress=True: counter cleared then set to 1
    assert state == {2: 1}
    assert not detected
