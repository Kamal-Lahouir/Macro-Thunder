# Phase 5: Record Logic Adaptation and Fixes - Research

**Researched:** 2026-03-02
**Domain:** PyQt6 UI extensions, pynput recording modes, system tray, global hotkeys, infinite loop playback
**Confidence:** HIGH (all findings grounded in existing codebase)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Click Recording Modes**
- Toggle lives in **Settings dialog only** (not the toolbar) — set once, applies to all future recordings
- Mode 1 (combined): applies to **both left and right clicks** — any click produces a single `MouseClick` block with a `button` field (left/right/middle)
- Mode 2 (current): `MouseButtonDown` + `MouseButtonUp` as separate blocks (existing behavior preserved)
- Changing the mode has **no effect on the currently open macro** — existing blocks are untouched; mode is a recording preference only
- The **active click mode is shown in the status bar** during recording (e.g. "Click: Combined")

**Repeat & Loop UX**
- Repeat count spin box + infinite loop (∞) toggle live in the **toolbar**, always visible
- Repeat prefs are **session-only** — not saved in the macro .json file; toolbar resets to defaults on app launch
- Default repeat count on launch: **1** (play once)
- Infinite loop stops **immediately mid-macro** when Stop hotkey is pressed (no finish-current-pass logic)

**Record Here Hotkey**
- Key combo is **user-configurable in Settings** (no hardcoded default)
- When fired from another app: **Macro Thunder stays in the background** — recording begins silently, window does not come to front
- If no block is selected when hotkey fires: new recording is **appended at the end** of the macro
- Feedback when activated from another app: **system tray icon changes** (turns red) + optional sound cue — no window flash or OS notification

**Settings Persistence**
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

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 5 extends the existing PyQt6 + pynput + pywin32 stack with four orthogonal features: click recording modes (in `RecorderService`), repeat/infinite-loop playback (in `PlaybackEngine` + toolbar), a global "Record Here" hotkey (in `HotkeyManager`), and a system tray icon for background-state feedback. All four features fit cleanly into the existing architecture without breaking the threading rule (pynput callbacks → queue → QTimer drain → Qt).

The existing `AppSettings` dataclass uses `{k: v for k, v in data.items() if k in fields}` for forward-compatible loading, so adding new fields with defaults is fully backwards-compatible. `SettingsDialog` needs restructuring from a flat `QFormLayout` into two tab/section groupings (Hotkeys + Options). `HotkeyManager` already supports dynamic re-registration via `register(settings)` — adding a fifth hotkey follows the same pattern.

The largest new surface area is the system tray icon (`QSystemTrayIcon`), which requires a PNG/icon resource and the tray-icon-change-on-record logic bridged through the queue pattern. All other features (click mode in recorder, repeat/infinite in engine, toolbar spin box) are surgical additions to existing classes.

**Primary recommendation:** Work plan-by-plan in this order: (1) AppSettings + SettingsDialog restructure, (2) click mode in RecorderService, (3) repeat/infinite in PlaybackEngine + toolbar, (4) Record Here global hotkey, (5) system tray icon.

---

## Standard Stack

### Core (already installed — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | existing | `QSystemTrayIcon`, `QSpinBox`, `QCheckBox`, `QTabWidget` | Already the UI framework |
| pynput | existing | `keyboard.GlobalHotKeys` for Record Here hotkey | Already used for hotkeys |
| Python stdlib `winsound` | stdlib | Optional sound cue (beep) | Zero-dep, Windows-only, matches project scope |

### No New Dependencies Required

All features can be implemented with PyQt6 + pynput + stdlib. `winsound.Beep(freq, duration)` provides a sound cue without any new install.

---

## Architecture Patterns

### Recommended File Changes

```
src/macro_thunder/
├── settings.py              # Add: click_mode, hotkey_record_here, sound_cue_enabled
├── recorder/__init__.py     # Add: click_mode parameter to _on_click logic
├── hotkeys.py               # Add: record_here signal + 5th GlobalHotKeys entry
├── engine/__init__.py       # Add: infinite-loop support (repeat=-1 sentinel)
├── ui/
│   ├── toolbar.py           # Add: QSpinBox (repeat), QCheckBox (∞), click mode label
│   ├── settings_dialog.py   # Restructure: QTabWidget with Hotkeys + Options tabs
│   └── main_window.py       # Add: QSystemTrayIcon, _start_record_here from hotkey
```

### Pattern 1: AppSettings Extension (backwards-compatible)

