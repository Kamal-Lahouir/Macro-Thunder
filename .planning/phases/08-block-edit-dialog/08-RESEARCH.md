# Phase 8: Block Edit Dialog - Research

**Researched:** 2026-03-04
**Domain:** PyQt6 modal dialog patterns, in-place block mutation, key capture UI
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Dialog trigger**
- Double-click on a block row opens the edit dialog
- LoopEnd blocks have no editable fields — do not open a dialog

**Dialog style**
- Simple modal form dialog (QDialog) with labeled fields, OK and Cancel buttons
- Not inline editing, not a side panel

**Block type coverage — all logically editable types**
- `MouseClickBlock`: x, y, button (left/right/middle), direction (down/up/click)
- `MouseMoveBlock`: x, y
- `MouseScrollBlock`: x, y, dx, dy
- `KeyPressBlock`: key (press-to-capture), direction (down/up/key)
- `DelayBlock`: duration (float seconds)
- `LabelBlock`: name
- `GotoBlock`: target label name
- `WindowFocusBlock`: all fields (executable, title, match_mode, timeout, on_failure_label, on_success_label, reposition, x, y, w, h)
- `LoopStartBlock`: repeat count
- `LoopEndBlock`: no dialog

**Paired MouseClick sync**
- A click in Mode 2 produces two blocks: direction="down" and direction="up" with the same button
- When editing either block of a pair, the edit dialog edits both atomically
- Pairing rule: from the edited block, find the nearest sibling with matching button and the complementary direction (down↔up)
- Both button AND x/y are synced — down and up happen at the same coordinates
- If no pair is found (e.g. orphaned block), edit only the single block

**Key capture for KeyPress**
- Uses press-to-capture: a button labeled "Press a key..." that captures the next physical keypress
- Same interaction pattern as the hotkey capture UI in Settings (Phase 6)

**Dirty flag**
- Confirming edits (OK) marks the macro as unsaved, same as delete/reorder/insert
- Cancelling leaves the block unchanged and does not dirty the document

### Claude's Discretion

None declared — all implementation decisions were locked.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 8 adds a double-click-to-edit flow for all block types. The domain is exclusively PyQt6 modal dialog construction and in-place block mutation — no new libraries, no new services, no threading concerns. Everything needed is already in the project: QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QCheckBox, and the `HotkeyField` widget pattern from `settings_dialog.py`.

The central correctness challenge is the paired MouseClickBlock edit: when the user double-clicks either the "down" or "up" block, the dialog must find its sibling by scanning `MacroDocument.blocks` for the nearest block with the complementary direction and matching button, then apply x, y, and button changes to both. The mutation model follows the existing pattern: a new `edit_block(flat_index, new_block)` method on `BlockTableModel` that calls `beginResetModel/endResetModel` and emits `document_modified`. For paired edits, the method takes two flat indices.

The key-capture widget for KeyPress is a simplified `HotkeyField` — same `keyPressEvent` approach, but without modifier handling and without the pynput format string conversion. It captures the raw pynput key name stored in `KeyPressBlock.key` (e.g. `"a"`, `"Key.space"`, `"Key.f10"`). The dialog must preserve the original key string on Cancel and apply only on OK.

**Primary recommendation:** Create a single `block_edit_dialog.py` in `src/macro_thunder/ui/` with one public function `edit_block_dialog(block, doc_blocks, parent) -> bool` that handles all block types, returns `True` if confirmed (OK) and `False` if cancelled, and applies mutations to the live document only on confirmation.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | already installed | QDialog, QFormLayout, QDialogButtonBox | Project standard — all UI uses PyQt6 |
| Python dataclasses | stdlib | Block mutation (in-place field update) | Blocks are dataclasses; fields are mutable attributes |

### Supporting
| Widget | Source | Purpose | When to Use |
|--------|--------|---------|-------------|
| `QSpinBox` | PyQt6.QtWidgets | Integer fields (x, y, dx, dy, repeat) | All integer block fields |
| `QDoubleSpinBox` | PyQt6.QtWidgets | Float fields (duration, timeout) | DelayBlock.duration, WindowFocusBlock.timeout |
| `QComboBox` | PyQt6.QtWidgets | Enum-like fields (button, direction, match_mode) | MouseClickBlock.button/direction, WindowFocusBlock.match_mode |
| `QLineEdit` | PyQt6.QtWidgets | Text fields (name, target, executable, title, labels) | LabelBlock, GotoBlock, WindowFocusBlock text fields |
| `QCheckBox` | PyQt6.QtWidgets | Boolean (reposition) | WindowFocusBlock.reposition |
| `QDialogButtonBox` | PyQt6.QtWidgets | OK + Cancel buttons | All dialogs |
| `QFormLayout` | PyQt6.QtWidgets | Label-field pairs | All dialog forms |

