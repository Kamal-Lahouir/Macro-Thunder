# Phase 2: Record and Play - Research

**Researched:** 2026-02-26
**Domain:** pynput input capture + PyQt6 UI state + perf_counter playback engine
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Recording controls**
- Record and Stop buttons live in the **toolbar at the top of the main window**
- While recording: **red blinking indicator + live block count** displayed in toolbar/status area
- On Stop: recording goes to a **temp buffer in memory** — user manually saves via File > Save (no auto-save, no immediate filename prompt)
- Recording captures **both mouse and keyboard** (full macro: moves, clicks, scrolls, key press/release)

**Playback controls**
- Play and Stop buttons are **distinct buttons in the same toolbar** as Record (not a toggle, not a separate panel)
- Speed control: **numeric input (0.1x–5.0x)** with preset shortcut buttons (0.5x, 1x, 2x)
- During playback: **progress bar + block index / total** (e.g. "Playing: 42 / 180 blocks")
- User **can play directly from the unsaved temp buffer** — no save required before playback

**Global stop hotkey (F8)**
- Default stop-playback key: **F8**, always registered on app startup
- F8 behavior: halts after the currently in-flight event completes, next event is cancelled
- F8 **does not** cancel recording — recording has its own Stop button in the toolbar
- F8 is active even when the macro app itself has focus
- When nothing is playing and F8 is pressed: **silently ignored**
- After F8 stops playback: UI **immediately resets to idle** (buttons re-enable, progress clears)

**Configurable hotkeys**
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

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REC-01 | User can start and stop recording via a button (and hotkey) | pynput.mouse.Listener + pynput.keyboard.Listener started/stopped from QThread; hotkeys via pynput.keyboard.GlobalHotKeys |
| REC-02 | Mouse movements captured with exact screen coordinates and timestamps | pynput on_move(x, y) callback; timestamp = time.perf_counter() - record_start |
| REC-03 | Mouse clicks (left, right, middle — down and up) are recorded | pynput on_click(x, y, button, pressed) — button is pynput.mouse.Button enum |
| REC-04 | Mouse scroll events are recorded (direction and amount) | pynput on_scroll(x, y, dx, dy) |
| REC-05 | Keyboard key presses (down and up) are recorded | pynput on_press(key) / on_release(key) — key is Key or KeyCode |
| REC-06 | Pixel threshold — mouse moves smaller than N pixels discarded during recording | Euclidean distance check against last recorded move position inside on_move callback |
| REC-07 | Recording does not capture own playback events (injected event filtering) | win32_event_filter with LLMHF_INJECTED flag (data.flags & 0x1) — see Architecture Patterns |
| PLAY-01 | Accurate timing playback (perf_counter-based) | Background thread; absolute targets via time.perf_counter(); time.sleep() for coarse wait + busy spin for final microseconds |
| PLAY-02 | Playback speed multiplier (0.5x, 1x, 2x) | Divide all inter-event delays by speed factor at dispatch time |
| PLAY-03 | Repeat count (run macro N times) | Loop counter in playback thread |
| PLAY-04 | Stop playback at any time via global hotkey (works even when another app has focus) | pynput GlobalHotKeys listener for F8; sets threading.Event; playback thread checks event between dispatches |
| PLAY-05 | Playback runs on background thread, does not freeze UI | Python threading.Thread wrapping playback loop; signals back to Qt via queue.Queue + QTimer drain |
</phase_requirements>

---

## Summary

Phase 2 builds the full recording + playback pipeline on top of the Phase 1 foundation. The technical scope is well-understood: pynput provides mouse and keyboard listeners (each a `threading.Thread`) and matching controller objects for injection. All pynput callbacks MUST NOT touch Qt objects — this is an existing project rule enforced through `queue.Queue` + `QTimer` drain. The playback engine runs on a plain `threading.Thread`, uses absolute `time.perf_counter()` targets (not per-event sleep), and communicates progress back to Qt via the same queue/timer pattern.

The most non-trivial requirement is REC-07: filtering the app's own injected playback events from the recording listener. On Windows, pynput exposes `win32_event_filter` with the raw `MSLLHOOKSTRUCT` and `KBDLLHOOKSTRUCT` data. The `LLMHF_INJECTED` flag (bit 0 of `data.flags`) is set by `SendInput` — which is what pynput's own Controller uses — making it a reliable filter signal. This approach is HIGH confidence and is the correct solution.

