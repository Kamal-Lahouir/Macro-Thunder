# Architecture Research

**Domain:** Python Windows desktop macro recorder and editor
**Researched:** 2026-02-25
**Confidence:** HIGH (architecture is derived from well-understood patterns for Qt model/view, threading with queues, and interpreter execution models; all design decisions are grounded in the confirmed stack from STACK.md)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          UI Layer (PyQt6, main thread)               │
├──────────────────┬──────────────────────┬───────────────────────────┤
│   MainWindow     │   MacroEditorWidget   │   MacroLibraryPanel       │
│  (shell, menus,  │  (QAbstractTableModel │  (list of saved macros,   │
│   toolbar, DPI)  │   + QTableView,       │   load/save/new/delete)   │
│                  │   block editor)       │                           │
├──────────────────┴──────────────────────┴───────────────────────────┤
│                     Application Controller Layer                     │
├──────────────┬──────────────────────┬──────────────────────────────┤
│  RecorderController  │  PlaybackController   │  MacroRepository        │
│  (start/stop record, │  (start/stop play,    │  (load/save JSON,       │
│   hotkey binding,    │   speed multiplier,   │   list macros,          │
│   threshold config)  │   loop count)         │   macro CRUD)           │
├──────────────┴──────────────────────┴──────────────────────────────┤
│                         Engine Layer                                 │
├──────────────────────────┬──────────────────────────────────────────┤
│     RecorderEngine       │          PlaybackEngine                   │
│  (pynput Listeners,      │  (reads MacroDocument, executes actions  │
│   runs on pynput thread, │   in a worker thread, emits progress     │
│   dispatches to queue)   │   signals, supports stop/pause)          │
└──────────────────────────┴──────────────────────────────────────────┘
                    ↕ (queue / Qt signals)              ↕ (Qt signals)
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Model Layer                             │
├──────────────────────────────────────────────────────────────────────┤
│   MacroDocument                                                      │
│     list[ActionBlock]                                                │
│       ActionBlock = MouseMove | MouseClick | Scroll | KeyPress |    │
│                     Delay | WindowFocus | Label | Goto | RunMacro   │
│                                                                      │
│   MoveGroup (virtual grouping of consecutive MouseMove blocks)       │
└──────────────────────────────────────────────────────────────────────┘
                    ↕ (read/write JSON)
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage Layer                                   │
│   macros/                                                            │
│     my_macro.json                                                    │
│     farm_run.json                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| MainWindow | Application shell: menus, toolbar, DPI awareness, hotkey registration (F9 record, F5 play, Escape stop) | MacroEditorWidget, MacroLibraryPanel, RecorderController, PlaybackController |
| MacroEditorWidget | Displays the MacroDocument as a block list; QAbstractTableModel drives QTableView; custom delegates for inline editing; handles block selection, reorder, insert, delete | MacroDocument (read/write), RecorderController (receive recorded blocks), PlaybackController (highlight active row) |
| MacroLibraryPanel | Lists saved macro files; triggers load/save/new/delete through MacroRepository | MacroRepository, MainWindow |
| RecorderController | Owns RecorderEngine lifecycle; translates raw recorded events into a MacroDocument; applies pixel threshold filtering and move-grouping; wires hotkeys | RecorderEngine (start/stop), MacroEditorWidget (deliver completed document), MacroDocument |
| PlaybackController | Owns PlaybackEngine lifecycle; configures speed multiplier and repeat count; receives stop/pause from UI; receives progress signals from engine | PlaybackEngine (start/stop/pause), MacroEditorWidget (current row highlight), MainWindow (status bar) |
| RecorderEngine | Runs pynput mouse + keyboard Listeners; puts raw events into a thread-safe queue; does NOT process events directly in callbacks | RecorderController (via queue) |
| PlaybackEngine | Runs in a QThread (or Python threading.Thread); reads MacroDocument sequentially; executes each ActionBlock; handles timing, speed multiplier, goto/label jumps; emits Qt signals for progress | PlaybackController (signals), Win32 APIs via pywin32 (for WindowFocus blocks) |
| MacroDocument | Passive data container; list of ActionBlock objects; serializes/deserializes to/from JSON | RecorderController (write), PlaybackEngine (read), MacroEditorWidget (read/write via model) |
| MacroRepository | File I/O only: enumerate macro files in the macros/ directory, load a macro JSON into a MacroDocument, save a MacroDocument to JSON | MacroDocument, MacroLibraryPanel, MacroEditorWidget |