### No New Packages Required
```bash
# Nothing to install — all widgets are in the existing PyQt6 installation
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/macro_thunder/ui/
├── block_edit_dialog.py   # NEW: all per-type edit dialogs + KeyCaptureField
├── editor_panel.py        # MODIFIED: connect doubleClicked signal
├── ...existing files...
src/macro_thunder/models/
└── view_model.py          # MODIFIED: add edit_block() and edit_block_pair() methods
```

### Pattern 1: Single Dialog Module with Per-Type Factory

**What:** One file, `block_edit_dialog.py`, contains `KeyCaptureField` widget plus one `QDialog` subclass per block type, plus a top-level dispatcher function.

**When to use:** When there are many types (9 editable types here) but each form is small — a factory dispatcher keeps `EditorPanel` clean.

**Example:**
```python
# src/macro_thunder/ui/block_edit_dialog.py

def open_edit_dialog(block: ActionBlock, doc_blocks: list, parent=None) -> bool:
    """Open the appropriate edit dialog for block. Returns True if user confirmed.

    For paired MouseClick blocks, doc_blocks is used to find the partner.
    Mutations are applied only on OK.
    """
    if isinstance(block, MouseClickBlock):
        partner_index, partner = _find_click_partner(block, doc_blocks)
        dlg = MouseClickEditDialog(block, partner, parent)
    elif isinstance(block, MouseMoveBlock):
        dlg = MouseMoveEditDialog(block, parent)
    elif isinstance(block, MouseScrollBlock):
        dlg = MouseScrollEditDialog(block, parent)
    elif isinstance(block, KeyPressBlock):
        dlg = KeyPressEditDialog(block, parent)
    elif isinstance(block, DelayBlock):
        dlg = DelayEditDialog(block, parent)
    elif isinstance(block, LabelBlock):
        dlg = LabelEditDialog(block, parent)
    elif isinstance(block, GotoBlock):
        dlg = GotoEditDialog(block, parent)
    elif isinstance(block, WindowFocusBlock):
        dlg = WindowFocusEditDialog(block, parent)
    elif isinstance(block, LoopStartBlock):
        dlg = LoopStartEditDialog(block, parent)
    else:
        return False  # LoopEndBlock or unknown — no dialog
    return dlg.exec() == QDialog.DialogCode.Accepted
```

### Pattern 2: Copy-and-Apply for Cancel Safety

**What:** The dialog holds a working copy of the block's values in its widgets. On OK, it writes back to the original block. On Cancel, the original block is untouched.

**When to use:** Always — this ensures Cancel truly leaves the block unchanged.

**Implementation approach:**
```python
class DelayEditDialog(QDialog):
    def __init__(self, block: DelayBlock, parent=None):
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit Delay")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._spin = QDoubleSpinBox()
        self._spin.setRange(0.001, 3600.0)
        self._spin.setDecimals(3)
        self._spin.setSuffix(" s")
        self._spin.setValue(block.duration)  # pre-filled from current value
        form.addRow("Duration:", self._spin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._block.duration = self._spin.value()  # only writes on OK
        super().accept()
```

### Pattern 3: Paired MouseClick Edit

**What:** When either block of a down/up pair is edited, find the partner and apply button + x/y to both.

**Pairing rule (confirmed from CONTEXT.md):**
- From edited block's position in `doc_blocks`, scan FORWARD for nearest `MouseClickBlock` with same `.button` and direction `"up"` (if edited is `"down"`), OR scan BACKWARD for nearest `MouseClickBlock` with same `.button` and direction `"down"` (if edited is `"up"`).
- If no partner found, edit single block only.

**Example:**
```python
def _find_click_partner(
    block: MouseClickBlock, doc_blocks: list
) -> tuple[int, MouseClickBlock | None]:
    """Return (flat_index, partner_block) or (-1, None) if not found."""
    try:
        idx = doc_blocks.index(block)
    except ValueError:
        return -1, None

    target_direction = "up" if block.direction == "down" else "down"

    if block.direction == "down":
        # Scan forward
        for i in range(idx + 1, len(doc_blocks)):
            b = doc_blocks[i]
            if isinstance(b, MouseClickBlock) and b.button == block.button and b.direction == target_direction:
                return i, b
    else:
        # Scan backward
        for i in range(idx - 1, -1, -1):
            b = doc_blocks[i]
            if isinstance(b, MouseClickBlock) and b.button == block.button and b.direction == target_direction:
                return i, b
    return -1, None
```

