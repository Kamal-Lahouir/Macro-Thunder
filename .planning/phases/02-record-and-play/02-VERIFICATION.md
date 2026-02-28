---
phase: 02-record-and-play
verified: 2026-02-28T00:00:00Z
status: human_needed
score: 18/18 must-haves verified
human_verification:
  - test: "Record-to-play end-to-end cycle"
    expected: "Press F9 -> red blink and block count appear; move mouse + press keys -> count increments; press F10 -> blink stops; press F6 -> mouse and keyboard replay on screen"
    why_human: "Requires real OS hooks, pynput listeners, and visual observation of mouse moving"
  - test: "Global F8 stop during playback in another window"
    expected: "Switch focus to another application while macro plays, press F8 -> playback halts and UI resets to idle state"
    why_human: "Requires multi-process focus change and real global hotkey behavior"
  - test: "File Save / Open round-trip"
    expected: "File > Save creates .json in Documents/MacroThunder/; after app restart File > Open loads it; pressing Play replays the same actions"
    why_human: "Requires app restart and real filesystem interaction"
  - test: "Settings dialog persists hotkey changes"
    expected: "File > Settings -> change a hotkey string -> OK -> new hotkey activates; settings.json updated on disk"
    why_human: "Requires verifying pynput re-registration and file content"
  - test: "UI does not freeze during recording or playback"
    expected: "Cursor coordinate readout in status bar continues updating and toolbar stays responsive while recording or playing"
    why_human: "Requires real-time visual observation of UI responsiveness"
---

# Phase 2: Record and Play Verification Report

**Phase Goal:** Users can record mouse and keyboard input, save the result, and play it back with accurate timing — the first end-to-end working macro
**Verified:** 2026-02-28
**Status:** human_needed (all automated checks pass; 5 behavioral items need manual testing)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | RecorderService.start() begins capturing and stop() ends capture cleanly | VERIFIED | `recorder/__init__.py` L48-89: start() creates/starts two Listeners; stop() nulls them with exception guard. TestStartStop passes (4 tests). |
| 2 | Mouse move events queued as MouseMoveBlock with correct x, y, relative timestamp | VERIFIED | `_on_move` L95-110: puts `MouseMoveBlock(x=x, y=y, timestamp=ts)`. TestOnMove passes (5 tests). |
| 3 | Mouse click events produce MouseClickBlock with button name and direction | VERIFIED | `_on_click` L112-122: `button=button.name`, `direction="down" if pressed else "up"`. TestOnClick passes (3 tests). |
| 4 | Mouse scroll events produce MouseScrollBlock with dx, dy | VERIFIED | `_on_scroll` L124-126: puts `MouseScrollBlock(x,y,dx,dy,timestamp)`. TestOnScroll passes (2 tests). |
| 5 | Keyboard events produce KeyPressBlock with key string and direction | VERIFIED | `_on_press/_on_release` L128-134: uses `_key_to_str`, direction "down"/"up". TestOnKeyboard passes (4 tests). |
| 6 | Mouse moves below pixel threshold are discarded; above are queued | VERIFIED | `_on_move` L104-110: `math.hypot` check; returns without put if below threshold. TestOnMove::test_move_below_threshold_discarded passes. |
| 7 | Injected mouse events (LLMHF_INJECTED) are filtered out | VERIFIED | `_mouse_filter` L150-153: `not bool(data.flags & 0x00000001)`. TestInjectedEventFilters passes (5 tests). |
| 8 | Injected keyboard events (LLKHF_INJECTED bit 4) are filtered out | VERIFIED | `_kb_filter` L156-159: `not bool(data.flags & 0x00000010)`. TestInjectedEventFilters passes. |
| 9 | PlaybackEngine dispatches each block type to correct pynput Controller | VERIFIED | `_dispatch` L103-126 handles MouseMove/Click/Scroll/KeyPress. TestDispatch passes (10 tests). |
| 10 | Playback runs on background thread; does not block caller | VERIFIED | `start()` L50-63: starts daemon threading.Thread, returns immediately. TestStop verifies thread exits. |
| 11 | Speed multiplier scales inter-event delays | VERIFIED | `_run` L87: `target = t0 + block.timestamp / speed`. TestSpeed::test_high_speed_dispatches_all_blocks passes. |
| 12 | Repeat count N causes block sequence to execute N times | VERIFIED | `_run` L80: `for _ in range(repeat)`. TestRepeat::test_repeat_calls_progress_n_times passes (2x3=6 calls). |
| 13 | stop() sets threading.Event that playback checks and exits | VERIFIED | `_stop_event.is_set()` checked L83 inside loop. TestStop::test_stop_halts_playback joins thread in <2s. |
| 14 | Progress callbacks emitted after each block dispatch (no Qt calls) | VERIFIED | `_on_progress(i+1, len(blocks))` L100-101; no Qt imports in engine. TestProgress verifies [(1,2),(2,2)]. |
| 15 | Toolbar shows Record/Stop/Play/Stop buttons, speed spin, 0.5x/1x/2x presets, blink indicator, progress bar | VERIFIED | `toolbar.py` L15-176: all widgets present, 4 signals declared, blink timer at 500ms, set_playback_progress implemented. |
| 16 | HotkeyManager uses queue+QTimer drain (no direct Qt calls from hotkey callbacks) | VERIFIED | `hotkeys.py` L42-46: lambdas only call `q.put(str)`. `_drain()` L59-73 emits signals from main thread QTimer. GlobalHotKeys L48. |
| 17 | AppSettings loads/saves to Documents/MacroThunder/settings.json with hotkey fields | VERIFIED | `settings.py` L6-31: `SETTINGS_FILE` path, `json.loads/dumps`, all 4 hotkey fields + threshold. |
| 18 | MainWindow wires all components: RecorderService, PlaybackEngine, HotkeyManager, persistence | VERIFIED | `main_window.py` L23-28 imports all; L90-91 constructs; L107-118 connects signals; L209-224 file save/load; AppState machine at L31-34. |

