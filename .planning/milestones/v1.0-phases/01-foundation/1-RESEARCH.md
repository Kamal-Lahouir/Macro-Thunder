# Phase 1: Foundation - Research

**Researched:** 2026-02-26
**Domain:** PyQt6 app shell, DPI awareness (Win32), data model design, JSON serialization
**Confidence:** HIGH (core stack decisions already locked; research confirms approaches)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Python 3.12**
- **PyQt6** (not PyQt5, not PySide6)
- **pynput** for mouse/keyboard input capture (lock in now for Phase 2)
- **Proper package layout from day 1**: `src/macro_thunder/` with submodules (e.g. `models/`, `ui/`, `engine/`)
- Full layout skeleton in Phase 1 — all three areas visible and positioned, even if empty
- Layout: toolbar row at top, library panel on the **left**, block editor fills the center/right
- Phase 2 fills in the toolbar widgets and recording controls into existing containers
- Phase 3 fills in the block editor and library list into existing containers — no restructuring
- **Status bar** at the bottom shows a **live mouse coordinate readout** (X, Y updating as mouse moves) — this visually satisfies the DPI-awareness success criterion

### Claude's Discretion

- Exact JSON serialization structure for each block type (type field + flat fields is reasonable)
- Dark theme implementation mechanism (QPalette vs stylesheet vs library)
- Git branching strategy (feature branches per phase recommended, e.g. `phase/1-foundation`)
- Exact package/module breakdown within `src/macro_thunder/`
- DPI awareness API call (Win32 `SetProcessDpiAwareness` or Qt's built-in)

### Deferred Ideas (OUT OF SCOPE)

- Git branching strategy — developer workflow choice, not a planner concern
- Dark theme fine-tuning / color customization — Phase 1 just needs "dark enough to work"
</user_constraints>

---

## Summary

Phase 1 establishes the structural foundation: a correctly-packaged Python application, DPI awareness set before any UI initializes, a typed data model for all 8 action block types, and a JSON persistence layer with a version field. The phase delivers a visually dark-themed main window with the full three-panel layout skeleton (toolbar top, library panel left, block editor center-right), plus a live mouse coordinate readout in the status bar as the DPI correctness proof.

All core technology decisions are already locked by the user: Python 3.12, PyQt6, pynput, src-layout packaging. Research confirms these are correct choices and surfaces the exact implementation patterns needed. The most critical implementation detail is that `ctypes.windll.shcore.SetProcessDpiAwareness(2)` must be the first executable statement in `main.py` — before any Qt or pynput import — or DPI coordinates will be wrong on scaled displays. Qt 6 enables high-DPI scaling by default; the ctypes call ensures the process is registered as Per-Monitor V2 aware at the Win32 level.

For dark theme, `PyQtDarkTheme-fork 2.3.4` (released Jan 2025) is the most reliable external option for a VS Code-style dark theme. However, since both pyqtdarktheme packages have low maintenance activity, a fallback QPalette-based implementation must be ready. For the data model and JSON serialization, plain Python dataclasses with a hand-rolled type-discriminated serializer (using a `"type"` field) is the right approach — no external serialization library is needed for 8 simple block types.

**Primary recommendation:** Set DPI awareness via ctypes before importing Qt, use PyQtDarkTheme-fork with a QPalette fallback, model blocks as a sealed hierarchy of dataclasses, serialize with a `"type"` discriminator field and `json.dumps(..., indent=2)`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOUND-01 | Application sets DPI awareness before any UI or input library initializes (prevents coordinate mismatch on scaled displays) | `ctypes.windll.shcore.SetProcessDpiAwareness(2)` must be first executable line of main.py. Confirmed by Win32 docs and PyQt6 community reports. |
| FOUND-02 | Macro data model supports all action block types: MouseMove, MouseClick, MouseScroll, KeyPress, Delay, WindowFocus, Label, Goto | Python dataclasses with a sealed union (`ActionBlock = Union[MouseMoveBlock, ...]`) and a `type` string field on each. No external library needed. |
| FOUND-03 | Macro files saved and loaded as JSON with a `version` field from the first save | `json.dumps(dataclasses.asdict(doc), indent=2)` + custom decoder using `"type"` discriminator. Round-trip verified by design. |
| FOUND-04 | Application launches with a dark-themed main window | PyQtDarkTheme-fork 2.3.4 via `qdarktheme.setup_theme("dark")` OR manual QPalette. QMainWindow with QSplitter skeleton layout. |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | Locked by user; latest stable LTS-style release |
| PyQt6 | >=6.4 | GUI framework | Locked by user; Qt 6 with high-DPI default, no separate AA flag needed |
| pynput | >=1.7 | Mouse/keyboard hooks (used Phase 2+, installed now) | Locked by user; ensures dependency installed from Phase 1 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyQtDarkTheme-fork | 2.3.4 | VS Code-style dark theme | Primary dark theme solution |
| QDarkStyle | 3.2.3 | Alternative dark theme | If PyQtDarkTheme-fork install fails |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyQtDarkTheme-fork | QPalette manually | Manual palette needs ~30 setColor() calls across Active/Inactive/Disabled groups; tedious but zero external deps |
| PyQtDarkTheme-fork | QDarkStyle | QDarkStyle last released Nov 2023; less polished on Qt6 |
| dataclasses + hand-rolled | pydantic / msgspec | Overkill for 8 simple types; adds build dependency; pydantic adds startup cost |
| json stdlib | orjson | No benefit at this scale; stdlib is sufficient |

**Installation:**
```bash
pip install PyQt6 pynput PyQtDarkTheme-fork
```

Or with a pyproject.toml (recommended):
```toml
[project]
dependencies = [
    "PyQt6>=6.4",
    "pynput>=1.7",
    "PyQtDarkTheme-fork>=2.3.4",
]
```

---

## Architecture Patterns

### Recommended Project Structure

```
Macro-Thunder/
├── src/
│   └── macro_thunder/
│       ├── __init__.py
│       ├── __main__.py          # Entry point; DPI call FIRST, then imports
│       ├── models/
│       │   ├── __init__.py
│       │   ├── blocks.py        # ActionBlock dataclasses (all 8 types)
│       │   └── document.py      # MacroDocument (name, version, blocks list)
│       ├── persistence/
│       │   ├── __init__.py
│       │   └── serializer.py    # to_json() / from_json() with version field
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py   # QMainWindow skeleton
│       │   ├── toolbar.py       # Toolbar placeholder widget
│       │   ├── library_panel.py # Left panel placeholder
│       │   └── editor_panel.py  # Center/right panel placeholder
│       └── engine/              # Empty in Phase 1 — reserved for Phase 2
│           └── __init__.py
├── tests/
│   └── __init__.py
├── pyproject.toml
└── CLAUDE.md
```

### Pattern 1: DPI Awareness Before Everything

**What:** Call `SetProcessDpiAwareness(2)` as the very first executable line of `__main__.py`, before any module-level Qt or pynput imports.

**When to use:** Always, unconditionally, on Windows. This is not optional.

**Example:**
```python
# src/macro_thunder/__main__.py
# DPI awareness MUST be set before any other import
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    pass  # Already set (e.g. by manifest), or running in non-Win32 context

# Only after DPI call: import Qt and everything else
from PyQt6.QtWidgets import QApplication
from macro_thunder.ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    # Apply dark theme here
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Why `(2)` not `(1)`:** Value 2 = `PROCESS_PER_MONITOR_DPI_AWARE`. This gives correct coordinates per monitor when dragging between displays with different scaling. Value 1 = system DPI only (wrong on multi-monitor setups with mixed scaling).

**Source:** [Microsoft SetProcessDpiAwareness docs](https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-setprocessdpiawareness)

### Pattern 2: Main Window Skeleton with QSplitter

**What:** QMainWindow with a central widget containing a QSplitter. Toolbar row at top (QToolBar or QFrame), library panel on left, block editor fills center-right. Status bar at bottom with coordinate label.

**When to use:** Phase 1 skeleton — panels are empty QFrame/QWidget placeholders. Future phases add content without touching the splitter structure.

**Example:**
```python
# Source: PyQt6 QSplitter + QMainWindow pattern
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QFrame, QVBoxLayout,
    QWidget, QStatusBar, QLabel, QToolBar
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Thunder")
        self.resize(1200, 700)

        # Toolbar row at top
        self._toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self._toolbar)

        # Central area: horizontal splitter (library | editor)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._library_panel = QFrame()
        self._library_panel.setMinimumWidth(180)
        self._library_panel.setMaximumWidth(320)

        self._editor_panel = QFrame()

        self._splitter.addWidget(self._library_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self._splitter)

        # Status bar with coordinate readout
        self._coord_label = QLabel("X: 0  Y: 0")
        self.statusBar().addPermanentWidget(self._coord_label)

        # Enable mouse tracking for coordinate display
        self.setMouseTracking(True)