**Dialog apply-on-OK for pair:**
```python
class MouseClickEditDialog(QDialog):
    def __init__(self, block: MouseClickBlock, partner: MouseClickBlock | None, parent=None):
        super().__init__(parent)
        self._block = block
        self._partner = partner  # may be None for orphaned block
        # ... build form with x, y, button, direction fields ...

    def accept(self) -> None:
        x = self._x_spin.value()
        y = self._y_spin.value()
        button = self._button_combo.currentText()
        direction = self._dir_combo.currentText()
        self._block.x = x
        self._block.y = y
        self._block.button = button
        self._block.direction = direction
        if self._partner is not None:
            self._partner.x = x
            self._partner.y = y
            self._partner.button = button
            # direction stays as partner's original direction (down↔up)
        super().accept()
```

### Pattern 4: Double-Click Signal in EditorPanel

**What:** Connect `QTableView.doubleClicked` signal to a slot that resolves the block and calls `open_edit_dialog`.

**Where to add in `editor_panel.py`:**
```python
# In EditorPanel.__init__, after table setup:
self._table.doubleClicked.connect(self._on_double_click)

# New slot:
def _on_double_click(self, index) -> None:
    if self._model is None:
        return
    row_obj = self._model.display_row(index.row())
    if row_obj is None:
        return
    # Resolve the flat block index
    flat_index = None
    if isinstance(row_obj, BlockRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, LoopHeaderRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, LoopChildRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, GroupChildRow):
        flat_index = row_obj.flat_index
    # GroupHeaderRow and LoopFooterRow: no edit dialog (group duration edit
    # handled inline; LoopEnd has no editable fields)
    if flat_index is None:
        return
    block = self._model._doc.blocks[flat_index]
    from macro_thunder.ui.block_edit_dialog import open_edit_dialog
    confirmed = open_edit_dialog(block, self._model._doc.blocks, self)
    if confirmed:
        self._model.beginResetModel()
        self._model._rebuild_display_rows()
        self._model.endResetModel()
        self._model.document_modified.emit()
        self.document_modified.emit()
```

### Pattern 5: KeyCaptureField for KeyPress Dialog

**What:** A simplified version of `HotkeyField` from `settings_dialog.py` that captures a single keypress and stores it in pynput key-name format (e.g. `"a"`, `"Key.space"`).

**Key difference from HotkeyField:** `HotkeyField` builds composite modifier+key strings like `"<ctrl>+a"`. For `KeyPressBlock.key`, the stored format is pynput's own key string (`"a"`, `"Key.f10"`, `"Key.space"`). The capture widget needs to output that format, not the hotkey format.

**Observed key format in project:** Looking at `_block_value` in `view_model.py`, `KeyPressBlock.key` displays raw as `block.key`, e.g. `"a"` or `"Key.space"`. The capture should convert `QKeyEvent` to this pynput format.

**Approach for key name conversion:**
```python
def _qt_key_to_pynput(event: QKeyEvent) -> str:
    """Convert QKeyEvent to pynput key string (no modifiers)."""
    key = event.key()
    # Named key map → pynput Key.xxx names
    named = {
        Qt.Key.Key_Space: "Key.space",
        Qt.Key.Key_Return: "Key.enter",
        Qt.Key.Key_Enter: "Key.enter",
        Qt.Key.Key_Backspace: "Key.backspace",
        Qt.Key.Key_Delete: "Key.delete",
        Qt.Key.Key_Tab: "Key.tab",
        Qt.Key.Key_Escape: "Key.esc",
        Qt.Key.Key_Up: "Key.up",
        Qt.Key.Key_Down: "Key.down",
        Qt.Key.Key_Left: "Key.left",
        Qt.Key.Key_Right: "Key.right",
        Qt.Key.Key_Home: "Key.home",
        Qt.Key.Key_End: "Key.end",
        Qt.Key.Key_PageUp: "Key.page_up",
        Qt.Key.Key_PageDown: "Key.page_down",
        Qt.Key.Key_Insert: "Key.insert",
        Qt.Key.Key_F1: "Key.f1", Qt.Key.Key_F2: "Key.f2",
        Qt.Key.Key_F3: "Key.f3", Qt.Key.Key_F4: "Key.f4",
        Qt.Key.Key_F5: "Key.f5", Qt.Key.Key_F6: "Key.f6",
        Qt.Key.Key_F7: "Key.f7", Qt.Key.Key_F8: "Key.f8",
        Qt.Key.Key_F9: "Key.f9", Qt.Key.Key_F10: "Key.f10",
        Qt.Key.Key_F11: "Key.f11", Qt.Key.Key_F12: "Key.f12",
        Qt.Key.Key_CapsLock: "Key.caps_lock",
        Qt.Key.Key_NumLock: "Key.num_lock",
        Qt.Key.Key_ScrollLock: "Key.scroll_lock",
        Qt.Key.Key_Print: "Key.print_screen",
        Qt.Key.Key_Pause: "Key.pause",
    }
    if key in named:
        return named[key]
    char = event.text()
    if char and char.isprintable():
        return char.lower()
    # Fallback: unknown key
    return f"Key.{Qt.Key(key).name.replace('Key_', '').lower()}"
```

