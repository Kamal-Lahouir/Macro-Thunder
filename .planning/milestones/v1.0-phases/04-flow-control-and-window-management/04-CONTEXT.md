# Phase 4: Flow Control and Window Management - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Add Label/Goto flow control blocks and a Window Focus action block with interactive window picker. Users can build loops, conditional jumps, and ensure coordinate-dependent actions always target the right window before executing. Macro Library and any other new capabilities are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Label/Goto UX
- Goto block has a text field — user types the target label name (no dropdown)
- Labels and Gotos can be inserted anywhere in the block list, no placement restrictions (forward and backward jumps both supported)
- Label and Goto blocks have a distinct visual style: different background color (muted purple/indigo) and clear icons (flag for Label, arrow for Goto) to make flow structure scannable
- Missing label error: shown as a dialog before playback starts, listing the missing label names; playback does not start until fixed

### Loop Detection
- On infinite loop detection: warn and stop playback (no "continue anyway" option)
- Detection strategy: execution count threshold — if the same Goto fires more than 1000 times without any non-flow-control block executing in between, it's a stuck loop
- Error message names the specific label: "Infinite loop detected at '[Label Name]' — execution stopped. Check your Goto blocks."
- After stopping, the offending Goto block is selected/highlighted in the block list so the user can find it immediately

### Window Focus Block — Failure and Success Handling
- Failure config (timeout duration + fallback label) is in the block's editor panel — two fields: "Timeout (seconds)" and "On failure: go to [label name]"
- Success path is configurable in the panel: defaults to "Next", user can override with a label name to jump elsewhere on success
- Reposition/resize fields (X, Y, W, H) are hidden behind a "Reposition window" checkbox — collapsed by default, revealed when checked
- During the timeout wait, poll for the window every ~500ms; if the window appears early, continue immediately rather than waiting the full duration

### Window Picker Interaction
- Picker triggered by a "Select Window..." button in the WindowFocus block panel
- When active: Macro Thunder minimizes and cursor changes to crosshair; user clicks their target window; app restores and fills in the fields
- Auto-fills: executable name + window title from the clicked window's process info; matching mode defaults to "Contains"
- "Select Window..." button stays available after filling — clicking again re-picks and overwrites current fields

### Claude's Discretion
- Exact color values for Label/Goto block styling (must fit existing dark theme)
- Icon choices for Label (flag) and Goto (arrow) — exact icon source
- Polling interval implementation details
- Windows API calls for window enumeration and process name extraction

</decisions>

<specifics>
## Specific Ideas

- The missing-label dialog and loop-detection dialog should follow the same error dialog pattern used elsewhere in the app
- Window picker minimize-and-crosshair pattern is similar in spirit to the existing record flow — reuse any existing minimize/restore helpers if they exist

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-flow-control-and-window-management*
*Context gathered: 2026-03-02*
