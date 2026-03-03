# Roadmap: Macro Thunder

## Overview

Four phases, each delivering a coherent and independently verifiable capability. Phase 1 establishes the foundation that every subsequent layer depends on — DPI awareness, data model, threading architecture, and the app shell. Phase 2 closes the core loop: record, save, load, play. Phase 3 makes the tool usable rather than just functional by adding the visual block editor and the movement grouping system that is the primary differentiator. Phase 4 adds the power features that enable real game automation workflows — flow control via Label/Goto and the Window Focus action that prevents coordinate drift when game windows move.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - App shell, data model, DPI awareness, and correct threading architecture (completed 2026-02-26)
- [x] **Phase 2: Record and Play** - Full recording pipeline and playback engine — first end-to-end working macro (completed 2026-02-28)
- [x] **Phase 3: Visual Block Editor** - QAbstractTableModel block editor with movement grouping and group duration editing (completed 2026-03-01)
- [ ] **Phase 4: Flow Control and Window Management** - Label/Goto flow control and Window Focus action with interactive window picker

## Phase Details

### Phase 1: Foundation
**Goal**: A runnable, correctly-architected app shell exists that all subsequent features can build on without structural rework
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Success Criteria** (what must be TRUE):
  1. Application launches to a dark-themed main window with no visible errors
  2. Mouse coordinates reported by the app match the operating system's screen coordinates at 125%, 150%, and 200% display scaling
  3. MacroDocument can represent all eight action block types (MouseMove, MouseClick, MouseScroll, KeyPress, Delay, WindowFocus, Label, Goto) in its data model
  4. A macro saved to JSON round-trips to an identical MacroDocument on load, and every saved file contains a `version` field
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold: pyproject.toml, src-layout package skeleton, CLAUDE.md rules
- [ ] 01-02-PLAN.md — Data model and JSON serializer (TDD): all 8 ActionBlock types, MacroDocument, save/load
- [ ] 01-03-PLAN.md — App shell: DPI-aware entry point, dark-themed main window with 3-panel layout and live coordinate readout

### Phase 2: Record and Play
**Goal**: Users can record mouse and keyboard input, save the result, and play it back with accurate timing — the first end-to-end working macro
**Depends on**: Phase 1
**Requirements**: REC-01, REC-02, REC-03, REC-04, REC-05, REC-06, REC-07, PLAY-01, PLAY-02, PLAY-03, PLAY-04, PLAY-05
**Success Criteria** (what must be TRUE):
  1. User can press Record, perform mouse and keyboard actions, press Stop, and see a saved macro file containing those actions
  2. Playing back a recorded macro reproduces mouse movements to the correct screen coordinates with timing accuracy — no visible drift over a 10-second recording
  3. Setting playback speed to 0.5x slows the macro proportionally; setting it to 2x doubles the speed
  4. User can press the global stop hotkey while another application has focus and playback halts immediately
  5. Mouse moves smaller than the configured pixel threshold are not present in the recorded macro, and the UI does not freeze during recording or playback
**Plans**: TBD

### Phase 3: Visual Block Editor
**Goal**: Users can view, edit, and reorder recorded macros in a visual block editor — and edit mouse movement group durations without touching individual coordinate rows
**Depends on**: Phase 2
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, GROUP-01, GROUP-02, GROUP-03, GROUP-04, LIB-01, LIB-02, LIB-03
**Success Criteria** (what must be TRUE):
  1. A recorded macro displays as a list of action blocks in the editor, with consecutive mouse move events collapsed into a single labeled group row
  2. User can select a movement group row and change its total duration — the individual move timestamps inside the group scale proportionally
  3. User can expand a group to see and select individual move lines within it
  4. User can delete, reorder (drag-and-drop or arrow controls), and manually insert action blocks at any position
  5. User can see all saved macros in a library panel, load any macro into the editor, and save the current macro to a named file
**Plans**: 6 plans