### Anti-Patterns to Avoid

- **Mutating blocks live during dialog interaction:** Do NOT connect spinbox `valueChanged` directly to block mutation (like the inline panels do). For a Cancel-safe modal, only write on `accept()`. The inline panels (LabelPanel, GotoPanel, etc.) write live because they have no Cancel path — the modal pattern is different.
- **Using `beginResetModel` inside the dialog:** The dialog should not hold a reference to the model. It operates on the block object directly. The `EditorPanel._on_double_click` slot handles the model reset after dialog returns.
- **Scanning display_rows for partner instead of doc.blocks:** The pair search must scan the flat `MacroDocument.blocks` list, not the display rows. Display rows may omit blocks (GroupChildRow inside collapsed group) or add extra rows (group headers).
- **Opening dialog for GroupHeaderRow double-click:** GroupHeaderRow double-click is already used by `BlockDelegate.editorEvent` for expand/collapse toggle. Do NOT open an edit dialog for group headers — only for block rows.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form layout with aligned labels | Custom QHBoxLayout per field | `QFormLayout` | Handles label alignment, tab order, and platform look automatically |
| OK/Cancel buttons | Manual QPushButton pair | `QDialogButtonBox` with StandardButton.Ok + StandardButton.Cancel | Handles platform button order (Windows: Ok left, Cancel right) and keyboard shortcuts automatically |
| Integer input with bounds | QLineEdit + int() parse | `QSpinBox` with setRange() | Prevents invalid input, arrow key navigation, scroll wheel support |
| Float input with bounds | QLineEdit + float() parse | `QDoubleSpinBox` with setRange() + setDecimals() | Same benefits as QSpinBox |
| Key capture widget | Custom event filter | Subclass the `HotkeyField` approach from settings_dialog.py | Pattern already validated in Phase 6 |

**Key insight:** The inline editing (via `setData()` / `_set_block_value()`) already exists for simple field changes. The dialog adds Cancel safety and multi-field atomic editing — it should NOT replace the inline editing path, just augment it for double-click.

---

## Common Pitfalls

### Pitfall 1: GroupHeaderRow Double-Click Conflict
**What goes wrong:** `QTableView.doubleClicked` fires for ALL rows including group headers. If the slot opens an edit dialog for a GroupHeaderRow, it conflicts with the toggle-group logic.
**Why it happens:** `BlockDelegate.editorEvent` handles the toggle on single-click via arrow area detection; doubleClicked signal also fires.
**How to avoid:** In `_on_double_click`, check `isinstance(row_obj, GroupHeaderRow)` early and return immediately. Only handle `BlockRow`, `LoopHeaderRow`, `LoopChildRow`, `GroupChildRow`.
**Warning signs:** Toggle stops working, or dialog opens for groups.

### Pitfall 2: LoopFooterRow (LoopEnd) Opens Dialog
**What goes wrong:** LoopEnd blocks appear as `LoopFooterRow`. If the slot resolves flat_index for LoopFooterRow, it could open a dialog with no fields.
**How to avoid:** `LoopEndBlock` has no editable fields — `open_edit_dialog` returns `False` for it. Also guard in `_on_double_click` by not resolving `LoopFooterRow`.

### Pitfall 3: Partner Block Identity vs. Index
**What goes wrong:** `doc_blocks.index(block)` relies on object identity (Python `is` comparison in list.index). If blocks are ever copied rather than referenced, the wrong index is found.
**Why it happens:** The view model holds `self._doc` and blocks are the live objects. As long as we pass `self._model._doc.blocks` and the actual block object from `self._doc.blocks[flat_index]`, identity is maintained.
**How to avoid:** Always get the block via `self._model._doc.blocks[flat_index]` — never copy it before passing to the dialog.

