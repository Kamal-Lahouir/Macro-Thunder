# Phase 4: Flow Control and Window Management - Research

**Researched:** 2026-03-02
**Domain:** PyQt6 editor extensions, Win32 window management via ctypes, playback executor flow control
**Confidence:** HIGH

## Summary

Phase 4 adds three independent capability clusters to an already-working macro editor: (1) Label/Goto blocks for looping and branching in playback, (2) pre-playback validation that detects missing targets and infinite loops, and (3) a WindowFocus action block with an interactive click-picker for targeting the correct window before coordinate-dependent actions.

The data model already declares `LabelBlock`, `GotoBlock`, and `WindowFocusBlock` as full `ActionBlock` types — they exist in `blocks.py`, are serializable, and appear in `BlockTypeDialog`. The playback engine already silently skips them (Phase 2 comment: "no-op (Phase 4)"). The view model already renders them in the table with value strings. Phase 4 is therefore primarily: (a) making the engine actually execute them, (b) adding validation before playback starts, (c) adding a rich editor panel for `WindowFocusBlock`, and (d) building the click-picker.

**pywin32 is NOT installed** on the active Python 3.14 runtime. All Win32 APIs must use `ctypes` exclusively. Verified working: `EnumWindows`, `WindowFromPoint`, `GetAncestor`, `GetWindowTextW`, `GetWindowThreadProcessId`, `QueryFullProcessImageNameW`, `SetForegroundWindow`, `ShowWindow (SW_RESTORE)`, `SetWindowPos`, `LoadCursorW`.

**Primary recommendation:** Use ctypes for all Win32 calls (no pywin32 dependency). Split the feature into engine work (flow control + WindowFocus execution) and UI work (editor panel + click-picker) as separate implementation waves.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Label/Goto UX**
- Goto block has a text field — user types the target label name (no dropdown)
- Labels and Gotos can be inserted anywhere in the block list, no placement restrictions (forward and backward jumps both supported)
- Label and Goto blocks have a distinct visual style: different background color (muted purple/indigo) and clear icons (flag for Label, arrow for Goto) to make flow structure scannable
- Missing label error: shown as a dialog before playback starts, listing the missing label names; playback does not start until fixed

**Loop Detection**
- On infinite loop detection: warn and stop playback (no "continue anyway" option)
- Detection strategy: execution count threshold — if the same Goto fires more than 1000 times without any non-flow-control block executing in between, it's a stuck loop
- Error message names the specific label: "Infinite loop detected at '[Label Name]' — execution stopped. Check your Goto blocks."
- After stopping, the offending Goto block is selected/highlighted in the block list so the user can find it immediately

**Window Focus Block — Failure and Success Handling**
- Failure config (timeout duration + fallback label) is in the block's editor panel — two fields: "Timeout (seconds)" and "On failure: go to [label name]"
- Success path is configurable in the panel: defaults to "Next", user can override with a label name to jump elsewhere on success
- Reposition/resize fields (X, Y, W, H) are hidden behind a "Reposition window" checkbox — collapsed by default, revealed when checked
- During the timeout wait, poll for the window every ~500ms; if the window appears early, continue immediately rather than waiting the full duration

**Window Picker Interaction**
- Picker triggered by a "Select Window..." button in the WindowFocus block panel
- When active: Macro Thunder minimizes and cursor changes to crosshair; user clicks their target window; app restores and fills in the fields
- Auto-fills: executable name + window title from the clicked window's process info; matching mode defaults to "Contains"
- "Select Window..." button stays available after filling — clicking again re-picks and overwrites current fields