---

## Threading Model

This is the most critical architectural decision. Two rules govern every threading choice:

**Rule 1: pynput callbacks must not block.**
pynput Listener callbacks run on a pynput-owned OS thread. Any blocking call (file I/O, GUI update, sleep) will stall input capture. All callback code must put events into a `queue.Queue` and return immediately.

**Rule 2: Qt UI must only be touched from the main thread.**
PyQt6 will crash or produce undefined behavior if widgets or models are modified from a worker thread. Cross-thread communication must go through Qt signals (which are thread-safe by design).

### Thread Map

```
Main Thread (Qt event loop)
    ├── MacroEditorWidget (QAbstractTableModel, QTableView)
    ├── MacroLibraryPanel
    ├── MainWindow
    └── All UI signal handlers

pynput Listener Thread (OS-managed, created by pynput)
    └── on_move / on_click / on_scroll / on_press / on_release callbacks
            ↓ (queue.put — non-blocking)
        raw_event_queue: queue.Queue

RecorderWorker Thread (QThread or threading.Thread)
    ├── Drains raw_event_queue
    ├── Applies pixel threshold filter
    ├── Builds ActionBlock objects
    └── Emits Qt signal: events_ready(list[ActionBlock])
            ↓ (Qt signal — crosses to main thread safely)
        RecorderController.on_events_ready()
            ↓
        MacroEditorWidget appends blocks to MacroDocument

PlaybackWorker Thread (QThread)
    ├── Reads MacroDocument (read-only after playback starts — no locking needed)
    ├── Executes actions sequentially with time.sleep for timing
    ├── Emits Qt signal: action_started(index: int)
    ├── Emits Qt signal: playback_finished()
    └── Checks a stop_event: threading.Event to abort mid-execution
            ↓ (Qt signals — crosses to main thread safely)
        PlaybackController → MacroEditorWidget.highlight_row(index)
```

### Why QThread over threading.Thread for PlaybackWorker

Use `QThread` for the PlaybackWorker so that Qt signal emission from the worker thread is automatically queued to the main thread's event loop. Using a plain `threading.Thread` that emits Qt signals requires manual `QMetaObject.invokeMethod` or wrapping signals in a `QObject`. QThread eliminates this complexity.

For the RecorderWorker, a plain `threading.Thread` is acceptable since it only puts events into a queue — it does not emit Qt signals directly. The RecorderController in the main thread polls the queue via a `QTimer` (10ms interval) and batches incoming events.

---

## Data Model

### ActionBlock Hierarchy

Each action in a macro is a typed dataclass. Using Python `dataclasses` with a `type` discriminant field makes JSON serialization and deserialization straightforward without a third-party schema library.

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class MouseMoveBlock:
    type: Literal["mouse_move"] = "mouse_move"
    x: int = 0
    y: int = 0
    timestamp_ms: int = 0        # relative to macro start

@dataclass
class MouseClickBlock:
    type: Literal["mouse_click"] = "mouse_click"
    x: int = 0
    y: int = 0
    button: str = "left"         # "left" | "right" | "middle"
    action: str = "press"        # "press" | "release"
    timestamp_ms: int = 0

@dataclass
class ScrollBlock:
    type: Literal["scroll"] = "scroll"
    x: int = 0
    y: int = 0
    dx: int = 0
    dy: int = 0
    timestamp_ms: int = 0

@dataclass
class KeyPressBlock:
    type: Literal["key_press"] = "key_press"
    key: str = ""                # e.g. "a", "Key.space", "Key.ctrl"
    action: str = "press"        # "press" | "release"
    timestamp_ms: int = 0

