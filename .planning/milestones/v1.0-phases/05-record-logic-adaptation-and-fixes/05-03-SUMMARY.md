---
phase: 05-record-logic-adaptation-and-fixes
plan: 03
subsystem: toolbar-repeat-and-engine-infinite-loop
tags: [toolbar, playback-engine, repeat, infinite-loop, on-done]
dependency_graph:
  requires: []
  provides: [repeat-ui, infinite-loop-engine, on-done-callback]
  affects: [toolbar.py, engine/__init__.py, main_window.py]
tech_stack:
  added: []
  patterns: [repeat-sentinel, on-done-callback, queue-bridge]
key_files:
  created: []
  modified:
    - src/macro_thunder/ui/toolbar.py
    - src/macro_thunder/engine/__init__.py
    - src/macro_thunder/ui/main_window.py
decisions:
  - "repeat=-1 used as sentinel for infinite loop; avoids extra boolean param"
  - "on_done fires only on natural completion; stop() returns early without calling it"
  - "on_done bridges to main thread via existing _play_progress_queue with (-1,-1) sentinel"
  - "Removed idx>=total auto-stop guard from _update_status — completion now driven by on_done"
metrics:
  duration: "~5 min"
  completed: 2026-03-02
  tasks_completed: 2
  files_modified: 3
---

# Phase 5 Plan 03: Repeat Count + Infinite Loop Summary

**One-liner:** Toolbar repeat spinbox (1–9999) and infinite-loop checkbox wired to PlaybackEngine repeat=-1 sentinel with on_done callback for natural completion signaling.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add repeat spinbox + infinite checkbox to toolbar | fda0dc2 | toolbar.py |
| 2 | Extend engine with infinite loop and on_done callback | 4aa800b | engine/__init__.py, main_window.py |

## What Was Built

### Toolbar (Task 1)
- Added `QSpinBox` (`_spin_repeat`) with range 1–9999, default 1
- Added `QCheckBox` (`_chk_infinite`) with ∞ character; toggling disables the spinbox
- Updated `_on_play_clicked` to emit `repeat=-1` when infinite is checked, otherwise spinbox value
- Added visual separator between speed and repeat controls
- Existing `play_requested = pyqtSignal(float, int)` signature unchanged

### PlaybackEngine (Task 2)
- Added `on_done: Optional[Callable[[], None]]` parameter to `__init__`
- Replaced `for _ in range(repeat):` with `while True:` outer loop checking `repeat != -1 and iteration >= repeat`
- `on_done` fires only when all passes complete naturally
- `stop()` (via `_stop_event`) causes early return without calling `on_done`
- Progress continues to fire per-block within each pass; no premature stop between passes

### MainWindow (Task 2)
- `PlaybackEngine` constructed with `on_done=self._on_play_done`
- `_on_play_done` puts `(-1, -1)` sentinel into `_play_progress_queue` (existing queue, no new timer)
- `_update_status` handles `(-1, -1)` sentinel by calling `_stop_play()`
- Removed `if idx >= total: self._stop_play()` guard — completion driven by `on_done` only

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- All 97 existing tests pass
- Toolbar repeat controls confirmed via PyQt6 instantiation test
- Engine repeat=2 calls on_done after 2 passes (verified)
- Engine repeat=-1 loops until stop(); on_done NOT called on stop (verified)

## Self-Check: PASSED

Files confirmed:
- src/macro_thunder/ui/toolbar.py — modified, _spin_repeat and _chk_infinite present
- src/macro_thunder/engine/__init__.py — modified, on_done and while-True loop present
- src/macro_thunder/ui/main_window.py — modified, on_done wired, sentinel handled

Commits confirmed:
- fda0dc2 feat(05-03): add repeat spinbox and infinite loop checkbox to toolbar
- 4aa800b feat(05-03): extend PlaybackEngine with infinite loop and on_done callback
