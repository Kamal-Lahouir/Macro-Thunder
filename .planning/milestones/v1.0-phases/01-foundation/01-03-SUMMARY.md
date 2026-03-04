---
phase: 01-foundation
plan: 03
subsystem: ui
tags: [pyqt6, qdarktheme, qpalette, dpi, main-window, qsplitter]

requires:
  - phase: 01-01
    provides: Package scaffold and pyproject.toml with PyQt6 dependency declared

provides:
  - Dark-themed PyQt6 main window with three-panel QSplitter layout (toolbar top, library left, editor center-right)
  - Entry point __main__.py with qdarktheme / QPalette fallback dark theme
  - Live mouse coordinate readout in status bar via QTimer polling QCursor.pos()
  - Confirmed: Qt6 handles DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 automatically

affects:
  - All future UI phases (panel widgets are placeholders to be filled in)
  - Phase 2 (playback engine display in editor panel)
  - Phase 3 (library panel and block editor replacing placeholders)

tech-stack:
  added: [PyQt6, qdarktheme (optional), QTimer, QCursor, QSplitter, QToolBar]
  patterns:
    - QTimer polling QCursor.pos() at 60 Hz for reliable screen-coordinate display
    - qdarktheme with QPalette fallback (try/except ImportError pattern)
    - QPalette.ColorGroup.Inactive set to prevent white flash on focus loss

key-files:
  created:
    - src/macro_thunder/__main__.py
    - src/macro_thunder/ui/main_window.py
    - src/macro_thunder/ui/toolbar.py
    - src/macro_thunder/ui/library_panel.py
    - src/macro_thunder/ui/editor_panel.py
  modified:
    - CLAUDE.md

key-decisions:
  - "Qt6 sets DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 automatically — do NOT call SetProcessDpiAwareness manually"
  - "Use QTimer polling QCursor.pos() at ~60 Hz for coordinate display instead of mouseMoveEvent override (which does not fire when child widgets handle events)"

patterns-established:
  - "Coord display: QTimer(16ms) -> QCursor.pos() — reliable over all child widgets"
  - "Dark theme: try qdarktheme.setup_theme('dark') except ImportError: _apply_fallback_dark_palette(app)"

requirements-completed: [FOUND-01, FOUND-04]

duration: ~25min
completed: 2026-02-26
---

# Phase 1 Plan 03: Main Window Shell Summary

**Dark-themed PyQt6 main window with three-panel QSplitter layout and live screen-coordinate readout via QTimer-polled QCursor.pos()**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-02-26T00:45:00Z
- **Completed:** 2026-02-26T01:13:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Entry point `__main__.py` with qdarktheme / QPalette fallback dark theme path
- `MainWindow` with QToolBar + QSplitter (LibraryPanel left, EditorPanel right) layout
- Status bar coordinate label updated at ~60 Hz by polling `QCursor.pos()` — works everywhere regardless of which child widget has focus
- Identified and fixed two Qt6 integration issues found during human-verify: DPI call rejection and mouseMoveEvent propagation failure

## Task Commits

1. **Task 1: Implement `__main__.py` entry point** - `054af5b` (feat)
2. **Task 2: Implement main window and panel placeholder widgets** - `92a60e7` (feat)
3. **Task 3 (continuation fixes): Remove manual DPI call; switch coord display to QTimer polling** - `99638f4` (fix)

## Files Created/Modified

- `src/macro_thunder/__main__.py` - Entry point; qdarktheme + QPalette fallback dark theme
- `src/macro_thunder/ui/main_window.py` - QMainWindow with QSplitter layout and QTimer coordinate polling
- `src/macro_thunder/ui/toolbar.py` - Placeholder QFrame (40px fixed height, "Toolbar — Phase 2" label)
- `src/macro_thunder/ui/library_panel.py` - Left panel placeholder (180-320px width)
- `src/macro_thunder/ui/editor_panel.py` - Center/right panel placeholder (stretch factor 1)
- `CLAUDE.md` - Updated DPI guidance: Qt6 handles it automatically

## Decisions Made

- **Qt6 DPI is automatic**: Qt6 internally sets `DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2` before user code runs. Calling `SetProcessDpiAwareness(2)` via ctypes fails with "Access is denied." Removed the manual call entirely. `QCursor.pos()` returns correct screen-absolute coordinates at all scaling levels.

- **QTimer over mouseMoveEvent for coordinates**: `mouseMoveEvent` on `QMainWindow` does not fire when child widgets (splitter, panels) handle the event. The reliable solution is a 16ms `QTimer` that polls `QCursor.pos()` — this is screen-global and always accurate.

## Deviations from Plan

### Auto-fixed Issues (during continuation after human-verify)

**1. [Rule 1 - Bug] Removed manual SetProcessDpiAwareness call**
- **Found during:** Task 3 — human-verify checkpoint (user reported Qt error)
- **Issue:** `ctypes.windll.shcore.SetProcessDpiAwareness(2)` was called before Qt imports, but Qt6 already set DPI context before Python user code, causing "Access is denied" error in Qt's internal call
- **Fix:** Removed the ctypes DPI call entirely from `__main__.py`; updated `CLAUDE.md` to document the correct behavior
- **Files modified:** `src/macro_thunder/__main__.py`, `CLAUDE.md`
- **Committed in:** `99638f4`

**2. [Rule 1 - Bug] Fixed coordinate display not updating over child widgets**
- **Found during:** Task 3 — human-verify checkpoint (user reported coordinate bugginess)
- **Issue:** `mouseMoveEvent` override on `QMainWindow` only fires when the mouse is over the window's own background — child widgets (QSplitter, LibraryPanel, EditorPanel) consume mouse events and the override never fires in normal use
- **Fix:** Replaced `mouseMoveEvent` with a `QTimer(16ms)` that calls `QCursor.pos()` directly — fires continuously regardless of which widget the mouse is over
- **Files modified:** `src/macro_thunder/ui/main_window.py`
- **Committed in:** `99638f4`

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both fixes necessary for correct visible behavior; discovered during human-verify. No scope creep.

## Issues Encountered

The plan's `must_haves.artifacts` list references `SetProcessDpiAwareness` in `__main__.py`. After fixing the DPI bug, this call no longer exists. The correctness requirement (DPI-accurate coordinates) is still satisfied — Qt6 handles it natively — but the file no longer contains that string. The PLAN.md artifact check for `SetProcessDpiAwareness` would fail a strict automated scan; this is a plan artifact that is now outdated.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Complete three-panel shell ready for Phase 2 (playback engine) and Phase 3 (block editor)
- Dark theme confirmed working with qdarktheme
- Coordinate display reliable at all display scaling levels
- All placeholder panels export correctly and are importable

---
*Phase: 01-foundation*
*Completed: 2026-02-26*