### Pitfall 4: KeyPress Direction Field Editable Despite Paired Down/Up Meaning
**What goes wrong:** Allowing user to change direction from "down" to "up" on a "down" block creates logical inconsistency (two "up" blocks, no "down").
**How to avoid:** For KeyPressBlock, the direction field is straightforward (it records each key event individually, unpaired) so editing direction is valid. For MouseClickBlock, if editing the "down" block, direction should remain locked or the dialog should explain the pairing. CONTEXT.md says direction is editable — allow it but note the risk.

### Pitfall 5: Cancel Safety with QDoubleSpinBox and Live Signals
**What goes wrong:** If the developer accidentally connects `valueChanged` to block mutation during dialog construction (like inline panels do), Cancel no longer works.
**How to avoid:** In modal dialogs, only write to `self._block` inside `accept()`. No `textChanged`/`valueChanged` connections that mutate blocks.

### Pitfall 6: WindowFocusEditDialog Reposition Sub-Group Visibility
**What goes wrong:** The reposition x/y/w/h group should be hidden when `reposition=False`, same as in `WindowFocusPanel`. Forgetting this makes the dialog appear with irrelevant fields.
**How to avoid:** Copy the `_reposition_check.toggled` → `_reposition_group.setVisible()` pattern from `WindowFocusPanel`. In the dialog, connect this in `__init__` but don't write to block — write only in `accept()`.

---

## Code Examples

### Double-Click Slot in EditorPanel (HIGH confidence — based on existing codebase)
```python
# In EditorPanel.__init__:
self._table.doubleClicked.connect(self._on_double_click)

def _on_double_click(self, index) -> None:
    if self._model is None:
        return
    row_obj = self._model.display_row(index.row())
    if row_obj is None:
        return
    # Resolve flat index — skip row types with no edit dialog
    if isinstance(row_obj, (GroupHeaderRow, LoopFooterRow)):
        return
    if isinstance(row_obj, BlockRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, LoopHeaderRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, LoopChildRow):
        flat_index = row_obj.flat_index
    elif isinstance(row_obj, GroupChildRow):
        flat_index = row_obj.flat_index
    else:
        return
    block = self._model._doc.blocks[flat_index]
    from macro_thunder.ui.block_edit_dialog import open_edit_dialog
    confirmed = open_edit_dialog(block, self._model._doc.blocks, self)
    if confirmed:
        self._model.beginResetModel()
        self._model._rebuild_display_rows()
        self._model.endResetModel()
        self._model.document_modified.emit()
        self.document_modified.emit()
```

### BlockTableModel.edit_block (Alternative: new model method — optional)
The double-click slot above calls `beginResetModel/_rebuild/endResetModel` directly after dialog confirmation. This is identical to how `wrap_in_loop` and `insert_block` work. A dedicated `edit_block()` method on `BlockTableModel` is optional — the same three lines can live in the EditorPanel slot. The CONTEXT.md suggests a new `edit_block(flat_index, new_block)` method, but since the dialog mutates the live block object in-place rather than replacing it, `beginResetModel` + `_rebuild_display_rows` + `endResetModel` + `document_modified.emit()` in the slot is sufficient.

### KeyCaptureField for KeyPress Dialog (HIGH confidence — adapted from HotkeyField)
```python
class KeyCaptureField(QWidget):
    """Simplified key capture: captures a single physical key, outputs pynput format."""

    def __init__(self, initial_value: str = "", parent=None):
        super().__init__(parent)
        self._capturing = False
        self._value = initial_value
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._display = QLineEdit(initial_value)
        self._display.setReadOnly(True)
        self._display.setMinimumWidth(160)
        self._btn = QPushButton("Press a key...")
        self._btn.setFixedWidth(110)
        self._btn.clicked.connect(self._start_capture)
        layout.addWidget(self._display)
        layout.addWidget(self._btn)

    def value(self) -> str:
        return self._value

    def _start_capture(self):
        self._capturing = True
        self._display.setText("… press a key …")
        self._btn.setText("Cancel")
        self._btn.clicked.disconnect()
        self._btn.clicked.connect(self._cancel_capture)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def _cancel_capture(self):
        self._capturing = False
        self._display.setText(self._value)
        self._btn.setText("Press a key...")
        self._btn.clicked.disconnect()
        self._btn.clicked.connect(self._start_capture)
        self.clearFocus()

    def keyPressEvent(self, event):
        if not self._capturing:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._cancel_capture()
            return
        modifier_only = {
            Qt.Key.Key_Shift, Qt.Key.Key_Control,
            Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr,
        }
        if key in modifier_only:
            return
        self._value = _qt_key_to_pynput(event)
        self._display.setText(self._value)
        self._capturing = False
        self._btn.setText("Press a key...")
        self._btn.clicked.disconnect()
        self._btn.clicked.connect(self._start_capture)
        self.clearFocus()
        event.accept()
```

