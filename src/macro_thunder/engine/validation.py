"""Pre-flight validation helpers for the playback engine."""
from __future__ import annotations

from macro_thunder.models.blocks import ActionBlock, GotoBlock, LabelBlock


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