Global hotkeys (F8 and the configurable Start/Stop Record + Start Playback) use `pynput.keyboard.GlobalHotKeys` running as a daemon thread. Callbacks queue an event to the main thread for UI state changes. The playback stop signal additionally sets a `threading.Event` that the playback worker polls between events.

**Primary recommendation:** Use pynput listeners (mouse + keyboard in parallel) for capture, `win32_event_filter` LLMHF_INJECTED for REC-07, a plain `threading.Thread` + `time.perf_counter()` busy-spin for playback, `pynput.keyboard.GlobalHotKeys` for F8, and `queue.Queue` + `QTimer` for all cross-thread Qt updates.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pynput | >=1.7 (already in deps) | Mouse/keyboard capture and injection | Only Python library supporting both capture and inject with Windows low-level hooks |
| PyQt6 | >=6.4 (already in deps) | UI toolbar widgets, QTimer drain, progress bar | Already locked in Phase 1 |
| queue.Queue | stdlib | Thread-safe channel from pynput/playback threads to Qt main thread | Project rule; prevents Qt crashes from callback threads |
| threading.Thread | stdlib | Playback engine background thread | Lightweight; no Qt event loop needed in worker |
| time.perf_counter | stdlib | High-resolution absolute timing for playback | Project timing rule; monotonic, microsecond resolution |
| threading.Event | stdlib | Playback stop signal from hotkey → worker thread | Polling `.is_set()` between dispatches is safe and trivial |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses.asdict | stdlib | Serialize ActionBlock to dict for queue messages | When passing block data from recorder to Qt via queue |
| time.sleep | stdlib | Coarse wait in playback loop before busy-spin | When gap to next event > 2 ms; avoids 100% CPU for long delays |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| threading.Thread (playback) | QThread | QThread adds no value here — worker never touches Qt objects; plain thread is simpler |
| pynput GlobalHotKeys | keyboard library (pip) | pynput already in deps; keyboard library has no advantage; don't add a dependency |
| win32_event_filter LLMHF_INJECTED | boolean "is_playing" flag | Flag approach is a race condition; LLMHF_INJECTED is the Win32 ground truth |

**Installation:** No new packages required — pynput already declared in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure
```
src/macro_thunder/
    recorder/
        __init__.py        # RecorderService: start/stop, owns pynput listeners
    engine/
        __init__.py        # PlaybackEngine: start/stop, owns playback thread
    ui/
        toolbar.py         # ToolbarPanel (replace placeholder) — Record/Play buttons, progress, speed
        settings_dialog.py # Hotkey + threshold configuration dialog
```

The `engine/` directory already exists as an empty stub from Phase 1. The `recorder/` subdirectory is new.

### Pattern 1: Queue + QTimer Drain (already established, extend here)
**What:** pynput callbacks and playback progress signals are put to `queue.Queue`; a `QTimer` in the main thread drains it every 16 ms and updates Qt widgets.
**When to use:** Any time a non-Qt thread needs to trigger a UI update.
**Example:**
```python
# Source: project CLAUDE.md + STATE.md threading rule
import queue
from PyQt6.QtCore import QTimer

_event_queue: queue.Queue = queue.Queue()

# In pynput callback (background thread — NEVER touch Qt here):
def on_move(x, y):
    _event_queue.put(("move", x, y, time.perf_counter()))

# In Qt widget __init__:
self._drain_timer = QTimer(self)
self._drain_timer.setInterval(16)
self._drain_timer.timeout.connect(self._drain)
self._drain_timer.start()

def _drain(self):
    while not _event_queue.empty():
        event = _event_queue.get_nowait()
        self._handle_event(event)
```

### Pattern 2: RecorderService — pynput Listeners
**What:** A service class that owns and manages the pynput mouse and keyboard listeners. Starts both on `start()`, stops both on `stop()`. All captured events are timestamped with `time.perf_counter() - record_start` and pushed to a shared queue.
**Key API:**
```python
# Source: https://pynput.readthedocs.io/en/latest/mouse.html
from pynput import mouse, keyboard

# Mouse listener callbacks
def on_move(x, y): ...           # (x: int, y: int)
def on_click(x, y, button, pressed): ...  # button: mouse.Button
def on_scroll(x, y, dx, dy): ...

ml = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll,
                    win32_event_filter=_injected_filter)

# Keyboard listener callbacks
def on_press(key): ...    # key: keyboard.Key (special) or keyboard.KeyCode (char)
def on_release(key): ...

kl = keyboard.Listener(on_press=on_press, on_release=on_release,
                       win32_event_filter=_kb_injected_filter)

ml.start()
kl.start()
```