Plans:
- [ ] 03-01-PLAN.md — TDD: DisplayRow types + timestamp/coordinate rescaling functions (view_model.py foundation)
- [ ] 03-02-PLAN.md — BlockTableModel: full QAbstractTableModel with group display, expand/collapse, drag-drop, mutations
- [ ] 03-03-PLAN.md — BlockDelegate + BlockTypeDialog: group row rendering and block type picker
- [ ] 03-04-PLAN.md — LibraryPanel: file list sorted by MRU, Load/Rename/Delete, unsaved-changes guard
- [ ] 03-05-PLAN.md — EditorPanel: QTableView wired to model + delegate, toolbar (Delete/Move/Add)
- [ ] 03-06-PLAN.md — MainWindow wiring: load → editor, record-stop → editor, dirty flag, library refresh + human verify checkpoint

### Phase 4: Flow Control and Window Management
**Goal**: Users can build macro workflows that loop, branch, and reliably focus the target game window before executing coordinate-dependent actions
**Depends on**: Phase 3
**Requirements**: FLOW-01, FLOW-02, FLOW-03, FLOW-04, WIN-01, WIN-02, WIN-03, WIN-04, WIN-05, WIN-06
**Success Criteria** (what must be TRUE):
  1. User can insert Label and Goto blocks; during playback, execution jumps to the named label unconditionally
  2. Playback refuses to start if any Goto block targets a label that does not exist in the macro, and displays a clear error message
  3. Playback detects a Goto loop that makes no progress and surfaces a warning before running indefinitely
  4. User can insert a Window Focus block, use the interactive picker to click on a running window and auto-fill its fields, and choose Contains/Exact/Starts With title matching
  5. On focus success, the window is optionally repositioned/resized and execution continues to Next or a named label; on failure, execution waits N seconds then jumps to a named label
**Plans**: 6 plans

Plans:
- [ ] 04-01-PLAN.md — TDD: validate_gotos + window_utils (matching modes, ctypes helpers)
- [ ] 04-02-PLAN.md — Data model: extend WindowFocusBlock with timeout/label/reposition fields
- [ ] 04-03-PLAN.md — Engine refactor: while-loop playback with Label/Goto/WindowFocus dispatch
- [ ] 04-04-PLAN.md — Label/Goto visual styling + WindowPickerService
- [ ] 04-05-PLAN.md — Block detail panels: LabelPanel, GotoPanel, WindowFocusPanel + EditorPanel wiring
- [x] 04-06-PLAN.md — MainWindow wiring: validation on play, loop detection, picker ownership + human verify

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-02-26 |
| 2. Record and Play | 4/4 | Complete | 2026-02-28 |
| 3. Visual Block Editor | 6/6 | Complete | 2026-03-01 |
| 4. Flow Control and Window Management | 6/6 | Complete | 2026-03-02 |
| 5. Record Logic Adaptation and Fixes | 2/4 | In Progress|  |
| 6. UI Enhancements for User Friendly | 0/TBD | Not started | - |
| 7. Loop Blocks | 4/4 | Complete   | 2026-03-03 |

### Phase 5: Record Logic Adaptation and Fixes

**Goal**: Recording is more flexible and playback is more powerful — users can choose how clicks are recorded and can run macros a set number of times or infinitely
**Depends on**: Phase 4
**Plans**: 4 plans

Scope:
- **Click recording modes** (toggle before recording):
  - Mode 1 (combined): Left/right click = single `MouseClick` action (no separate press/release blocks)
  - Mode 2 (current): Records `MouseButtonDown` + `MouseButtonUp` as separate blocks
- **Repeat count**: Playback can run macro N times (integer) or infinitely (loop until Stop hotkey)
- **Record Here hotkey**: Global hotkey to trigger "Record Here" without UI focus
- Settings/AppSettings updated to persist click mode and repeat preferences

