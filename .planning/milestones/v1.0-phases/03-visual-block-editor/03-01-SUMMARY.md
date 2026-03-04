---
phase: 03-visual-block-editor
plan: 01
subsystem: models/view_model
tags: [tdd, rescaling, view-model, group-edit]
dependency_graph:
  requires: []
  provides: [view_model.py DisplayRow types, _rescale_group_duration, _rescale_group_coords]
  affects: [BlockTableModel.setData (Phase 3 plans 02+)]
tech_stack:
  added: []
  patterns: [TDD RED-GREEN, module-level pure functions for testability without Qt]
key_files:
  created:
    - src/macro_thunder/models/view_model.py
    - tests/test_view_model_rescale.py
  modified: []
decisions:
  - "_rescale_group_coords single-move is a no-op (not apply new_start) — consistent with _rescale_group_duration single-move no-op contract"
  - "Functions are module-level (not methods) so tests can run without Qt"
metrics:
  duration: "~3 min"
  completed: "2026-03-01"
  tasks: 2
  files: 2
requirements:
  - GROUP-02
---

# Phase 03 Plan 01: Rescaling Logic + DisplayRow Types Summary

Pure rescaling helpers and DisplayRow dataclasses TDD-verified for the GROUP-02 group duration editor.

## What Was Built

`src/macro_thunder/models/view_model.py` — the view-layer foundation for Phase 3:

- **DisplayRow types:** `BlockRow`, `GroupHeaderRow`, `GroupChildRow` dataclasses + `DisplayRow` Union alias
- **`_rescale_group_duration`:** Proportional timestamp rescaling — scales all move timestamps so the group total duration equals the requested value. No-op for single/zero-duration groups.
- **`_rescale_group_coords`:** Linear x/y interpolation between `new_start` and `new_end` anchors across all intermediate moves. No-op for single moves.

`tests/test_view_model_rescale.py` — 5 tests, all GREEN:
- `test_rescale_duration_proportional`: 3 moves t=[0, 0.5, 1] → t=[0, 1, 2] for new_duration=2.0
- `test_rescale_duration_single_move`: single block unchanged
- `test_rescale_duration_zero_old`: all-same-timestamp group unchanged
- `test_rescale_coords_linear`: 3 moves remapped from (0,0)→(100,100) to (0,0)→(100,200), intermediate at (50,100)
- `test_rescale_coords_single_move`: no crash, no mutation on single block

## TDD Execution

| Phase | Status | Commit |
|-------|--------|--------|
| RED | ModuleNotFoundError (view_model.py absent) | 5016de4 |
| GREEN | All 5 tests pass | f5fd6ac |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `src/macro_thunder/models/view_model.py` exists
- [x] `tests/test_view_model_rescale.py` exists
- [x] Commit 5016de4 exists (RED tests)
- [x] Commit f5fd6ac exists (GREEN implementation)
- [x] 56 total tests pass, no regressions