@dataclass
class DelayBlock:
    type: Literal["delay"] = "delay"
    duration_ms: int = 1000

@dataclass
class WindowFocusBlock:
    type: Literal["window_focus"] = "window_focus"
    exe_name: str = ""           # e.g. "notepad.exe"
    title: str = ""
    title_match: str = "contains"  # "contains" | "exact" | "starts_with"
    set_position: bool = False
    pos_x: int = 0
    pos_y: int = 0
    set_size: bool = False
    size_w: int = 0
    size_h: int = 0
    on_success_goto: str = "next"   # label name or "next"
    on_failure_wait_ms: int = 5000
    on_failure_goto: str = "end"    # label name or "end"

@dataclass
class LabelBlock:
    type: Literal["label"] = "label"
    name: str = ""               # unique within macro

@dataclass
class GotoBlock:
    type: Literal["goto"] = "goto"
    target: str = ""             # label name

@dataclass
class RunMacroBlock:
    type: Literal["run_macro"] = "run_macro"
    macro_name: str = ""         # filename without .json extension

ActionBlock = (MouseMoveBlock | MouseClickBlock | ScrollBlock | KeyPressBlock |
               DelayBlock | WindowFocusBlock | LabelBlock | GotoBlock | RunMacroBlock)

@dataclass
class MacroDocument:
    name: str = ""
    blocks: list[ActionBlock] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""
```

### JSON Serialization

Each dataclass serializes to a dict with a `type` field as the discriminant. Deserialization inspects `type` and instantiates the correct dataclass. No third-party library needed — `dataclasses.asdict()` + a `from_dict(d)` factory function.

```python
TYPE_MAP = {
    "mouse_move": MouseMoveBlock,
    "mouse_click": MouseClickBlock,
    "scroll": ScrollBlock,
    "key_press": KeyPressBlock,
    "delay": DelayBlock,
    "window_focus": WindowFocusBlock,
    "label": LabelBlock,
    "goto": GotoBlock,
    "run_macro": RunMacroBlock,
}

def block_from_dict(d: dict) -> ActionBlock:
    cls = TYPE_MAP[d["type"]]
    return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
```

---

## Mouse Movement Grouping

### The Problem

Raw pynput data for a 2-second drag produces 200–400 `MouseMoveBlock` entries. Showing each as a separate row makes the editor unusable. Users want to see and edit "the move path" as a single unit.

### The Solution: Virtual MoveGroup

Groups are NOT stored in `MacroDocument.blocks`. The underlying list remains flat. Groups are computed by the `MacroEditorModel` (the QAbstractTableModel subclass) at display time.

```python
def compute_groups(blocks: list[ActionBlock]) -> list[RowItem]:
    """
    Returns a list of RowItems for the table view.
    Consecutive MouseMoveBlocks between non-move blocks
    are collapsed into a MoveGroupRow.
    Individual moves within the group are sub-rows
    (shown when group is expanded).
    """
    rows = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if isinstance(block, MouseMoveBlock):
            # Collect the run
            run_start = i
            while i < len(blocks) and isinstance(blocks[i], MouseMoveBlock):
                i += 1
            run = blocks[run_start:i]
            rows.append(MoveGroupRow(
                start_index=run_start,
                end_index=i - 1,
                blocks=run,
                expanded=False,  # collapsed by default
            ))
        else:
            rows.append(SingleRow(index=i, block=block))
            i += 1
    return rows
```

This means:
- The flat list is the source of truth (serializes cleanly to JSON).
- Groups are a view-level computation; recomputed whenever `blocks` changes.
- Group expansion state (collapsed/expanded) lives in the model, not in `MacroDocument`.
- Editing group duration scales all `timestamp_ms` values within the run proportionally without touching the structure.

### Group Duration Edit

When a user selects a group and edits total duration:

```python
def scale_group_duration(blocks: list[MouseMoveBlock], new_duration_ms: int):
    if len(blocks) < 2:
        return
    original_duration = blocks[-1].timestamp_ms - blocks[0].timestamp_ms
    if original_duration == 0:
        return
    ratio = new_duration_ms / original_duration
    base_ts = blocks[0].timestamp_ms
    for b in blocks:
        offset = b.timestamp_ms - base_ts
        b.timestamp_ms = base_ts + int(offset * ratio)
