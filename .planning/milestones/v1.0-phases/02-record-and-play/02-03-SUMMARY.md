---
phase: 02-record-and-play
plan: 03
subsystem: ui-toolbar-hotkeys-settings
tags: [toolbar, hotkeys, settings, pyqtSignal, pynput, queue-drain]
dependency_graph:
  requires: []
  provides: [ToolbarPanel, HotkeyManager, AppSettings]
  affects: [ui/main_window.py]
tech_stack:
  added: []
  patterns: [queue+QTimer-drain, pyqtSignal, QDoubleSpinBox, QProgressBar, QTimer-blink]
key_files:
  created:
    - src/macro_thunder/settings.py
    - src/macro_thunder/hotkeys.py
  modified:
    - src/macro_thunder/ui/toolbar.py
decisions:
  - "Speed repeat count fixed at 1 for Phase 2; PLAY-03 repeat UI deferred to toolbar iteration"
  - "HotkeyManager lambdas capture queue alias (q) not self, preventing accidental Qt access from thread"
metrics:
  duration: 92s
  completed: 2026-02-28
---

# Phase 02 Plan 03: Toolbar, HotkeyManager, and AppSettings Summary

**One-liner:** ToolbarPanel with blinking record indicator and playback progress bar, HotkeyManager via pynput GlobalHotKeys + queue+QTimer drain, and AppSettings JSON persistence in Documents/MacroThunder/.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Implement AppSettings and HotkeyManager | 1d3ebad | settings.py, hotkeys.py |
| 2 | Implement ToolbarPanel with full Phase 2 controls | d7aa51d | ui/toolbar.py |

## What Was Built

**AppSettings** (`src/macro_thunder/settings.py`): Dataclass with five fields (four hotkey strings + mouse_threshold_px). `load()` reads `Documents/MacroThunder/settings.json` and filters unknown keys; `save()` creates the directory and writes pretty-printed JSON. Default hotkeys: F9/F10 (record), F6/F8 (play).

**HotkeyManager** (`src/macro_thunder/hotkeys.py`): QObject subclass with four pyqtSignals. `register(settings)` builds a pynput GlobalHotKeys map where each lambda only calls `q.put(action_str)` on a queue — no Qt objects touched from the listener thread. A 16ms QTimer drains the queue on the main thread and emits the matching signal. Fully satisfies the project threading rule.

**ToolbarPanel** (`src/macro_thunder/ui/toolbar.py`): Full replacement of the Phase 1 placeholder. Layout: recording group (Record/Stop + blinking red QLabel toggled by 500ms QTimer + block count label) | separator | playback group (Play/Stop + QProgressBar + Playing: N/M label) | stretch | speed group (QDoubleSpinBox 0.1-5.0 + 0.5x/1x/2x preset buttons). Four pyqtSignals. Public API: `set_recording()`, `update_block_count()`, `set_playback()`, `set_playback_progress()`.

## Verification Results

- `AppSettings.load()` round-trip: hotkey_stop_play == `<f8>` — PASSED
- `from macro_thunder.hotkeys import HotkeyManager` — PASSED
- `ToolbarPanel()` instantiates and shows without error — PASSED
- Threading rule: no Qt calls in hotkey lambdas (grep confirmed) — PASSED
- `Documents/MacroThunder/settings.json` created with default hotkeys — CONFIRMED

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `src/macro_thunder/settings.py` — exists
- [x] `src/macro_thunder/hotkeys.py` — exists
- [x] `src/macro_thunder/ui/toolbar.py` — modified (172 lines, up from 9)
- [x] Commit 1d3ebad — AppSettings + HotkeyManager
- [x] Commit d7aa51d — ToolbarPanel

## Self-Check: PASSED
