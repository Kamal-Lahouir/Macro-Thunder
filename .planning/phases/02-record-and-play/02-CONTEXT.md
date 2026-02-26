# Phase 2: Record and Play - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Full recording pipeline (pynput-based input capture for mouse + keyboard) and playback engine (perf_counter timing) — the first end-to-end working macro. UI additions are limited to toolbar controls, status/progress feedback, and a configurable hotkeys settings entry. The visual block editor is Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Recording controls
- Record and Stop buttons live in the **toolbar at the top of the main window**
- While recording: **red blinking indicator + live block count** displayed in toolbar/status area
- On Stop: recording goes to a **temp buffer in memory** — user manually saves via File > Save (no auto-save, no immediate filename prompt)
- Recording captures **both mouse and keyboard** (full macro: moves, clicks, scrolls, key press/release)

### Playback controls
- Play and Stop buttons are **distinct buttons in the same toolbar** as Record (not a toggle, not a separate panel)
- Speed control: **numeric input (0.1x–5.0x)** with preset shortcut buttons (0.5x, 1x, 2x)
- During playback: **progress bar + block index / total** (e.g. "Playing: 42 / 180 blocks")
- User **can play directly from the unsaved temp buffer** — no save required before playback

### Global stop hotkey (F8)
- Default stop-playback key: **F8**, always registered on app startup
- F8 behavior: halts after the currently in-flight event completes, next event is cancelled
- F8 **does not** cancel recording — recording has its own Stop button in the toolbar
- F8 is active even when the macro app itself has focus
- When nothing is playing and F8 is pressed: **silently ignored**
- After F8 stops playback: UI **immediately resets to idle** (buttons re-enable, progress clears)

### Configurable hotkeys
- All 4 hotkeys are **user-configurable** with defaults:
  - Start Record: (default TBD by planner)
  - Stop Record: (default TBD by planner)
  - Start Playback: (default TBD by planner)
  - Stop Playback: F8
- Hotkey configuration lives in a **settings area** (settings panel or dialog — planner decides location)
- All hotkeys registered on app startup

### Claude's Discretion
- Default key assignments for Start Record, Stop Record, Start Playback (F8 is fixed for stop-playback)
- Exact settings UI layout (panel vs dialog vs inline toolbar)
- Mouse threshold default value and where the threshold setting lives in the UI
- Visual design of the blinking record indicator (animation style, placement)
- Exact progress bar widget placement within the toolbar/status area

</decisions>

<specifics>
## Specific Ideas

- The toolbar should make it visually obvious whether the app is in "recording" vs "playing" vs "idle" state — red blinking indicator is the key signal for recording
- Speed presets (0.5x, 1x, 2x) should be quick-click buttons alongside the numeric input, not a dropdown

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-record-and-play*
*Context gathered: 2026-02-26*