**What:** Add new fields with defaults to the `AppSettings` dataclass. The existing load logic (`{k: v for k, v in data.items() if k in fields}`) silently ignores unknown keys from old files and falls back to default for new fields.

**New fields:**
```python
# In settings.py
@dataclasses.dataclass
class AppSettings:
    hotkey_start_record: str = "<f9>"
    hotkey_stop_record: str = "<f10>"
    hotkey_start_play: str = "<f6>"
    hotkey_stop_play: str = "<f8>"
    hotkey_record_here: str = ""          # NEW — empty = disabled
    mouse_threshold_px: int = 3
    click_mode: str = "separate"          # NEW — "separate" | "combined"
    sound_cue_enabled: bool = False       # NEW — Claude's discretion: off by default
```

**Click mode values:** `"separate"` (existing Mode 2 behavior) and `"combined"` (new Mode 1).

### Pattern 2: Click Mode in RecorderService

**What:** `RecorderService.__init__` accepts `click_mode: str = "separate"`. The `_on_click` callback branches on this value.

**Mode "separate" (existing):**
```python
# No change — records MouseClickBlock with direction="down"/"up"
```

**Mode "combined" (new):**
```python
def _on_click(self, x, y, button, pressed):
    if self._click_mode == "combined":
        if pressed:  # only record on press; ignore release
            ts = time.perf_counter() - self._record_start
            self._queue.put(MouseClickBlock(
                x=x, y=y,
                button=button.name,
                direction="click",   # new direction value
                timestamp=ts,
            ))
        # ignore `not pressed` in combined mode
    else:
        # existing separate behavior unchanged
        ...
```

**Critical:** `direction="click"` is a new value for `MouseClickBlock.direction`. The playback engine's `_dispatch` must handle it:
```python
elif isinstance(block, MouseClickBlock):
    btn = mouse.Button[block.button]
    if block.direction == "down":
        self._mouse_ctrl.press(btn)
    elif block.direction == "up":
        self._mouse_ctrl.release(btn)
    elif block.direction == "click":    # NEW
        self._mouse_ctrl.press(btn)
        self._mouse_ctrl.release(btn)
```

**Status bar feedback during recording:** `MainWindow._update_status` (runs every 16ms) should append click mode when `_state == AppState.RECORDING`. Example: add a `_click_mode_label` to the status bar, updated when recording starts.

### Pattern 3: Infinite Loop in PlaybackEngine

**What:** Use `repeat=-1` as the infinite sentinel. The existing `for _ in range(repeat)` loop becomes:

```python
def _run(self, blocks, speed, repeat):
    label_index = ...
    iteration = 0
    while True:
        if repeat != -1 and iteration >= repeat:
            break
        # existing loop body (stop_event checks intact)
        iteration += 1
    # signal completion
    if self._on_progress:
        self._on_progress(len(blocks), len(blocks))
```

**Stop semantics:** `self._stop_event.set()` already causes `return` inside the inner `while i < len(blocks)` loop — this is the "immediately mid-macro" behavior required by the decision. No changes needed for stop logic.

**Toolbar signal change:** `play_requested` currently emits `(float, int)` — speed and repeat. With infinite loop, the repeat value will be `-1` when the checkbox is checked. The signal type stays `(float, int)`; `-1` is the sentinel.

```python
# In toolbar.py
def _on_play_clicked(self):
    repeat = -1 if self._chk_infinite.isChecked() else self._spin_repeat.value()
    self.play_requested.emit(self._speed_spin.value(), repeat)
```

**Toolbar new widgets:**
```python
# After speed controls, add:
self._spin_repeat = QSpinBox()
self._spin_repeat.setRange(1, 9999)   # Claude's discretion: 1–9999
self._spin_repeat.setValue(1)
self._spin_repeat.setFixedWidth(60)

self._chk_infinite = QCheckBox("∞")
self._chk_infinite.setToolTip("Loop infinitely until Stop is pressed")
self._chk_infinite.toggled.connect(lambda on: self._spin_repeat.setEnabled(not on))
```

### Pattern 4: Record Here Global Hotkey

**What:** Add a fifth signal to `HotkeyManager` and a fifth entry in the `GlobalHotKeys` map.