```

### Pattern 3: Type-Discriminated Block Dataclasses

**What:** Each action block is a frozen dataclass with a `type: str` field set as a class-level default. `MacroDocument` holds a flat `list[ActionBlock]`. Serialization reads the `"type"` field to dispatch to the correct class.

**When to use:** Always. This is the only data model pattern — no inheritance hierarchies needed at this scale.

**Example:**
```python
# src/macro_thunder/models/blocks.py
from dataclasses import dataclass, field
from typing import Literal, Union

@dataclass
class MouseMoveBlock:
    type: Literal["MouseMove"] = field(default="MouseMove", init=False)
    x: int = 0
    y: int = 0
    timestamp: float = 0.0

@dataclass
class MouseClickBlock:
    type: Literal["MouseClick"] = field(default="MouseClick", init=False)
    x: int = 0
    y: int = 0
    button: str = "left"   # "left", "right", "middle"
    direction: str = "down"  # "down", "up"
    timestamp: float = 0.0

@dataclass
class MouseScrollBlock:
    type: Literal["MouseScroll"] = field(default="MouseScroll", init=False)
    x: int = 0
    y: int = 0
    dx: int = 0
    dy: int = 0
    timestamp: float = 0.0

@dataclass
class KeyPressBlock:
    type: Literal["KeyPress"] = field(default="KeyPress", init=False)
    key: str = ""          # e.g. "a", "Key.ctrl", "Key.shift"
    direction: str = "down"  # "down", "up"
    timestamp: float = 0.0

