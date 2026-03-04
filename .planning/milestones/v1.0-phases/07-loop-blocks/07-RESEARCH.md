# Phase 7: Loop Blocks - Research

**Researched:** 2026-03-03
**Domain:** PyQt6 block editor extension + playback engine loop semantics
**Confidence:** HIGH (all findings from direct codebase inspection — no external libraries needed)

---

## Summary

Phase 7 adds LoopStart/LoopEnd sentinel block types to the existing flat-list data model. The architecture is a direct extension of the Label/Goto pattern already established in Phase 4 — two new dataclasses, engine dispatch logic inside `_run`, view-layer rendering in `BlockTableModel`/`BlockDelegate`, and a new detail panel. No third-party libraries are required beyond what is already installed.

The critical design constraint from CLAUDE.md is already satisfied by the proposed approach: `MacroDocument.blocks` remains a flat list. LoopStart/LoopEnd are sentinel values in that flat list, exactly like Label/Goto. The grouping visual (indented child rows, colored left border) is view-layer only, analogous to how GroupHeaderRow/GroupChildRow render MouseMove groups without restructuring data.

**Primary recommendation:** Mirror the Label/Goto pattern throughout every layer — data model, serializer dispatch, engine `_run` loop, `BlockTableModel._rebuild_display_rows`, `BlockDelegate.paint`, `block_panels.py`, `block_type_dialog.py`. Each layer has a narrow, well-defined extension point.

---

## Standard Stack

### Core (already installed — no new packages needed)
| Component | Version | Purpose |
|-----------|---------|---------|
| PyQt6 | existing | QAbstractTableModel display rows, delegate painting |
| Python dataclasses | stdlib | LoopStartBlock / LoopEndBlock definitions |
| threading.Event | stdlib | Playback stop — already used |
| time.perf_counter | stdlib | Timing — already used |

### No new packages required
All functionality is achieved by extending existing code. Phase 7 introduces zero new dependencies.

---

## Architecture Patterns

### How Label/Goto was implemented (the pattern to mirror)

Every layer has a known extension point. Phase 7 follows the same path:

| Layer | Label/Goto approach | Loop extension |
|-------|--------------------|----|
| `models/blocks.py` | Two dataclasses + `_BLOCK_CLASSES` dict | Add `LoopStartBlock`, `LoopEndBlock` to both |
| `ActionBlock` Union | `Union[..., LabelBlock, GotoBlock]` | Add new types to Union |
| `engine/__init__.py` `_run` | `isinstance` checks before timing dispatch | Add LoopStart/LoopEnd handling |
| `view_model.py` `_rebuild_display_rows` | `BlockRow` wraps Label/Goto | Add `LoopRegionRow` display type |
| `view_model.py` `_block_value` | `if isinstance(block, LabelBlock)` branch | Add LoopStart/LoopEnd branches |
| `view_model.py` `data()` BackgroundRole | Indigo tint for Label/Goto | Add teal/green tint for loop rows |
| `block_delegate.py` `paint` | Standard Qt paint for Label/Goto | Add left border stripe for loop rows |
| `block_panels.py` | `LabelPanel`, `GotoPanel` classes | Add `LoopStartPanel` (repeat spinbox) |
| `block_type_dialog.py` `_BLOCK_TYPES` | List of (label, default block) | Append LoopStart and LoopEnd entries |
| `editor_panel.py` `_on_selection_changed` | `isinstance(block, LabelBlock)` panel routing | Add `isinstance(block, LoopStartBlock)` routing |
| `persistence/serializer.py` | `block_from_dict` uses `_BLOCK_CLASSES` — auto-handled | No change needed if `_BLOCK_CLASSES` is updated |

### Recommended Project Structure (additions only)

No new files required. All changes are extensions within existing files. This matches the pattern established in Phase 4 (Label/Goto also required no new files, only extensions to existing ones).

### Pattern 1: LoopStart/LoopEnd as Flat Sentinels

**What:** Two blocks in the flat list. LoopStart carries `repeat` count. LoopEnd has no fields. Engine tracks a call stack (list of `(loop_start_index, remaining_iterations)`) to handle the jump-back.

**When to use:** Always — this is the only approved design per CLAUDE.md.

```python
# Source: direct extension of blocks.py pattern
@dataclass
class LoopStartBlock:
    repeat: int  # number of times to repeat the enclosed region
    type: Literal["LoopStart"] = field(default="LoopStart", init=False)

@dataclass
class LoopEndBlock:
    type: Literal["LoopEnd"] = field(default="LoopEnd", init=False)
```

