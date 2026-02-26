# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.
**Current focus:** Phase 1 — Foundation

## Current Position

Phase: 1 of 4 (Foundation)
Plan: 1 of 4 in current phase
Status: In Progress
Last activity: 2026-02-26 — Plan 01-01 complete (package scaffold + CLAUDE.md)

Progress: [█░░░░░░░░░] 6%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 3 min
- Total execution time: 0.05 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 1/4 | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 3 min
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Stack: PyQt6 + pynput + pywin32 on Python 3.11 (no viable alternative for QAbstractTableModel block editor)
- DPI: `ctypes.windll.shcore.SetProcessDpiAwareness(2)` must be first line of main.py before any imports
- Threading: pynput callbacks must never touch Qt objects — queue.Queue + QTimer drain pattern exclusively
- Timing: Playback uses absolute `time.perf_counter()` targets, not per-event sleep, to avoid scheduler drift
- Data model: MacroDocument.blocks is always a flat list — grouping is view-layer only, not stored structure
- [Phase 01-foundation]: PyQtDarkTheme-fork moved to optional dependency (Python 3.14 incompatible); QPalette fallback required

### Pending Todos

None yet.

### Blockers/Concerns

- pyqtdarktheme maintenance status unclear — PyQtDarkTheme-fork (2.3.4) is fallback if install fails in Phase 1
- Phase 3: QAbstractTableModel with variable-height rows (collapsed vs. expanded group) may warrant research before coding
- Phase 4: pywin32 SetForegroundWindow limitations and interactive window picker (low-level mouse hook) are non-trivial — research recommended before coding

## Session Continuity

Last session: 2026-02-26
Stopped at: Completed 01-01-PLAN.md — package scaffold and CLAUDE.md
Resume file: .planning/phases/01-foundation/01-01-SUMMARY.md
