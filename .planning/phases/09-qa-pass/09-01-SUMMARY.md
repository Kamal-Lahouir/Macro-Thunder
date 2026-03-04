---
phase: 09-qa-pass
plan: "01"
subsystem: recorder-and-playback
tags: [bugfix, tdd, recorder, playback]
dependency_graph:
  requires: []
  provides: [stale-sentinel-guard, stop-key-residue-fix]
  affects: [src/macro_thunder/ui/main_window.py, src/macro_thunder/recorder/__init__.py]
tech_stack:
  added: []
  patterns: [TDD red-green, guard-clause, bool-flag-consumer-pattern]
key_files:
  created:
    - tests/test_playback_state.py
    - tests/test_recorder_residue.py
  modified:
    - src/macro_thunder/ui/main_window.py
    - src/macro_thunder/recorder/__init__.py
decisions:
  - Guard sentinel branch on AppState.PLAYING so stale (-1,-1) from natural completion does not clear amber cursor after hotkey stop
  - _stop_key_consumed bool flag is the simplest correct fix — no set needed because stop hotkey is a single key, and reset on release closes the window cleanly
metrics:
  duration: "1.5 min"
  completed_date: "2026-03-04"
  tasks_completed: 2
  files_changed: 4
---

# Phase 9 Plan 1: Core Record/Play Bug Fixes Summary

One-liner: Two surgical one-line guards fix the stale-sentinel amber-cursor erasure and stop-key release leak.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix stale sentinel bug in _update_status drain loop | 3116e1e | main_window.py, test_playback_state.py |
| 2 | Fix stop-key release leak in RecorderService | 227ff75 | recorder/__init__.py, test_recorder_residue.py |

## What Was Built

### Task 1 — Stale sentinel guard

Added `if self._state == AppState.PLAYING:` guard inside the `(-1, -1)` sentinel branch of `_update_status`. Previously, if the user pressed Stop hotkey then pressed Play to resume from the amber cursor row, the engine's natural-completion sentinel would arrive stale in the queue and call `_stop_play(clear_cursor=True)`, erasing the amber position. The guard discards the stale sentinel when state is already IDLE.

### Task 2 — Stop-key release suppression

Added `_stop_key_consumed: bool = False` to `RecorderService.__init__`. Set to `True` in `_on_press` immediately before queuing `STOP_SENTINEL`. In `_on_release`, inserted a guard that checks `_stop_key_consumed and _matches_stop_hotkey(key)` — if matched, the release is silently dropped and the flag reset. This prevents the stop-key key-up event from appearing as a `KeyPressBlock(direction="up")` in the recorded blocks.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- tests/test_playback_state.py: EXISTS
- tests/test_recorder_residue.py: EXISTS
- src/macro_thunder/ui/main_window.py contains `if self._state == AppState.PLAYING:`: CONFIRMED
- src/macro_thunder/recorder/__init__.py contains `_stop_key_consumed`: CONFIRMED
- Commits 3116e1e and 227ff75: CONFIRMED
- 10 new tests pass; 130 total tests pass (15 pre-existing errors in test_editor_ui.py due to missing pytest-qt, not caused by this plan)
