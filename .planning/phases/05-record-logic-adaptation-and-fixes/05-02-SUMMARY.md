---
plan: 05-02
status: complete
date: 2026-03-02
---

# Plan 05-02 Summary: Click Mode Recording

## What Was Built

Added `click_mode` parameter to `RecorderService` so that in `"combined"` mode a left/right click emits a single `MouseClickBlock(direction="click")` instead of separate down/up blocks. Extended `PlaybackEngine._dispatch` to handle `direction="click"` by pressing then releasing the button atomically. Wired `click_mode=self._settings.click_mode` when constructing `RecorderService` in `_start_record` and `_start_record_here`. Added a `_click_mode_label` to the status bar showing "Click: Combined" or "Click: Separate" while recording.

## Commits

- `ab6f752` feat(05-02): add click_mode to RecorderService and engine dispatch; wire status bar label

## Self-Check: PASSED

- [x] combined mode emits direction="click" on press, suppresses release
- [x] separate mode (default) unchanged — down/up pairs
- [x] engine dispatches direction="click" as press+release
- [x] status bar label shows during recording, clears on stop
- [x] 97 tests pass
