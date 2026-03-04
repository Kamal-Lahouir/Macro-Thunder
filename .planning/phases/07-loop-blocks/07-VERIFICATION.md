---
phase: 07-loop-blocks
verified: 2026-03-03T02:00:00Z
status: gaps_found
score: 9/10 must-haves verified
gaps:
  - truth: "LOOP-01 through LOOP-10 requirement IDs are tracked in REQUIREMENTS.md"
    status: failed
    reason: "REQUIREMENTS.md defines only LOOP-01 as 'User can set repeat to infinite' (v2 requirement). Plans 07-01 through 07-04 use LOOP-01 through LOOP-10 as an internal Phase 7 numbering scheme that was never added to REQUIREMENTS.md. These IDs do not exist in REQUIREMENTS.md and the traceability table has no Phase 7 entries."
    artifacts:
      - path: ".planning/REQUIREMENTS.md"
        issue: "Only LOOP-01 exists (line 80), defined as infinite repeat. LOOP-02 through LOOP-10 are absent. Phase 7 traceability rows missing from table."
    missing:
      - "Add LOOP-01 through LOOP-10 to REQUIREMENTS.md under a new 'Loop Blocks' section in v2 requirements, or retract the IDs from the plan frontmatter and map to the correct Phase 7 goal"
      - "Add Phase 7 entries to the Traceability table"
human_verification:
  - test: "Full loop workflow end-to-end"
    expected: "Insert LoopStart/LoopEnd via + Add Block, wrap selection via right-click, select LoopStart row to see repeat spinbox, play with amber cursor stepping through loop body N times"
    why_human: "UI behavior, playback visual, context menu interaction cannot be verified programmatically"
  - test: "validate_loops blocks invalid macro at play time"
    expected: "Inserting orphaned LoopStart with no LoopEnd and pressing Play shows QMessageBox warning about loop structure error"
    why_human: "Modal dialog behavior requires running app"
---

# Phase 7: Loop Blocks Verification Report

**Phase Goal:** Implement Loop Blocks — LoopStart/LoopEnd block types that repeat a section of the macro N times, with full UI support (insert, wrap selection, visual styling, detail panel) and engine execution.
**Verified:** 2026-03-03
**Status:** gaps_found (1 gap: REQUIREMENTS.md traceability missing; all functional code verified)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | LoopStartBlock and LoopEndBlock exist and round-trip through JSON | VERIFIED | `blocks.py` lines 79-113: dataclasses with `Literal["LoopStart"]`/`Literal["LoopEnd"]` fields, registered in `_BLOCK_CLASSES`, `block_from_dict` uses pop-type pattern |
| 2 | validate_loops() detects unmatched sentinels and nested loops | VERIFIED | `engine/validation.py` lines 23-48: depth-counter scan, returns error strings for orphaned LoopEnd, unclosed LoopStart, nested LoopStart |
| 3 | PlaybackEngine executes loop body exactly repeat times | VERIFIED | `engine/__init__.py` lines 164-186: loop_stack dispatch with `(i, repeat-1)` push and decrement-or-pop logic; 21 tests pass |
| 4 | loop_stack resets between outer macro repeat iterations | VERIFIED | `engine/__init__.py` line 130: `loop_stack: list[tuple[int, int]] = []` is inside `while True` (outer repeat loop), not module-level |
| 5 | LoopHeaderRow/LoopFooterRow/LoopChildRow emitted by _rebuild_display_rows | VERIFIED | `view_model.py` lines 208-253: LoopStart emits LoopHeaderRow, LoopEnd emits LoopFooterRow, in-loop blocks emit LoopChildRow with correct flat indices |
| 6 | Amber playback cursor works on loop rows | VERIFIED | `view_model.py` lines 335-337: `elif isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow)): if row_obj.flat_index == pi: return QBrush(QColor(210, 160, 0))` |
| 7 | Loop region visual: teal background + 4px left border stripe | VERIFIED | `view_model.py` line 339: `QBrush(QColor(0, 60, 55))` for teal tint; `block_delegate.py` lines 46-50: 4px stripe via `fillRect` with `QColor(0, 160, 140)` |
| 8 | LoopStartPanel shows QSpinBox for repeat count, mutates block.repeat | VERIFIED | `block_panels.py` line 53+: `LoopStartPanel` with `QSpinBox(min=1, max=9999)`, `valueChanged.connect(_on_value_changed)` which sets `self._block.repeat = value` |
| 9 | BlockTypeDialog offers Loop Start and Loop End | VERIFIED | `block_type_dialog.py` lines 39-40: `("Loop Start", LoopStartBlock(repeat=2))` and `("Loop End", LoopEndBlock())` in `_BLOCK_TYPES` |
| 10 | Selecting LoopStart row shows LoopStartPanel in detail area | VERIFIED | `editor_panel.py` lines 273-275: `if isinstance(row_obj, LoopHeaderRow): block = ...; panel = LoopStartPanel(block, self._emit_modified)` |
| 11 | Right-click "Wrap in Loop" inserts LoopStart/LoopEnd around selection | VERIFIED | `editor_panel.py` lines 238-257: `_on_context_menu` with `wrap_action`, calls `_wrap_selection_in_loop()` → `self._model.wrap_in_loop(flat_indices)` |
| 12 | wrap_in_loop inserts LoopEnd at hi+1 first then LoopStart at lo | VERIFIED | `view_model.py` lines 782-793: `insert(hi + 1, LoopEndBlock())` then `insert(lo, LoopStartBlock(repeat=2))` |
| 13 | validate_loops called before engine.start() in main_window | VERIFIED | `main_window.py` lines 29 (import), 381-389: `validate_loops(self._macro_buffer.blocks)` with `QMessageBox.warning` gate |
| 14 | Pair-delete removes only LoopStart+LoopEnd; children survive as BlockRows | VERIFIED | `view_model.py` lines 617-648: LoopHeaderRow branch scans forward to matching LoopEnd, adds only boundary to `flat_to_delete` (not children) |
| 15 | LOOP-01 through LOOP-10 are tracked in REQUIREMENTS.md | FAILED | Only `LOOP-01` (infinite repeat, v2) exists in REQUIREMENTS.md. Phase 7 plans use LOOP-01 through LOOP-10 as internal IDs not defined in REQUIREMENTS.md. No Phase 7 entries in traceability table. |