### Pattern 3: REC-07 — Injected Event Filtering via win32_event_filter
**What:** On Windows, any event injected by `SendInput` (used by pynput Controller) has `LLMHF_INJECTED` (bit 0) set in `data.flags` of `MSLLHOOKSTRUCT` / `KBDLLHOOKSTRUCT`. Returning `False` from the filter prevents the event from reaching the listener callbacks.
**Confidence:** HIGH — verified against MSLLHOOKSTRUCT Win32 docs and pynput issue tracker.
**Example:**
```python
# Source: Win32 MSLLHOOKSTRUCT docs + pynput issue #170
LLMHF_INJECTED = 0x00000001

def _injected_filter(msg, data):
    # If the event was injected (e.g. by our own pynput Controller during playback),
    # return False to skip it — prevents recording own playback events.
    if data.flags & LLMHF_INJECTED:
        return False
    return True

mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll,
    win32_event_filter=_injected_filter,
)
```
**Note:** The same pattern applies to `keyboard.Listener` with its own `win32_event_filter`. The keyboard struct equivalent is `KBDLLHOOKSTRUCT` and the flag constant is `LLKHF_INJECTED = 0x00000010` (bit 4, not bit 0). Verify this before coding — mouse and keyboard structs use different bit positions.

### Pattern 4: PlaybackEngine — perf_counter Timing Loop
**What:** Background thread iterates blocks in order. For each block, compute absolute target time = `playback_start + block.timestamp / speed`. Sleep until near that target, then busy-spin to land within ~0.1 ms.
**Confidence:** HIGH — project CLAUDE.md timing rule.
**Example:**
```python
# Source: CLAUDE.md Timing Rule
import time, threading

class PlaybackEngine:
    def __init__(self, on_progress):  # on_progress: called with (index, total) — via queue
        self._stop_event = threading.Event()

    def start(self, blocks, speed, repeat):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run,
                                        args=(blocks, speed, repeat), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self, blocks, speed, repeat):
        for _ in range(repeat):
            t0 = time.perf_counter()
            for i, block in enumerate(blocks):
                if self._stop_event.is_set():
                    return
                target = t0 + block.timestamp / speed
                # Coarse sleep
                remaining = target - time.perf_counter()
                if remaining > 0.002:
                    time.sleep(remaining - 0.002)
                # Busy-spin for precision
                while time.perf_counter() < target:
                    pass
                self._dispatch(block)
                # Signal progress via queue (NOT direct Qt call)
                _progress_queue.put((i + 1, len(blocks)))
```

### Pattern 5: GlobalHotKeys for F8 and Configurable Hotkeys
**What:** `pynput.keyboard.GlobalHotKeys` runs as a daemon thread, intercepts hotkeys system-wide regardless of focus.
**Key format:** `'<f8>'`, `'<ctrl>+<f1>'`, `'a'` etc. Stored as strings in settings JSON.
**Example:**
```python
# Source: https://pynput.readthedocs.io/en/latest/keyboard.html
from pynput import keyboard

hotkey_map = {
    '<f8>': self._on_stop_playback,
    '<f9>': self._on_start_record,
    '<f10>': self._on_stop_record,
    '<f6>': self._on_start_playback,
}
self._hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
self._hotkey_listener.daemon = True
self._hotkey_listener.start()
```
The `GlobalHotKeys` callbacks fire on the listener thread — use queue to communicate back to Qt.

### Pattern 6: Key Serialization for Settings Storage
**What:** pynput key strings use angle-bracket syntax for special keys: `'<f8>'`, `'<ctrl>+<shift>+a'`. This format is accepted directly by `HotKey.parse()` and `GlobalHotKeys`. Store in settings JSON as plain strings.
**Confidence:** MEDIUM — verified from official pynput docs examples.

