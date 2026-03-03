from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union
from typing import Literal


@dataclass
class MouseMoveBlock:
    x: int
    y: int
    timestamp: float
    type: Literal["MouseMove"] = field(default="MouseMove", init=False)


@dataclass
class MouseClickBlock:
    x: int
    y: int
    button: str
    direction: str
    timestamp: float
    type: Literal["MouseClick"] = field(default="MouseClick", init=False)


@dataclass
class MouseScrollBlock:
    x: int
    y: int
    dx: int
    dy: int
    timestamp: float
    type: Literal["MouseScroll"] = field(default="MouseScroll", init=False)


@dataclass
class KeyPressBlock:
    key: str
    direction: str
    timestamp: float
    type: Literal["KeyPress"] = field(default="KeyPress", init=False)


@dataclass
class DelayBlock:
    duration: float
    type: Literal["Delay"] = field(default="Delay", init=False)


@dataclass
class WindowFocusBlock:
    executable: str
    title: str
    match_mode: str          # "Contains" | "Exact" | "Starts With"
    timeout: float = 5.0     # seconds to wait for window to appear
    on_failure_label: str = ""   # empty = continue to next block on failure
    on_success_label: str = ""   # empty = "Next" (continue to next block)
    reposition: bool = False     # whether to reposition/resize window on success
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    type: Literal["WindowFocus"] = field(default="WindowFocus", init=False)


@dataclass
class LabelBlock:
    name: str
    type: Literal["Label"] = field(default="Label", init=False)


@dataclass
class GotoBlock:
    target: str
    type: Literal["Goto"] = field(default="Goto", init=False)


@dataclass
class LoopStartBlock:
    repeat: int
    type: Literal["LoopStart"] = field(default="LoopStart", init=False)


@dataclass
class LoopEndBlock:
    type: Literal["LoopEnd"] = field(default="LoopEnd", init=False)


ActionBlock = Union[
    MouseMoveBlock,
    MouseClickBlock,
    MouseScrollBlock,
    KeyPressBlock,
    DelayBlock,
    WindowFocusBlock,
    LabelBlock,
    GotoBlock,
    LoopStartBlock,
    LoopEndBlock,
]

_BLOCK_CLASSES: dict[str, type] = {
    "MouseMove": MouseMoveBlock,
    "MouseClick": MouseClickBlock,
    "MouseScroll": MouseScrollBlock,
    "KeyPress": KeyPressBlock,
    "Delay": DelayBlock,
    "WindowFocus": WindowFocusBlock,
    "Label": LabelBlock,
    "Goto": GotoBlock,
    "LoopStart": LoopStartBlock,
    "LoopEnd": LoopEndBlock,
}


def block_from_dict(d: dict) -> ActionBlock:
    """Reconstruct an ActionBlock from a dict (e.g. loaded from JSON)."""
    d = dict(d)
    block_type = d.pop("type")
    cls = _BLOCK_CLASSES[block_type]  # raises KeyError for unknown types
    return cls(**d)