```

The group's start timestamp is anchored; only offsets within the group are scaled. This preserves the shape of the movement path while changing its speed.

---

## Flow Control Execution

### Label/Goto Implementation

During playback, the engine builds a label index once before starting execution:

```python
def build_label_index(blocks: list[ActionBlock]) -> dict[str, int]:
    """Maps label name -> block index in the flat list."""
    index = {}
    for i, block in enumerate(blocks):
        if isinstance(block, LabelBlock):
            index[block.name] = i
    return index
```

Execution uses an integer program counter (`pc`) rather than iterating with a for-loop:

```python
def run(self, document: MacroDocument, speed: float, stop_event: threading.Event):
    blocks = document.blocks
    label_index = build_label_index(blocks)
    pc = 0
    while pc < len(blocks) and not stop_event.is_set():
        block = blocks[pc]
        self.action_started.emit(pc)   # Qt signal → highlight row in UI

        if isinstance(block, MouseMoveBlock):
            pyautogui_or_ctypes_move(block.x, block.y)
            self._sleep(timing_delta(blocks, pc, speed), stop_event)
            pc += 1

        elif isinstance(block, GotoBlock):
            target = block.target
            if target == "end":
                break
            if target not in label_index:
                raise PlaybackError(f"Label '{target}' not found")
            pc = label_index[target]
            # Do NOT increment pc — execution resumes AT the label

        elif isinstance(block, LabelBlock):
            pc += 1  # Labels are no-ops during execution; just advance

        elif isinstance(block, WindowFocusBlock):
            hwnd = find_window(block)
            if hwnd:
                activate_window(hwnd, block)
                if block.on_success_goto == "next":
                    pc += 1
                else:
                    pc = label_index[block.on_success_goto]
            else:
                self._sleep(block.on_failure_wait_ms / 1000.0, stop_event)
                if block.on_failure_goto == "end":
                    break
                pc = label_index[block.on_failure_goto]

        # ... other block types
```

Key properties of this design:
- `GotoBlock` sets `pc` to the label's index directly; the loop condition re-evaluates at the label's position.
- `LabelBlock` during execution is a no-op — it just increments `pc`.
- `stop_event.is_set()` is checked at the top of the while loop, guaranteeing the engine stops within one action's execution time.
- `WindowFocusBlock` emits its own goto logic, reusing the same `label_index` dict.

### Timing During Playback

For sequential actions, the delay between them is derived from the `timestamp_ms` difference between consecutive blocks, divided by the speed multiplier:

```python
def timing_delta(blocks: list[ActionBlock], current_pc: int, speed: float) -> float:
    """
    Returns seconds to sleep after executing blocks[current_pc].
    Uses timestamp of next time-bearing block to derive gap.
    """
    current = blocks[current_pc]
    if not hasattr(current, "timestamp_ms"):
        return 0.0
    next_pc = current_pc + 1
    while next_pc < len(blocks):
        nxt = blocks[next_pc]
        if hasattr(nxt, "timestamp_ms"):
            gap_ms = nxt.timestamp_ms - current.timestamp_ms
            return max(0.0, gap_ms / 1000.0 / speed)
        next_pc += 1
    return 0.0
```

`DelayBlock` does not use timestamp-derived timing — it uses its own `duration_ms` value directly, also divided by speed.

---

## Event Model Between Components

The architecture uses **Qt signals/slots** as the primary cross-thread communication mechanism, with a `queue.Queue` at the OS-thread boundary (pynput).

### Signal Map

```
RecorderEngine (pynput thread)
    → raw_event_queue: queue.Queue
        ← polled by QTimer(10ms) in RecorderController (main thread)