**Score:** 14/15 truths verified (1 failed — traceability only, no functional code gap)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/macro_thunder/models/blocks.py` | LoopStartBlock, LoopEndBlock dataclasses + registry | VERIFIED | Lines 79-113: both classes, both in `_BLOCK_CLASSES` and `ActionBlock` Union |
| `src/macro_thunder/engine/validation.py` | validate_loops() | VERIFIED | Lines 23-48: full implementation, returns `list[str]` |
| `src/macro_thunder/engine/__init__.py` | loop_stack dispatch in _run | VERIFIED | Lines 130, 164-186: initialized inside outer loop, LoopStart/LoopEnd handled |
| `src/macro_thunder/models/view_model.py` | LoopHeaderRow/LoopFooterRow/LoopChildRow + _rebuild + wrap_in_loop | VERIFIED | Lines 46-64, 208-253, 782-793 |
| `src/macro_thunder/ui/block_delegate.py` | 4px teal left stripe for loop rows | VERIFIED | Lines 46-50 |
| `src/macro_thunder/ui/block_panels.py` | LoopStartPanel with QSpinBox | VERIFIED | Line 53+: full implementation |
| `src/macro_thunder/ui/block_type_dialog.py` | Loop Start and Loop End entries | VERIFIED | Lines 39-40 |
| `src/macro_thunder/ui/editor_panel.py` | Context menu + selection routing + _wrap_selection_in_loop | VERIFIED | Lines 238-257, 273-275 |
| `src/macro_thunder/ui/main_window.py` | validate_loops pre-play gate | VERIFIED | Lines 29, 381-389 |
| `tests/test_loop_blocks.py` | 21 TDD tests | VERIFIED | All 21 pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `engine/_run` | `LoopStartBlock/LoopEndBlock` | isinstance checks lines 165, 173 | WIRED | Before WindowFocusBlock check; loop_stack push/pop/jump |
| `validate_loops` | blocks list | depth counter scan | WIRED | Returns list of error strings |
| `_rebuild_display_rows` | `LoopStartBlock/LoopEndBlock` | isinstance checks before MouseMoveBlock | WIRED | LoopHeaderRow, LoopFooterRow, LoopChildRow emitted correctly |
| `set_playback_flat_index` | `LoopHeaderRow/LoopFooterRow/LoopChildRow` | isinstance checks lines 276-281 | WIRED | dirty = flat_index in (old, flat_index) |
| `block_delegate.paint` | loop row types | isinstance check line 46 | WIRED | 4px stripe drawn after amber check |
| `editor_panel._on_selection_changed` | `LoopStartPanel` | isinstance(row_obj, LoopHeaderRow) line 273 | WIRED | Panel shown for LoopHeaderRow selections |
| `editor_panel._on_context_menu` | `wrap_in_loop` | QMenu action trigger line 243 | WIRED | `_wrap_selection_in_loop()` → `self._model.wrap_in_loop()` |
| `main_window._start_play` | `validate_loops` | import + call line 381 | WIRED | Called after validate_gotos, before engine.start() |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| LOOP-01 (plan) | 07-01 | LoopStartBlock data model + JSON round-trip | SATISFIED | `blocks.py` lines 79-113 |
| LOOP-02 (plan) | 07-01 | LoopEndBlock data model + JSON round-trip | SATISFIED | `blocks.py` lines 84-86 |
| LOOP-03 (plan) | 07-01 | Engine loop_stack dispatch + validate_loops | SATISFIED | `engine/__init__.py` lines 164-186, `validation.py` lines 23-48 |
| LOOP-04 (plan) | 07-02 | LoopHeaderRow/LoopFooterRow/LoopChildRow view model types | SATISFIED | `view_model.py` lines 46-64 |
| LOOP-05 (plan) | 07-02 | _rebuild_display_rows loop region classification | SATISFIED | `view_model.py` lines 208-253 |
| LOOP-06 (plan) | 07-03 | Block delegate 4px teal left stripe | SATISFIED | `block_delegate.py` lines 46-50 |
| LOOP-07 (plan) | 07-03 | LoopStartPanel + BlockTypeDialog entries | SATISFIED | `block_panels.py` line 53+, `block_type_dialog.py` lines 39-40 |
| LOOP-08 (plan) | 07-04 | EditorPanel LoopStartPanel routing | SATISFIED | `editor_panel.py` lines 273-275 |
| LOOP-09 (plan) | 07-04 | Right-click "Wrap in Loop" context menu | SATISFIED | `editor_panel.py` lines 238-257 |
| LOOP-10 (plan) | 07-04 | validate_loops pre-play gate in MainWindow | SATISFIED | `main_window.py` lines 381-389 |
| **LOOP-01 (REQUIREMENTS.md)** | None | "User can set repeat to infinite" (v2 requirement) | ORPHANED | This REQUIREMENTS.md item is distinct from the Phase 7 internal LOOP-01. It remains unimplemented. |

**REQUIREMENTS.md traceability gap:** Plans 07-01 through 07-04 declare `requirements: [LOOP-01..LOOP-10]` in their frontmatter, but these IDs do not exist in `.planning/REQUIREMENTS.md`. The only `LOOP-01` in REQUIREMENTS.md refers to infinite repeat (a v2 feature, not Phase 7's loop blocks). Phase 7 effectively implements a new set of requirements that were never formally defined in REQUIREMENTS.md.

---

## Anti-Patterns Found

| File | Lines | Pattern | Severity | Impact |
|------|-------|---------|----------|--------|
| `src/macro_thunder/engine/__init__.py` | 217-239 | Duplicate LoopStart/LoopEnd isinstance blocks | Warning | Dead code — the first occurrence at lines 164-186 has `continue` statements so lines 217-239 are unreachable. Harmless but confusing; should be removed. |

---

## Human Verification Required

### 1. Full Loop Workflow

**Test:** Launch `python -m macro_thunder`. Add two Delay blocks. Select both, right-click, choose "Wrap selection in Loop". Click the LoopStart row. Set repeat count to 3. Click Play.
**Expected:** Teal border appears around loop region. LoopStartPanel spinbox shows in detail area. Amber cursor steps through Delay blocks 3 times before playback stops.
**Why human:** Visual styling, UI interaction, playback cursor behavior cannot be verified programmatically.

### 2. validate_loops Blocks Playback

**Test:** Insert a LoopStart block via "+ Add Block" but no matching LoopEnd. Click Play.
**Expected:** QMessageBox warning dialog appears with "Loop Structure Error" title and message about unclosed loop. Playback does not start.
**Why human:** Modal dialog behavior, QMessageBox display, requires running app.

---

## Gaps Summary

**One functional gap (traceability only):**

REQUIREMENTS.md does not contain LOOP-01 through LOOP-10 as declared in the plan frontmatter of all four Phase 7 plans. The REQUIREMENTS.md file defines `LOOP-01` as something different (infinite repeat, v2). The Phase 7 implementation is functionally complete and correct — all 14 functional truths are verified — but the requirements register is inconsistent.

**Duplicate engine code (warning):**

`engine/__init__.py` contains the LoopStart/LoopEnd dispatch blocks duplicated at lines 217-239. The first copy (lines 164-186) executes; the second is dead code after the WindowFocusBlock handler. No functional impact, but should be cleaned up.

---

## Test Results

- `tests/test_loop_blocks.py`: 21/21 passed
- Full suite: 120 passed, 15 errors (pre-existing: pytest-qt not installed, unrelated to Phase 7)

---

_Verified: 2026-03-03_
_Verifier: Claude (gsd-verifier)_