@dataclass
class DelayBlock:
    type: Literal["Delay"] = field(default="Delay", init=False)
    duration: float = 0.0  # seconds

@dataclass
class WindowFocusBlock:
    type: Literal["WindowFocus"] = field(default="WindowFocus", init=False)
    executable: str = ""
    title: str = ""
    match_mode: str = "Contains"  # "Contains", "Exact", "Starts With"

@dataclass
class LabelBlock:
    type: Literal["Label"] = field(default="Label", init=False)
    name: str = ""

@dataclass
class GotoBlock:
    type: Literal["Goto"] = field(default="Goto", init=False)
    target: str = ""  # label name

ActionBlock = Union[
    MouseMoveBlock, MouseClickBlock, MouseScrollBlock, KeyPressBlock,
    DelayBlock, WindowFocusBlock, LabelBlock, GotoBlock
]

_BLOCK_CLASSES = {
    "MouseMove": MouseMoveBlock,
    "MouseClick": MouseClickBlock,
    "MouseScroll": MouseScrollBlock,
    "KeyPress": KeyPressBlock,
    "Delay": DelayBlock,
    "WindowFocus": WindowFocusBlock,
    "Label": LabelBlock,
    "Goto": GotoBlock,
}

def block_from_dict(d: dict) -> ActionBlock:
    block_type = d["type"]
    cls = _BLOCK_CLASSES[block_type]
    # Remove "type" before passing to constructor (it's set by default)
    kwargs = {k: v for k, v in d.items() if k != "type"}
    return cls(**kwargs)
```

### Pattern 4: MacroDocument and JSON Serialization

**What:** `MacroDocument` is a simple container dataclass. Serialization uses `dataclasses.asdict()` for encoding and a custom `block_from_dict()` dispatcher for decoding. The `version` field is always written and validated on load.

**Example:**
```python
# src/macro_thunder/models/document.py
from dataclasses import dataclass, field
from typing import List
from macro_thunder.models.blocks import ActionBlock

CURRENT_VERSION = 1

@dataclass
class MacroDocument:
    name: str = "Untitled"
    version: int = CURRENT_VERSION
    blocks: List[ActionBlock] = field(default_factory=list)
```

```python
# src/macro_thunder/persistence/serializer.py
import json
import dataclasses
from pathlib import Path
from macro_thunder.models.blocks import block_from_dict
from macro_thunder.models.document import MacroDocument, CURRENT_VERSION

