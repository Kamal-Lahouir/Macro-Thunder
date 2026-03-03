"""Pre-flight validation helpers for the playback engine."""
from __future__ import annotations

from macro_thunder.models.blocks import ActionBlock, GotoBlock, LabelBlock, LoopStartBlock, LoopEndBlock


def validate_gotos(blocks: list[ActionBlock]) -> list[str]:
    """Return list of missing label names (deduplicated, order-preserved).

    Empty list means all GotoBlock targets resolve to a LabelBlock in blocks.
    """
    labels = {b.name for b in blocks if isinstance(b, LabelBlock)}
    missing: list[str] = []
    seen: set[str] = set()
    for b in blocks:
        if isinstance(b, GotoBlock) and b.target not in labels:
            if b.target not in seen:
                missing.append(b.target)
                seen.add(b.target)
    return missing


def validate_loops(blocks: list[ActionBlock]) -> list[str]:
    """Return list of error strings for loop structure problems.

    Detects:
    - Nested LoopStart (LoopStart inside an already-open loop region)
    - Orphaned LoopEnd (LoopEnd with no preceding unmatched LoopStart)
    - Unclosed LoopStart (LoopStart with no following LoopEnd)
    """
    errors: list[str] = []
    depth = 0
    for idx, block in enumerate(blocks):
        if isinstance(block, LoopStartBlock):
            if depth > 0:
                errors.append(
                    f"Nested loop at block {idx}: LoopStart inside another loop is not supported"
                )
            else:
                depth += 1
        elif isinstance(block, LoopEndBlock):
            if depth == 0:
                errors.append(f"Orphaned LoopEnd at block {idx}: no matching LoopStart")
            else:
                depth -= 1
    if depth > 0:
        errors.append(f"Unclosed loop: {depth} LoopStart block(s) have no matching LoopEnd")
    return errors
