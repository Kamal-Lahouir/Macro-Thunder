# Macro Thunder

## What This Is

A Windows desktop macro recorder and editor built in Python with PyQt6, focused on precision mouse automation for game automation. Users record mouse movements, clicks, keyboard, and scroll events, then edit macros in a visual block editor with movement grouping, flow control (Label/Goto), loop blocks, and Window Focus actions — then replay with configurable speed and repeat count.

## Core Value

Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.

## Requirements

### Validated

- ✓ App sets DPI awareness correctly, coordinates match OS at all scaling — v1.0
- ✓ All 8 action block types in data model (MouseMove, MouseClick, MouseScroll, KeyPress, Delay, WindowFocus, Label, Goto) — v1.0
- ✓ Macro files saved/loaded as JSON with version field — v1.0
- ✓ Dark-themed main window — v1.0
- ✓ Record start/stop via button and hotkey — v1.0
- ✓ Mouse movements captured with exact coords and timestamps — v1.0
- ✓ Mouse clicks (left/right/middle, down/up) recorded — v1.0
- ✓ Mouse scroll events recorded — v1.0
- ✓ Keyboard key presses recorded — v1.0
- ✓ Configurable pixel threshold filters sub-N-pixel moves during recording — v1.0
- ✓ Recording does not capture injected playback events — v1.0
- ✓ Playback with perf_counter-based timing (not sleep) — v1.0
- ✓ Configurable playback speed multiplier — v1.0
- ✓ Repeat count (run N times) — v1.0
- ✓ Global stop hotkey works when another app has focus — v1.0
- ✓ Playback on background thread, UI stays responsive — v1.0
- ✓ Block list editor showing all action types — v1.0
- ✓ Delete, reorder blocks — v1.0
- ✓ Drag-and-drop block reorder — v1.0
- ✓ Multi-select (click, shift-click, ctrl-click) — v1.0
- ✓ Manual block insertion at any position — v1.0
- ✓ Consecutive MouseMove blocks auto-grouped in editor — v1.0
- ✓ Group duration editable (timestamps scale proportionally) — v1.0
- ✓ Expand group to edit individual move lines — v1.0
- ✓ Select individual lines within expanded group — v1.0
- ✓ Save macro to named file — v1.0
- ✓ Open/load saved macro — v1.0
- ✓ Macro library panel listing saved macros — v1.0
- ✓ Label blocks (named jump targets) — v1.0
- ✓ Goto blocks (unconditional jump to label) — v1.0
- ✓ Pre-flight Goto validation (missing labels block playback) — v1.0
- ✓ Infinite loop detection (Goto loops with no progress) — v1.0
- ✓ Window Focus block with executable + title matching — v1.0
- ✓ Title matching modes: Contains, Exact, Starts With — v1.0
- ✓ Interactive window picker (click on running window) — v1.0
- ✓ Window Focus on success: reposition/resize + flow to label/Next — v1.0
- ✓ Window Focus on failure: wait N seconds + jump to label — v1.0

### Active

- [ ] Click recording mode toggle (Mode 1: single click block / Mode 2: down+up) — Phase 5 shipped; UI hotkey-capture button shipped as part of settings refactor
- [ ] Block edit dialog UI (Phase 8 complete — shipped v1.0)
- [ ] Loop blocks LoopStart/LoopEnd (Phase 7 complete — shipped v1.0)
- [ ] **Hotkey capture UI polish** — settings hotkey fields use key-capture button; repeat/click mode toolbar indicators added in Phase 5/6
- [ ] **Post-execution actions** (do nothing / close window / shutdown after N plays)
- [ ] **Macro chaining** — "Run macro" block calling another saved macro
- [ ] **Undo/redo** in block editor
- [ ] **Copy/paste blocks**
- [ ] **Relative coordinates** (window-relative, not absolute screen)

### Out of Scope

- AI-powered OCR or image recognition — not needed for game automation use case
- Cross-platform support — Windows only; Win32 APIs are core
- Cloud sync or web UI — personal use only
- Distribution / licensing — personal use only
- Full scripting language — visual blocks + goto/label cover real needs
- Input suppression in DirectInput/RawInput games — Windows architecture limitation at Python level
- Multi-monitor relative coordinates — deferred; absolute coords cover primary use case

## Context

- **Shipped v1.0** (2026-03-04): ~4,804 LOC Python, 143 files
- **Tech stack**: Python 3.12, PyQt6, pynput, pywin32, PyQtDarkTheme-fork
- **Python 3.14 note**: pynput crashes on 3.14 (ACCESS VIOLATION); project uses Python 3.12
- **PyQtDarkTheme-fork**: requires Python <3.14; QPalette fallback available for future compatibility
- **Architecture**: queue.Queue + QTimer drain for all pynput→Qt bridges; never touch Qt from pynput callbacks
- **Data model**: `MacroDocument.blocks` is always a flat list; grouping is view-layer only
- **Timing**: playback uses absolute `perf_counter()` targets, not sleep

## Constraints

- **Platform**: Windows only — Win32 APIs for window management
- **Language**: Python 3.12 — pynput incompatible with 3.14
- **Scope**: Personal use — no auth, licensing, or multi-user concerns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Visual block editor over text scripting | Non-painful editing UX, no code exposure | ✓ Good — core differentiator |
| Auto-grouping of mouse move sequences | Raw move data is uneditable without grouping | ✓ Good — essential for usability |
| Proportional time scaling on group edit | Preserves movement shape while adjusting speed | ✓ Good — validates core value |
| General goto/label flow control | Window focus failure handling extends naturally to full branching | ✓ Good — enabled loop/flow use cases |
| PyQt6 + QAbstractTableModel | Full control over block rendering and group collapse | ✓ Good — complex but correct |
| perf_counter + coarse-sleep + spin-wait | Timing precision without pure busy-wait | ✓ Good — no drift observed |
| Flat blocks list, view-layer grouping | Simpler data model, avoids nested structure complexity | ✓ Good — held up through Phase 8 |
| Python 3.12 (not 3.14) | pynput 1.8.1 crashes with ACCESS VIOLATION on 3.14 | ✓ Good — stable |
| PyQtDarkTheme-fork optional dep | Python 3.14 incompatibility; QPalette fallback | ✓ Good — forward-compatible |
| Win32HotkeyService parallel to pynput GlobalHotKeys | Handles games that block pynput global hooks | ✓ Good — both run in parallel |
| LoopStart/LoopEnd as flat sentinel blocks | Consistent with flat data model; view layer handles region rendering | ✓ Good — clean engine dispatch |
| BlockEditDialog Cancel = no-op on block fields | Writes only in accept() — cancel leaves block unchanged | ✓ Good — safe edit pattern |

---
*Last updated: 2026-03-04 after v1.0 milestone*
