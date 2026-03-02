---
phase: 04-flow-control-and-window-management
plan: "04"
subsystem: ui-view
tags: [label-goto-styling, window-picker, view-model, pyqtSignal, pynput]
dependency_graph:
  requires: [04-02]
  provides: [Label/Goto visual styling, WindowPickerService]
  affects: [src/macro_thunder/models/view_model.py, src/macro_thunder/ui/window_picker.py, src/macro_thunder/ui/main_window.py]
tech_stack:
  added: []
  patterns: [BackgroundRole/DecorationRole in QAbstractTableModel, pyqtSignal cross-thread emission for pynput callbacks]
key_files:
  created:
    - src/macro_thunder/ui/window_picker.py
  modified:
    - src/macro_thunder/models/view_model.py
    - src/macro_thunder/ui/main_window.py
decisions:
  - "SP_CommandLink used as Label icon (right-arrow flag stand-in) and SP_ArrowRight for Goto — both theme-aware Qt standard pixmaps"
  - "WindowPickerService._on_pick() emits pyqtSignal only (no Qt object calls) — queued connection ensures main-thread slot execution"
metrics:
  duration: "70s"
  completed: "2026-03-02"
  tasks: 2
  files: 3
---

# Phase 04 Plan 04: Label/Goto Styling + WindowPickerService Summary

Label/Goto row visual styling (muted indigo BackgroundRole + standard icon DecorationRole) added to BlockTableModel, and WindowPickerService implemented with minimize/click/restore cycle using pynput.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Label/Goto visual styling in BlockTableModel | 601d454 | view_model.py |
| 2 | WindowPickerService + MainWindow wiring | 7ff2bc5 | window_picker.py, main_window.py |

## What Was Built

**Task 1 — BackgroundRole + DecorationRole:**
- `BlockTableModel.data()` now handles `BackgroundRole`: returns `QBrush(QColor(55, 45, 80))` (muted indigo) for `LabelBlock` and `GotoBlock` rows
- `DecorationRole` branch returns `SP_CommandLink` icon for `LabelBlock` (flag stand-in) and `SP_ArrowRight` for `GotoBlock`, column 0 only
- Icons are Qt standard pixmaps — theme-aware, no external assets needed
- Existing imports (`LabelBlock`, `GotoBlock`) were already in place from Phase 04-02

**Task 2 — WindowPickerService:**
- `src/macro_thunder/ui/window_picker.py` created with `WindowPickerService(QObject)`
- `start()` (no args): minimizes `_main_window`, sets crosshair cursor (best-effort), starts `pynput.mouse.Listener`
- `cancel()`: stops listener safely, usable from `closeEvent`
- `_on_pick()`: calls `_hwnd_from_point` + `_get_window_info`, then emits `picked(exe, title)` or `cancelled()` — no Qt object access
- `MainWindow` wired: `_picker` constructed in `__init__`, `_on_picker_picked` and `_on_picker_cancelled` slots call `showNormal()/activateWindow()` on main thread via queued connection

## Deviations from Plan

None — plan executed exactly as written.

## Verification

- 97 pytest tests pass (no regressions)
- `from macro_thunder.ui.window_picker import WindowPickerService` imports successfully

## Self-Check: PASSED

- `src/macro_thunder/ui/window_picker.py` — created and importable
- `src/macro_thunder/models/view_model.py` — BackgroundRole/DecorationRole branches added
- Commits 601d454 and 7ff2bc5 verified in git log
