# Retrospective: Macro Thunder

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-04
**Phases:** 9 (32 plans) | **Timeline:** 8 days (2026-02-25 → 2026-03-04)

### What Was Built

- DPI-aware PyQt6 app shell with dark theme and 3-panel layout
- Full record/play pipeline: pynput → queue → typed ActionBlocks → perf_counter playback
- Visual block editor: QAbstractTableModel with collapse/expand groups, drag-drop, multi-select
- Mouse movement grouping with proportional time scaling
- Flow control: Label/Goto with missing-label validation and infinite-loop detection
- Window Focus action: ctypes FindWindow, title-matching modes, interactive picker, reposition/resize
- Click mode (combined vs separate), repeat count, infinite loop, Record Here hotkey, tray icon
- Loop blocks (LoopStart/LoopEnd) with teal visual region, repeat count editing, pre-play validation
- Block edit dialog: double-click any block, paired down/up MouseClick sync, press-to-capture key field
- QA pass: amber cursor resume, stop-key residue fix, smoke test of all features

### What Worked

- **Flat data model** held up through all 9 phases — never needed nested structures
- **queue.Queue + QTimer drain** pattern was rock-solid; zero thread-safety issues after Phase 2
- **perf_counter timing** delivered accurate playback without drift across all test scenarios
- **Phase-by-phase layering** — each phase had clear success criteria that validated the previous layer
- **QAbstractTableModel** was complex to implement but gave full control over the group-row rendering
- **Win32HotkeyService parallel to pynput** solved game-window hotkey blocking cleanly

### What Was Inefficient

- Phase 6 was defined upfront but never planned or executed — scope was partially absorbed into Phase 5; should have been removed from roadmap earlier
- ROADMAP.md progress table drifted out of sync with actual state; was not maintained as phases completed
- 08-02 was committed without a SUMMARY.md — Phase 9 QA covered it but the docs gap needed manual resolution at milestone time
- Python 3.14 → 3.12 migration was discovered at the start (pynput crash) rather than during stack selection

### Patterns Established

- `_start_recording_common()` unified pattern for all record-start paths
- `_load_document()` central helper for all load paths (file, library, record-stop)
- Block detail panel container with `maxHeight` guard prevents field clipping at high DPI
- `field(default=..., init=False)` for block `type` field enables clean `block_from_dict` dispatch
- Phase verify checkpoint plan (always last plan in phase) — catches integration gaps before moving on

### Key Lessons

1. **Define Python version constraint before writing any code** — pynput on Python 3.14 is a showstopper; test the full stack on day 0
2. **Phase 6 "UI Polish" phases need concrete scope or they stay empty** — vague improvement phases don't execute; break them into specific requirements
3. **Write SUMMARY.md immediately after each plan commit** — the 08-02 gap created milestone cleanup work
4. **Win32 hotkey registration in showEvent is correct** — registering in __init__ silently fails before HWND exists
5. **QAbstractTableModel resets (beginResetModel/endResetModel) are simpler than fine-grained updates** for a list that rebuilds on every mutation

### Cost Observations

- Sessions: ~15 across 8 days
- Notable: Most plans executed in 2–7 minutes; Phase 4-06 (MainWindow wiring) took 30 min due to multiple interconnected systems

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Days | LOC |
|-----------|--------|-------|------|-----|
| v1.0 MVP  | 9      | 32    | 8    | ~4,804 |

| Pattern | v1.0 |
|---------|------|
| Flat data model held | ✓ |
| Thread safety issues | 0 |
| Timing drift | None observed |
| Empty/skipped phases | 1 (Phase 6) |
| QA pass required hotfixes | No (clean smoke test) |