**Success Criteria** (what must be TRUE):
  1. User can toggle click mode in Settings before recording; Mode 1 produces one block per click, Mode 2 produces two (current behavior preserved)
  2. User can set repeat count to N — macro plays exactly N times then stops
  3. User can enable infinite loop — macro repeats until Stop hotkey is pressed
  4. Record Here hotkey triggers insert-recording at the selected block position even when another app has focus

Plans:
- [ ] 05-01-PLAN.md — AppSettings extension + SettingsDialog restructure (QTabWidget, hotkey conflict detection, top-level Settings menu)
- [ ] 05-02-PLAN.md — Click recording mode in RecorderService + direction='click' dispatch in engine + status bar indicator
- [ ] 05-03-PLAN.md — Repeat count spinbox + infinite loop checkbox in toolbar + PlaybackEngine while-True loop with on_done callback
- [ ] 05-04-PLAN.md — Record Here global hotkey + system tray icon (gray/red) + sound cue + EditorPanel.get_selected_flat_index

### Phase 6: UI Enhancements for User Friendly

**Goal**: The interface is polished, stable, and configurable — hotkeys are set by pressing a key (not typing), the toolbar does not shift layout during recording, and the user can customize the app's visual theme
**Depends on**: Phase 5
**Plans**: TBD

Scope:
- **Hotkey capture UI**: Button next to each hotkey field — click it, press any key, that key is set as the hotkey (replaces manual `<f9>` text entry)
- **Repeat count UI**: Spinbox in the toolbar to set how many times to play (1 to N, or ∞ toggle)
- **Click mode UI**: Visible toggle/indicator in the toolbar or settings to switch Mode 1 / Mode 2
- **Toolbar stability**: The recording blink indicator and block count label should not shift other controls when they appear/disappear — use reserved space or fixed-position overlay
- **Theme/color customization**: Settings panel with theme options (dark, light, accent color, or preset themes)

**Success Criteria** (what must be TRUE):
  1. User clicks a hotkey capture button, presses a key, and the field is filled — no manual typing required
  2. Toolbar layout does not shift when recording starts/stops (blink dot and block count appear in-place without pushing other controls)
  3. User can set repeat count directly from the toolbar before pressing Play
  4. User can switch theme/color scheme from Settings and the change applies immediately without restart

Plans:
- [ ] TBD (run /gsd:plan-phase 6 to break down)

### Phase 7: Loop Blocks — LoopStart/LoopEnd block types that repeat a segment of actions N times, with playback engine support and visual loop region rendering in the editor

**Goal**: Users can wrap any selection of blocks in a loop region that repeats N times during playback, with clear visual bracket rendering in the editor and pre-flight validation that prevents malformed loop structures from running
**Requirements**: LOOP-01, LOOP-02, LOOP-03, LOOP-04, LOOP-05, LOOP-06, LOOP-07, LOOP-08, LOOP-09, LOOP-10
**Depends on**: Phase 6
**Plans**: 4 plans

**Success Criteria** (what must be TRUE):
  1. User can insert LoopStart/LoopEnd blocks via Add Block dialog or right-click "Wrap in Loop"
  2. Loop regions render with a teal left border and indented child rows in the block editor
  3. Selecting a LoopStart row shows a detail panel with an editable repeat count spinbox
  4. Playback executes the loop body exactly repeat times then continues after the LoopEnd
  5. Playback is blocked with a clear error if loop sentinels are unmatched or nested

Plans:
- [ ] 07-01-PLAN.md — TDD: LoopStartBlock/LoopEndBlock data model + engine loop_stack dispatch + validate_loops()
- [ ] 07-02-PLAN.md — View model: LoopHeaderRow/LoopFooterRow/LoopChildRow + _rebuild_display_rows + set_playback_flat_index
- [ ] 07-03-PLAN.md — Visual styling: block_delegate left-border stripe + LoopStartPanel + BlockTypeDialog entries
- [ ] 07-04-PLAN.md — UI wiring: wrap_in_loop mutation + EditorPanel context menu + MainWindow validate_loops + human verify