### Claude's Discretion
- Exact color values for Label/Goto block styling (must fit existing dark theme)
- Icon choices for Label (flag) and Goto (arrow) — exact icon source
- Polling interval implementation details
- Windows API calls for window enumeration and process name extraction

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FLOW-01 | User can insert a Label block anywhere in the macro | Data model already exists. Editor already supports insertion. Needs distinct visual style (color + icon) in `BlockDelegate`/`view_model`. |
| FLOW-02 | User can insert a Goto block that jumps execution to any label | Data model already exists. Engine needs a flow-control execution path (index-based jump). Needs distinct visual style matching Label. |
| FLOW-03 | Playback executor validates all Goto targets exist before execution begins | Pre-flight validation function: scan blocks for GotoBlocks, check each `target` against LabelBlock `name` values. Show `QMessageBox` listing missing names. |
| FLOW-04 | Infinite loop detection — executor detects goto loops with no progress and surfaces a warning | Per-Goto counter dict keyed by flat index; reset when a non-flow-control block executes. Threshold = 1000. Stop + signal offending index back to UI via queue. |
| WIN-01 | User can insert a Window Focus action block specifying target executable name and window title | Data model (`WindowFocusBlock`) exists with `executable`, `title`, `match_mode`. Needs extension: add `timeout`, `on_failure_label`, `on_success_label`, `reposition`, `x`, `y`, `w`, `h` fields. |
| WIN-02 | Window title matching supports three modes: Contains, Exact, Starts With | Pure Python string matching. Three-way branch in window search function. |
| WIN-03 | User can use an interactive "Select Window..." picker — click on a running window to fill the fields | ctypes `pynput` global mouse hook (or `QApplication.overrideCursor` + QEvent filter + `WindowFromPoint`). Requires minimize-before-pick, restore-after. |
| WIN-04 | On success: optionally set window position (X, Y) and size (W, H) | `SetWindowPos` via ctypes (verified working). Hidden behind "Reposition window" checkbox. |
| WIN-05 | On success: flow continues to "Next" or a named label | Configurable `on_success_label` field on block. Engine checks after successful focus. |
| WIN-06 | On failure: wait N seconds, then jump to a named label | `timeout` + `on_failure_label` fields. Engine polls every 500ms; on timeout fires goto logic. |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt6 | >=6.4 (6.10.2 installed) | All UI — new editor panel, dialogs, delegate styling | Already the project UI stack |
| ctypes (stdlib) | Python 3.14 stdlib | Win32 API calls — EnumWindows, WindowFromPoint, SetForegroundWindow, SetWindowPos, QueryFullProcessImageNameW | pywin32 NOT installed; ctypes confirmed working for all required APIs |
| pynput | 1.8.1 (installed) | Global mouse listener for the click-picker event | Already installed; avoids raw Win32 hook setup |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `os.path.basename` (stdlib) | — | Extract `.exe` name from full path returned by `QueryFullProcessImageNameW` | In window picker, after resolving the full image path |
| `threading.Event` (stdlib) | — | Signals between window-picker listener thread and Qt main thread | Picker needs cross-thread cancel/complete signaling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ctypes | pywin32 | pywin32 not installed, Python 3.14 pip install likely works but adds a new dependency; ctypes covers everything needed |
| pynput global mouse hook for picker | Win32 `SetWindowsHookEx(WH_MOUSE_LL)` via ctypes | pynput already present and abstracts the hook; avoids second raw hook implementation |
| QTimer polling for window focus wait | `threading.Event` + busy poll in engine thread | QTimer is main-thread only; engine runs on background thread; use `threading.Event.wait(timeout=0.5)` in engine loop |

**Installation:** No new packages required. All needed libraries are stdlib ctypes or already-installed pynput.

---

## Architecture Patterns

### Recommended Project Structure

New files this phase:

```
src/macro_thunder/
    engine/
        __init__.py         # extend PlaybackEngine: flow control + WindowFocus dispatch
    ui/
        window_picker.py    # WindowPickerService: minimize/crosshair/click/restore
        block_panels.py     # (new) per-block-type editor panels for Label, Goto, WindowFocus
    models/
        blocks.py           # extend WindowFocusBlock with timeout/label/reposition fields
tests/
    test_flow_control.py    # FLOW-01..04: validation, loop detection, executor behavior
    test_window_focus.py    # WIN-01..06: matching, timeout, reposition logic
```