def save(doc: MacroDocument, path: Path) -> None:
    data = {
        "version": doc.version,
        "name": doc.name,
        "blocks": [dataclasses.asdict(b) for b in doc.blocks],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def load(path: Path) -> MacroDocument:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" not in data:
        raise ValueError(f"Missing 'version' field in {path}")
    blocks = [block_from_dict(b) for b in data.get("blocks", [])]
    return MacroDocument(
        name=data.get("name", path.stem),
        version=data["version"],
        blocks=blocks,
    )
```

### Pattern 5: Dark Theme Application

**What:** Apply `qdarktheme.setup_theme("dark")` immediately after creating `QApplication`, before creating any windows. Fall back to manual QPalette if import fails.

**Example:**
```python
app = QApplication(sys.argv)

try:
    import qdarktheme
    qdarktheme.setup_theme("dark")
except ImportError:
    # Fallback: manual QPalette dark theme
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import Qt
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    # Apply same colors for Inactive group to prevent white flash on focus loss
    for role in [QPalette.ColorRole.Window, QPalette.ColorRole.Base]:
        palette.setColor(QPalette.ColorGroup.Inactive, role,
                         palette.color(QPalette.ColorGroup.Active, role))
    app.setPalette(palette)
```

### Pattern 6: Live Mouse Coordinate Readout in Status Bar

**What:** Override `mouseMoveEvent` on the central widget (or install an event filter). Use `QCursor.pos()` for screen-absolute coordinates (these are the DPI-correct values after `SetProcessDpiAwareness(2)`). Display in status bar label.

**Why `QCursor.pos()` not `event.position()`:** `event.position()` gives widget-relative coordinates. `QCursor.pos()` gives global screen coordinates — the values that must match the OS cursor position at any display scale.

**Example:**
```python
from PyQt6.QtGui import QCursor

# In the central widget or main window, enable tracking:
self.setMouseTracking(True)
self.centralWidget().setMouseTracking(True)

def mouseMoveEvent(self, event):
    pos = QCursor.pos()  # screen-absolute, DPI-correct
    self._coord_label.setText(f"X: {pos.x()}  Y: {pos.y()}")
    super().mouseMoveEvent(event)
```

### Anti-Patterns to Avoid

- **Importing Qt before DPI call:** Any `from PyQt6 import ...` at module level in `__main__.py` before the ctypes call will cause coordinate errors at 125%+ scaling. The DPI call must precede all Qt imports.
- **Using `event.position()` for status bar coords:** This returns widget-local coords, not screen coords. Use `QCursor.pos()` instead.
- **Setting `AA_EnableHighDpiScaling` in PyQt6:** This attribute was removed in Qt6 — it causes an `AttributeError`. High DPI is always enabled in PyQt6.
- **Using `setMouseTracking(True)` only on the window:** Mouse move events only fire if tracking is enabled on the widget that receives them. Enable tracking on both the main window and the central widget (and any nested widget that fills the area).
- **Storing blocks in a nested/grouped structure:** `MacroDocument.blocks` is always a flat list. Grouping is a view-layer concern only (Phase 3). Storing groups in the data model would require structural rework in Phase 3.
- **Using `dataclasses.asdict()` with `type` as init param:** The `type` field must use `field(default="...", init=False)` so that `block_from_dict` can reconstruct from a dict that omits `"type"` in kwargs. If `type` is an `init=True` field, the round-trip breaks when passing `**kwargs` after removing `"type"`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark theme | Custom color stylesheet from scratch | PyQtDarkTheme-fork or QPalette pattern (provided above) | Getting all widget states (Inactive, Disabled, Hover, Pressed) correct manually is 200+ lines; easy to miss states |
| DPI detection per-monitor | Custom Win32 monitor enumeration | `QScreen.devicePixelRatio()` for reporting, ctypes for the process-level setting | Qt already wraps per-monitor DPI after SetProcessDpiAwareness(2) is set |
| JSON schema validation | Custom validator | `if "version" not in data: raise ValueError(...)` — simple field presence check is enough for Phase 1 | No schema evolution in Phase 1; full validation deferred to when format stabilizes |

**Key insight:** The only "hard" problem in Phase 1 is DPI awareness timing. Everything else is standard PyQt6 boilerplate.

---

## Common Pitfalls

### Pitfall 1: DPI Call After Qt Import

**What goes wrong:** Mouse coordinates reported by `QCursor.pos()` are divided by the scaling factor — at 150% scaling, a cursor at pixel 1500 is reported as pixel 1000.

**Why it happens:** Qt registers DPI awareness when the Qt runtime loads. If the process DPI awareness level is already set by Qt before the ctypes call, the ctypes call either fails silently or is ignored.

**How to avoid:** `ctypes.windll.shcore.SetProcessDpiAwareness(2)` must be the first two lines of `__main__.py` (after any `# comment`), before any import that transitively imports PyQt6.

**Warning signs:** Coordinates at 100% scaling match the OS, but at 125%+ they are off by a consistent multiplier.

### Pitfall 2: PyQtDarkTheme Package Name Confusion

**What goes wrong:** `pip install pyqtdarktheme` installs the original unmaintained package (last release ~2022). `import qdarktheme` then fails because version may be incompatible with PyQt6 on newer systems.

**Why it happens:** Two separate packages on PyPI with similar names and the same import name `qdarktheme`:
- `pyqtdarktheme` — original, low maintenance
- `PyQtDarkTheme-fork` — active fork, latest release Jan 3 2025

**How to avoid:** Always install `PyQtDarkTheme-fork`, not `pyqtdarktheme`. Both expose `import qdarktheme`. Wrap in try/except and fall back to QPalette.

**Warning signs:** `qdarktheme.setup_theme()` raises `AttributeError` or `TypeError` — sign of wrong package version.

### Pitfall 3: QPalette Inactive Group Not Set

**What goes wrong:** Window background turns light gray or white when the window loses focus, because the Inactive color group defaults to the system color.

**Why it happens:** Qt uses three color groups (Active, Inactive, Disabled). Setting only Active colors leaves Inactive at defaults.

**How to avoid:** When building manual QPalette, call `setColor(QPalette.ColorGroup.Inactive, role, color)` for every color role that should stay dark when focus is lost.

**Warning signs:** Dark window while focused; light/gray window when clicking another app.

### Pitfall 4: `MacroDocument` Default Save Path Not Existing

**What goes wrong:** `json.dumps()` or `path.write_text()` raises `FileNotFoundError` when `Documents/MacroThunder/` doesn't exist yet.

**Why it happens:** `Path.write_text()` does not create parent directories.

**How to avoid:** Always call `path.parent.mkdir(parents=True, exist_ok=True)` before `write_text()` in the serializer.

**Warning signs:** First save after fresh install raises `FileNotFoundError`.

### Pitfall 5: `dataclasses.asdict()` with `type` field as `init=True`

**What goes wrong:** Round-trip fails — saving works, loading crashes with `TypeError: __init__() got an unexpected keyword argument 'type'`.

**Why it happens:** `dataclasses.asdict()` includes the `type` field in the dict. If the deserializer passes `**kwargs` to the constructor (after removing `"type"`), but `type` was declared as a regular `init=True` field, removing it from kwargs makes the constructor call succeed — but if it was kept, it would fail.

**How to avoid:** Declare `type` fields as `field(default="MouseMove", init=False)`. This means the constructor does not accept `type` as a parameter, so removing `"type"` from deserialized kwargs and calling `cls(**kwargs)` always works.

---

## Code Examples

### Full `__main__.py` Entry Point

```python
# src/macro_thunder/__main__.py
# IMPORTANT: DPI awareness MUST be set before any other import
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except (AttributeError, OSError):
    pass  # Non-Windows or already set via manifest

import sys
from PyQt6.QtWidgets import QApplication
from macro_thunder.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    try:
        import qdarktheme
        qdarktheme.setup_theme("dark")
    except ImportError:
        _apply_fallback_dark_palette(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def _apply_fallback_dark_palette(app: QApplication) -> None:
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    near_black = QColor(30, 30, 30)
    text = QColor(220, 220, 220)
    base = QColor(20, 20, 20)
    button = QColor(45, 45, 45)
    highlight = QColor(0, 120, 212)
    palette.setColor(QPalette.ColorRole.Window, near_black)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    # Keep dark in Inactive group to avoid white flash on focus loss
    for role in [QPalette.ColorRole.Window, QPalette.ColorRole.Base,
                 QPalette.ColorRole.Button]:
        palette.setColor(QPalette.ColorGroup.Inactive, role,
                         palette.color(QPalette.ColorGroup.Active, role))
    app.setPalette(palette)


if __name__ == "__main__":
    main()
```

### Default Save Path (Documents/MacroThunder/)

```python
# src/macro_thunder/persistence/serializer.py
from pathlib import Path

def default_macro_dir() -> Path:
    """Returns ~/Documents/MacroThunder/, creating it if needed."""
    p = Path.home() / "Documents" / "MacroThunder"
    p.mkdir(parents=True, exist_ok=True)
    return p
```

### Minimal pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "macro-thunder"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "PyQt6>=6.4",
    "pynput>=1.7",
    "PyQtDarkTheme-fork>=2.3.4",
]