**HotkeyManager changes:**
```python
class HotkeyManager(QObject):
    start_record = pyqtSignal()
    stop_record = pyqtSignal()
    start_play = pyqtSignal()
    stop_play = pyqtSignal()
    record_here = pyqtSignal()    # NEW

    def register(self, settings: AppSettings) -> None:
        ...
        hotkey_map = {
            settings.hotkey_start_record: lambda: q.put("start_record"),
            settings.hotkey_stop_record:  lambda: q.put("stop_record"),
            settings.hotkey_start_play:   lambda: q.put("start_play"),
            settings.hotkey_stop_play:    lambda: q.put("stop_play"),
        }
        # Only add record_here entry if configured
        if settings.hotkey_record_here:
            hotkey_map[settings.hotkey_record_here] = lambda: q.put("record_here")
        ...

    def _drain(self):
        ...
        elif action == "record_here":
            self.record_here.emit()
```

**MainWindow wiring:**
```python
self._hotkeys.record_here.connect(self._on_record_here_hotkey)

def _on_record_here_hotkey(self) -> None:
    """Global Record Here hotkey — window stays in background."""
    if self._state != AppState.IDLE:
        return
    # Get selected flat index from editor (or -1 for append at end)
    flat_index = self._editor_panel.get_selected_flat_index()
    self._start_record_here(flat_index)
    # Do NOT call showNormal() or activateWindow() — stays in background
```

**EditorPanel needs a new method:**
```python
def get_selected_flat_index(self) -> int:
    """Return the flat index of the currently selected block, or -1 if none."""
    indexes = self._table.selectedIndexes()
    if not indexes:
        return -1
    return indexes[0].row()  # flat row in display model
    # Note: if the selected row is a group header, return its flat_start
```

### Pattern 5: System Tray Icon

**What:** `QSystemTrayIcon` in `MainWindow.__init__`. Two states: normal (app icon) and recording (red/recording icon).

```python
# In MainWindow.__init__
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor

# Create tray icon
self._tray_icon = QSystemTrayIcon(self)
self._tray_icon.setIcon(self._make_tray_icon("gray"))

tray_menu = QMenu()
show_action = QAction("Show", self)
show_action.triggered.connect(self.showNormal)
quit_action = QAction("Quit", self)
quit_action.triggered.connect(QApplication.quit)
tray_menu.addAction(show_action)
tray_menu.addAction(quit_action)
self._tray_icon.setContextMenu(tray_menu)
self._tray_icon.show()

@staticmethod
def _make_tray_icon(color: str) -> QIcon:
    """Create a simple 16x16 colored circle icon."""
    pix = QPixmap(16, 16)
    pix.fill(QColor(color))
    return QIcon(pix)
```

**State changes:**
```python
# When recording starts (in _start_record / _start_record_here):
self._tray_icon.setIcon(self._make_tray_icon("red"))

# When recording stops (in _stop_record):
self._tray_icon.setIcon(self._make_tray_icon("gray"))
```