### Pattern 1: Flow Control Execution in PlaybackEngine

**What:** Replace the `for i, block in enumerate(blocks)` sequential loop with an index-controlled `while` loop that supports arbitrary jumps.

**When to use:** Whenever Goto/Label/WindowFocus need to redirect execution.

```python
# Replace current for-loop in _run():
i = 0
goto_fire_count: dict[int, int] = {}  # flat_index -> consecutive fire count
progress_since_last_goto = False

while i < len(blocks):
    if self._stop_event.is_set():
        return

    block = blocks[i]

    if isinstance(block, LabelBlock):
        progress_since_last_goto = True  # labels count as progress
        i += 1
        continue

    if isinstance(block, GotoBlock):
        # Loop detection
        count = goto_fire_count.get(i, 0) + 1
        if progress_since_last_goto:
            goto_fire_count.clear()
            count = 1
        goto_fire_count[i] = count
        progress_since_last_goto = False

        if count > 1000:
            if self._on_loop_detected:
                self._on_loop_detected(i, block.target)
            return

        # Find target label
        target_idx = label_index.get(block.target)
        if target_idx is None:
            # Should not happen (validated pre-flight) but fail-safe
            return
        i = target_idx
        continue

    progress_since_last_goto = True
    goto_fire_count.clear()
    # ... timing + dispatch as before
    i += 1
```

Build `label_index: dict[str, int]` once before the loop:
```python
label_index = {
    b.name: idx
    for idx, b in enumerate(blocks)
    if isinstance(b, LabelBlock)
}
```

### Pattern 2: Pre-Flight Validation

**What:** Standalone function, testable without Qt, called from `MainWindow._start_play` before `engine.start()`.

```python
# src/macro_thunder/engine/validation.py

def validate_gotos(blocks) -> list[str]:
    """Return list of missing label names, empty if all gotos resolve."""
    labels = {b.name for b in blocks if isinstance(b, LabelBlock)}
    missing = []
    seen = set()
    for b in blocks:
        if isinstance(b, GotoBlock) and b.target not in labels:
            if b.target not in seen:
                missing.append(b.target)
                seen.add(b.target)
    return missing
```

Call in `MainWindow._start_play`:
```python
missing = validate_gotos(self._macro_buffer.blocks)
if missing:
    QMessageBox.critical(self, "Missing Labels",
        "Cannot play: the following labels are not defined:\n" +
        "\n".join(f"  • {m}" for m in missing))
    return
```

### Pattern 3: WindowFocus Execution

**What:** Inside the `while` loop, handle `WindowFocusBlock` as a blocking wait on the engine thread.

```python
if isinstance(block, WindowFocusBlock):
    deadline = time.perf_counter() + block.timeout
    found_hwnd = None
    while time.perf_counter() < deadline:
        found_hwnd = _find_window(block.executable, block.title, block.match_mode)
        if found_hwnd:
            break
        self._stop_event.wait(timeout=0.5)  # poll interval, respects stop
        if self._stop_event.is_set():
            return

    if found_hwnd:
        _activate_window(found_hwnd)
        if block.reposition and block.w > 0 and block.h > 0:
            _set_window_rect(found_hwnd, block.x, block.y, block.w, block.h)
        # Success path
        if block.on_success_label and block.on_success_label in label_index:
            i = label_index[block.on_success_label]
        else:
            i += 1
    else:
        # Failure path — jump to failure label
        if block.on_failure_label and block.on_failure_label in label_index:
            i = label_index[block.on_failure_label]
        else:
            i += 1  # no label configured: continue anyway
    continue
```

### Pattern 4: Window Picker Service

**What:** A service object owned by `MainWindow` that encapsulates the minimize/crosshair/click/restore cycle.

