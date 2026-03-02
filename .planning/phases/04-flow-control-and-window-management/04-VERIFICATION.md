---
phase: 04-flow-control-and-window-management
verified: 2026-03-02T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
human_verification:
  - test: "Play a macro with a missing Goto target"
    expected: "QMessageBox appears listing the missing label name; playback does not start"
    why_human: "UI dialog behavior cannot be verified programmatically"
  - test: "Play a macro containing an infinite Goto loop (no non-flow-control blocks between Label and Goto)"
    expected: "Engine fires on_loop_detected after >1000 iterations; playback stops; offending Goto row is selected in editor; QMessageBox 'Infinite Loop Detected' appears"
    why_human: "Real engine thread + Qt queue drain + dialog interaction required"
  - test: "Click 'Select Window...' in a WindowFocus detail panel"
    expected: "Macro Thunder minimizes, cursor becomes crosshair; clicking a running window restores the app and auto-fills executable and title fields with match mode set to Contains"
    why_human: "pynput global click capture + window restore + field auto-fill are live-session interactions"
  - test: "Play a macro with Label/Goto blocks and a WindowFocus block"
    expected: "Execution jumps correctly at Goto; WindowFocus polls at 500ms intervals; on find it activates the target window and follows on_success_label; on timeout it follows on_failure_label"
    why_human: "Requires live Windows desktop with real windows; timing behavior needs observation"
  - test: "Label and Goto rows in the block table"
    expected: "Muted indigo/purple background visible; LabelBlock row shows a right-arrow (command-link) icon, GotoBlock row shows a right-arrow icon in column 0"
    why_human: "Visual rendering verification requires running the application"
  - test: "Save a macro with WindowFocusBlock that has new fields (timeout, on_failure_label, etc.), reload it"
    expected: "All new fields round-trip correctly through JSON serialization; old macros without these fields still load without error"
    why_human: "Requires file I/O and human inspection of loaded document state"
---

# Phase 4: Flow Control and Window Management Verification Report

