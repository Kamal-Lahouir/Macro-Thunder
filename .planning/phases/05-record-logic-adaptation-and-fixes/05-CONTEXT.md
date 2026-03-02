# Phase 5: Record Logic Adaptation and Fixes - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Make recording more flexible (click modes) and playback more powerful (repeat count, infinite loop, Record Here global hotkey). Settings dialog and AppSettings class already exist — this phase extends them with new fields. No new data model nesting; MacroDocument.blocks remains a flat list.

</domain>

<decisions>
## Implementation Decisions

### Click Recording Modes
- Toggle lives in **Settings dialog only** (not the toolbar) — set once, applies to all future recordings
- Mode 1 (combined): applies to **both left and right clicks** — any click produces a single `MouseClick` block with a `button` field (left/right/middle)
- Mode 2 (current): `MouseButtonDown` + `MouseButtonUp` as separate blocks (existing behavior preserved)
- Changing the mode has **no effect on the currently open macro** — existing blocks are untouched; mode is a recording preference only
- The **active click mode is shown in the status bar** during recording (e.g. "Click: Combined")

### Repeat & Loop UX
- Repeat count spin box + infinite loop (∞) toggle live in the **toolbar**, always visible
- Repeat prefs are **session-only** — not saved in the macro .json file; toolbar resets to defaults on app launch
- Default repeat count on launch: **1** (play once)
- Infinite loop stops **immediately mid-macro** when Stop hotkey is pressed (no finish-current-pass logic)

### Record Here Hotkey
- Key combo is **user-configurable in Settings** (no hardcoded default)
- When fired from another app: **Macro Thunder stays in the background** — recording begins silently, window does not come to front
- If no block is selected when hotkey fires: new recording is **appended at the end** of the macro
- Feedback when activated from another app: **system tray icon changes** (turns red) + optional sound cue — no window flash or OS notification

### Settings Persistence
- Click mode and Record Here hotkey stored in **AppSettings** (app-wide, persisted to disk) — survives restarts, shared across all macros
- **Settings menu item** in the menu bar alongside File (not buried in a submenu)
- Settings dialog has distinct sections:
  - **Hotkeys** — Record Here hotkey combo + existing hotkeys (Play, Stop, Record)
  - **Options** — repeat defaults, speed, and future playback options
- If user picks a Record Here hotkey that conflicts with existing hotkeys: **show an error in Settings and reject the combo**, telling the user which hotkey conflicts

### Claude's Discretion
- Exact spin box range for repeat count (min/max values)
- Sound cue implementation details (whether a beep is on by default or opt-in)
- Exact tray icon design for recording state

</decisions>

<specifics>
## Specific Ideas

- Settings menu item should appear **next to File** in the menu bar (same level, not inside File menu)
- Settings dialog sections: **Hotkeys** tab/section + **Options** tab/section (Options covers repeats, speed, future settings — additive to hotkeys, not replacing them)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-record-logic-adaptation-and-fixes*
*Context gathered: 2026-03-02*
