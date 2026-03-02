---
phase: 04-flow-control-and-window-management
plan: 02
subsystem: models
tags: [dataclass, window-focus, backwards-compatibility]
requirements: [WIN-01]

dependency_graph:
  requires: []
  provides: [extended-WindowFocusBlock]
  affects: [engine, block-panels]

tech_stack:
  added: []
  patterns: [dataclass-defaults-for-compat]

key_files:
  modified:
    - src/macro_thunder/models/blocks.py

decisions:
  - "All new WindowFocusBlock fields use defaults so block_from_dict deserializes old macros without modification"
  - "type field kept last with init=False per CLAUDE.md project rule"

metrics:
  duration: "2 min"
  completed: "2026-03-02"
  tasks: 1
  files: 1
---

# Phase 04 Plan 02: Extend WindowFocusBlock Summary

WindowFocusBlock extended with 8 new fields (timeout, on_failure_label, on_success_label, reposition, x, y, w, h) — all with defaults for backwards-compatible deserialization.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend WindowFocusBlock dataclass | a923dea | src/macro_thunder/models/blocks.py |

## What Was Built

Added 8 new fields to `WindowFocusBlock`:
- `timeout: float = 5.0` — seconds to wait for window to appear
- `on_failure_label: str = ""` — empty means continue on failure
- `on_success_label: str = ""` — empty means continue to next block
- `reposition: bool = False` — whether to move/resize window on success
- `x: int = 0`, `y: int = 0`, `w: int = 0`, `h: int = 0` — target window geometry

The `type` field remains last with `init=False` per project rules. All 71 existing tests pass.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- [x] src/macro_thunder/models/blocks.py modified with 11 total fields
- [x] Commit a923dea exists
- [x] 71 tests pass (no regression)
- [x] `WindowFocusBlock("game.exe", "Game", "Contains")` constructs with timeout=5.0, reposition=False