**How the picker works:**
1. `MainWindow.showMinimized()` hides the app
2. A pynput `mouse.Listener` is started to capture ONE click
3. `QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)` — but since the app is minimized this is mainly cosmetic; the system cursor should change globally using `SetCursor(LoadCursorW(0, IDC_CROSS))` via ctypes
4. On click: `WindowFromPoint(cursor_pos)` → `GetAncestor(hwnd, GA_ROOT)` → title + exe extraction
5. Stop listener, restore app (`MainWindow.showNormal()` + `activateWindow()`)
6. Emit a signal with `(executable: str, title: str)` to fill the panel

```python
# src/macro_thunder/ui/window_picker.py
import ctypes, ctypes.wintypes, os
from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal

IDC_CROSS = 32515

class WindowPickerService(QObject):
    picked = pyqtSignal(str, str)  # (executable, title)
    cancelled = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._listener = None

    def start(self):
        self._main_window.showMinimized()
        user32 = ctypes.windll.user32
        hcursor = user32.LoadCursorW(0, IDC_CROSS)
        user32.SetCursor(hcursor)

        def on_click(x, y, button, pressed):
            if pressed:
                self._on_pick(x, y)
                return False  # stop listener

        self._listener = mouse.Listener(on_click=on_click)
        self._listener.start()

    def _on_pick(self, x, y):
        hwnd = _hwnd_from_point(x, y)
        title, exe = _get_window_info(hwnd) if hwnd else ("", "")
        self._main_window.showNormal()
        self._main_window.activateWindow()
        if exe or title:
            self.picked.emit(exe, title)
        else:
            self.cancelled.emit()
```

**Threading note:** `_on_pick` is called from the pynput listener thread. `pyqtSignal.emit()` is thread-safe in PyQt6 (queued connection across thread boundary when receiver is in a different thread). This matches the established queue pattern already used in the project.

### Pattern 5: WindowFocusBlock Data Model Extension

The current `WindowFocusBlock` only has `executable`, `title`, `match_mode`. It needs extension:

```python
@dataclass
class WindowFocusBlock:
    executable: str
    title: str
    match_mode: str          # "Contains" | "Exact" | "Starts With"
    timeout: float = 5.0     # seconds to wait
    on_failure_label: str = ""
    on_success_label: str = ""  # empty = "Next"
    reposition: bool = False
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    type: Literal["WindowFocus"] = field(default="WindowFocus", init=False)
```

All new fields have defaults, so existing saved macros with just `executable`/`title`/`match_mode` will still deserialize correctly via `block_from_dict` (missing kwargs use defaults).

### Pattern 6: Label/Goto Visual Styling in BlockDelegate

The existing `BlockDelegate` does not override `paint()` — it relies on `data(DisplayRole)` text. To achieve distinct background color for Label/Goto rows, the cleanest approach is to return a `QBrush` from `data(Qt.ItemDataRole.BackgroundRole)` in `BlockTableModel.data()`:

```python
# In BlockTableModel.data():
if role == Qt.ItemDataRole.BackgroundRole:
    if isinstance(row_obj, BlockRow):
        block = self._doc.blocks[row_obj.flat_index]
        if isinstance(block, (LabelBlock, GotoBlock)):
            return QBrush(QColor(60, 50, 90))  # muted indigo — exact value: Claude's discretion
    return None
```

For icons, Qt provides `QStyle.StandardPixmap` but a simpler approach is Unicode prefix characters already used for group arrows: prepend "🏁 " for Label and "→ " for Goto in `_block_value()`. Since the existing code already uses `→` for GotoBlock (`f"→ {block.target}"`) and `COL_TYPE` returns `block.type` as a bare string, the type column text for Label/Goto could include the icon character.

### Anti-Patterns to Avoid

