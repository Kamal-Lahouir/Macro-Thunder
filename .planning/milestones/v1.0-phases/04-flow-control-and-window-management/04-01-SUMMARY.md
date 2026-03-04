---
phase: 04-flow-control-and-window-management
plan: 01
subsystem: engine
tags: [tdd, validation, window-management, ctypes, flow-control]
dependency_graph:
  requires: []
  provides: [engine/validation.py, engine/window_utils.py]
  affects: [engine/__init__.py (Plan 02 will call validate_gotos + window_utils)]
tech_stack:
  added: []
  patterns:
    - validate_gotos pure function with order-preserved deduplication
    - AttachThreadInput reliable foreground activation
    - _title_matches pure helper extracted for testability
key_files:
  created:
    - src/macro_thunder/engine/validation.py
    - src/macro_thunder/engine/window_utils.py
    - tests/test_flow_control.py
    - tests/test_window_utils.py
  modified: []
decisions:
  - "_title_matches extracted as standalone pure function so Contains/Exact/Starts With logic is unit-testable without ctypes"
  - "Unknown match_mode falls back to Contains to prevent silent failures on bad input"
  - "Loop detection counter logic tested via _simulate_loop_counter helper rather than exercising engine thread — documents the contract without requiring full engine integration"
metrics:
  duration: "4 min"
  completed: "2026-03-02"
  tasks: 2
  files: 4
---

# Phase 04 Plan 01: Engine Helpers — Validation and Window Utils Summary

**One-liner:** TDD-built `validate_gotos` (missing-label detection) and `window_utils` (ctypes Win32 helpers + pure `_title_matches` for Contains/Exact/Starts With matching).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | TDD — validate_gotos and loop detection counter logic | c9514a5 | engine/validation.py, tests/test_flow_control.py |
| 2 | TDD — window_utils: title matching modes + ctypes Win32 helpers | aaf7a6d | engine/window_utils.py, tests/test_window_utils.py |

## What Was Built

### engine/validation.py
`validate_gotos(blocks) -> list[str]` — pure function, scans a flat block list for GotoBlocks whose targets have no corresponding LabelBlock. Returns missing names deduplicated in first-seen order.

### engine/window_utils.py
Seven helpers:
- `_title_matches(title_query, window_title, match_mode)` — pure Python, case-insensitive, three modes
- `_get_visible_windows()` — EnumWindows + QueryFullProcessImageNameW for (hwnd, exe, title) list
- `_find_window(executable, title, match_mode)` — wraps _get_visible_windows + _title_matches
- `_activate_window(hwnd)` — AttachThreadInput pattern from RESEARCH.md Pitfall 1
- `_set_window_rect(hwnd, x, y, w, h)` — SetWindowPos with SWP_NOZORDER | SWP_NOACTIVATE
- `_hwnd_from_point(x, y)` — WindowFromPoint + GetAncestor(GA_ROOT) for top-level HWND
- `_get_window_info(hwnd)` — returns (title, exe_basename)

### Tests
- `test_flow_control.py` — 13 tests: 7 for validate_gotos, 6 for loop counter logic
- `test_window_utils.py` — 13 tests: all pure _title_matches cases (Contains/Exact/Starts With, edge cases, unknown mode fallback)

**Total test count:** 97 (up from 71; all pass, no regressions)

## Decisions Made

- `_title_matches` extracted as a pure helper separate from `_find_window` so it can be unit-tested without a live Windows session
- Unknown `match_mode` falls back to Contains (consistent with RESEARCH.md `_find_window` example)
- Loop detection counter contract tested via a `_simulate_loop_counter` helper directly in the test file — avoids pulling in the full engine thread for a pure logic contract test

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files verified:
- FOUND: src/macro_thunder/engine/validation.py
- FOUND: src/macro_thunder/engine/window_utils.py
- FOUND: tests/test_flow_control.py
- FOUND: tests/test_window_utils.py

Commits verified:
- FOUND: c9514a5
- FOUND: aaf7a6d