[tool.hatch.build.targets.wheel]
packages = ["src/macro_thunder"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `Qt.AA_EnableHighDpiScaling` attribute | Not needed — always enabled in PyQt6 | Qt6 (2021) | Setting this attr in PyQt6 raises `AttributeError` |
| `event.pos()` / `event.globalPos()` | `event.position()` / `event.globalPosition()` (returns QPointF) | PyQt6 / Qt6 | Old methods exist but deprecated; new methods return float coords |
| `setup.py` + `setup.cfg` | `pyproject.toml` with hatchling/setuptools | ~2022-2023 | Use pyproject.toml exclusively for new projects |
| `from PyQt6.QtCore import Qt; Qt.AA_EnableHighDpiScaling` | Remove entirely | Qt6 | High DPI non-optional |

**Deprecated/outdated:**
- `QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)`: Do not use — raises AttributeError in PyQt6.
- `event.globalPos()`: Deprecated in Qt6; use `event.globalPosition().toPoint()` instead.
- `pyqtdarktheme` (original): Last significant release ~2022; use `PyQtDarkTheme-fork` instead.

---

## Open Questions

1. **Is `SetProcessDpiAwareness(2)` ever pre-set by a system manifest that would make the ctypes call fail?**
   - What we know: The call fails with `OSError` (Access denied) if the process DPI awareness was already set via an embedded manifest at a *higher* or *equal* level. This is actually desirable — if already set correctly, `except OSError: pass` is safe.
   - What's unclear: Whether `python.exe` ships with a manifest that sets DPI awareness on the user's system.
   - Recommendation: Wrap in `try/except (AttributeError, OSError): pass`. If the call is already set, coordinates will be correct. If it fails silently for another reason, the status bar readout makes verification trivial.

2. **`pyqtdarktheme` vs `PyQtDarkTheme-fork` import name collision**
   - What we know: Both packages use `import qdarktheme`. If both are installed, the one installed last wins.
   - What's unclear: Whether CI/fresh environments would ever have both.
   - Recommendation: Pin `PyQtDarkTheme-fork>=2.3.4` in `pyproject.toml` and document that `pyqtdarktheme` (original) must NOT also be installed. Add to project CLAUDE.md when it's created.

---

## Sources

### Primary (HIGH confidence)

- [Microsoft SetProcessDpiAwareness Docs](https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-setprocessdpiawareness) — DPI awareness values and behavior
- [Qt High DPI Documentation](https://doc.qt.io/qt-6/highdpi.html) — Qt6 DPI handling, removed attributes
- [QMouseEvent Qt6 Docs](https://doc.qt.io/qt-6/qmouseevent.html) — `position()` / `globalPosition()` current API
- [PyQtDarkTheme-fork PyPI](https://pypi.org/project/PyQtDarkTheme-fork/) — v2.3.4, Jan 3 2025, PyQt6 confirmed
- [Python src-layout packaging guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — src layout recommendation

### Secondary (MEDIUM confidence)

- [Qt Forum: SetProcessDpiAwareness with PyQt6](https://forum.qt.io/topic/144320/how-to-efficiently-identify-the-cause-of-qt-6-5-high-dpi-bug-in-windows) — Community confirms DPI call timing issue
- [QDarkStyle PyPI](https://pypi.org/project/QDarkStyle/) — v3.2.3, Nov 2023, PyQt6 confirmed as fallback option
- [Structuring a Large PyQt Application](https://www.pythonguis.com/faq/structuring-a-large-pyqt-application/) — MVC/MVP pattern for PyQt6

### Tertiary (LOW confidence)

- Various StackOverflow/forum posts on QPalette dark theme — confirmed by official QPalette docs, elevated to MEDIUM
- Community reports on pyqtdarktheme original maintenance status — flagged as inactive

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed on PyPI with current versions; no external API calls needed in Phase 1
- Architecture: HIGH — patterns derived from official Qt6 docs and confirmed pyproject.toml packaging standards
- DPI awareness: HIGH — Win32 API docs are authoritative; timing constraint confirmed by Qt community
- Dark theme: MEDIUM — PyQtDarkTheme-fork maintenance is sparse (last release Jan 2025); QPalette fallback documented
- JSON serialization: HIGH — stdlib `json` + `dataclasses.asdict()` round-trip; no external library risk

**Research date:** 2026-02-26
**Valid until:** 2026-05-26 (PyQt6 stable; 90 days for core stack; check PyQtDarkTheme-fork within 30 days if install issues arise)
