---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [python, pyqt6, pynput, hatchling, src-layout]

# Dependency graph
requires: []
provides:
  - Installable Python package skeleton with hatchling build backend
  - src/macro_thunder package with models, persistence, ui, engine submodules
  - CLAUDE.md with critical project rules for DPI, threading, data model, and timing
affects:
  - 01-02
  - 01-03
  - 01-04
  - all subsequent phases

# Tech tracking
tech-stack:
  added:
    - PyQt6>=6.4
    - pynput>=1.7
    - PyQtDarkTheme-fork>=2.3.4 (optional, incompatible with Python 3.14)
    - hatchling (build backend)
  patterns:
    - src-layout package structure (src/macro_thunder/)
    - optional dependencies for Python-version-constrained packages

key-files:
  created:
    - pyproject.toml
    - CLAUDE.md
    - src/macro_thunder/__init__.py
    - src/macro_thunder/__main__.py
    - src/macro_thunder/models/__init__.py
    - src/macro_thunder/persistence/__init__.py
    - src/macro_thunder/ui/__init__.py
    - src/macro_thunder/engine/__init__.py
    - tests/__init__.py
  modified: []

key-decisions:
  - "PyQtDarkTheme-fork moved to optional dependency because it requires Python <3.14 and the system has Python 3.14.2"
  - "QPalette fallback required for dark theme on Python 3.14+; check importlib.util.find_spec('qdarktheme') before importing"

patterns-established:
  - "DPI awareness: ctypes.windll.shcore.SetProcessDpiAwareness(2) must be first executable lines in __main__.py"
  - "Threading: pynput callbacks must never touch Qt — use queue.Queue + QTimer drain"
  - "Data model: MacroDocument.blocks is always a flat list"
  - "Timing: absolute time.perf_counter() targets, never per-event sleep"

requirements-completed: [FOUND-01, FOUND-02, FOUND-03, FOUND-04]

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 1 Plan 01: Package Scaffold and Project Rules Summary

**hatchling src-layout package with PyQt6 + pynput installed, PyQtDarkTheme-fork as optional dependency due to Python 3.14 incompatibility, and CLAUDE.md encoding all critical runtime constraints**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-26T00:58:33Z
- **Completed:** 2026-02-26T01:00:48Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Package installs via `pip install -e .` on Python 3.14 with `import macro_thunder` succeeding
- All 5 submodule directories created with `__init__.py` files (models, persistence, ui, engine, tests)
- CLAUDE.md documents DPI-first constraint, threading rule, data model flat-list rule, timing rule, and PyQt6 API notes

## Task Commits

1. **Task 1: Create pyproject.toml and package skeleton** - `58167f8` (feat)
2. **Task 2: Create CLAUDE.md with project rules** - `2bfca85` (feat)

## Files Created/Modified

- `pyproject.toml` - hatchling build config; PyQt6 + pynput as core deps; PyQtDarkTheme-fork as optional[darktheme]
- `src/macro_thunder/__init__.py` - package root with `__version__ = "0.1.0"`
- `src/macro_thunder/__main__.py` - placeholder comment only
- `src/macro_thunder/models/__init__.py` - empty submodule
- `src/macro_thunder/persistence/__init__.py` - empty submodule
- `src/macro_thunder/ui/__init__.py` - empty submodule
- `src/macro_thunder/engine/__init__.py` - empty submodule (reserved Phase 2+)
- `tests/__init__.py` - empty test root
- `CLAUDE.md` - authoritative project rules for all Claude executors

## Decisions Made

- **PyQtDarkTheme-fork as optional dependency:** The package declares `Requires-Python >=3.8,<3.14` and the system runs Python 3.14.2. Moved to `[project.optional-dependencies] darktheme` so `pip install -e .` succeeds. Future UI code must check `importlib.util.find_spec("qdarktheme")` and fall back to QPalette if unavailable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PyQtDarkTheme-fork incompatible with Python 3.14**
- **Found during:** Task 1 (pip install -e .)
- **Issue:** PyQtDarkTheme-fork 2.3.4 has `Requires-Python >=3.8,<3.14`; system has Python 3.14.2; pip refused to install
- **Fix:** Moved `PyQtDarkTheme-fork>=2.3.4` from core `dependencies` to `[project.optional-dependencies] darktheme`; added Python 3.14 fallback note to CLAUDE.md
- **Files modified:** pyproject.toml, CLAUDE.md
- **Verification:** `pip install -e .` succeeded; `import macro_thunder` prints `0.1.0`
- **Committed in:** `58167f8` (Task 1 commit), `2bfca85` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - blocking install error)
**Impact on plan:** Necessary to make the package installable on the current Python version. The dark theme is still declared and can be installed on compatible Python versions. No scope creep.

## Issues Encountered

- Python not on PATH in MINGW64 shell — used absolute path `/c/Users/AMD/AppData/Local/Programs/Python/Python314/python.exe` for all commands.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Package is installed and importable — ready for Plan 02 (data models) and Plan 03 (entry point)
- All submodule stubs in place; implementation plans can add code without directory setup
- Dark theme: if a Plan adds `qdarktheme` theming, it must guard with `importlib.util.find_spec("qdarktheme")` and provide QPalette fallback

---
*Phase: 01-foundation*
*Completed: 2026-02-26*