### Anti-Patterns to Avoid
- **Direct Qt calls in pynput callbacks:** Crashes unpredictably on Windows (project CLAUDE.md rule). Use queue only.
- **time.sleep() only for playback timing:** Drifts under scheduler load (project timing rule). Must use perf_counter absolute targets.
- **Boolean "is_playing" flag for REC-07:** Race condition — the flag may be False when the injection event fires. Use `LLMHF_INJECTED` instead.
- **Stopping pynput listener from its own callback:** Raises `RuntimeError`. Always stop from a different thread or use `return False` from on_press/on_release to stop.
- **Sharing a single pynput listener for both recording and global hotkeys:** The GlobalHotKeys listener and the recorder listeners are separate objects and must remain separate.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Global hotkeys that work when app lacks focus | Custom Win32 SetWindowsHookEx wrapper | `pynput.keyboard.GlobalHotKeys` | pynput already handles hook lifecycle, thread management, key parsing |
| Mouse/keyboard injection for playback | ctypes SendInput directly | `pynput.mouse.Controller` + `pynput.keyboard.Controller` | Already handles Win32 INPUT struct, button mapping, key normalization |
| High-res timer loop | Custom async event scheduler | `time.perf_counter()` + `time.sleep()` + busy-spin | Sufficient for ~0.1ms precision; custom schedulers add complexity with no gain |
| Injected event detection | Process-level flag tracking | `win32_event_filter` + `LLMHF_INJECTED` | OS provides this exactly for this use case |

**Key insight:** pynput abstracts every Win32 input hook API needed for this phase. Nothing needs to be replaced.

---

## Common Pitfalls

### Pitfall 1: Qt Crash from pynput Callback Thread
**What goes wrong:** Code tries to update a QLabel or call `self.some_widget.setText()` from inside an `on_move` or `on_press` callback.
**Why it happens:** pynput listeners run on OS threads (not the Qt main thread). Qt widgets are not thread-safe.
**How to avoid:** Put a message on `queue.Queue`; a `QTimer` drains it on the main thread. This is an existing project rule.
**Warning signs:** Random segfaults or "QObject: Cannot create children for a parent that is in a different thread" errors.

### Pitfall 2: Recording Own Playback Events (REC-07 Missed)
**What goes wrong:** While recording is active AND playback is running (or both listeners are active), the injected mouse/keyboard events from the Controller get recorded as if they were real user input.
**Why it happens:** pynput's listener is a low-level hook — it sees ALL input including injected events.
**How to avoid:** Pass `win32_event_filter` that returns `False` when `data.flags & LLMHF_INJECTED`.
**Warning signs:** After playback, recorded macro has double the expected blocks; timestamps show microsecond-level spacing between events.

### Pitfall 3: Stopping a pynput Listener from Its Own Callback
**What goes wrong:** `RuntimeError: cannot join current thread` or deadlock.
**Why it happens:** Calling `listener.stop()` from within `on_press` attempts to join the listener's own thread.
**How to avoid:** `return False` from the callback to stop it, or queue a stop request for the main thread to call `listener.stop()`.

### Pitfall 4: Keyboard LLMHF_INJECTED vs Mouse LLMHF_INJECTED Bit Position
**What goes wrong:** Mouse filter works; keyboard filter silently fails to filter injected events.
**Why it happens:** Mouse uses `LLMHF_INJECTED = 0x1` (bit 0); keyboard `KBDLLHOOKSTRUCT` uses `LLKHF_INJECTED = 0x10` (bit 4). They are NOT the same constant.
**How to avoid:** Define both constants explicitly; use the correct one in each filter.
**Warning signs:** Keyboard events appear in macro even during playback.

### Pitfall 5: GlobalHotKeys Conflict with Recorder Listener
**What goes wrong:** Both `GlobalHotKeys` and `keyboard.Listener` (recorder) are running simultaneously. The hotkey callback may fire inside the recorder listener's thread scope, or key events may be double-processed.
**Why it happens:** They are separate listeners on the same keyboard hook. This is actually fine — pynput supports multiple simultaneous listeners — but callbacks from each run on separate threads, so no shared state should be used without locks or queue.
**How to avoid:** Keep them separate with no shared mutable state; use queues for all communication.

### Pitfall 6: Speed Multiplier Applied to Timestamps Incorrectly
**What goes wrong:** Playback at 2x takes just as long as 1x, or 0.5x is twice as fast as expected.
**Why it happens:** Dividing timestamp by speed is correct (higher speed = smaller delay = earlier target). Multiplying by speed is wrong.
**How to avoid:** `target = t0 + block.timestamp / speed` — dividing by speed gives the scaled absolute time.

### Pitfall 7: QProgressBar Range Not Set
**What goes wrong:** Progress bar shows nothing or stays full.
**Why it happens:** QProgressBar default range is 0–100. Setting value to 42 out of 180 blocks requires `setRange(0, 180)` first, or normalize to 0–100.
**How to avoid:** Call `progress_bar.setRange(0, total_blocks)` when playback starts; call `progress_bar.setValue(current_index)` on each update.

---

## Code Examples

Verified patterns from official sources:

