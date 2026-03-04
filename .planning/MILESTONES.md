# Milestones

## v1.0 MVP (Shipped: 2026-03-04)

**Phases completed:** 9 phases, 32 plans
**Files changed:** 143 | **LOC:** ~4,804 Python | **Timeline:** 8 days (2026-02-25 → 2026-03-04)
**Requirements:** 36/36 v1 requirements complete

**Key accomplishments:**
1. Full record/play pipeline — pynput captures mouse + keyboard into typed ActionBlocks; perf_counter-based playback with configurable speed and repeat count
2. Visual block editor — QAbstractTableModel with group collapsing, drag-drop reorder, multi-select, and manual block insertion
3. Mouse movement grouping — consecutive moves auto-grouped; group duration editable with proportional timestamp scaling
4. Flow control (Label/Goto) + Window Focus action with interactive window picker, title-matching modes, and pre-flight validation
5. Loop blocks (LoopStart/LoopEnd) with teal visual region rendering, repeat-count editing, and pre-play loop validation
6. Block edit dialog — double-click any block to edit in-place; paired MouseClick down/up sync; press-to-capture key field
7. QA pass — amber-cursor resume, stop-key residue fix, and full smoke-test verification of all features

---

