---
phase: 02-record-and-play
plan: 02
subsystem: engine
tags: [playback, threading, pynput, tdd, timing]
dependency_graph:
  requires: [macro_thunder.models.blocks]
  provides: [macro_thunder.engine.PlaybackEngine]
  affects: [ui-playback-controls, recorder-integration]
tech_stack:
  added: [threading.Event, time.perf_counter, pynput.mouse.Controller, pynput.keyboard.Controller]
  patterns: [dependency-injection, daemon-thread, perf_counter-spin-wait, callback-progress-bridge]
key_files:
  created:
    - src/macro_thunder/engine/__init__.py
    - tests/test_engine.py
  modified: []
decisions:
  - "Dispatch loop checks _stop_event at top of each iteration (not mid-sleep) for deterministic exit"
  - "Coarse sleep (remaining - 2ms) + spin-wait pattern for timing precision without pure busy-wait"
  - "Stop test uses 2ms sleep in counting_dispatch wrapper to ensure loop doesn't finish before stop() runs"
  - "Unknown block types silently ignored via isinstance chain (no-op, not raise)"
metrics:
  duration_minutes: 2
  completed_date: "2026-02-28"
  tasks_completed: 1
  files_changed: 2
---

# Phase 02 Plan 02: PlaybackEngine Summary

**One-liner:** perf_counter-based PlaybackEngine with pynput injection, speed scaling, repeat, stop via threading.Event, and progress callbacks — no Qt imports.

## What Was Built

`PlaybackEngine` is the core timing and dispatch engine for macro playback. It:

- Accepts injected mouse/keyboard controllers (or creates real pynput ones)
- Runs a daemon background thread so `start()` returns immediately
- Uses `time.perf_counter()` with a coarse-sleep + spin-wait pattern for sub-millisecond timing precision
- Scales block timestamps by `1/speed` (2x speed = target at `t0 + timestamp/0.5`)
- Runs the block sequence `repeat` times in a loop
- Checks `_stop_event.is_set()` at the top of each block iteration — exits cleanly on `stop()`
- Emits `on_progress(index, total)` after each dispatch from the playback thread (caller bridges to Qt via queue)

Dispatch is handled via `isinstance` branching:
- `MouseMoveBlock` → `_mouse_ctrl.position = (x, y)`
- `MouseClickBlock` → `_mouse_ctrl.press/release(Button[button])`
- `MouseScrollBlock` → `_mouse_ctrl.scroll(dx, dy)`
- `KeyPressBlock` → `_parse_key()` then `_kb_ctrl.press/release(key)`
- `DelayBlock`, `LabelBlock`, `GotoBlock`, `WindowFocusBlock` → no-op (Phase 4 placeholder)
- Unknown types → silently ignored

## Tests (14 total, all passing)

| Class | Tests | Coverage |
|-------|-------|----------|
| TestDispatch | 10 | All 6 block types + 4 no-op/unknown cases |
| TestStop | 1 | Thread exits within 2s after stop() |
| TestProgress | 1 | [(1,2),(2,2)] callback order |
| TestRepeat | 1 | 2 blocks x 3 repeats = 6 calls |
| TestSpeed | 1 | speed=10x dispatches all blocks in < 2s |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stop test assertion boundary condition**
- **Found during:** GREEN phase test run
- **Issue:** With all blocks at `timestamp=0.0` and `repeat=100`, the loop completed all 300 dispatches in ~1ms — faster than the 50ms `time.sleep()` in the test. The assertion `dispatch_count[0] < 300` failed with exactly 300.
- **Fix:** Added `time.sleep(0.002)` (2ms) inside the dispatch counting wrapper so 300 dispatches would take ~600ms, ensuring `stop()` runs mid-loop. This correctly tests the stop behavior without changing engine internals.
- **Files modified:** tests/test_engine.py
- **Commit:** 423482c (included in GREEN commit)

## Self-Check: PASSED

- FOUND: src/macro_thunder/engine/__init__.py
- FOUND: tests/test_engine.py
- FOUND commit d6ca38f (failing tests)
- FOUND commit 423482c (implementation + all tests green)
