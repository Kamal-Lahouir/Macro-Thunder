---
phase: 07-loop-blocks
plan: 01
subsystem: models, engine
tags: [loop-blocks, data-model, engine, tdd, validation]
dependency_graph:
  requires: []
  provides: [LoopStartBlock, LoopEndBlock, validate_loops, engine-loop-dispatch]
  affects: [engine/__init__.py, models/blocks.py, engine/validation.py]
tech_stack:
  added: []
  patterns: [dataclass-type-field, block-registry, loop-stack-dispatch]
key_files:
  created:
    - tests/test_loop_blocks.py
  modified:
    - src/macro_thunder/models/blocks.py
    - src/macro_thunder/engine/validation.py
    - src/macro_thunder/engine/__init__.py
decisions:
  - "loop_stack initialized inside outer repeat loop (not module-level) so it resets between macro repeat iterations"
  - "LoopStart/LoopEnd count as non-flow progress (set progress_since_last_goto=True) to avoid defeating goto loop detection"
  - "Orphaned LoopEnd silently skipped (i += 1, continue) to avoid crashes on malformed macros"
  - "validate_loops uses depth counter: depth>0 on LoopStart = nested error; depth<0 = orphaned LoopEnd; depth>0 at end = unclosed LoopStart"
metrics:
  duration: "94 seconds"
  completed: "2026-03-03"
  tasks_completed: 2
  files_modified: 4
---

# Phase 7 Plan 01: LoopStart/LoopEnd Data Model, Engine Dispatch, and Validation Summary

**One-liner:** LoopStartBlock/LoopEndBlock dataclasses with JSON round-trip, loop_stack engine dispatch, and validate_loops() pre-flight validation.

## What Was Built

- `LoopStartBlock(repeat: int)` and `LoopEndBlock()` dataclasses following the existing `field(default=..., init=False)` type pattern
- Both registered in `_BLOCK_CLASSES` and added to the `ActionBlock` Union for automatic JSON serialization via `block_from_dict`
- `validate_loops(blocks) -> list[str]` in `engine/validation.py`: detects orphaned LoopEnd, unclosed LoopStart, and nested loops using a depth counter
- `loop_stack: list[tuple[int, int]]` inside the outer `while True` repeat loop in `engine/_run` — resets correctly between macro repeat iterations
- LoopStart pushes `(i, repeat-1)` onto stack (first pass already in progress); LoopEnd either jumps back or pops the stack
- Orphaned LoopEnd (empty stack) silently skipped with `i += 1`

## Test Results

- 21 new tests in `tests/test_loop_blocks.py` — all pass (GREEN confirmed)
- Full test suite: 103 passed, 15 pre-existing errors (pytest-qt not installed; unrelated to this plan)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| RED  | 819340b | test(07-01): add failing tests for LoopStart/LoopEnd |
| GREEN | cd42667 | feat(07-01): implement LoopStartBlock, LoopEndBlock, validate_loops, and engine loop dispatch |

## Deviations from Plan

None - plan executed exactly as written. The linter auto-applied some import formatting which was harmless.

## Self-Check

Files created/modified:
- tests/test_loop_blocks.py: FOUND
- src/macro_thunder/models/blocks.py: FOUND (LoopStartBlock, LoopEndBlock)
- src/macro_thunder/engine/validation.py: FOUND (validate_loops)
- src/macro_thunder/engine/__init__.py: FOUND (loop_stack)