RecorderController (main thread)
    → signal: recording_complete(MacroDocument)
        → MacroEditorWidget.load_document(doc)

PlaybackEngine (QThread)
    → signal: action_started(int)          # emitted before executing each block
        → PlaybackController → MacroEditorWidget.highlight_row(index)
    → signal: playback_finished()
        → PlaybackController → MainWindow (update status bar, re-enable UI)
    → signal: playback_error(str)
        → PlaybackController → MainWindow (show error dialog)

MacroEditorWidget (main thread)
    → signal: document_changed()           # emitted after any edit to MacroDocument
        → MainWindow (mark document dirty, update title bar)
```

### Why Queue at the pynput Boundary

pynput Listener callbacks are invoked on a thread created and managed by pynput (which is ultimately an OS thread via ctypes hooks). This thread has strict callback latency requirements — Windows low-level hooks have a timeout (~200ms) after which the OS considers the hook unhealthy and may remove it. A `queue.Queue.put()` is effectively instantaneous. Any non-trivial processing in the callback risks hitting this timeout.

The `QTimer`-based drain (10ms interval, draining all pending items per tick) batches the events and delivers them to the main thread in bulk. This is more efficient than emitting one Qt signal per event at 100Hz.

### No Direct Model Mutation from PlaybackEngine

The PlaybackEngine reads `MacroDocument.blocks` as a read-only snapshot. It does not modify the document during playback. If playback needs to report position, it does so via signals carrying the `pc` index — not by writing to the model. This avoids any need for locks on the document.

---

## Recommended Project Structure

```
macro_thunder/
├── main.py                   # Entry point: DPI awareness, QApplication, MainWindow
├── models/
│   ├── __init__.py
│   ├── action_blocks.py      # All ActionBlock dataclasses, MacroDocument, block_from_dict
│   └── move_group.py         # MoveGroupRow, SingleRow, compute_groups, scale_group_duration
├── engines/
│   ├── __init__.py
│   ├── recorder_engine.py    # pynput Listeners, raw_event_queue population
│   └── playback_engine.py    # QThread subclass, pc-based executor, build_label_index
├── controllers/
│   ├── __init__.py
│   ├── recorder_controller.py  # QTimer drain, threshold filter, document assembly
│   └── playback_controller.py  # Speed/repeat config, PlaybackEngine lifecycle
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # App shell, menus, toolbar, docking
│   ├── macro_editor_widget.py  # QAbstractTableModel subclass, QTableView, delegates
│   ├── macro_library_panel.py  # File list widget
│   ├── block_delegates.py      # Custom QStyledItemDelegate for each block type
│   └── window_picker.py        # Interactive window selector dialog
├── storage/
│   ├── __init__.py
│   └── macro_repository.py     # load/save JSON, enumerate macros/ directory
└── macros/                     # Default user macro storage directory
```

### Structure Rationale

- **models/**: Pure data — no Qt imports, no Win32 imports. Testable in isolation. All ActionBlock types here.
- **engines/**: Low-level I/O (pynput, Win32 mouse movement). No Qt UI dependencies. Engines are single-responsibility: RecorderEngine captures events; PlaybackEngine executes them.
- **controllers/**: Mediate between engines and UI. Owns Qt signals, configuration, lifecycle management. This is where speed multiplier, threshold config, and repeat count live.
- **ui/**: All PyQt6 widget code. Depends on models and controllers; never imports from engines directly.
- **storage/**: Pure file I/O. No Qt, no pynput. Easy to test with temp directories.

---

## Architectural Patterns

### Pattern 1: QTimer-Polled Queue for pynput Events

**What:** pynput callbacks enqueue raw events into `queue.Queue`. A `QTimer` in the main thread fires every 10ms, drains all pending events, and delivers them as a batch to the controller.

**When to use:** Whenever OS callbacks (pynput, Win32 hooks, sockets) produce events that must reach the Qt UI thread without blocking the callback thread.

**Trade-offs:** 10ms polling introduces up to 10ms latency in the recorder UI feedback. This is imperceptible to users. The alternative (Qt signals from a foreign thread) requires careful `moveToThread` / `QMetaObject.invokeMethod` plumbing that is error-prone.

**Example:**
```python
class RecorderController(QObject):
    recording_complete = pyqtSignal(object)  # MacroDocument

    def __init__(self):
        super().__init__()
        self._queue: queue.Queue = queue.Queue()
        self._engine = RecorderEngine(self._queue)
        self._timer = QTimer()
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._drain_queue)

    def start_recording(self):
        self._pending_blocks: list[ActionBlock] = []
        self._engine.start()
        self._timer.start()

    def stop_recording(self):
        self._engine.stop()
        self._timer.stop()
        self._drain_queue()  # Final drain before signaling complete
        doc = MacroDocument(blocks=self._pending_blocks)
        self.recording_complete.emit(doc)

    def _drain_queue(self):
        while not self._queue.empty():
            raw_event = self._queue.get_nowait()
            block = self._convert(raw_event)
            if block:
                self._pending_blocks.append(block)