### Pattern 2: Engine Loop Stack

**What:** The playback engine `_run` method maintains a `loop_stack: list[tuple[int, int]]` — a list of `(loop_start_flat_index, iterations_remaining)`. When the engine hits a `LoopStartBlock` it pushes onto the stack. When it hits `LoopEndBlock` it peeks the stack: if iterations remain, decrements and jumps back to `loop_start_flat_index + 1`; if zero, pops and continues.

**Critical:** The stack must be reset at each outer iteration (repeat loop). It must also be cleared on stop.

```python
# Inside _run while-loop, before normal dispatch:

if isinstance(block, LoopStartBlock):
    # Push loop entry: remember where this loop starts, how many to go
    loop_stack.append((i, block.repeat - 1))  # -1: first pass already in progress
    i += 1
    continue

if isinstance(block, LoopEndBlock):
    if loop_stack:
        start_idx, remaining = loop_stack[-1]
        if remaining > 0:
            loop_stack[-1] = (start_idx, remaining - 1)
            i = start_idx + 1  # jump back to first block after LoopStart
        else:
            loop_stack.pop()
            i += 1
    else:
        # Orphaned LoopEnd — skip (validated before playback in ideal world)
        i += 1
    continue
```

**No nested loops needed** (user confirmed), but the stack approach handles nesting for free and is cleaner than a single-level counter. Since user said no nesting, validation can forbid it, but the engine can silently handle it correctly via the stack.

**Loop blocks count as non-flow progress** for the goto loop-detection counter (unlike LabelBlock). They are real execution steps, just with a jump side-effect. Treat them like WindowFocusBlock for the `progress_since_last_goto` flag.

### Pattern 3: View-Layer Loop Region Display

**What:** `_rebuild_display_rows` scans the flat list. When it encounters a `LoopStartBlock`, it adds a `LoopHeaderRow` display row; when it encounters a `LoopEndBlock`, it adds a `LoopFooterRow`. All blocks between them are wrapped in `LoopChildRow` display rows (indented).

**New DisplayRow types needed:**
```python
@dataclass
class LoopHeaderRow:
    """LoopStart block display row."""
    flat_index: int  # index of the LoopStartBlock

@dataclass
class LoopFooterRow:
    """LoopEnd block display row."""
    flat_index: int  # index of the LoopEndBlock

@dataclass
class LoopChildRow:
    """A block inside a loop region."""
    flat_index: int
    loop_header_flat_index: int  # flat index of owning LoopStartBlock
```

**`_rebuild_display_rows` change:** After placing a `LoopHeaderRow`, set a flag/counter tracking current loop depth. All subsequent blocks (until matching LoopEndBlock) are wrapped as `LoopChildRow`. On `LoopEndBlock`, emit `LoopFooterRow` and clear depth counter. Since nesting is out of scope, depth > 1 need not be handled specially — but guarding against unmatched sentinels prevents crashes.

**Amber playback cursor:** `set_playback_flat_index` already iterates all display rows. Add `LoopHeaderRow`, `LoopFooterRow`, and `LoopChildRow` cases analogous to `GroupHeaderRow` / `GroupChildRow` / `BlockRow`.

### Pattern 4: Visual Styling for Loop Rows

**What:** The `BlockDelegate.paint` method draws a colored left border stripe on LoopHeaderRow, LoopFooterRow, and LoopChildRow cells. This is a self-contained visual change with no data model impact.

```python
# In BlockDelegate.paint, after amber check:
if isinstance(row_data, (LoopHeaderRow, LoopFooterRow, LoopChildRow)):
    # Draw a 4px teal left border stripe
    painter.fillRect(option.rect.adjusted(0, 0, -option.rect.width() + 4, 0), QColor(0, 160, 140))
    # Then fall through to super().paint for normal content
```

Background tint (light teal, distinct from the indigo used for Label/Goto):
```python
# In BlockTableModel.data() BackgroundRole:
if isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow)):
    return QBrush(QColor(0, 60, 55))  # dark teal — fits dark theme
```

### Pattern 5: Right-Click "Wrap Selection in Loop"

**What:** The `EditorPanel._table` has a context menu (right-click). "Wrap selection in loop" inserts a `LoopStartBlock(repeat=1)` before the lowest selected flat index and a `LoopEndBlock()` after the highest. Implemented as `QTableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)` + `customContextMenuRequested.connect(...)`.

