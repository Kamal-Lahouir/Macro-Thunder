---
phase: 05-record-logic-adaptation-and-fixes
plan: 01
subsystem: settings
tags: [settings, ui, hotkeys, tabwidget]
dependency_graph:
  requires: []
  provides: [AppSettings.click_mode, AppSettings.hotkey_record_here, AppSettings.sound_cue_enabled, SettingsDialog-tabbed, Settings-top-level-menu]
  affects: [src/macro_thunder/settings.py, src/macro_thunder/ui/settings_dialog.py, src/macro_thunder/ui/main_window.py]
tech_stack:
  added: []
  patterns: [QTabWidget two-tab layout, hotkey conflict detection with QMessageBox]
key_files:
  created: []
  modified:
    - src/macro_thunder/settings.py
    - src/macro_thunder/ui/settings_dialog.py
    - src/macro_thunder/ui/main_window.py
decisions:
  - "click_mode default is 'separate' to preserve existing behavior for all current users"
  - "Record Here hotkey stored as empty string when disabled — HotkeyManager must guard against registering empty string"
  - "Settings menu moved to top-level for discoverability and to separate it from File operations"
metrics:
  duration: "~7 min"
  completed: "2026-03-02"
  tasks: 2
  files_modified: 3
---

# Phase 5 Plan 01: Settings Extension and SettingsDialog Restructure Summary

AppSettings extended with click_mode/hotkey_record_here/sound_cue_enabled fields; SettingsDialog rebuilt as QTabWidget with Hotkeys + Options tabs and Record Here conflict detection; Settings promoted to top-level menu.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend AppSettings with click_mode, hotkey_record_here, sound_cue_enabled | 4ac6cb1 | settings.py |
| 2 | Restructure SettingsDialog to QTabWidget + move Settings menu | bc6ae0d | settings_dialog.py, main_window.py |

## What Was Built

- **AppSettings** now has three new fields: `click_mode` (str, default "separate"), `hotkey_record_here` (str, default ""), `sound_cue_enabled` (bool, default False). The existing `load()` field-filter pattern means old settings files load without error.

- **SettingsDialog** rebuilt as QTabWidget with two tabs:
  - Hotkeys tab: 5 hotkey inputs (Start Record, Stop Record, Start Playback, Stop Playback, Record Here) with format hint label
  - Options tab: click mode QComboBox, mouse threshold QSpinBox, sound cue QCheckBox

- **Hotkey conflict detection** in `accept()`: if Record Here value matches any of the 4 existing hotkeys, QMessageBox.warning is shown and save is blocked.

- **Settings menu** moved from File submenu to top-level `&Settings > &Preferences...` for better discoverability.

## Verification

- All 97 existing tests pass (no regressions)
- `python -c "from macro_thunder.settings import AppSettings; s = AppSettings(); ..."` confirms fields at correct defaults
- `SettingsDialog` instantiation confirmed to have exactly 1 QTabWidget with 2 tabs ("Hotkeys", "Options")

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- src/macro_thunder/settings.py: FOUND (3 new fields added)
- src/macro_thunder/ui/settings_dialog.py: FOUND (QTabWidget, conflict detection)
- src/macro_thunder/ui/main_window.py: FOUND (settings_menu top-level)
- Commit 4ac6cb1: FOUND
- Commit bc6ae0d: FOUND
