# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.
**Current focus:** Phase 3 — Visual Block Editor

## Current Position

Phase: 3 of 4 (Visual Block Editor)
Plan: 4 of 4 in current phase
Status: In Progress
Last activity: 2026-03-01 — Plan 03-04 complete (LibraryPanel + rename_macro)

Progress: [███████░░░] 70%

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
| Phase 02-record-and-play P04 | 8 | 2 tasks | 3 files |
| Phase 02-record-and-play P04 | 15 | 2 tasks | 3 files |
| Phase 03-visual-block-editor P04 | 3 min | 2 tasks | 2 files |
| Phase 03-visual-block-editor P01 | 3 min | 2 tasks | 2 files |
| Phase 03-visual-block-editor P02 | 2 min | 2 tasks | 1 files |
| Phase 03-visual-block-editor P03 | 4min | 2 tasks | 3 files |
| Phase 03-visual-block-editor P05 | 5min | 1 tasks | 1 files |
| Phase 03-visual-block-editor P06 | 5min | 1 tasks | 1 files |
| Phase 04-flow-control-and-window-management P02 | 2 min | 1 tasks | 1 files |

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
- [Phase 02-record-and-play 02-01]: Last-position for threshold check only updates when event is queued — distance is measured from last accepted position, not last seen position
- [Phase 02-record-and-play]: QAction must come from PyQt6.QtGui, not PyQt6.QtWidgets (moved in Qt6)
- [Phase 02-record-and-play]: QAction must come from PyQt6.QtGui, not PyQt6.QtWidgets (moved in Qt6)
- [Phase 02-record-and-play]: Play progress queue drained in existing 16ms coord timer — no third timer added
- [Phase 03-04]: LibraryPanel emits signals to MainWindow for load/save separation of concerns
- [Phase 03-01]: _rescale_group_coords single-move is a no-op — consistent with _rescale_group_duration no-op contract
- [Phase 03-visual-block-editor]: BlockTableModel uses beginResetModel/endResetModel for all mutations — simpler than fine-grained insertRows given full display list rebuild
- [Phase 03-visual-block-editor]: Expanded group state stored in Dict[int,bool] keyed on flat_start so it survives _rebuild_display_rows creating new GroupHeaderRow instances
- [Phase 03-visual-block-editor]: BlockDelegate skips paint() override — arrows live in data() DisplayRole text; editorEvent-only approach keeps delegate lightweight
- [Phase 03-visual-block-editor]: UserRole branch added to BlockTableModel.data() to expose DisplayRow objects to delegate without coupling
- [Phase 03-visual-block-editor]: EditorPanel buttons disabled until load_document() called; clearSelection() before delete_rows for UI consistency
- [Phase 03-visual-block-editor]: _load_document() central helper: all load paths (file open, library, record stop) funnel through single method for consistent dirty-reset, editor update, block count
- [Phase 04-02]: All new WindowFocusBlock fields use defaults for backwards-compatible deserialization

### Pending Todos

None yet.

### Blockers/Concerns

- pyqtdarktheme maintenance status unclear — PyQtDarkTheme-fork (2.3.4) is fallback if install fails in Phase 1
- Phase 3: QAbstractTableModel with variable-height rows (collapsed vs. expanded group) may warrant research before coding
- Phase 4: pywin32 SetForegroundWindow limitations and interactive window picker (low-level mouse hook) are non-trivial — research recommended before coding

## Session Continuity

Last session: 2026-03-01
Stopped at: Completed 03-01-PLAN.md — Rescaling Logic + DisplayRow Types
Resume file: .planning/phases/03-visual-block-editor/03-01-SUMMARY.md
