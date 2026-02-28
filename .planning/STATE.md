# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.
**Current focus:** Phase 2 — Record and Play

## Current Position

Phase: 2 of 4 (Record and Play)
Plan: 3 of 4 in current phase
Status: In Progress
Last activity: 2026-02-28 — Plan 02-03 complete (Toolbar, HotkeyManager, AppSettings)

Progress: [████░░░░░░] 40%

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
| Phase 01-foundation P02 | 8 | 2 tasks | 4 files |
| Phase 02-record-and-play P02 | 2 | 1 tasks | 2 files |
| Phase 02-record-and-play P03 | 92s | 2 tasks | 3 files |
| Phase 02-record-and-play P01 | 2 min | 1 task | 2 files |

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
- [Phase 01-foundation]: type field uses field(default=..., init=False) so block_from_dict strips it before dispatch; block_from_dict raises KeyError for unknown types
- [Phase 01-foundation 01-03]: Qt6 sets DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 automatically — do NOT call SetProcessDpiAwareness manually
- [Phase 01-foundation 01-03]: Use QTimer polling QCursor.pos() at ~60 Hz for coordinate display — mouseMoveEvent on QMainWindow does not fire over child widgets
- [Phase 02-record-and-play]: perf_counter + coarse-sleep + spin-wait pattern for playback timing precision without pure busy-wait
- [Phase 02-record-and-play 02-03]: Speed repeat count fixed at 1 for Phase 2; PLAY-03 repeat UI deferred to toolbar iteration
- [Phase 02-record-and-play 02-03]: HotkeyManager lambdas capture queue alias (q) not self, preventing accidental Qt access from thread

### Pending Todos

None yet.

### Blockers/Concerns

- pyqtdarktheme maintenance status unclear — PyQtDarkTheme-fork (2.3.4) is fallback if install fails in Phase 1
- Phase 3: QAbstractTableModel with variable-height rows (collapsed vs. expanded group) may warrant research before coding
- Phase 4: pywin32 SetForegroundWindow limitations and interactive window picker (low-level mouse hook) are non-trivial — research recommended before coding

## Session Continuity

Last session: 2026-02-28
Stopped at: Completed 02-03-PLAN.md — Toolbar, HotkeyManager, AppSettings
Resume file: .planning/phases/02-record-and-play/02-03-SUMMARY.md
