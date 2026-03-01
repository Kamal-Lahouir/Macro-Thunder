"""View-layer types and pure rescaling helpers for the visual block editor (Phase 3).

DisplayRow variants represent what is rendered in BlockTableModel:
- BlockRow: a single non-move block, or a lone move block outside any group
- GroupHeaderRow: the header row for a collapsed/expanded consecutive-move group
- GroupChildRow: one move block visible inside an expanded group

The rescaling functions (_rescale_group_duration, _rescale_group_coords) are
module-level pure functions so they can be imported and unit-tested without Qt.
They mutate blocks in-place and are called by BlockTableModel.setData().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, List, Tuple

from macro_thunder.models.blocks import ActionBlock


@dataclass
class BlockRow:
    """A single non-move block, or a lone move block outside any group."""
    flat_index: int


@dataclass
class GroupHeaderRow:
    """Collapsed or expanded group header spanning flat_start..flat_end inclusive."""
    flat_start: int
    flat_end: int
    expanded: bool = False


@dataclass
class GroupChildRow:
    """One move block visible inside an expanded group."""
    flat_index: int
    group_flat_start: int


DisplayRow = Union[BlockRow, GroupHeaderRow, GroupChildRow]


def _rescale_group_duration(
    blocks: List[ActionBlock],
    flat_start: int,
    flat_end: int,
    new_duration: float,
) -> None:
    """Rescale timestamps of blocks[flat_start..flat_end] so total span == new_duration.

    Proportional rescaling: each block's offset from the group start is multiplied
    by (new_duration / old_duration).  Mutates timestamps in-place.

    No-op if flat_start == flat_end (single block) or old_duration <= 0.
    """
    if flat_start == flat_end:
        return

    old_start_t: float = blocks[flat_start].timestamp  # type: ignore[attr-defined]
    old_end_t: float = blocks[flat_end].timestamp  # type: ignore[attr-defined]
    old_duration = old_end_t - old_start_t

    if old_duration <= 0:
        return

    scale = new_duration / old_duration
    for block in blocks[flat_start : flat_end + 1]:
        block.timestamp = old_start_t + (block.timestamp - old_start_t) * scale  # type: ignore[attr-defined]


def _rescale_group_coords(
    blocks: List[ActionBlock],
    flat_start: int,
    flat_end: int,
    new_start: Tuple[int, int],
    new_end: Tuple[int, int],
) -> None:
    """Linearly interpolate x/y of each block in blocks[flat_start..flat_end].

    Interpolation parameter t = i / max(n-1, 1) where i is the block's position
    within the group and n is the group size.  Mutates x/y in-place.

    No-op if flat_start == flat_end (single block).
    """
    if flat_start == flat_end:
        return

    n = flat_end - flat_start + 1
    x0, y0 = new_start
    xN, yN = new_end

    for i, block in enumerate(blocks[flat_start : flat_end + 1]):
        t = i / max(n - 1, 1)
        block.x = round(x0 + t * (xN - x0))  # type: ignore[attr-defined]
        block.y = round(y0 + t * (yN - y0))  # type: ignore[attr-defined]
