---
phase: 02-record-and-play
plan: "04"
subsystem: ui
tags: [pyqt6, pynput, mainwindow, recorder, playback, hotkeys, settings, persistence]

requires:
  - phase: 02-record-and-play/02-01
    provides: RecorderService TDD implementation
  - phase: 02-record-and-play/02-02
    provides: PlaybackEngine TDD implementation
  - phase: 02-record-and-play/02-03
    provides: ToolbarPanel, HotkeyManager, AppSettings

provides:
  - MainWindow wired with AppState machine, RecorderService, PlaybackEngine, HotkeyManager
  - SettingsDialog for hotkey + threshold configuration
  - File menu with Save Macro / Open Macro / Settings
  - Full record-play loop: F9 start, F10 stop, F6 play, F8 stop-play

affects: [03-block-editor, 04-advanced-features]

tech-stack:
  added: []
  patterns:
    - AppState enum guards all state transitions (IDLE/RECORDING/PLAYING)
    - play progress bridged from thread via queue drained in existing 16ms status timer
    - QAction imported from PyQt6.QtGui (not QtWidgets) in Qt6

key-files:
  created:
    - src/macro_thunder/ui/settings_dialog.py
  modified:
    - src/macro_thunder/ui/main_window.py
    - src/macro_thunder/persistence/__init__.py

key-decisions:
  - "QAction must come from PyQt6.QtGui, not PyQt6.QtWidgets (moved in Qt6)"
  - "persistence/__init__.py exposes save_macro/load_macro aliases over bare save/load"
  - "Play progress queue drained in existing 16ms coord timer — no third timer added"

patterns-established:
  - "AppState enum pattern: all slots guard on self._state before acting"
  - "Thread-safe progress: callback puts to queue, main-thread timer drains"

requirements-completed: [REC-01, REC-03, REC-04, REC-05, REC-06, REC-07, PLAY-01, PLAY-03, PLAY-04, PLAY-05]

duration: 8min
completed: 2026-02-28
---

# Phase 2 Plan 04: Integration Wiring Summary

**SettingsDialog + MainWindow AppState machine wiring RecorderService, PlaybackEngine, HotkeyManager, File menu, and Settings into a complete record-play loop**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-02-28T00:00:00Z
- **Completed:** 2026-02-28
- **Tasks:** 2 of 2 auto tasks complete (checkpoint:human-verify APPROVED — all 9 steps passed)
- **Files modified:** 3

## Accomplishments
- Created SettingsDialog with 5 form fields (4 hotkeys + threshold spinbox) and OK/Cancel
- Wired MainWindow with AppState enum (IDLE/RECORDING/PLAYING) controlling all transitions
- Connected RecorderService drain timer, PlaybackEngine progress queue, HotkeyManager signals
- Added File menu: Save Macro (Ctrl+S), Open Macro (Ctrl+O), Settings
- All 51 tests pass

## Task Commits

1. **Task 1: Add SettingsDialog** - `ffe2a7d` (feat)
2. **Task 2: Wire MainWindow** - `139f464` (feat)

## Files Created/Modified
- `src/macro_thunder/ui/settings_dialog.py` - QDialog with hotkey fields and threshold spinbox
- `src/macro_thunder/ui/main_window.py` - Full AppState wiring, File menu, all slots
- `src/macro_thunder/persistence/__init__.py` - Exports save_macro/load_macro aliases

## Decisions Made
- `QAction` imported from `PyQt6.QtGui` (not `QtWidgets`) — moved in Qt6; auto-fixed during task 2
- persistence `__init__.py` given `save_macro`/`load_macro` aliases to match plan spec
- Play progress drained in existing 16ms `_update_status` timer — no extra timer added

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] QAction not in PyQt6.QtWidgets**
- **Found during:** Task 2 (Wire MainWindow)
- **Issue:** `ImportError: cannot import name 'QAction' from 'PyQt6.QtWidgets'` — Qt6 moved QAction to QtGui
- **Fix:** Changed import to `from PyQt6.QtGui import QAction, QCursor`
- **Files modified:** src/macro_thunder/ui/main_window.py
- **Verification:** `py -c "from macro_thunder.ui.main_window import MainWindow; print('OK')"`
- **Committed in:** 139f464

**2. [Rule 2 - Missing Critical] persistence/__init__.py was empty**
- **Found during:** Task 2 (Wire MainWindow)
- **Issue:** Plan uses `save_macro`/`load_macro` but persistence `__init__.py` exported nothing
- **Fix:** Added `save_macro = save` and `load_macro = load` aliases in `__init__.py`
- **Files modified:** src/macro_thunder/persistence/__init__.py
- **Verification:** Import succeeds; all 51 tests pass
- **Committed in:** 139f464

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both fixes necessary for the module to run. No scope creep.

## Issues Encountered
None beyond the two auto-fixed deviations above.

## Next Phase Readiness
- Full record-play loop verified by user (all 9 checkpoint steps passed)
- Phase 3 (block editor) can proceed; MacroDocument.blocks flat list is stable
- Phase 3 note: QAbstractTableModel with variable-height rows warrants research before coding

---
*Phase: 02-record-and-play*
*Completed: 2026-02-28*