```

### Pattern 2: PC-Based Interpreter for Playback

**What:** Playback maintains an integer program counter (`pc`) indexing into `MacroDocument.blocks`. Each iteration executes one block and updates `pc`. Goto/label jumps set `pc` directly.

**When to use:** Any time execution order is non-sequential (jumps, loops, branching). A for-loop cannot express jumps without continue/break hacks.

**Trade-offs:** Slightly more complex than a simple for-loop. Prevents any use of Python for-loop sugar. The payoff is that label jumps, conditional branches, and future `if pixel_color` blocks all fit naturally without restructuring.

### Pattern 3: Flat List as Source of Truth, Computed Groups as View

**What:** `MacroDocument.blocks` is always a flat list. The `MacroEditorModel` (QAbstractTableModel) computes `MoveGroup` rows lazily when the model is invalidated. Group expansion state is held only in the model, not persisted.

**When to use:** When display grouping must not corrupt the underlying data structure or its serialization.

**Trade-offs:** `compute_groups()` runs on every model invalidation. For a macro with 10,000 blocks this is still sub-millisecond on modern hardware — not a concern. The benefit is that JSON serialization remains trivially simple (flat list of typed dicts) and no "un-grouping" step is needed on load.

---

## Data Flow

### Recording Flow

```
[User moves mouse]
    ↓
pynput on_move callback (pynput thread)
    ↓ queue.put(RawEvent)
raw_event_queue
    ↓ QTimer drain (main thread, 10ms)
RecorderController._drain_queue()
    ↓ apply pixel threshold filter
    ↓ convert to MouseMoveBlock
_pending_blocks: list[ActionBlock]
    ↓ on stop_recording()
MacroDocument(blocks=_pending_blocks)
    ↓ signal: recording_complete(doc)
MacroEditorWidget.load_document(doc)
    ↓ MacroEditorModel.invalidate()
QTableView re-renders (groups computed)
```

### Playback Flow

```
[User presses F5]
    ↓
PlaybackController.start()
    ↓ passes MacroDocument snapshot + speed + repeat_count
PlaybackEngine.run() (QThread)
    ↓ build_label_index(blocks)
    ↓ pc = 0
    loop:
        emit action_started(pc)  → (Qt signal → main thread)
            → MacroEditorWidget.highlight_row(pc)
        execute blocks[pc]
        compute sleep duration (timestamp delta / speed)
        time.sleep(duration)  [checks stop_event periodically]
        pc += 1 (or jump to label)
    emit playback_finished()  → (Qt signal → main thread)
        → PlaybackController.on_finished()
        → MainWindow.on_playback_done() (re-enable UI)
```

### Save/Load Flow

```
[User: File → Save]
    ↓
MainWindow → MacroRepository.save(doc, path)
    ↓ dataclasses.asdict(doc)
    ↓ json.dump(dict, file, indent=2)
    .json file on disk

[User: opens macro from library]
    ↓