**Phase Goal:** Label/Goto flow control and Window Focus action with interactive window picker
**Verified:** 2026-03-02
**Status:** human_needed — all automated checks passed; runtime behavior requires human testing
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | validate_gotos() returns missing label names (deduplicated, order-preserved) | VERIFIED | `engine/validation.py` L7-20: correct implementation; `tests/test_flow_control.py` L14-63: 7 tests covering all cases |
| 2 | Window title matching uses Contains/Exact/Starts With logic (case-insensitive) | VERIFIED | `engine/window_utils.py` L41-60: `_title_matches` correct; `tests/test_window_utils.py`: 11 tests covering all three modes plus edge cases |
| 3 | Loop detection counter > 1000 consecutive Goto fires triggers on_loop_detected | VERIFIED | `engine/__init__.py` L113-145: `goto_fire_count` dict, threshold check at L137, `_on_loop_detected` called at L139; contract tested in `tests/test_flow_control.py` L102-148 |
| 4 | Engine uses while-loop with index pointer; LabelBlock advances without action | VERIFIED | `engine/__init__.py` L116: `while i < len(blocks)`; L123-127: LabelBlock increments i and continues |
| 5 | WindowFocusBlock polls every 500ms up to timeout; on find activates + routes; on timeout routes to failure label | VERIFIED | `engine/__init__.py` L149-175: deadline-based poll with 0.5s wait, `_activate_window` call, `_set_window_rect` on reposition, success/failure label routing |
| 6 | Engine signals loop detection back to UI via on_loop_detected callback through queue | VERIFIED | `main_window.py` L120-125: `_loop_detect_queue` and `on_loop_detected=self._on_loop_detected_callback`; L315-317: puts to queue; L184-198: drained in `_update_status` timer on main thread |
| 7 | WindowFocusBlock has all Phase 4 fields with defaults (backward compatible) | VERIFIED | `models/blocks.py` L51-63: `timeout=5.0`, `on_failure_label=""`, `on_success_label=""`, `reposition=False`, `x=0`, `y=0`, `w=0`, `h=0`; all have defaults so old macros load correctly |
| 8 | WindowPickerService minimizes app, captures click via pynput, emits picked/cancelled | VERIFIED | `ui/window_picker.py` L39-81: `start()` calls `showMinimized()`, `mouse.Listener` captures click, `_on_pick` only calls `pyqtSignal.emit()` (CLAUDE.md thread rule respected) |
| 9 | Label/Goto rows have muted indigo background and icons in column 0 | VERIFIED | `models/view_model.py` L237-255: BackgroundRole returns `QBrush(QColor(55,45,80))` for Label/Goto; DecorationRole returns `SP_CommandLink`/`SP_ArrowRight` icons |
| 10 | Detail panels (LabelPanel, GotoPanel, WindowFocusPanel) appear on row selection; field edits update block | VERIFIED | `ui/block_panels.py`: all three panels implemented with field-to-block wiring; `ui/editor_panel.py` L201-223: `_on_selection_changed` instantiates correct panel per block type |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/macro_thunder/engine/validation.py` | validate_gotos pure function | VERIFIED | 21 lines; imports LabelBlock/GotoBlock; correct deduplication logic |
| `src/macro_thunder/engine/window_utils.py` | window matching, activation, rect helpers | VERIFIED | 168 lines; all 7 helpers present; AttachThreadInput pattern used in `_activate_window` |
| `src/macro_thunder/engine/__init__.py` | Refactored PlaybackEngine with flow control | VERIFIED | while-loop at L116; label_index dict; goto_fire_count; WindowFocusBlock poll; on_loop_detected callback |
| `src/macro_thunder/models/blocks.py` | Extended WindowFocusBlock dataclass | VERIFIED | All Phase 4 fields with defaults; LabelBlock and GotoBlock present |
| `src/macro_thunder/ui/window_picker.py` | WindowPickerService QObject | VERIFIED | picked/cancelled signals; start()/cancel() methods; pynput thread safety enforced |
| `src/macro_thunder/ui/block_panels.py` | LabelPanel, GotoPanel, WindowFocusPanel | VERIFIED | 171 lines; all three panels; WindowFocusPanel has full field set including reposition group and Select Window button |
| `src/macro_thunder/ui/editor_panel.py` | Detail panel container below table | VERIFIED | `_detail_container` at L73; `_on_selection_changed` at L201 dispatches correct panel |
| `src/macro_thunder/ui/main_window.py` | validate_gotos + WindowPickerService + on_loop_detected wiring | VERIFIED | validate_gotos called at L293; WindowPickerService at L58; on_loop_detected at L124; closeEvent at L401 |
| `tests/test_flow_control.py` | validate_gotos + loop detection tests | VERIFIED | 149 lines; 13 tests; covers all plan-specified scenarios |
| `tests/test_window_utils.py` | Window matching mode tests | VERIFIED | 92 lines; 11 tests; all three match modes + edge cases |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `engine/validation.py` | `models/blocks` | `isinstance(b, LabelBlock)`, `isinstance(b, GotoBlock)` | WIRED | L4: imports both; L12/L16: isinstance checks present |
| `engine/window_utils.py` | `ctypes.windll.user32` | ctypes Win32 calls | WIRED | L29: `user32 = ctypes.windll.user32`; used in all ctypes helpers |
| `engine/__init__.py` | `engine/validation.py` | label_index dict from LabelBlock.name | WIRED | L25-29: imports `_find_window`, `_activate_window`, `_set_window_rect`; label_index built at L95-99 |
| `engine/__init__.py` | `engine/window_utils.py` | `from macro_thunder.engine.window_utils import` | WIRED | L25-29: direct imports used at L153, L161, L163 |
| `engine/__init__.py` | queue.Queue bridge in MainWindow | on_loop_detected callback | WIRED | L51/L56: constructor stores callback; L139: called in _run thread; main_window L315-317: puts to queue |
| `models/view_model.py` | `models/blocks` | `isinstance(block, (LabelBlock, GotoBlock))` in BackgroundRole/DecorationRole | WIRED | L241/L251/L254: isinstance checks with correct block types |
| `ui/window_picker.py` | `engine/window_utils.py` | `_hwnd_from_point` + `_get_window_info` | WIRED | L15: imports both; L75-76: called in `_on_pick` |
| `ui/window_picker.py` | `pynput.mouse.Listener` | global mouse click capture | WIRED | L60: `self._listener = mouse.Listener(on_click=on_click)` |
| `ui/editor_panel.py` | `ui/block_panels.py` | selection change -> panel subclass | WIRED | L18: imports all three panels; L214-219: isinstance dispatch |
| `ui/block_panels.py` | `models/blocks` | panel reads/writes block fields | WIRED | L141-158: direct field assignment (`block.name`, `block.target`, `block.executable`, etc.) |
| `ui/block_panels.py` | `ui/window_picker.py` | `WindowPickerService.start()` on pick click | WIRED | L161-162: `_on_pick_clicked` calls `self._picker.start()` |
| `ui/main_window.py` | `engine/validation.py` | `validate_gotos` called in `_start_play` | WIRED | L26: import; L293: `missing = validate_gotos(...)` before engine.start |
| `ui/main_window.py` | `engine/__init__.py` | `on_loop_detected` callback to PlaybackEngine | WIRED | L124: `on_loop_detected=self._on_loop_detected_callback` |
| `ui/main_window.py` | `ui/window_picker.py` | `WindowPickerService(self)` owned by MainWindow | WIRED | L58: instantiation; L135-136: signals connected; L401: `cancel()` in closeEvent |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| FLOW-01 | 04-03 | User can insert a Label block | SATISFIED | LabelBlock in models/blocks.py; BlockTypeDialog expected to include it; LabelPanel for editing |
| FLOW-02 | 04-03 | User can insert a Goto block | SATISFIED | GotoBlock in models/blocks.py; GotoPanel for editing |
| FLOW-03 | 04-01, 04-06 | Pre-flight validates all Goto targets before execution | SATISFIED | `validate_gotos` called in `_start_play` at main_window.py L293; QMessageBox shown on failure; engine not started |
| FLOW-04 | 04-03 | Infinite loop detection with warning | SATISFIED | goto_fire_count dict + threshold at engine/__init__.py L113-145; on_loop_detected fires; main_window drains queue and shows QMessageBox with offending row selected |
| WIN-01 | 04-02, 04-05 | User can insert WindowFocus action block | SATISFIED | WindowFocusBlock with executable/title fields; WindowFocusPanel with all fields |
| WIN-02 | 04-01, 04-05 | Three title matching modes: Contains, Exact, Starts With | SATISFIED | `_title_matches` in window_utils.py; QComboBox with three modes in WindowFocusPanel |
| WIN-03 | 04-04, 04-05 | Interactive window picker | SATISFIED | WindowPickerService + WindowFocusPanel "Select Window..." button wired to picker |
| WIN-04 | 04-05 | On success: optionally reposition window | SATISFIED | `reposition` checkbox; x/y/w/h fields; `_set_window_rect` called in engine when `block.reposition and block.w > 0 and block.h > 0` |
| WIN-05 | 04-03, 04-05 | On success: continue to Next or named label | SATISFIED | engine/__init__.py L164-167: `on_success_label` routing; empty = advance index |
| WIN-06 | 04-03, 04-05 | On failure: wait N seconds then jump to named label | SATISFIED | engine/__init__.py L150-172: deadline poll loop; `on_failure_label` routing on timeout; `timeout` field in WindowFocusPanel |

**All 10 requirement IDs accounted for. No orphaned requirements.**

### Anti-Patterns Found

No blocking anti-patterns detected. Spot checks of key files found no TODO/FIXME/placeholder comments, no empty return stubs, and no console.log-only handlers.

One noted design point (not a defect): `main_window._on_picker_picked` (L388-392) restores the window but does not consume `(exe, title)`. The actual consumption is handled by `WindowFocusPanel._on_picker_result` via a direct `self._picker.picked.connect` at `block_panels.py` L139. This pattern is intentional — the panel connects when instantiated and disconnects when destroyed. The MainWindow slot is purely for window restoration.

### Human Verification Required

The following items require a running application on a live Windows session to verify:

#### 1. Pre-flight Goto Validation Dialog

**Test:** Load a macro with a GotoBlock targeting a label that does not exist. Click Play.
**Expected:** QMessageBox titled "Missing Labels" appears listing the missing name with a bullet. Playback does not start. Dismissing the dialog returns to IDLE state.
**Why human:** UI dialog display and button state are runtime behaviors.

#### 2. Infinite Loop Detection and Row Selection

**Test:** Create a macro with only a LabelBlock "loop" followed by a GotoBlock targeting "loop". Click Play.
**Expected:** Engine runs, detects the loop after >1000 Goto fires, stops playback, selects the GotoBlock row in the editor table, and shows QMessageBox "Infinite Loop Detected".
**Why human:** Requires live engine thread, queue drain timer, and dialog observation.

#### 3. Window Picker Interaction

**Test:** Insert a WindowFocusBlock, select it, click "Select Window..." in the detail panel.
**Expected:** Application minimizes to taskbar; cursor shows as crosshair (best-effort). Clicking on a running window (e.g., Notepad) restores Macro Thunder, auto-fills the Executable field with the process basename and the Window Title field with the window title, and sets Match Mode to Contains.
**Why human:** pynput global mouse capture and ctypes cursor change require live Windows desktop session.

#### 4. WindowFocus Engine Execution

**Test:** Create a macro: LabelBlock "retry", WindowFocusBlock targeting a known window with timeout=3s, on_failure_label="retry". Run the macro with the target window closed, then open the window mid-execution.
**Expected:** Engine polls every 500ms, finds the window within the timeout, activates it, and continues execution. If the window does not appear within 3s, execution jumps back to "retry".
**Why human:** Timing behavior and live window interactions require physical observation.

#### 5. Label/Goto Visual Styling

**Test:** Insert a LabelBlock and a GotoBlock into a macro. Observe the block table.
**Expected:** Both rows show a muted indigo/purple background distinct from normal rows. The LabelBlock row shows a command-link arrow icon and GotoBlock shows a right-arrow icon in the first column.
**Why human:** Visual rendering requires the application to be running.

#### 6. WindowFocusBlock JSON Round-Trip

**Test:** Create a WindowFocusBlock with timeout=10.0, on_failure_label="end", reposition=True, x=100, y=100, w=800, h=600. Save the macro. Reload it.
**Expected:** All new fields restore correctly. Load an old macro saved before Phase 4 (missing these fields). Verify it still loads without error (defaults apply).
**Why human:** Requires file I/O and inspection of loaded document.

---

_Verified: 2026-03-02_
_Verifier: Claude (gsd-verifier)_
