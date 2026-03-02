---
phase: 04-flow-control-and-window-management
plan: 03
subsystem: engine
tags: [playback, flow-control, pynput, threading]

requires:
  - phase: 04-01
    provides: validate_gotos + window_utils (_find_window, _activate_window, _set_window_rect)
  - phase: 04-02
    provides: LabelBlock, GotoBlock, WindowFocusBlock data models
provides:
  - PlaybackEngine with while-loop index-pointer execution
  - LabelBlock/GotoBlock/WindowFocusBlock runtime dispatch
  - on_loop_detected callback for infinite-loop detection signal
affects:
  - 04-04 (UI wiring of on_loop_detected callback via queue.Queue)
  - 04-05 (integration tests against refactored engine)

tech-stack:
  added: []
  patterns:
    - "while-loop with index pointer replaces for-enumerate for flow control"
    - "GotoBlock loop guard: fire count per block index, cleared on progress"
    - "WindowFocusBlock polling uses stop_event.wait(0.5) not time.sleep for stop-signal responsiveness"

key-files:
  created: []
  modified:
    - src/macro_thunder/engine/__init__.py

key-decisions:
  - "GotoBlock loop detection threshold is 1000 fires without non-flow progress; on_loop_detected signals UI via callback (queue bridge in Plan 06)"
  - "WindowFocusBlock wait uses stop_event.wait(timeout=0.5) so stop() exits the poll immediately"
  - "label_index dict built once per _run() call (outside repeat loop) for O(1) goto resolution"

patterns-established:
  - "Flow-control blocks (Label, Goto, WindowFocus) skip timing/dispatch path and use continue — only normal action blocks advance virtual_time"
  - "progress_since_last_goto tracks whether any non-goto work happened since last goto fire to reset loop counter"

requirements-completed: [FLOW-01, FLOW-02, FLOW-04, WIN-04, WIN-05, WIN-06]

duration: 5min
completed: 2026-03-02
---

# Phase 4 Plan 03: Engine Flow Control Refactor Summary

**PlaybackEngine._run() refactored from for-enumerate to while-loop with LabelBlock/GotoBlock/WindowFocusBlock runtime dispatch, loop detection at >1000 fires, and stop-signal-responsive window polling**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-02T00:00:00Z
- **Completed:** 2026-03-02T00:05:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced `for i, block in enumerate(blocks)` with `while i < len(blocks)` for index-pointer control
- LabelBlock: marks progress, increments index, no dispatch
- GotoBlock: jumps to label position, detects >1000 loops without progress and fires on_loop_detected
- WindowFocusBlock: polls _find_window every 500ms using stop_event.wait (respects stop signal), activates/repositions, routes on success/failure labels
- Added on_loop_detected(flat_index, label_name) callback parameter

## Task Commits

1. **Task 1: Refactor PlaybackEngine._run() to while-loop with flow control dispatch** - `e364773` (feat)

## Files Created/Modified

- `src/macro_thunder/engine/__init__.py` - While-loop engine with LabelBlock/GotoBlock/WindowFocusBlock dispatch

## Decisions Made

- label_index built once outside the repeat loop — O(1) resolution, avoids rebuilding on each iteration
- goto_fire_count cleared when non-goto progress detected, preventing false positives across unrelated loops
- WindowFocusBlock poll uses `stop_event.wait(0.5)` not `time.sleep(0.5)` — stop() exits polling within 500ms max

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Engine fully implements flow control; ready for UI wiring in Plan 04 (on_loop_detected queue bridge in MainWindow)
- All 97 existing tests pass against refactored engine

---
*Phase: 04-flow-control-and-window-management*
*Completed: 2026-03-02*