MacroLibraryPanel → MacroRepository.load(path)
    ↓ json.load(file)
    ↓ block_from_dict(d) for each block
MacroDocument
    ↓ MacroEditorWidget.load_document(doc)
QTableView renders
```

---

## Build Order (Dependency Graph)

Build in this order; each phase depends only on the layer beneath it.

```
Phase 1: Data Model (no dependencies)
    models/action_blocks.py
    models/move_group.py
    storage/macro_repository.py

Phase 2: Engines (depends on: data model, stdlib queue)
    engines/recorder_engine.py    (pynput)
    engines/playback_engine.py    (QThread + data model)

Phase 3: Controllers (depends on: engines, data model)
    controllers/recorder_controller.py
    controllers/playback_controller.py

Phase 4: UI Foundation (depends on: PyQt6, data model)
    ui/main_window.py             (shell only — no editor yet)
    ui/macro_library_panel.py
    ui/macro_editor_widget.py     (QAbstractTableModel + flat display, no groups yet)

Phase 5: Wiring (connects UI + controllers)
    main.py                       (DPI awareness, QApplication, connect signals)
    → End of phase: record + play works end-to-end

Phase 6: Editor Features (depends on: UI Foundation)
    ui/block_delegates.py         (inline editing per block type)
    models/move_group.py          (group computation + expand/collapse)
    → End of phase: full editor with grouping and inline editing

Phase 7: Flow Control
    PlaybackEngine: goto/label interpreter
    WindowFocus block + ui/window_picker.py
    → End of phase: looping macros and window automation work
