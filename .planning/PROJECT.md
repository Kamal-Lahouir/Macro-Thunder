# Macro Thunder

## What This Is

A Windows desktop macro recorder and editor built in Python, focused on precision mouse automation for game automation use cases. Users record mouse movements and clicks, then edit and replay macros with fine-grained control over timing, grouping, and flow logic.

## Core Value

Exact mouse movement replay with a non-painful editor — record once, tune the timing, loop it.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Recording**
- [ ] Record mouse movements with exact coordinates and timestamps
- [ ] Configurable pixel threshold to filter sub-N-pixel movements during recording
- [ ] Record mouse clicks (left, right, middle)
- [ ] Record mouse scroll events
- [ ] Record keyboard key presses

**Playback**
- [ ] Replay macros with exact timing fidelity
- [ ] Configurable playback speed multiplier (e.g. 0.5x, 2x)
- [ ] Repeat N times or infinite loop (with stop hotkey)

**Editor — Action Blocks**
- [ ] Visual block-based editor (each action is a row/block)
- [ ] Action types: mouse move, mouse click, scroll, key press, delay, window focus, label, goto
- [ ] Add actions manually (insert blocks at any position)
- [ ] Delete, reorder, copy/paste action blocks

**Editor — Mouse Movement Grouping**
- [ ] Mouse movement lines auto-group (consecutive move events between non-move actions)
- [ ] Select a group and edit total duration (timestamps scale proportionally)
- [ ] Select individual lines within a group for fine-grained edits
- [ ] Multi-select across lines/groups

**Editor — Window Focus Action**
- [ ] Target window by executable name + window title
- [ ] Title matching modes: Contains, Exact, Starts With
- [ ] Interactive "Select Window..." picker (click on a running window to fill fields)
- [ ] On success: optionally set window position (X, Y) and size (W, H), then go to label/Next
- [ ] On failure: wait N seconds, then go to label (e.g. End)

**Editor — Flow Control**
- [ ] Label blocks (named jump targets)
- [ ] Goto blocks (jump to any label unconditionally)
- [ ] Conditional goto (if pixel color / if window exists — deferred, but architecture supports it)

**Editor — Macro Chaining**
- [ ] "Run macro" action block that calls another saved macro

**UI**
- [ ] Dark theme desktop app
- [ ] Macro list / library panel
- [ ] Save and load macros (file-based)

### Out of Scope

- AI-powered OCR or image recognition — not needed for this use case
- Cross-platform support — Windows only
- Multi-monitor relative coordinates — window-relative coords deferred
- Distribution / licensing — personal use only
- Cloud sync or web UI — local only

## Context

- Target use: game automation (precise, repeatable mouse paths)
- Python stack: likely pynput or pyWin32 for input capture, PyQt6 or CustomTkinter for UI
- Windows-only allows use of Win32 APIs (SetForegroundWindow, FindWindow, etc.)
- Pixel threshold on recording is key UX — raw mouse data produces hundreds of lines per second; filtering makes the editor usable
- Movement grouping is the core editing insight: users care about "how long did this path take" not each individual coordinate

## Constraints

- **Platform**: Windows only — Win32 APIs for window management
- **Language**: Python — user's chosen stack
- **Scope**: Personal use — no auth, licensing, or multi-user concerns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Visual block editor over text scripting | Non-painful editing UX, no code exposure | — Pending |
| Auto-grouping of mouse move sequences | Raw move data is uneditable without grouping | — Pending |
| Proportional time scaling on group edit | Preserves movement shape while adjusting speed | — Pending |
| General goto/label flow control | Window focus failure handling extends naturally to full branching | — Pending |

---
*Last updated: 2026-02-25 after initialization*