**Score:** 18/18 truths verified (automated)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/macro_thunder/recorder/__init__.py` | RecorderService with start/stop, threshold, injected filter | VERIFIED | 159 lines, exports RecorderService, no Qt imports |
| `tests/test_recorder.py` | Unit tests, min 60 lines | VERIFIED | 269 lines, 24 tests all pass |
| `src/macro_thunder/engine/__init__.py` | PlaybackEngine with timing, speed, repeat, progress | VERIFIED | 137 lines, exports PlaybackEngine, no Qt imports |
| `tests/test_engine.py` | Unit tests, min 60 lines | VERIFIED | 231 lines, 18 tests all pass |
| `src/macro_thunder/ui/toolbar.py` | ToolbarPanel with all controls, min 80 lines | VERIFIED | 176 lines, 4 signals, blink timer, progress bar |
| `src/macro_thunder/hotkeys.py` | HotkeyManager with queue+QTimer drain | VERIFIED | 73 lines, GlobalHotKeys, queue drain pattern |
| `src/macro_thunder/settings.py` | AppSettings dataclass with load/save | VERIFIED | 31 lines, json round-trip, correct defaults |
| `src/macro_thunder/ui/settings_dialog.py` | SettingsDialog with 5 form fields | VERIFIED | 71 lines, QFormLayout, 5 fields, get_settings() |
| `src/macro_thunder/ui/main_window.py` | MainWindow wired with all services | VERIFIED | 234 lines, AppState enum, all slots connected |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `recorder/__init__.py` | `models/blocks.py` | constructs MouseMoveBlock, MouseClickBlock, MouseScrollBlock, KeyPressBlock | WIRED | L15-20 imports; L101/114/126/130/134 constructs |
| `recorder/__init__.py` | `queue.Queue` | `_event_queue.put(block)` | WIRED | L101/114/126/130/134 all call `self._queue.put(...)` |
| `engine/__init__.py` | `pynput.mouse.Controller` | `_mouse_ctrl.position / press / release / scroll` | WIRED | L106/110/113/116 in `_dispatch` |
| `engine/__init__.py` | `pynput.keyboard.Controller` | `_kb_ctrl.press / _kb_ctrl.release` | WIRED | L121/123 in `_dispatch` |
| `engine/__init__.py` | `threading.Event` | `_stop_event.is_set()` checked between each dispatch | WIRED | L83: `if self._stop_event.is_set(): return` |
| `toolbar.py` | `PyQt6.QtCore.pyqtSignal` | signals: record_requested, stop_record_requested, play_requested, stop_play_requested | WIRED | L18-21: 4 pyqtSignal declarations |
| `hotkeys.py` | `pynput.keyboard.GlobalHotKeys` | daemon thread in register() | WIRED | L48-50: creates, sets daemon=True, starts |
| `hotkeys.py` | `queue.Queue` | `_hotkey_queue.put(action_str)` | WIRED | L42-45: lambdas call `q.put(str)` |
| `settings.py` | `Documents/MacroThunder/settings.json` | `json.load / json.dump` | WIRED | L21 `json.loads`, L29 `json.dumps` |
| `main_window.py` | `recorder/__init__.py` | `RecorderService(queue, threshold)` | WIRED | L90: `RecorderService(self._rec_queue, ...)` |
| `main_window.py` | `engine/__init__.py` | `PlaybackEngine(on_progress=...)` | WIRED | L91: `PlaybackEngine(on_progress=self._on_play_progress)` |
| `main_window.py` | `hotkeys.py` | HotkeyManager signals connected to slots | WIRED | L113-118: all 4 hotkey signals connected |
| `main_window.py` | `persistence/__init__.py` | `save_macro / load_macro` | WIRED | L217/224: both called in save/open slots |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REC-01 | 02-01, 02-03, 02-04 | Start/stop recording via button and hotkey | SATISFIED | ToolbarPanel buttons + HotkeyManager F9/F10 -> MainWindow slots |
| REC-02 | 02-01 | Mouse moves captured with exact coordinates and timestamps | SATISFIED | MouseMoveBlock(x,y,timestamp) with perf_counter delta |
| REC-03 | 02-01 | Mouse clicks (left/right/middle, down/up) recorded | SATISFIED | MouseClickBlock with button.name and direction |
| REC-04 | 02-01, 02-04 | Mouse scroll events recorded | SATISFIED | MouseScrollBlock with dx, dy |
| REC-05 | 02-01 | Keyboard key presses (down/up) recorded | SATISFIED | KeyPressBlock with _key_to_str and direction |
| REC-06 | 02-01, 02-03 | Pixel threshold configurable; sub-threshold moves discarded | SATISFIED | RecorderService(pixel_threshold); AppSettings.mouse_threshold_px; SettingsDialog |
| REC-07 | 02-01 | Recording does not capture playback's own injected events | SATISFIED | _mouse_filter / _kb_filter with LLMHF_INJECTED / LLKHF_INJECTED |
| PLAY-01 | 02-02, 02-04 | Play macro with accurate perf_counter timing | SATISFIED | PlaybackEngine._run uses t0 + block.timestamp / speed with spin-wait |
| PLAY-02 | 02-02, 02-03 | Speed multiplier configurable (0.5x/1x/2x) | SATISFIED | toolbar speed spin + presets; speed passed to engine.start() |
| PLAY-03 | 02-02, 02-04 | Repeat count N | SATISFIED | PlaybackEngine.start(repeat=N); UI defers to toolbar (repeat=1 for Phase 2) |
| PLAY-04 | 02-02, 02-03, 02-04 | Stop playback via global hotkey from any window | SATISFIED | HotkeyManager F8 -> stop_play signal -> _stop_play() -> engine.stop() |
| PLAY-05 | 02-02, 02-04 | Playback on background thread; UI does not freeze | SATISFIED | daemon threading.Thread; progress via queue drain; coordinate readout unblocked |

All 12 Phase 2 requirements (REC-01 through REC-07, PLAY-01 through PLAY-05) are satisfied by implementation evidence. No orphaned requirements found.

---

## Anti-Patterns Found

None. Grep for TODO/FIXME/PLACEHOLDER/return null/return []/return {} found zero matches across all Phase 2 source files.

---

## Human Verification Required

### 1. Record-to-Play End-to-End Cycle

**Test:** Run `py -m macro_thunder`. Press F9 (or Record button). Move the mouse in a pattern and press a few keys. Watch toolbar. Press F10 (or Stop button). Press F6 (or Play button).
**Expected:** Red blinking dot appears on F9 and block count increments as events are captured. Blinking stops on F10. On F6 the mouse cursor physically moves through the recorded path and key presses replay.
**Why human:** Requires real OS hooks (pynput listeners), physical hardware input, and visual observation of cursor movement on screen.

### 2. Global F8 Stop During Playback in Another Window

**Test:** After recording a macro, start playback with F6. Switch focus to a different application (e.g. Notepad). Press F8.
**Expected:** Playback halts before completing; toolbar returns to idle state (Play button re-enabled, Stop Play disabled, progress bar hidden).
**Why human:** Requires multi-application focus change and real global hotkey registration — cannot be verified without running OS.

### 3. File Save / Open Round-Trip

**Test:** Record a short macro. File > Save Macro, save as `test.json` in Documents/MacroThunder/. Close the app. Restart with `py -m macro_thunder`. File > Open Macro, load `test.json`. Press Play.
**Expected:** File is created at correct path. After reload the same mouse and keyboard actions replay identically.
**Why human:** Requires app restart cycle and real filesystem read/write verification.

### 4. Settings Dialog Persists Hotkey Changes

**Test:** File > Settings. Change "Start Record" from `<f9>` to `<f7>`. Click OK. Press F7.
**Expected:** Recording starts on F7 (not F9). Check Documents/MacroThunder/settings.json — should contain `"hotkey_start_record": "<f7>"`.
**Why human:** Requires pynput GlobalHotKeys re-registration and file content inspection.

### 5. UI Responsiveness During Recording/Playback

**Test:** Start recording (F9). While the blinking indicator is active, observe the coordinate readout in the status bar as you move the mouse.
**Expected:** X/Y coordinates update smoothly (~60 Hz) with no lag or freezing. The toolbar remains clickable.
**Why human:** Requires real-time visual observation of Qt event loop responsiveness.

---

## Gaps Summary

No gaps. All 18 automated must-have truths pass. All 12 phase requirements are satisfied by code evidence. 42 unit tests pass (24 recorder + 18 engine). No Qt imports in recorder or engine. No anti-patterns found.

The only open items are 5 behavioral tests that require running the application with real hardware — these are expected human-verified items for any Phase 2 gate.

---

_Verified: 2026-02-28_
_Verifier: Claude (gsd-verifier)_