### Minimal QDialog structure (HIGH confidence — matches existing BlockTypeDialog and SettingsDialog)
```python
class LabelEditDialog(QDialog):
    def __init__(self, block: LabelBlock, parent=None):
        super().__init__(parent)
        self._block = block
        self.setWindowTitle("Edit Label")
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._name_edit = QLineEdit(block.name)
        self._name_edit.setPlaceholderText("Unique label name")
        form.addRow("Label Name:", self._name_edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._block.name = self._name_edit.text().strip()
        super().accept()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline editing via `setData()` | Modal dialog on double-click (this phase) | Phase 8 | Adds Cancel safety and multi-field editing |
| Detail panel (side-panel inline) | Modal dialog (this phase) | Phase 8 for new types | Existing detail panels remain for Label, Goto, WindowFocus, LoopStart |

**Note on coexistence:** The existing detail panels (LabelPanel, GotoPanel, WindowFocusPanel, LoopStartPanel) will still appear on single-click. Double-click opens the modal. The modal is the definitive edit path with Cancel safety; the panel is a live-edit convenience. No removal of existing panels is required.

---

## Open Questions

1. **KeyPress direction field: should it be editable in the dialog?**
   - What we know: CONTEXT.md says KeyPressBlock has `key (press-to-capture)` and `direction (down/up/key)` as editable fields
   - What's unclear: Whether changing direction is intentionally supported or an oversight (a "down" block recorded without a matching "up" is valid in some modes)
   - Recommendation: Include direction as a QComboBox with options "down"/"up"/"key" — the user can fix mis-recorded direction events

2. **WindowFocusBlock in edit dialog vs. existing detail panel**
   - What we know: WindowFocusPanel in the current detail panel already has all fields + window picker. The modal will duplicate this functionality.
   - What's unclear: Should the modal also include the "Select Window..." picker button (which requires `picker_service`)?
   - Recommendation: Include the picker button only if `picker_service` is passed to `open_edit_dialog`. Add `picker_service=None` parameter. If None, omit the button. This matches the existing `EditorPanel._picker_service` pattern.

3. **GroupChildRow double-click (individual move in expanded group)**
   - What we know: GroupChildRow is a `MouseMoveBlock`. It has x, y, timestamp as editable fields.
   - What's unclear: Should double-clicking a GroupChildRow open an edit dialog for x/y, or is this handled by existing inline editing?
   - Recommendation: Support GroupChildRow → open `MouseMoveEditDialog`. The flat_index is available on GroupChildRow. Keep it consistent — all block types get the dialog.

---

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/macro_thunder/ui/settings_dialog.py` — HotkeyField key capture pattern (lines 25-202)
- Existing codebase: `src/macro_thunder/ui/block_type_dialog.py` — QDialog modal pattern
- Existing codebase: `src/macro_thunder/ui/block_panels.py` — per-type form patterns (LabelPanel, GotoPanel, WindowFocusPanel, LoopStartPanel)
- Existing codebase: `src/macro_thunder/models/view_model.py` — beginResetModel mutation pattern, all DisplayRow types
- Existing codebase: `src/macro_thunder/models/blocks.py` — all block dataclasses and field names
- Existing codebase: `src/macro_thunder/ui/editor_panel.py` — EditorPanel signal connections, `_on_selection_changed` pattern

### Secondary (MEDIUM confidence)
- PyQt6 docs (training knowledge, stable API): `QTableView.doubleClicked` signal, `QDialog.exec()`, `QDialogButtonBox.StandardButton`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all widgets are already in use in the project
- Architecture: HIGH — patterns are derived directly from existing code (BlockTypeDialog, HotkeyField, BlockTableModel mutation methods)
- Pitfalls: HIGH — identified from direct inspection of existing code and signal interactions

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (stable — no external dependencies, no fast-moving libraries)
