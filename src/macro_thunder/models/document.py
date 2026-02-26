from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from macro_thunder.models.blocks import ActionBlock

CURRENT_VERSION = 1


@dataclass
class MacroDocument:
    name: str = "Untitled"
    version: int = CURRENT_VERSION
    blocks: List[ActionBlock] = field(default_factory=list)