- **Modifying `blocks` structure for flow control:** The flat list must remain flat. Flow control is purely an execution-time index pointer, not a data structure change.
- **`time.sleep()` in WindowFocus wait:** Use `self._stop_event.wait(timeout=0.5)` instead. This respects the stop signal immediately.
- **Qt objects from engine thread:** Engine callbacks (loop detection, progress) must go through `queue.Queue` + `QTimer` drain. Same pattern as existing `on_progress`.
- **`SetForegroundWindow` without `ShowWindow` first:** If the target window is minimized, `SetForegroundWindow` alone will not restore it. Call `ShowWindow(hwnd, SW_RESTORE)` first.
- **Using `SetForegroundWindow` when macro thunder is not the foreground process:** This API has OS-level restrictions — it silently fails if the calling process is not the current foreground process. Call `AllowSetForegroundWindow(ASFW_ANY)` before handing control to the engine thread, OR use `AttachThreadInput` + `BringWindowToTop`. The most reliable pattern: `ShowWindow(SW_RESTORE)` → `SetForegroundWindow` → `BringWindowToTop`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Global mouse click capture for window picker | Raw `SetWindowsHookEx(WH_MOUSE_LL)` via ctypes | `pynput.mouse.Listener` | pynput already installed, abstracts the low-level hook, handles thread lifecycle, already pattern-matched in project |
| Window title/exe matching | Complex regex or fuzzy match | Simple str methods: `in`, `==`, `.startswith()` | Requirements specify exactly three modes; no fuzzy matching needed |
| Loop detection algorithm | Graph cycle analysis, DFS | Execution count threshold (counter dict) | Simpler, covers the practical case of runaway loops, user-decided threshold = 1000 |

---

## Common Pitfalls

### Pitfall 1: SetForegroundWindow Silently Fails
**What goes wrong:** After the WindowFocus block finds the target window, `SetForegroundWindow()` returns non-zero (success) but the window does not actually come to foreground.
**Why it happens:** Windows restricts which processes can steal focus. If the calling process has not been in the foreground recently (which is true during macro playback), the OS silently flashes the taskbar button instead.
**How to avoid:** Call `AllowSetForegroundWindow(ASFW_ANY)` from the main thread before starting the playback engine. OR use the `AttachThreadInput` pattern: get the foreground window's thread ID, attach to it, then call `SetForegroundWindow`, then detach.
**Warning signs:** Window taskbar button flashes but window does not raise.

```python
# Reliable foreground activation pattern:
SW_RESTORE = 9
user32.ShowWindow(hwnd, SW_RESTORE)
fg_hwnd = user32.GetForegroundWindow()
fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
this_tid = kernel32.GetCurrentThreadId()
if fg_tid != this_tid:
    user32.AttachThreadInput(this_tid, fg_tid, True)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    user32.AttachThreadInput(this_tid, fg_tid, False)
else:
    user32.SetForegroundWindow(hwnd)
```

### Pitfall 2: Window Picker Click Captured by Wrong Window
**What goes wrong:** User tries to click the target window but accidentally clicks on a child widget (e.g., a toolbar button), getting a child HWND instead of the top-level window.
**Why it happens:** `WindowFromPoint` returns the deepest child HWND, not the top-level.
**How to avoid:** Always call `GetAncestor(hwnd, GA_ROOT)` (GA_ROOT = 2) to walk up to the top-level window.

### Pitfall 3: Crosshair Cursor Not Applied System-Wide
**What goes wrong:** `QApplication.setOverrideCursor(CrossCursor)` only affects Qt windows. After minimizing Macro Thunder, the cursor reverts to the default pointer.
**Why it happens:** Qt's cursor override only applies while the Qt application has mouse capture.
**How to avoid:** Use `ctypes.windll.user32.SetCursor(LoadCursorW(0, IDC_CROSS))` to set the Win32 system cursor directly. Note: this must be called from the thread that owns the cursor context, and the cursor will reset on the next `WM_SETCURSOR` message. The simplest pattern is to set it in the pynput callback thread right before or after minimizing, or to let pynput's underlying hook handle it naturally.
**Practical note:** The crosshair cursor requirement is cosmetic UX feedback. If it does not persist system-wide reliably, a fallback of showing a tooltip or notification ("Click target window...") is acceptable.

