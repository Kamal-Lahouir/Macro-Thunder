# Macro Thunder — Project Rules for Claude

## Critical: DPI Awareness

`ctypes.windll.shcore.SetProcessDpiAwareness(2)` MUST be the first two executable lines
of `src/macro_thunder/__main__.py` — before ANY import that transitively imports PyQt6.

If this call appears after any Qt import, mouse coordinates at 125%+ display scaling
will be wrong (divided by the scale factor). This is NOT a test concern — it's a
runtime correctness issue that only manifests at non-100% display scaling.

## Package Name Warning

Install `PyQtDarkTheme-fork` (NOT `pyqtdarktheme`). Both expose `import qdarktheme`
but the original `pyqtdarktheme` is unmaintained and may fail with PyQt6.

Both cannot be installed simultaneously — the last-installed wins the `qdarktheme`
namespace. Only `PyQtDarkTheme-fork>=2.3.4` is supported.

**Python 3.14 note:** `PyQtDarkTheme-fork` requires Python <3.14 (`Requires-Python >=3.8,<3.14`).
On Python 3.14+, the package is declared as an optional dependency (`pip install -e ".[darktheme]"`).
The UI must use a QPalette fallback when `qdarktheme` is unavailable. Check availability with
`importlib.util.find_spec("qdarktheme")` before importing.

## Threading Rule

pynput listener callbacks MUST NEVER touch Qt objects directly. Use `queue.Queue` +
`QTimer` drain pattern exclusively. Violation causes unpredictable crashes.

## Data Model Rule

`MacroDocument.blocks` is ALWAYS a flat list of `ActionBlock`. Grouping of consecutive
MouseMove blocks is view-layer only (Phase 3). Never add nested/grouped structures to
the data model.

## Timing Rule

Playback uses absolute `time.perf_counter()` targets — never per-event `time.sleep()`.
Sleep-based playback drifts under scheduler load.

## PyQt6 API Notes

- Do NOT use `Qt.AA_EnableHighDpiScaling` — removed in Qt6, raises AttributeError
- Use `event.position()` / `event.globalPosition()` not `event.pos()` / `event.globalPos()`
- Use `QCursor.pos()` for screen-absolute coordinates in the status bar readout
- Enable mouse tracking on BOTH the main window AND any nested widget that fills the area

## Project Structure

```
src/macro_thunder/
    __init__.py         # version only
    __main__.py         # entry point; DPI call FIRST, then all other imports
    models/             # ActionBlock dataclasses + MacroDocument
    persistence/        # JSON serializer (save/load)
    ui/                 # QMainWindow + panel widgets
    engine/             # Playback engine (Phase 2+)
tests/                  # pytest tests
```

## Block Type Serialization

All ActionBlock subclasses declare `type` as `field(default="...", init=False)`.
This allows `block_from_dict` to reconstruct blocks by removing `"type"` from kwargs
before calling `cls(**kwargs)`. Never change `type` to an `init=True` field.
