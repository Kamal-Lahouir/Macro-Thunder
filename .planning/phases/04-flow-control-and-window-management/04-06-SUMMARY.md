---
phase: 04-flow-control-and-window-management
plan: 06
subsystem: ui-integration
tags: [main-window, validation, loop-detection, window-picker, playback]
dependency_graph:
  requires: [04-03, 04-05]
  provides: [full-phase-4-integration]
  affects: [src/macro_thunder/ui/main_window.py, src/macro_thunder/ui/editor_panel.py]
tech_stack:
  added: []
  patterns: [queue-drain-pattern, preflight-validation, loop-detection-callback]
key_files:
  created: []
  modified:
    - src/macro_thunder/ui/main_window.py
    - src/macro_thunder/ui/editor_panel.py
    - src/macro_thunder/ui/window_picker.py
    - src/macro_thunder/engine/__init__.py
    - src/macro_thunder/engine/window_utils.py
decisions:
  - "WindowPickerService owned by MainWindow and passed to EditorPanel; closeEvent calls cancel() for cleanup"
  - "on_loop_detected callback bridges playback thread to main thread via queue drain in _update_status"
  - "validate_gotos called in _start_play before engine.start() to block playback on missing labels"
  - "select_flat_index added to EditorPanel to highlight offending Goto row after loop detection"
  - "Right-click cancels window picker; minimized window restore avoids un-maximizing already-maximized windows"
metrics:
  duration: "~30 min"
  completed: "2026-03-02"
  tasks_completed: 2
  files_modified: 5
---

# Phase 04 Plan 06: MainWindow Integration Summary

Wire all Phase 4 capabilities into MainWindow — pre-flight Goto validation, infinite loop detection via queue bridge, WindowPickerService ownership, and closeEvent cleanup.

## What Was Built

Integration layer connecting all Phase 4 subsystems into a cohesive user experience:

- **Pre-flight validation:** `_start_play` calls `validate_gotos(blocks)` before starting the engine. If any Goto targets a label that doesn't exist, a `QMessageBox.critical` lists the missing names and playback is blocked.
- **Loop detection queue bridge:** `PlaybackEngine` now receives `on_loop_detected` callback. The callback puts `(flat_index, label_name)` into `_loop_detect_queue` from the playback thread. `_update_status` (running on main thread via QTimer) drains the queue, stops playback, shows a warning dialog, and calls `editor_panel.select_flat_index(flat_index)` to highlight the offending row.
- **`select_flat_index` on EditorPanel:** Iterates display rows to find the matching `BlockRow.flat_index`, then calls `selectRow` + `scrollTo` to bring the Goto into view.
- **WindowPickerService ownership:** MainWindow constructs `WindowPickerService(self)` and passes it to `EditorPanel`. `closeEvent` calls `picker_service.cancel()` to stop any active pynput listener before Qt teardown.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire MainWindow integration points | 0589e57 | main_window.py, editor_panel.py |
| 2 | Human verify — full Phase 4 end-to-end | (approved) | — |

## Post-Checkpoint Bug Fixes

After human verification approval, several bugs were found and fixed:

| Commit | Fix |
|--------|-----|
| f62eb6c | Select goto row before showing loop dialog; right-click cancels window picker |
| fd360d6 | Don't un-maximize window when activating via WindowFocusBlock |
| 3d6def3 | LabelBlock must not reset loop-detection progress flag |
| d28022a | Add New Macro menu item; guard Record/Open against unsaved changes |
| 2a1abad | Mark document dirty after recording so discard guard fires correctly |

## Verification

All 97 tests pass. Manual verification of all 5 test scenarios approved:
1. Label/Goto visual style (muted purple background, inline name/target editors)
2. Missing label validation blocks playback with QMessageBox listing missing names
3. Infinite loop detection stops playback, shows warning, highlights offending Goto row
4. WindowFocus panel with reposition checkbox toggling X/Y/W/H fields
5. Window picker minimizes app, captures clicked window exe/title, restores app

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Right-click did not cancel window picker**
- Found during: Post-checkpoint testing
- Issue: Right-clicking during picker activated window instead of cancelling
- Fix: Added right-click detection to cancel picker flow
- Files modified: src/macro_thunder/ui/window_picker.py
- Commit: f62eb6c

**2. [Rule 1 - Bug] WindowFocusBlock un-maximized already-maximized windows**
- Found during: Post-checkpoint testing
- Issue: `ShowWindow(SW_RESTORE)` called unconditionally, collapsing maximized windows
- Fix: Skip restore when window is already in the foreground/visible state
- Files modified: src/macro_thunder/engine/window_utils.py
- Commit: fd360d6

**3. [Rule 1 - Bug] LabelBlock reset loop-detection progress counter**
- Found during: Post-checkpoint testing
- Issue: Label blocks were counted as "non-flow" progress, resetting the Goto fire counter and allowing infinite loops to evade detection
- Fix: LabelBlock excluded from non-flow progress flag
- Files modified: src/macro_thunder/engine/__init__.py
- Commit: 3d6def3

**4. [Rule 2 - Missing functionality] No guard for unsaved changes on Record/Open**
- Found during: Post-checkpoint testing
- Issue: Starting a new recording or opening a file silently discarded unsaved changes
- Fix: Added discard confirmation guard; added New Macro menu item
- Files modified: src/macro_thunder/ui/main_window.py
- Commit: d28022a

**5. [Rule 1 - Bug] Document not marked dirty after recording**
- Found during: Post-checkpoint testing
- Issue: After recording stopped, `_dirty` flag was not set, so the discard guard never fired
- Fix: Set dirty flag when recording produces a new document
- Files modified: src/macro_thunder/ui/main_window.py
- Commit: 2a1abad

## Self-Check: PASSED

All listed commits are present in git history. All listed files exist. 97 tests pass.