### Mouse Listener with win32_event_filter (REC-07)
```python
# Source: https://pynput.readthedocs.io/en/latest/mouse.html + Win32 MSLLHOOKSTRUCT
from pynput import mouse
import time

LLMHF_INJECTED = 0x00000001
_record_start: float = 0.0
_event_queue = None  # queue.Queue set at runtime

def _mouse_injected_filter(msg, data):
    return not bool(data.flags & LLMHF_INJECTED)

def on_move(x, y):
    ts = time.perf_counter() - _record_start
    _event_queue.put(("MouseMove", x, y, ts))

def on_click(x, y, button, pressed):
    ts = time.perf_counter() - _record_start
    btn_str = button.name  # "left", "right", "middle"
    direction = "down" if pressed else "up"
    _event_queue.put(("MouseClick", x, y, btn_str, direction, ts))

def on_scroll(x, y, dx, dy):
    ts = time.perf_counter() - _record_start
    _event_queue.put(("MouseScroll", x, y, dx, dy, ts))

listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll,
    win32_event_filter=_mouse_injected_filter,
)
```

### Keyboard Listener (REC-05) with Key Serialization
```python
# Source: https://pynput.readthedocs.io/en/latest/keyboard.html
from pynput import keyboard

LLKHF_INJECTED = 0x00000010  # bit 4, different from mouse

def _kb_injected_filter(msg, data):
    return not bool(data.flags & LLKHF_INJECTED)

def _key_to_str(key) -> str:
    """Serialize pynput key to storable string."""
    if isinstance(key, keyboard.Key):
        return f"Key.{key.name}"   # e.g. "Key.shift", "Key.f8"
    elif hasattr(key, 'char') and key.char:
        return key.char            # e.g. "a", "1"
    else:
        return str(key)            # fallback

def on_press(key):
    ts = time.perf_counter() - _record_start
    _event_queue.put(("KeyPress", _key_to_str(key), "down", ts))

def on_release(key):
    ts = time.perf_counter() - _record_start
    _event_queue.put(("KeyPress", _key_to_str(key), "up", ts))

kb_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release,
    win32_event_filter=_kb_injected_filter,
)
```

### Playback Dispatch
```python
# Source: CLAUDE.md Timing Rule + pynput docs
from pynput import mouse as pmouse, keyboard as pkeyboard
from macro_thunder.models.blocks import (
    MouseMoveBlock, MouseClickBlock, MouseScrollBlock, KeyPressBlock
)

_mouse_ctrl = pmouse.Controller()
_kb_ctrl = pkeyboard.Controller()

def dispatch_block(block):
    if isinstance(block, MouseMoveBlock):
        _mouse_ctrl.position = (block.x, block.y)
    elif isinstance(block, MouseClickBlock):
        btn = getattr(pmouse.Button, block.button)
        if block.direction == "down":
            _mouse_ctrl.press(btn)
        else:
            _mouse_ctrl.release(btn)
    elif isinstance(block, MouseScrollBlock):
        _mouse_ctrl.scroll(block.dx, block.dy)
    elif isinstance(block, KeyPressBlock):
        key = _parse_key(block.key)
        if block.direction == "down":
            _kb_ctrl.press(key)
        else:
            _kb_ctrl.release(key)

def _parse_key(key_str: str):
    """Reverse of _key_to_str."""
    if key_str.startswith("Key."):
        return pkeyboard.Key[key_str[4:]]
    return pkeyboard.KeyCode.from_char(key_str)
```

### GlobalHotKeys Registration
```python
# Source: https://pynput.readthedocs.io/en/latest/keyboard.html
from pynput import keyboard
import queue

_hotkey_queue: queue.Queue = queue.Queue()

def _make_handler(action: str):
    def handler():
        _hotkey_queue.put(action)
    return handler

def register_hotkeys(bindings: dict[str, str]):
    """bindings: {"<f8>": "stop_playback", "<f9>": "start_record", ...}"""
    hotkey_map = {key: _make_handler(action) for key, action in bindings.items()}
    listener = keyboard.GlobalHotKeys(hotkey_map)
    listener.daemon = True
    listener.start()
    return listener
```

### Pixel Threshold Check (REC-06)
```python
import math

_last_move_x: int = 0
_last_move_y: int = 0
THRESHOLD_PX: int = 5  # configurable; planner decides where in UI

def on_move(x, y):
    global _last_move_x, _last_move_y
    dx = x - _last_move_x
    dy = y - _last_move_y
    if math.hypot(dx, dy) < THRESHOLD_PX:
        return  # discard sub-threshold move
    _last_move_x = x
    _last_move_y = y
    ts = time.perf_counter() - _record_start
    _event_queue.put(("MouseMove", x, y, ts))
```

