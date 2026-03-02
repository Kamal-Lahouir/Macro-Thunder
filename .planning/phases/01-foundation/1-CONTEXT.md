# Phase 1: Foundation - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

A runnable, correctly-architected app shell that all subsequent phases build on without structural rework. Delivers: DPI awareness set before any UI initializes, a data model for all 8 action block types, JSON round-trip serialization with a version field, and a dark-themed main window with the full layout skeleton.

</domain>

<decisions>
## Implementation Decisions

### Python framework & tech stack
- **Python 3.12**
- **PyQt6** (not PyQt5, not PySide6)
- **pynput** for mouse/keyboard input capture (Phase 2 will use it — lock it in now)
- **Proper package layout from day 1**: `src/macro_thunder/` with submodules (e.g. `models/`, `ui/`, `engine/`)

### App shell structure
- Full layout skeleton in Phase 1 — all three areas visible and positioned, even if empty
- Layout: toolbar row at top, library panel on the **left**, block editor fills the center/right
- Phase 2 fills in the toolbar widgets and recording controls into existing containers
- Phase 3 fills in the block editor and library list into existing containers — no restructuring
- **Status bar** at the bottom shows a **live mouse coordinate readout** (X, Y updating as mouse moves) — this visually satisfies the DPI-awareness success criterion

### Dark theme
- Claude's discretion on implementation approach (QPalette, qdarkstyle, or stylesheet)
- Should be near-black / VS Code-style dark, not medium gray

### JSON file format
- **Claude's discretion** on exact block encoding (type-discriminated flat objects is the natural fit)
- **Timestamps are relative to recording start** — first action = 0.0s, each subsequent = elapsed seconds
- **Pretty-printed with 2-space indent** — human-readable, git-diffable
- **Default save location: `Documents/MacroThunder/`** on the user's system

### Claude's Discretion
- Exact JSON serialization structure for each block type (type field + flat fields is reasonable)
- Dark theme implementation mechanism (QPalette vs stylesheet vs library)
- Git branching strategy (feature branches per phase recommended, e.g. `phase/1-foundation`)
- Exact package/module breakdown within `src/macro_thunder/`
- DPI awareness API call (Win32 `SetProcessDpiAwareness` or Qt's built-in)

</decisions>

<specifics>
## Specific Ideas

- The status bar coordinate display is the primary visual proof that DPI awareness is working correctly at 125%, 150%, 200% scaling — it should update live as the mouse moves across the screen
- Phase 1 is a skeleton: toolbar area, left library panel, central editor panel are all present but empty/placeholder. Future phases fill containers, not restructure the window

</specifics>

<deferred>
## Deferred Ideas

- Git branching strategy (e.g. `phase/1-foundation`) — developer workflow choice, not a planner concern
- Dark theme fine-tuning / color customization — Phase 1 just needs "dark enough to work"

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-26*