**Implementation approach:** Add `_on_context_menu(pos)` to `EditorPanel`. Build a `QMenu`, add "Wrap selection in Loop" action. On trigger: collect selected flat indices, call a new `BlockTableModel.wrap_in_loop(flat_indices)` method that inserts the sentinels at correct positions.

```python
def wrap_in_loop(self, flat_indices: list[int]) -> None:
    """Insert LoopStart before min(flat_indices) and LoopEnd after max(flat_indices)."""
    if not flat_indices:
        return
    lo = min(flat_indices)
    hi = max(flat_indices)
    # Insert end first so lo index stays valid
    self.beginResetModel()
    self._doc.blocks.insert(hi + 1, LoopEndBlock())
    self._doc.blocks.insert(lo, LoopStartBlock(repeat=2))
    self._rebuild_display_rows()
    self.endResetModel()
    self.document_modified.emit()
```

### Pattern 6: LoopStart Inline Repeat Count Edit

**What:** The LoopHeaderRow in COL_VALUE shows `repeat=N`. `flags()` returns `ItemIsEditable` for LoopHeaderRow + COL_VALUE. `setData()` parses the new integer and updates `block.repeat`. Alternatively, a detail panel (`LoopStartPanel`) with a QSpinBox handles editing — consistent with LabelPanel/GotoPanel.

**Recommendation:** Use the detail panel pattern (LoopStartPanel with QSpinBox) rather than inline editing. Inline editing of an integer directly in the table cell is error-prone (no range validation). The detail panel approach is already established and tested.

### Anti-Patterns to Avoid

- **Nested data structures for loops:** CLAUDE.md explicitly forbids. LoopStart/LoopEnd as flat sentinels is the only correct approach.
- **Storing loop state in the block objects:** `remaining_iterations` must live in the engine's `loop_stack`, not in `LoopStartBlock`. Blocks are immutable during playback.
- **Rebuilding `loop_stack` outside `_run`:** The stack is ephemeral playback state. Build it per-iteration of the repeat loop, not once per `start()` call.
- **Calling `beginResetModel` in `_rebuild_display_rows`:** The existing pattern is: callers wrap with `beginResetModel/endResetModel`; `_rebuild_display_rows` is a pure internal rebuild. Do not change this contract.
- **Adding `LoopStart/LoopEnd` to group-detection logic:** `_rebuild_display_rows` currently groups consecutive `MouseMoveBlock` runs. A `LoopStartBlock` between move blocks should break the group (it is not a MouseMove). This is automatic since the existing `isinstance(block, MouseMoveBlock)` check will fail and terminate the run.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Loop iteration tracking | Custom counter attached to block objects | Engine-local `loop_stack` list (ephemeral) |
| Visual region bracket | Completely custom widget | `BlockDelegate.paint` left-border stripe (QPainter) |
| Persistence | Custom loop serialization | Existing `dataclasses.asdict` + `block_from_dict` — works automatically once `_BLOCK_CLASSES` is updated |

**Key insight:** `dataclasses.asdict` in `serializer.save` already handles all ActionBlock subclasses generically. Adding LoopStartBlock/LoopEndBlock to `_BLOCK_CLASSES` is the only persistence change needed. Round-trip is free.

---

## Common Pitfalls

### Pitfall 1: Orphaned Sentinels After Delete

**What goes wrong:** User selects only the LoopStart or only the LoopEnd row and deletes it, leaving an unmatched sentinel.

**Why it happens:** `delete_rows` operates on selected display rows. A user can select only one side.

**How to avoid:** Two strategies (pick one):
1. **Warn on delete:** Before deleting, check if selected rows include a LoopStart or LoopEnd without its partner. Prompt user: "Deleting a loop boundary also deletes its partner. Continue?" Then delete both.
2. **Silent pair-delete:** In `BlockTableModel.delete_rows`, when a `LoopHeaderRow` or `LoopFooterRow` is in the delete set, automatically add its partner's flat index to `flat_to_delete`.

**Recommendation:** Strategy 2 (silent pair-delete). It is non-disruptive and consistent with how group deletion works (deleting a GroupHeaderRow deletes all children automatically).

**Warning signs:** `_rebuild_display_rows` sees a `LoopEndBlock` with no preceding `LoopStartBlock` (empty stack) or reaches end-of-list with non-empty stack.

### Pitfall 2: Loop Stack Not Reset Between Outer Repeats

**What goes wrong:** If the outer macro repeat count is > 1, the `loop_stack` must be empty at the start of each outer iteration. If it is not cleared, the second repeat starts with stale loop state.