### Blinking Record Indicator (QTimer-based)
```python
# Source: PyQt6 QTimer docs — QTimer periodic toggle
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel

class BlinkingIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__("●", parent)
        self._visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(500)  # 500ms on/off
        self._blink_timer.timeout.connect(self._toggle)

    def start_blinking(self):
        self._blink_timer.start()
        self.setStyleSheet("color: red;")

    def stop_blinking(self):
        self._blink_timer.stop()
        self.setStyleSheet("color: transparent;")

    def _toggle(self):
        self._visible = not self._visible
        self.setStyleSheet("color: red;" if self._visible else "color: transparent;")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| per-event time.sleep() for playback | perf_counter absolute targets | Project decision | Eliminates scheduler drift accumulation |
| PyAutoGUI for mouse/keyboard | pynput | Phase 1 stack lock | pynput supports low-level hooks; pyautogui doesn't |
| keyboard library for hotkeys | pynput GlobalHotKeys | Phase 1 stack lock | Single dependency, consistent API |

**Deprecated/outdated:**
- `pyautogui`: Not in stack; pynput preferred for hook-based capture.
- `Qt.AA_EnableHighDpiScaling`: Removed in Qt6 — do not use (CLAUDE.md).
- `event.pos()` / `event.globalPos()`: Removed in Qt6; use `event.position()` / `event.globalPosition()` (CLAUDE.md).

---

## Open Questions

1. **KBDLLHOOKSTRUCT LLKHF_INJECTED bit position for keyboard filter (REC-07)**
   - What we know: Mouse uses `LLMHF_INJECTED = 0x1` (bit 0); keyboard struct is different
   - What's unclear: The exact constant value for `LLKHF_INJECTED` in the keyboard struct — documented as bit 4 (`0x10`) in Win32 docs but not verified through pynput source directly
   - Recommendation: Verify against `pynput/keyboard/_win32.py` source before implementing the keyboard filter; if bit 4 is wrong, the filter silently fails

2. **Settings persistence format for hotkeys**
   - What we know: pynput HotKey.parse() accepts `'<f8>'` format strings; Key enum serializes as `'Key.f8'` in KeyPress blocks
   - What's unclear: Whether to store hotkey settings in the same macro JSON or a separate app-config JSON
   - Recommendation: Separate `settings.json` in the same directory as macros (Documents/MacroThunder/settings.json); hotkeys stored as pynput format strings (e.g. `"<f8>"`)

3. **Mouse threshold default value (REC-06)**
   - What we know: User wants configurable threshold; planner decides location
   - What's unclear: What default px value produces the best recording quality vs. smoothness tradeoff
   - Recommendation: Default 3px; range 0–20px; setting lives in a toolbar spinbox or the settings dialog (planner decides)

---

## Sources

### Primary (HIGH confidence)
- [pynput mouse docs](https://pynput.readthedocs.io/en/latest/mouse.html) — Listener callbacks, Controller API, win32_event_filter signature
- [pynput keyboard docs](https://pynput.readthedocs.io/en/latest/keyboard.html) — Listener callbacks, GlobalHotKeys, HotKey.parse, Key enum
- [MSLLHOOKSTRUCT Win32 docs](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-msllhookstruct) — LLMHF_INJECTED flag definition
- Project CLAUDE.md — Threading rule, timing rule, DPI rule, PyQt6 API notes
- Project STATE.md — Confirmed architecture decisions from Phase 1

### Secondary (MEDIUM confidence)
- [pynput issue #170 - Suppressing hotkey events](https://github.com/moses-palmer/pynput/issues/170) — win32_event_filter usage pattern for injected events verified with official docs
- [pynput PyPI](https://pypi.org/project/pynput/) — Version 1.7.6 is latest stable

### Tertiary (LOW confidence)
- Search result claim that keyboard LLKHF_INJECTED is bit 4 (0x10) — needs source code verification before relying on it

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pynput already in dependencies; all APIs verified in official docs
- Architecture: HIGH — queue+timer pattern already proven in Phase 1; perf_counter timing is a project rule
- Pitfalls: HIGH for threading pitfalls (known project rules); MEDIUM for KBDLLHOOKSTRUCT bit position (single source)

**Research date:** 2026-02-26
**Valid until:** 2026-09-01 (pynput 1.7.x is stable; PyQt6 APIs stable)