```

**Rationale for this order:**
- Data model first: all other layers depend on `ActionBlock` types. Define them once, import everywhere.
- Engines before controllers: controllers wrap engines; testing engines standalone is easier.
- UI foundation before wiring: need a shell to wire signals into.
- "Record and play works" as Phase 5 exit: this gives the earliest runnable milestone where the core value proposition is exercisable. Editor polish and flow control are additive from there.

---

## Anti-Patterns

### Anti-Pattern 1: Touching Qt Widgets from a Worker Thread

**What people do:** Call `self.table_view.scrollTo(index)` or `self.model.appendRow(block)` from inside the PlaybackEngine's `run()` method or from a pynput callback.

**Why it's wrong:** PyQt6 is not thread-safe for UI operations. This causes random crashes, frozen UI, or silent data corruption — all intermittent and hard to debug.

**Do this instead:** Emit a Qt signal from the worker. Connect the signal to a slot in the main thread. PyQt6 queues signal delivery across thread boundaries automatically when using `Qt.ConnectionType.QueuedConnection` (which is the default when signal and slot are in different threads).

### Anti-Pattern 2: Blocking in pynput Callbacks

**What people do:** Process events, build blocks, and emit signals directly inside `on_move`, `on_click`, etc.

**Why it's wrong:** Windows low-level mouse/keyboard hooks have a hard timeout (~200ms by default). Exceeding it causes the OS to silently remove the hook, ending recording without any error. File I/O, PyQt6 signal emission across threads, and even heavy Python computation can exceed this.

**Do this instead:** `queue.put(event)` and return. Drain the queue on a separate thread or via QTimer in the main thread.

### Anti-Pattern 3: Storing Groups in MacroDocument

**What people do:** Introduce a `MoveGroup` type that wraps a list of `MouseMoveBlock` objects and stores it in `blocks` as a nested structure to simplify the display logic.

**Why it's wrong:** Nested structures complicate the playback engine (must flatten on play), the serialization format (nested JSON arrays), and every place that iterates `blocks`. It also makes the `pc` counter ambiguous — does `pc` index into groups or into moves within groups?

**Do this instead:** Keep `blocks` flat. Groups are a view-level computation in `MacroEditorModel.compute_groups()`. The playback engine always sees a flat list and a simple integer `pc`.

### Anti-Pattern 4: Using for-loop for Playback

**What people do:** `for i, block in enumerate(blocks): execute(block)` — simple, Pythonic.

**Why it's wrong:** Cannot jump backward to a label. `goto` to an earlier label requires either an exception-based restart or a refactor to a while loop. The first goto implementation will force a rewrite of the playback loop.

**Do this instead:** Use a `while pc < len(blocks)` loop with explicit `pc` management from the start. It's only marginally more code and supports jumps trivially.

### Anti-Pattern 5: Building the Label Index on Every Goto

**What people do:** When executing a `GotoBlock`, scan the entire `blocks` list for a matching `LabelBlock`.

**Why it's wrong:** O(n) label lookup on every goto. In a looping macro that executes a goto 10,000 times per minute, this is measurable overhead and adds latency jitter to the playback timing.

**Do this instead:** Build `label_index: dict[str, int]` once before execution starts. O(1) lookup per goto.

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| pynput thread → RecorderController | `queue.Queue` | One-directional. RecorderController owns the queue. |
| RecorderController → MacroEditorWidget | Qt signal `recording_complete(MacroDocument)` | Queued connection (automatic cross-thread). |
| PlaybackEngine → PlaybackController | Qt signals `action_started(int)`, `playback_finished()`, `playback_error(str)` | PlaybackEngine is a QThread; signals are auto-queued. |
| PlaybackController → MacroEditorWidget | Direct method call `highlight_row(index)` | Both in main thread; no queuing needed. |
| MacroEditorWidget → MacroDocument | Direct read/write | Both owned by main thread. |
| MacroRepository → disk | `json.load` / `json.dump` | Synchronous. For very large macros (>50k blocks), consider moving save to a thread — unlikely to be needed. |
| PlaybackEngine → Win32 (WindowFocus) | `pywin32` direct calls | Runs in PlaybackEngine's QThread. Win32 calls are thread-safe. |

---

## Scaling Considerations

This is a single-user desktop tool. Scaling here means "how does the architecture hold up as macro complexity grows."

| Scale | Concern | Architecture Response |
|-------|---------|-----------------------|
| < 1,000 blocks | Baseline | All patterns above handle this trivially. |
| 1,000–10,000 blocks | `compute_groups()` performance | Still sub-millisecond. QAbstractTableModel only renders visible rows — 10k blocks in a QTableView is fine. |
| > 10,000 blocks | Memory | Each block is ~5–10 fields. 10k blocks ≈ 500KB in RAM. Not a concern. JSON file ≈ 2MB. Load time may become perceptible (>100ms). Add progress indicator on load. |
| Hundreds of macros in library | MacroLibraryPanel | Enumerate files lazily. Load MacroDocument only on selection, not on startup. |
| RunMacro chains (deep nesting) | Recursive macro execution | Maintain a call stack in PlaybackEngine. Set a recursion depth limit (e.g., 10) to prevent infinite loops. |

---

## Sources

- PyQt6 model/view architecture: [Qt6 Model/View Programming docs](https://doc.qt.io/qt-6/model-view-programming.html) — QAbstractTableModel pattern. HIGH confidence.
- pynput threading constraints: [pynput readthedocs — Handling the keyboard](https://pynput.readthedocs.io/en/latest/keyboard.html) — "The callback is invoked from a thread. Do not perform any I/O operations or any operations that require a running message loop." HIGH confidence.
- Windows hook timeout: [MSDN SetWindowsHookEx documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexw) — hook timeout behavior. HIGH confidence.
- QThread signal queuing: [Qt6 Signals and Slots Across Threads](https://doc.qt.io/qt-6/threads-qobject.html) — auto-queued connection when signal/slot are in different threads. HIGH confidence.
- PC-based interpreter pattern: well-established in interpreter design literature (e.g., Crafting Interpreters, Nystrom). HIGH confidence (training data).
- Flat list vs nested grouping for display: design judgment derived from Qt model/view pattern; view-layer computation is idiomatic Qt. HIGH confidence.

---

*Architecture research for: Python Windows desktop macro recorder (Macro Thunder)*
*Researched: 2026-02-25*