**Sound cue (Claude's discretion — off by default):**
```python
import winsound
if self._settings.sound_cue_enabled:
    threading.Thread(
        target=winsound.Beep, args=(880, 100), daemon=True
    ).start()
```
Run in a daemon thread because `winsound.Beep` blocks the calling thread for the duration.

### Pattern 6: Hotkey Conflict Detection in SettingsDialog

**What:** When user clicks OK in Settings, check the Record Here field against existing hotkeys before saving.

```python
def accept(self) -> None:
    record_here = self._edit_record_here.text().strip()
    if record_here:
        existing = {
            self._edit_start_record.text().strip(): "Start Record",
            self._edit_stop_record.text().strip(): "Stop Record",
            self._edit_start_play.text().strip(): "Start Playback",
            self._edit_stop_play.text().strip(): "Stop Playback",
        }
        if record_here in existing:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Hotkey Conflict",
                f"'{record_here}' is already assigned to: {existing[record_here]}"
            )
            return  # reject — do NOT call super().accept()
    # proceed with save
    ...
    super().accept()
```

### Pattern 7: SettingsDialog Restructure (QTabWidget)

**What:** Replace the flat `QFormLayout` with a `QTabWidget` containing two tabs.

```python
tabs = QTabWidget()
layout.addWidget(tabs)

# Tab 1: Hotkeys
hotkeys_widget = QWidget()
hotkeys_form = QFormLayout(hotkeys_widget)
hotkeys_form.addRow("Start Record:", self._edit_start_record)
hotkeys_form.addRow("Stop Record:", self._edit_stop_record)
hotkeys_form.addRow("Start Playback:", self._edit_start_play)
hotkeys_form.addRow("Stop Playback:", self._edit_stop_play)
hotkeys_form.addRow("Record Here:", self._edit_record_here)   # NEW
tabs.addTab(hotkeys_widget, "Hotkeys")

# Tab 2: Options
options_widget = QWidget()
options_form = QFormLayout(options_widget)
options_form.addRow("Click mode:", self._combo_click_mode)    # NEW QComboBox
options_form.addRow("Mouse threshold (px):", self._spin_threshold)
options_form.addRow("Sound cue on record:", self._chk_sound_cue)  # NEW
tabs.addTab(options_widget, "Options")
```

**Click mode widget:** `QComboBox` with items `["Separate (down + up)", "Combined (single click)"]`; index 0 = "separate", index 1 = "combined".

### Pattern 8: Settings Menu Item (Top-Level)

**Current state:** Settings is inside the File menu (`file_menu.addAction(settings_action)`).

**Required change:** Add a separate top-level `&Settings` menu in `MainWindow.__init__`:

```python
# Remove settings_action from file_menu
# Add after file_menu:
settings_menu = self.menuBar().addMenu("&Settings")
settings_action = QAction("&Preferences...", self)
settings_action.triggered.connect(self._open_settings)
settings_menu.addAction(settings_action)
```

### Anti-Patterns to Avoid

- **Touching Qt from the record_here hotkey thread:** The pynput `GlobalHotKeys` callback MUST only `q.put("record_here")` — never call `showNormal()` or any Qt method.
- **Calling `winsound.Beep` on the main thread:** It blocks. Always run in a daemon thread.
- **Using `repeat=0` as infinite sentinel:** Python's `range(0)` is empty (no iterations). Use `-1` explicitly.
- **Re-registering hotkeys on every settings field change:** Only re-register on `accept()` — call `self._hotkeys.register(new_settings)` from `MainWindow._open_settings` after the dialog is accepted (same as current code).
- **Forgetting to guard `hotkey_record_here = ""` in GlobalHotKeys:** An empty string key in `GlobalHotKeys` will raise. Always check `if settings.hotkey_record_here:` before adding the entry.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| System tray icon | Custom overlay/notification | `QSystemTrayIcon` (PyQt6 built-in) | Full platform integration, context menu, tooltip |
| Sound notification | Win32 `PlaySound` P/Invoke | `winsound.Beep` (stdlib) | Zero-dep, sufficient for a short beep |
| Tab-based dialog layout | Manual stacked widgets | `QTabWidget` | Qt standard, keyboard navigation, consistent look |
| Click mode storage | Separate config file | `AppSettings` dataclass field | Already the settings mechanism; load/save already handled |

---

## Common Pitfalls

### Pitfall 1: `QSystemTrayIcon.show()` before `QApplication` is fully initialized
**What goes wrong:** Tray icon may not appear or crash on some Windows configurations.
**How to avoid:** Call `self._tray_icon.show()` in `MainWindow.__init__` (after `super().__init__()`). This is safe — `QApplication` is already running by the time `MainWindow` is constructed.

### Pitfall 2: `GlobalHotKeys` with empty-string keys
**What goes wrong:** pynput `GlobalHotKeys({""": lambda: ...})` raises a parse error.
**How to avoid:** Always guard: `if settings.hotkey_record_here: hotkey_map[...] = ...`.

### Pitfall 3: Infinite loop sentinel with `range()`
**What goes wrong:** `range(-1)` is empty — zero iterations.
**How to avoid:** Replace `for _ in range(repeat)` with the `while True` + `if repeat != -1 and iteration >= repeat: break` pattern shown above.

### Pitfall 4: `direction="click"` in old JSON files
**What goes wrong:** Existing macros saved before Phase 5 will never have `direction="click"`. The engine must handle both old values (`"down"`, `"up"`) and new (`"click"`) without crashing.
**How to avoid:** The `elif block.direction == "click"` branch is additive — old behavior is unchanged.

### Pitfall 5: `winsound.Beep` on Windows ARM / some VM environments
**What goes wrong:** `winsound.Beep` may fail silently or raise `RuntimeError` on some Windows configurations (e.g., no audio device).
**How to avoid:** Wrap in `try/except Exception: pass` inside the daemon thread.

### Pitfall 6: Status bar click mode label during background recording
**What goes wrong:** `_update_status` runs on the main thread via `QTimer` — safe to update. But the label must not be set from the pynput thread.
**How to avoid:** Set the click mode label in `_start_record` / `_start_record_here` (both run on the main thread). Clear it in `_stop_record`.

### Pitfall 7: `get_selected_flat_index` when a group header is selected
**What goes wrong:** If the selected row is a `GroupHeaderRow` (collapsed group), its display row index maps to a range of flat blocks. Returning the raw `selectedIndexes()[0].row()` gives the display index, not the flat block index.
**How to avoid:** Use `EditorPanel`'s existing `_display_rows` list to resolve display index → flat index, same as `insert_blocks_at` already does.

---

## Code Examples

### Adding a new AppSettings field (backwards-compatible)
```python
# Source: existing settings.py pattern
@dataclasses.dataclass
class AppSettings:
    # ... existing fields ...
    click_mode: str = "separate"       # new field with default
    hotkey_record_here: str = ""       # new field with default

    @classmethod
    def load(cls) -> "AppSettings":
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            fields = {f.name for f in dataclasses.fields(cls)}
            return cls(**{k: v for k, v in data.items() if k in fields})
        return cls()
    # save() uses dataclasses.asdict() — picks up new fields automatically
```

### Infinite loop playback engine change
```python
# In PlaybackEngine._run — replace: for _ in range(repeat):
iteration = 0
while True:
    if repeat != -1 and iteration >= repeat:
        break
    if self._stop_event.is_set():
        return
    # ... existing inner loop body unchanged ...
    iteration += 1
# Signal done
if self._on_progress:
    self._on_progress(len(blocks), len(blocks))
```

### Toolbar play signal with repeat support
```python
# In ToolbarPanel
def _on_play_clicked(self) -> None:
    repeat = -1 if self._chk_infinite.isChecked() else self._spin_repeat.value()
    self.play_requested.emit(self._speed_spin.value(), repeat)
```

### HotkeyManager drain with record_here
```python
def _drain(self) -> None:
    while not self._hotkey_queue.empty():
        try:
            action = self._hotkey_queue.get_nowait()
        except queue.Empty:
            break
        if action == "start_record":
            self.start_record.emit()
        elif action == "stop_record":
            self.stop_record.emit()
        elif action == "start_play":
            self.start_play.emit()
        elif action == "stop_play":
            self.stop_play.emit()
        elif action == "record_here":   # NEW
            self.record_here.emit()
```

---

## Open Questions

1. **Tray icon asset**
   - What we know: `QSystemTrayIcon` accepts any `QIcon`; a solid-color `QPixmap` works
   - What's unclear: Should there be a distinct "idle" icon vs the generic Qt icon?
   - Recommendation: Use a simple programmatically-generated colored circle (gray = idle, red = recording). No image asset needed.

2. **Progress bar during infinite loop**
   - What we know: `set_playback_progress(index, total)` currently auto-stops when `index >= total`
   - What's unclear: On the last block of one pass in infinite mode, `index == total` would trigger `_stop_play()`
   - Recommendation: In `_update_status`, only call `_stop_play()` on `idx >= total` when the engine is *actually done* (not still looping). Simplest fix: engine sends `on_progress(len(blocks), len(blocks))` only after the final pass. During intermediate passes, send `on_progress(i+1, len(blocks))` but never `(total, total)` unless done. Alternatively: toolbar progress bar shows `(block_in_pass / total)` without auto-stop logic; auto-stop uses a separate `on_done` callback.
   - The planner should pick one approach and specify it.

3. **`play_requested` signal type with `-1` repeat**
   - What we know: Signal is declared as `pyqtSignal(float, int)` — `-1` is a valid `int`
   - What's unclear: Nothing — this works fine in PyQt6
   - Recommendation: No change needed.

---

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/macro_thunder/` — all patterns derived directly from working code
- Python stdlib docs: `winsound.Beep(frequency, duration)` — Windows-only, no install needed
- PyQt6 docs: `QSystemTrayIcon`, `QTabWidget`, `QSpinBox`, `QCheckBox`, `QComboBox` — standard widgets used throughout existing codebase

### Secondary (MEDIUM confidence)
- pynput `GlobalHotKeys` empty-key behavior: verified by reading existing `HotkeyManager.register()` which already guards against bad hotkey strings via try/except in `MainWindow._open_settings`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns are extensions of existing code
- Architecture: HIGH — all patterns follow existing queue/signal conventions exactly
- Pitfalls: HIGH — derived from existing code analysis + known PyQt6/pynput constraints in CLAUDE.md

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable stack, no fast-moving dependencies)
