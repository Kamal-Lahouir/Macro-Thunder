# Requirements: Macro Thunder

**Defined:** 2026-02-25
**Core Value:** Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.

## v1 Requirements

### Foundation

- [x] **FOUND-01**: Application sets DPI awareness before any UI or input library initializes (prevents coordinate mismatch on scaled displays)
- [x] **FOUND-02**: Macro data model supports all action block types: MouseMove, MouseClick, MouseScroll, KeyPress, Delay, WindowFocus, Label, Goto
- [x] **FOUND-03**: Macro files saved and loaded as JSON with a `version` field from the first save
- [x] **FOUND-04**: Application launches with a dark-themed main window

### Recording

- [x] **REC-01**: User can start and stop recording via a button (and hotkey)
- [x] **REC-02**: Mouse movements are captured with exact screen coordinates and timestamps
- [x] **REC-03**: Mouse clicks (left, right, middle — down and up) are recorded
- [x] **REC-04**: Mouse scroll events are recorded (direction and amount)
- [x] **REC-05**: Keyboard key presses (down and up) are recorded
- [x] **REC-06**: User can configure a pixel threshold — mouse moves smaller than N pixels are discarded during recording
- [x] **REC-07**: Recording does not capture the macro application's own playback events (injected event filtering)

### Playback

- [x] **PLAY-01**: User can play a macro from start to finish with accurate timing (perf_counter-based, not sleep-based)
- [x] **PLAY-02**: User can set a playback speed multiplier (e.g. 0.5x, 1x, 2x) before running
- [x] **PLAY-03**: User can set repeat count (run macro N times)
- [x] **PLAY-04**: User can stop playback at any time via a global hotkey (works even when another app has focus)
- [x] **PLAY-05**: Playback runs on a background thread and does not freeze the UI

### Editor — Block List

- [x] **EDIT-01**: Recorded macro is displayed as a list of action blocks in the editor
- [x] **EDIT-02**: User can delete one or multiple selected blocks
- [x] **EDIT-03**: User can reorder blocks via drag-and-drop or up/down controls
- [x] **EDIT-04**: User can multi-select blocks (click, shift-click, ctrl-click)
- [x] **EDIT-05**: User can manually insert a new action block at any position (from a block type menu)

### Editor — Movement Grouping

- [x] **GROUP-01**: Consecutive MouseMove blocks between non-move actions are visually grouped in the editor
- [x] **GROUP-02**: User can select a movement group and edit its total duration — timestamps scale proportionally
- [x] **GROUP-03**: User can expand a group to edit individual move lines within it
- [x] **GROUP-04**: User can select individual lines within an expanded group

### Flow Control

- [ ] **FLOW-01**: User can insert a Label block (named jump target) anywhere in the macro
- [ ] **FLOW-02**: User can insert a Goto block that jumps execution to any label
- [ ] **FLOW-03**: Playback executor validates all Goto targets exist before execution begins (no mid-run crashes)
- [ ] **FLOW-04**: Infinite loop detection — executor detects goto loops with no progress and surfaces a warning

### Window Focus Action

- [ ] **WIN-01**: User can insert a Window Focus action block specifying target executable name and window title
- [ ] **WIN-02**: Window title matching supports three modes: Contains, Exact, Starts With
- [ ] **WIN-03**: User can use an interactive "Select Window..." picker — click on a running window to fill the fields
- [ ] **WIN-04**: On success: optionally set window position (X, Y) and size (W, H)
- [ ] **WIN-05**: On success: flow continues to "Next" or a named label
- [ ] **WIN-06**: On failure: wait N seconds, then jump to a named label (e.g. End)

### Macro Library

- [x] **LIB-01**: User can save a macro to a named file
- [x] **LIB-02**: User can open/load a saved macro
- [x] **LIB-03**: A macro library panel lists all saved macros in a designated folder

## v2 Requirements

### Post-Execution Actions

- **POST-01**: After N playbacks, user can choose: do nothing, close focused window, close Macro Thunder, idle (no action)
- **POST-02**: After N playbacks, user can trigger system shutdown
- **POST-03**: After N playbacks, user can trigger system restart

### Infinite Loop

- **LOOP-01**: User can set repeat to "infinite" (loop until stop hotkey)

### Macro Chaining

- **CHAIN-01**: User can insert a "Run Macro" action block that calls another saved macro

### Editor Enhancements

- **EDIT-V2-01**: Undo/redo support in the editor
- **EDIT-V2-02**: Search/find within macro block list
- **EDIT-V2-03**: Copy/paste blocks

### Relative Coordinates

- **COORD-01**: Option to record coordinates relative to a target window position (not absolute screen)

## Out of Scope

| Feature | Reason |
|---------|--------|
| AI-powered OCR / image recognition | Not needed for game automation use case; high complexity, fragile |
| Cross-platform (Mac/Linux) | Windows-only; Win32 APIs are core to window management |
| Cloud sync / web UI | Personal use only; local files sufficient |
| Distribution / licensing system | Personal use only |
| Full scripting language (Python/Lua in macros) | Visual block editor + goto/label covers real needs without building a runtime |
| Input suppression in DirectInput/RawInput games | Windows architecture limitation — not fixable at Python level |
| Multi-monitor relative coordinates | Deferred; absolute coords cover the primary use case |

## Traceability

Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Complete |
| FOUND-02 | Phase 1 | Complete |
| FOUND-03 | Phase 1 | Complete |
| FOUND-04 | Phase 1 | Complete |
| REC-01 | Phase 2 | Complete |
| REC-02 | Phase 2 | Complete |
| REC-03 | Phase 2 | Complete |
| REC-04 | Phase 2 | Complete |
| REC-05 | Phase 2 | Complete |
| REC-06 | Phase 2 | Complete |
| REC-07 | Phase 2 | Complete |
| PLAY-01 | Phase 2 | Complete |
| PLAY-02 | Phase 2 | Complete |
| PLAY-03 | Phase 2 | Complete |
| PLAY-04 | Phase 2 | Complete |
| PLAY-05 | Phase 2 | Complete |
| EDIT-01 | Phase 3 | Complete |
| EDIT-02 | Phase 3 | Complete |
| EDIT-03 | Phase 3 | Complete |
| EDIT-04 | Phase 3 | Complete |
| EDIT-05 | Phase 3 | Complete |
| GROUP-01 | Phase 3 | Complete |
| GROUP-02 | Phase 3 | Complete |
| GROUP-03 | Phase 3 | Complete |
| GROUP-04 | Phase 3 | Complete |
| LIB-01 | Phase 3 | Complete |
| LIB-02 | Phase 3 | Complete |
| LIB-03 | Phase 3 | Complete |
| FLOW-01 | Phase 4 | Pending |
| FLOW-02 | Phase 4 | Pending |
| FLOW-03 | Phase 4 | Pending |
| FLOW-04 | Phase 4 | Pending |
| WIN-01 | Phase 4 | Pending |
| WIN-02 | Phase 4 | Pending |
| WIN-03 | Phase 4 | Pending |
| WIN-04 | Phase 4 | Pending |
| WIN-05 | Phase 4 | Pending |
| WIN-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 after initial definition*