### Pitfall 4: Serialization Breaks on WindowFocusBlock Field Addition
**What goes wrong:** Adding new fields (`timeout`, `on_failure_label`, etc.) to `WindowFocusBlock` breaks loading of existing saved macros that only have the original three fields.
**Why it happens:** `block_from_dict` calls `cls(**kwargs)` after removing `type`. If saved JSON lacks the new fields, Python raises `TypeError: __init__() missing keyword argument`.
**How to avoid:** All new fields MUST have default values in the dataclass definition. Verified: Python dataclasses with `field(default=...)` resolve this correctly.

### Pitfall 5: Label Index Built Outside Repeat Loop
**What goes wrong:** If `label_index` is built once outside the `for _ in range(repeat)` loop, it remains valid across repeats (blocks don't change). This is correct. But if blocks were mutated during playback, it would be stale.
**Why it happens:** N/A in this design (blocks are immutable during playback).
**How to avoid:** Build `label_index` once per `start()` call, inside `_run()` but outside the repeat loop.

### Pitfall 6: pynput Listener in Picker Not Stopped on App Close
**What goes wrong:** If the user closes the app while the window picker is active, the pynput listener thread stays alive.
**Why it happens:** `mouse.Listener` is a daemon thread but may delay GC.
**How to avoid:** `WindowPickerService.cancel()` method that calls `self._listener.stop()`. Connect to `MainWindow.closeEvent`.

---

## Code Examples

Verified patterns from ctypes testing on this machine:

### EnumWindows + QueryFullProcessImageNameW
```python
import ctypes, ctypes.wintypes, os

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def _get_visible_windows() -> list[tuple[int, str, str]]:
    """Return list of (hwnd, exe_basename, title) for visible top-level windows."""
    results = []
    def _cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        if not title:
            return True
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        exe = ""
        h = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if h:
            size = ctypes.wintypes.DWORD(512)
            path_buf = ctypes.create_unicode_buffer(512)
            if kernel32.QueryFullProcessImageNameW(h, 0, path_buf, ctypes.byref(size)):
                exe = os.path.basename(path_buf.value)
            kernel32.CloseHandle(h)
        results.append((hwnd, exe, title))
        return True
    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return results
```

### Finding a Window by Executable + Title
```python
def _find_window(executable: str, title: str, match_mode: str) -> int | None:
    """Return hwnd of first matching visible window, or None."""
    exe_lower = executable.lower()
    title_lower = title.lower()
    for hwnd, exe, win_title in _get_visible_windows():
        exe_match = (not exe_lower) or (exe_lower in exe.lower())
        wt_lower = win_title.lower()
        if match_mode == "Contains":
            title_match = title_lower in wt_lower
        elif match_mode == "Exact":
            title_match = title_lower == wt_lower
        elif match_mode == "Starts With":
            title_match = wt_lower.startswith(title_lower)
        else:
            title_match = title_lower in wt_lower
        if exe_match and title_match:
            return hwnd
    return None
```

### Activating a Window (reliable pattern)
```python
def _activate_window(hwnd: int) -> None:
    SW_RESTORE = 9
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.ShowWindow(hwnd, SW_RESTORE)
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    this_tid = kernel32.GetCurrentThreadId()
    if fg_tid and fg_tid != this_tid:
        user32.AttachThreadInput(this_tid, fg_tid, True)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        user32.AttachThreadInput(this_tid, fg_tid, False)
    else:
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
```

### SetWindowPos (reposition + resize)
```python
def _set_window_rect(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010
    ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)
```

### WindowFromPoint for picker
```python
def _hwnd_from_point(x: int, y: int) -> int:
    GA_ROOT = 2
    user32 = ctypes.windll.user32
    pt = ctypes.wintypes.POINT(x, y)
    hwnd = user32.WindowFromPoint(pt)
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return root if root else hwnd
```

### Label/Goto background color in BlockTableModel.data()
```python
# In BlockTableModel.data(), add BackgroundRole handling:
if role == Qt.ItemDataRole.BackgroundRole:
    if isinstance(row_obj, BlockRow):
        block = self._doc.blocks[row_obj.flat_index]
        if isinstance(block, (LabelBlock, GotoBlock)):
            from PyQt6.QtGui import QBrush, QColor
            return QBrush(QColor(55, 45, 80))  # muted indigo — adjust to taste
return None
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pywin32 for Win32 API access | ctypes stdlib | Always an option; pywin32 simply not installed | No new dependency needed |
| `for i, block in enumerate(blocks)` sequential loop | `while i < len(blocks)` with index manipulation | Phase 4 | Enables jumps without restructuring the block list |

---

## Open Questions

1. **SetForegroundWindow reliability under game conditions**
   - What we know: Works reliably in normal desktop conditions. The `AttachThreadInput` workaround is well-established.
   - What's unclear: Games running in exclusive fullscreen may not respond to `SetForegroundWindow` at all (OS-level limitation).
   - Recommendation: Document as a known limitation in the UI. "Window focus may not work with exclusive fullscreen games." This matches the existing "Out of Scope" note about DirectInput/RawInput.

2. **Crosshair cursor system-wide persistence**
   - What we know: `SetCursor` sets the cursor but the next `WM_SETCURSOR` message from any window resets it.
   - What's unclear: Whether the cursor will visibly be a crosshair for long enough during the pick.
   - Recommendation: Show a small non-modal overlay or status bar message ("Click the target window...") as primary UX feedback; crosshair is best-effort.

3. **WindowFocusBlock panel — where does it live?**
   - What we know: Current editor has no per-block-type detail panel. Block editing is inline in the table (click cell, edit value).
   - What's unclear: Whether to add a detail panel below/beside the table, or use a dialog opened by double-clicking a WindowFocus row.
   - Recommendation: Add a `DetailPanel` QWidget that appears at the bottom of `EditorPanel` when a WindowFocus/Label/Goto block is selected. This is consistent with the "editor panel" pattern established in the CONTEXT.md ("in the block's editor panel — two fields"). The panel replaces/augments the table's inline editing for complex blocks.

---

## Validation Architecture

Not included — `workflow.nyquist_validation` not present in config.json (feature not enabled).

---

## Sources

### Primary (HIGH confidence)
- ctypes stdlib — verified live on project runtime (Python 3.14.0, Windows 10/11). All Win32 APIs confirmed working with direct code execution.
- PyQt6 6.10.2 installed — `BackgroundRole`, `QBrush`, `QColor`, `pyqtSignal` cross-thread behavior verified by project's existing patterns.
- Project source code — `blocks.py`, `engine/__init__.py`, `ui/view_model.py`, `ui/editor_panel.py` read directly.

### Secondary (MEDIUM confidence)
- SetForegroundWindow + AttachThreadInput pattern — widely documented Win32 behavior, consistent across multiple MSDN-adjacent sources. Confirmed via direct API availability test.
- pynput cross-thread signal safety — established pattern in project (existing `queue.Queue` bridge for recorder). pynput mouse.Listener confirmed installed (1.8.1).

### Tertiary (LOW confidence)
- Crosshair cursor via `SetCursor` persistence: behavior observed in test but not formally benchmarked in a game environment.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified live on actual runtime; no new dependencies needed
- Architecture: HIGH — engine loop refactor is mechanical; Win32 APIs confirmed working
- Pitfalls: HIGH for SetForegroundWindow (well-known); MEDIUM for crosshair cursor persistence (observed but not benchmarked)

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable Win32 APIs, stable PyQt6)