**How to avoid:** Initialize `loop_stack = []` inside the outer `while True` loop (inside the iteration setup block), not outside it. Verify with a test: repeat=2 outer, loop body runs correctly on both passes.

### Pitfall 3: Amber Cursor Missing on LoopStart/LoopEnd Rows

**What goes wrong:** `set_playback_flat_index` does not handle the new `LoopHeaderRow`, `LoopFooterRow`, `LoopChildRow` display types, so the amber highlight never appears when playback is executing blocks inside or at loop boundaries.

**How to avoid:** Extend the `set_playback_flat_index` method with cases for the new display row types, matching the existing pattern for `BlockRow` / `GroupHeaderRow` / `GroupChildRow`.

### Pitfall 4: Pause/Resume Inside a Loop

**What goes wrong:** If the user pauses playback (stop_event set, then somehow resumed — currently playback does not support pause/resume mid-stream, stop is terminal), the `loop_stack` state is lost.

**How to avoid:** Currently, stop is terminal — resuming means restarting from a `start_index`. For Phase 7, the amber cursor is preserved at stop. If the user restarts from the amber cursor position mid-loop, `loop_stack` starts empty, which means LoopEnd has no matching entry and is treated as an orphan (skipped). This is acceptable behavior for now — document it. The engine already has this limitation for Goto-based loops.

### Pitfall 5: Block Deletion Invalidates Loop Stack Indices

**What goes wrong:** Loop stack stores flat indices. If blocks are deleted after playback starts (impossible in current design — playback uses a snapshot), indices would be stale.

**How to avoid:** Non-issue. The engine receives the `blocks` list at `start()` time and operates on that snapshot. Mutations during playback are already an existing constraint.

### Pitfall 6: Wrap-in-Loop with GroupHeaderRow Selection

**What goes wrong:** When the user right-clicks "Wrap in Loop" with a GroupHeaderRow selected, `_display_row_to_flat_indices` returns the full range `flat_start..flat_end`. This is correct — all child move blocks should be inside the loop.

**How to avoid:** Use `_display_row_to_flat_indices` (already exists in `BlockTableModel`) to collect all flat indices for selected display rows, then take `min`/`max`. No special case needed.

---

## Code Examples

Verified from codebase inspection:

### Existing `_BLOCK_CLASSES` extension point (blocks.py line 89-98)
```python
# Add to _BLOCK_CLASSES dict:
_BLOCK_CLASSES: dict[str, type] = {
    ...existing...,
    "LoopStart": LoopStartBlock,
    "LoopEnd": LoopEndBlock,
}
# block_from_dict automatically works — no other change needed in serializer.py
```

### Existing engine dispatch location (engine/__init__.py line 135-159)
```python
# Inside _run, after LabelBlock/GotoBlock checks:
if isinstance(block, LoopStartBlock):
    loop_stack.append((i, block.repeat - 1))
    i += 1
    continue

if isinstance(block, LoopEndBlock):
    if loop_stack:
        start_idx, remaining = loop_stack[-1]
        if remaining > 0:
            loop_stack[-1] = (start_idx, remaining - 1)
            i = start_idx + 1
        else:
            loop_stack.pop()
            i += 1
    else:
        i += 1  # orphaned LoopEnd — skip
    continue
```

### Existing `_rebuild_display_rows` extension point (view_model.py line 179-210)
```python
# Add inside while loop, before the MouseMoveBlock check:
if isinstance(block, LoopStartBlock):
    rows.append(LoopHeaderRow(flat_index=i))
    in_loop = True  # set flag
    i += 1
    continue

if isinstance(block, LoopEndBlock):
    rows.append(LoopFooterRow(flat_index=i))
    in_loop = False
    i += 1
    continue

# For all other blocks: if in_loop, wrap as LoopChildRow:
if in_loop:
    rows.append(LoopChildRow(flat_index=i, loop_header_flat_index=loop_start_fi))
else:
    ... existing logic ...
```

### Existing background color extension (view_model.py line 267-288)
```python
# Add case in BackgroundRole branch:
if isinstance(row_obj, (LoopHeaderRow, LoopFooterRow, LoopChildRow)):
    return QBrush(QColor(0, 60, 55))  # dark teal
```

