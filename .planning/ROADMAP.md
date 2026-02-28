# Roadmap: Macro Thunder

## Overview

Four phases, each delivering a coherent and independently verifiable capability. Phase 1 establishes the foundation that every subsequent layer depends on — DPI awareness, data model, threading architecture, and the app shell. Phase 2 closes the core loop: record, save, load, play. Phase 3 makes the tool usable rather than just functional by adding the visual block editor and the movement grouping system that is the primary differentiator. Phase 4 adds the power features that enable real game automation workflows — flow control via Label/Goto and the Window Focus action that prevents coordinate drift when game windows move.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - App shell, data model, DPI awareness, and correct threading architecture (completed 2026-02-26)
- [ ] **Phase 2: Record and Play** - Full recording pipeline and playback engine — first end-to-end working macro
- [ ] **Phase 3: Visual Block Editor** - QAbstractTableModel block editor with movement grouping and group duration editing
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
**Plans**: TBD

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
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-02-26 |
| 2. Record and Play | 3/4 | In Progress|  |
| 3. Visual Block Editor | 0/? | Not started | - |
| 4. Flow Control and Window Management | 0/? | Not started | - |
