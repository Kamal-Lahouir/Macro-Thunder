---
plan: 05-04
status: complete
date: 2026-03-02
---

# Plan 05-04 Summary: Record Here Hotkey + System Tray

## What Was Built

- `hotkeys.py`: Added `record_here = pyqtSignal()`, registered a 5th `GlobalHotKeys` entry guarded by `if settings.hotkey_record_here:`, and added drain branch emitting `record_here`.
- `editor_panel.py`: Added `get_selected_flat_index()` public method that delegates to `_selected_flat_end_index()`.
- `main_window.py`:
  - `QSystemTrayIcon` created with gray/red 16×16 pixel icons; tray context menu has Show and Quit.
  - `_on_record_here_hotkey()` reads `editor.get_selected_flat_index()` and calls `_start_record_here()` — no window foreground.
  - `_play_sound_cue()` calls `winsound.Beep(880, 120)` when `sound_cue_enabled=True`; silently skipped on non-Windows.
  - `_start_record` / `_start_record_here` set tray icon red + play sound cue.
  - `_stop_record` resets tray icon to gray.

## Commits

- `1f55e67` feat(05-04): add record_here hotkey signal, get_selected_flat_index, system tray icon, sound cue

## Self-Check: PASSED

- [x] record_here hotkey optional (guarded by empty-string check)
- [x] get_selected_flat_index() public method present
- [x] tray icon always visible, red during recording, gray otherwise
- [x] tray menu has Show and Quit
- [x] sound cue plays on record start when enabled
- [x] 97 tests pass