### Existing `_block_value` extension (view_model.py line 112-130)
```python
# Add before final `return ""`:
if isinstance(block, LoopStartBlock):
    return f"repeat x{block.repeat}"
if isinstance(block, LoopEndBlock):
    return "end loop"
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| No loop blocks | Phase 7: LoopStart/LoopEnd flat sentinels | Users can loop a segment N times without Goto/Label boilerplate |
| Label/Goto only for repetition | LoopStart/LoopEnd dedicated types | Cleaner intent, validated pairing, visual grouping |

---

## Open Questions

1. **Validation pre-flight for unmatched sentinels**
   - What we know: Phase 4 added `validate_gotos()` called before playback. A similar `validate_loops()` could check for balanced LoopStart/LoopEnd.
   - What's unclear: Whether to block playback on orphaned sentinels or silently skip them.
   - Recommendation: Add `validate_loops()` called alongside `validate_gotos()` in `_start_play`. Show a `QMessageBox` and block playback if unmatched sentinels are found. This is consistent with the existing validation pattern.

2. **LoopStart repeat=0 behavior**
   - What we know: `repeat=0` would mean "never execute" — LoopEnd immediately pops the stack.
   - Recommendation: Set minimum repeat=1 in `LoopStartPanel` QSpinBox. Document that repeat=0 skips the body entirely (edge case, probably unintended).

3. **Nested loops (explicitly out of scope)**
   - User confirmed no nested loops needed. The stack-based engine handles them anyway.
   - Recommendation: Validate that no LoopStart appears between another LoopStart and its matching LoopEnd. Surface error if found. This prevents confusing behavior even if the stack would technically handle it.

4. **Context menu placement**
   - What's unclear: Whether "Wrap in Loop" should be in the existing toolbar or as a right-click context menu.
   - User said "Right-click → Wrap selection in Loop". Follow user decision exactly.

---

## Implementation Plan Hint (for planner)

The work naturally breaks into 4 plans:

1. **Data model + serializer + engine:** `LoopStartBlock`/`LoopEndBlock` dataclasses, `_BLOCK_CLASSES` registration, engine `loop_stack` logic, `validate_loops`. TDD-first.
2. **View model:** `LoopHeaderRow`/`LoopFooterRow`/`LoopChildRow` display types, `_rebuild_display_rows` extension, `_block_value`/`_block_timestamp`/`data()` extensions, `set_playback_flat_index` extension.
3. **Delegate + visual styling:** `BlockDelegate.paint` left-border stripe, background tint in `data()` BackgroundRole.
4. **UI wiring:** `LoopStartPanel`, `block_type_dialog.py` extension, `editor_panel.py` context menu + selection routing, `_start_play` validation call.

---

## Sources

### Primary (HIGH confidence)
- `src/macro_thunder/models/blocks.py` — direct inspection; dataclass pattern, `_BLOCK_CLASSES`, `block_from_dict`
- `src/macro_thunder/engine/__init__.py` — direct inspection; `_run` dispatch loop, Label/Goto/WindowFocus patterns, `loop_stack` insertion point
- `src/macro_thunder/models/view_model.py` — direct inspection; `DisplayRow` types, `_rebuild_display_rows`, `BlockTableModel`, `set_playback_flat_index`
- `src/macro_thunder/ui/block_delegate.py` — direct inspection; paint override pattern
- `src/macro_thunder/ui/block_panels.py` — direct inspection; panel pattern for LabelPanel/GotoPanel
- `src/macro_thunder/ui/block_type_dialog.py` — direct inspection; `_BLOCK_TYPES` list extension point
- `src/macro_thunder/ui/editor_panel.py` — direct inspection; `_on_selection_changed` routing, `_on_context_menu` insertion point
- `src/macro_thunder/persistence/serializer.py` — direct inspection; `dataclasses.asdict` + `block_from_dict` auto-handles new types

### No external sources needed
All research is from direct codebase inspection. The technology (PyQt6, Python dataclasses) is already in use throughout the project. No new libraries are introduced.

---

## Metadata

**Confidence breakdown:**
- Data model extension: HIGH — exact pattern established by Label/Goto in Phase 4
- Engine loop semantics: HIGH — read entire `_run` method; stack-based approach is standard for loop dispatch
- View model extension: HIGH — read entire `_rebuild_display_rows`; new DisplayRow types follow established pattern
- Visual rendering: HIGH — read `BlockDelegate.paint`; QPainter left-border stripe is straightforward
- UI wiring: HIGH — read `EditorPanel`; context menu and panel routing are established patterns
- Serialization: HIGH — `dataclasses.asdict` + `_BLOCK_CLASSES` dict; adding entries is sufficient

**Research date:** 2026-03-03
**Valid until:** Stable — internal codebase; no external API dependencies introduced
