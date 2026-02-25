# Pitfalls Research

**Domain:** Python Windows desktop macro recorder and editor
**Researched:** 2026-02-25
**Confidence:** HIGH (pynput/Qt threading verified via official docs and community issues; timing verified via Python stdlib docs and real-world macro recorder analysis)

---

## Critical Pitfalls

### Pitfall 1: pynput Listener Thread Calling Qt Widgets Directly

**What goes wrong:**
pynput's `Mouse.Listener` and `Keyboard.Listener` run callbacks on OS-managed system threads — not the Qt main thread. If a callback directly calls any Qt widget method (`label.setText()`, `table.insertRow()`, `model.appendRow()`, etc.), the app will either crash with a vague `QObject: Cannot create children for a parent that is in a different thread` message, or silently corrupt UI state. On Windows, PyQt6 crashes are often silent — no traceback, the window just disappears.

**Why it happens:**
Beginners wire pynput callbacks directly to UI update logic. The error appears to work in simple tests (the OS doesn't always enforce this immediately) but fails unpredictably in production. PyQt6 does not guard against this with a clear error — it is undefined behavior at the C++ level.

**How to avoid:**
Never touch Qt objects from a pynput callback. The correct pattern is:

```python
# In your recorder worker class:
from PyQt6.QtCore import QObject, pyqtSignal

class RecorderSignals(QObject):
    event_recorded = pyqtSignal(dict)  # dict = serialized event

class MouseRecorder:
    def __init__(self):
        self.signals = RecorderSignals()

    def _on_move(self, x, y):
        # This runs on pynput's system thread — ONLY emit signals, nothing else
        self.signals.event_recorded.emit({"type": "move", "x": x, "y": y})
```

Connect `event_recorded` to a slot in the main thread. Qt's event system queues the signal and delivers it on the GUI thread automatically. Never use `Qt.ConnectionType.DirectConnection` for cross-thread signals.

**Warning signs:**
- App crashes on recording start with no visible error
- `QObject::startTimer: Timers can only be used with threads started with QThread` in console
- UI freezes or flickers during recording
- Rare/intermittent crashes that are hard to reproduce

**Phase to address:** Phase 1 (Core Recording). The threading architecture must be correct from the first line of recording code — retrofitting it after building the full recording pipeline is a significant rewrite.

---

### Pitfall 2: DPI Scaling — pynput Listener vs Controller Coordinate Mismatch

**What goes wrong:**
Without explicit DPI awareness configuration, pynput's Mouse Listener receives physical pixel coordinates while the Mouse Controller sends input using scaled (logical) coordinates. On a 1920x1080 display with 150% scaling, the listener sees coordinates up to (1920, 1080) but the controller would need to move to ~(1280, 720) to reach the same point. Recorded macros replay to the wrong location — subtly wrong on 125% scaling, drastically wrong on 200% scaling. This affects every modern Windows laptop.

**Why it happens:**
Windows runs unaware processes in a virtualized coordinate space. When `SetProcessDpiAwareness` is not called, the DWM intercepts and scales coordinates. pynput cannot set DPI awareness automatically because it is a process-global setting that must precede any window creation. The mismatch is invisible in testing on a 100% DPI monitor.

**How to avoid:**
Call `SetProcessDpiAwareness(2)` as the **very first line of the application** — before importing PyQt6, before creating `QApplication`, before starting any pynput listener:

```python
# main.py — top of file, before all other imports
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE

# Only then:
from PyQt6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
```

For multi-monitor setups with mixed DPI (e.g., 4K primary at 200% + 1080p secondary at 100%): coordinates at the boundary between monitors can be discontinuous in logical space but continuous in physical space. Always record in physical coordinates (achieved by the DPI fix above) and replay using `ctypes.windll.user32.SetCursorPos` or `SendInput` with absolute physical coordinates.

**Warning signs:**
- Playback clicks are offset by a fixed percentage of screen size
- Correct position on developer machine, wrong on user machine
- Works correctly at 100% DPI, fails at 125%/150%/200%
- Multi-monitor playback coordinates jump unexpectedly at screen boundaries

**Phase to address:** Phase 1 (Core Recording). This must be the startup sequence from day one. Changing DPI handling after recording and playback are built risks breaking recorded macro files (if physical vs. logical coordinates were inconsistently stored).

---

### Pitfall 3: Input Suppression Unreliable for Games (DirectInput / RawInput)

**What goes wrong:**
`pynput.mouse.Listener(suppress=True)` and `pynput.keyboard.Listener(suppress=True)` suppress input via Windows low-level hooks (`WH_MOUSE_LL`, `WH_KEYBOARD_LL`). These hooks intercept WM_INPUT messages in the standard Windows input pipeline. Games using DirectInput or RawInput read from the device driver directly — below the hook layer. Result: pynput's suppression has no effect on game input. The user's mouse and keyboard still reach the game during recording. Additionally, mouse movement suppression is specifically broken — pynput can suppress button events but not raw mouse movement.

**Why it happens:**
pynput's hook level (Win32 low-level hooks) sits above the driver level where DirectInput reads. This is a Windows architecture limitation, not a pynput bug. It affects all Python-level input interception libraries.

**How to avoid:**
For the current scope (record only — not suppress during recording), this is not a blocking issue. The user's actions reach the game AND get recorded. If input suppression during recording is required in future (e.g., "record without sending to game"), the only viable solutions are:

- **Interception driver** (`interception` Python bindings) — operates at kernel level, intercepts before any application sees input
- **Virtual machine isolation** — run the game in a VM that receives synthetic input only

Do NOT attempt to fix this with pynput's `suppress` parameter. Document this limitation clearly in any user-facing feature description. The current PROJECT.md scope does not require suppression — keep it that way.

**Warning signs:**
- Users report that game still responds to mouse/keyboard during recording
- Testing with `suppress=True` appears to work in non-game apps but fails in games
- Game anti-cheat systems detecting hook presence even when suppression fails

**Phase to address:** Phase 1 (Core Recording) — accept and document the limitation. If suppression is later required, it is a separate research spike that requires kernel-mode driver work.

---

### Pitfall 4: Playback Timing Drift Using time.sleep()

**What goes wrong:**
A naive playback loop records `dt = next_event.time - current_event.time` and calls `time.sleep(dt)` between events. On Windows, the OS timer resolution defaults to ~15.6ms (64 Hz tick rate). Any sleep shorter than ~15ms is rounded up to the next tick. Over 200 mouse move events in a 2-second path, the accumulated error reaches 50–200ms of total drift. Fast paths (100ms of recorded movement) can end up taking 200–250ms on replay. The macro "works" but feels sluggish and inaccurate — subtly wrong for game automation where timing matters.

**Why it happens:**
`time.sleep()` is a minimum-wait guarantee, not an exact wait. The Windows scheduler wakes the thread at the next scheduler tick after the requested duration. Each event's sleep error compounds into drift over the macro.

**How to avoid:**
Use `time.perf_counter()` with absolute target timestamps, not per-interval sleeps:

```python
def playback(events):
    start = time.perf_counter()
    for event in events:
        target = start + event["time_offset"]  # absolute time from macro start
        # Coarse sleep to yield CPU, then busy-wait for precision
        remaining = target - time.perf_counter()
        if remaining > 0.002:  # >2ms: sleep to yield
            time.sleep(remaining - 0.001)
        while time.perf_counter() < target:  # final precision spin
            pass
        execute(event)
```

This pattern: (1) sleeps most of the wait to avoid burning CPU, (2) busy-waits the final ~1ms for precision. CPU usage during playback increases slightly but timing accuracy is sub-millisecond. For speed multiplier support, divide all `time_offset` values by the multiplier before playback.

**Warning signs:**
- "2x speed" playback is actually 1.5x because each sleep is overshooting
- Long macros drift progressively further from expected timing
- 16ms chunks visible in event timing logs
- Simple `time.sleep(0.001)` tests show actual sleep of 15ms in profiling

**Phase to address:** Phase 2 (Core Playback). The absolute-timestamp pattern must be the initial implementation — it is not much more complex than naive sleep and avoids a rewrite when timing bugs are reported.

---

### Pitfall 5: PyQt6 Widget Calls from Background Threads (Silent Crashes)

**What goes wrong:**
Any PyQt6 widget method called from a non-main thread is undefined behavior. Unlike some frameworks that throw an immediately visible exception, PyQt6 often crashes without a Python traceback — the C++ layer fails, the process terminates, and the user sees only a Windows "application has stopped working" dialog. The crashes are intermittent (race conditions) making them hard to reproduce and diagnose. Common trigger: a `QThread` or `threading.Thread` worker calls `self.table.model().appendRow()` or `self.progress_bar.setValue()` directly.

**Why it happens:**
Qt's entire widget system is single-threaded by design (X11 and Win32 window management are not thread-safe). PyQt6 does not add Python-level locking around widget calls. The crash happens in Qt's C++ internals below the Python layer, so Python's exception machinery never fires.

**How to avoid:**
Enforce one invariant: **only the main thread touches widgets**. Worker threads (pynput recorder, playback engine, file I/O) communicate back to the UI exclusively via signals:

```python
class PlaybackWorker(QObject):
    progress_updated = pyqtSignal(int)   # connect to progress bar in main thread
    finished = pyqtSignal()

    def run(self):
        for i, event in enumerate(self.events):
            execute(event)
            self.progress_updated.emit(i)  # safe: signal queued to main thread
        self.finished.emit()
```

Never subclass `QThread` and touch widgets in `run()`. Use `QObject.moveToThread()` pattern instead. Add a lint check / code review rule: any direct widget method call inside a `QThread.run()` or `threading.Thread.run()` is a bug.

**Warning signs:**
- App closes with no error message during playback
- Intermittent crash reproducible only under load
- Windows event log shows `python.exe` crash in `Qt6Widgets.dll`
- Works fine in single-threaded tests but crashes in integration

**Phase to address:** Phase 1 (Architecture setup). The signal/slot architecture must be established before any worker threads are written. This is not retrofittable — it requires revisiting every thread/widget interaction.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Call Qt widget directly from pynput callback | Simpler code, no signal boilerplate | Silent crashes, impossible to debug, requires full rewrite | Never |
| Use `time.sleep(dt)` for playback timing | Simple implementation | Accumulated timing drift, user reports "wrong speed" | Never for playback; OK for non-timing operations |
| Skip DPI awareness call | One fewer startup line | Wrong coordinates on all modern laptops at first user test | Never |
| Store raw mouse move events without threshold filtering | Zero filtering logic | Editor becomes unusable (thousands of rows per recording) | Never; pixel threshold is core UX |
| No version field in macro JSON | Simpler format | Cannot load old macros after adding new action types | Never; add `"version": 1` from day one |
| Store recording events in a Python list in the pynput callback thread | Simple shared state | Race conditions when main thread reads list while callback writes | Never; use `queue.Queue` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| pynput + PyQt6 | Emit signals from wrong thread context | Always emit signals; connect with default (queued) connection type |
| pynput Mouse Controller + DPI | Call `controller.move()` with recorded physical coordinates | Set DPI awareness first; coordinates then stay consistent |
| pywin32 `SetForegroundWindow` | Call it without bringing window to foreground first | Use `win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)` before `SetForegroundWindow`; Windows requires the calling process to own the foreground |
| pywin32 `FindWindow` | Match on full title string | Use `EnumWindows` + partial match; titles change dynamically in games |
| JSON macro files | Load without version check | Always validate `"version"` field first; reject or migrate unknown versions |
| pynput `GlobalHotKeys` + recording listener | Start `GlobalHotKeys` after recording listener | Both use system hooks; start `GlobalHotKeys` first, recording listener second to avoid hook ordering issues |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Storing every raw mouse move event | Recording a 10-second path at 200 events/sec = 2,000 rows in the editor; editor becomes unusable | Apply pixel-distance threshold during recording (skip events where distance from last recorded point < N pixels) | Immediately on first real recording session |
| Appending to a Python list inside pynput callback | Race condition when main thread reads the list | Use `queue.Queue` (thread-safe FIFO); drain queue periodically from main thread | Intermittently; worst under heavy mouse movement |
| Rebuilding the entire Qt table model on every new event during recording | Qt repaints entire table at 200 Hz; UI lags | Batch inserts: drain the event queue at 30 Hz via `QTimer`, insert rows in batches | As soon as pixel threshold is disabled for testing |
| Loading entire macro into memory as Python objects before playback | Fine for 100-event macros; problematic for 100k-event chained macros | Macros at current scope are small; but chain depth must be bounded to prevent recursive loading | Not a current concern; flag if "run macro" chaining grows deep |
| Busy-wait spin loop on main thread during playback | GUI freezes during playback | Run playback on a `QThread`; emit progress signals back to UI | Immediately if naive implementation |

---

## "Looks Done But Isn't" Checklist

- [ ] **DPI awareness:** Recording works at 100% — verify coordinates are correct at 125%, 150%, 200% system scaling before calling recording "done"
- [ ] **Thread safety:** Recording starts without crash — verify by running for 30 seconds of fast mouse movement, not just a click
- [ ] **Timing:** Playback "looks right" — verify with a stopwatch that a 10-second recorded path replays in exactly 10.0 ± 0.1 seconds
- [ ] **Pixel threshold:** Editor shows filtered events — verify that a 5-second fast mouse wiggle produces fewer than 100 rows, not 1,000+
- [ ] **Macro file version field:** JSON saves — verify `"version"` field is present in every saved file from day one
- [ ] **goto/label:** Goto jumps to label — verify what happens when the label does not exist (should error gracefully, not hang)
- [ ] **goto/label:** Single goto works — verify that `goto A → ... → goto A` detects as an infinite loop and offers a stop, rather than running forever
- [ ] **Stop hotkey:** Macro stops on hotkey — verify stop hotkey is processed even when the playback thread is in a busy-wait spin

---

## goto/label Execution Pitfalls

These deserve specific detail because they are non-obvious implementation problems.

### Jump to Nonexistent Label

**What goes wrong:** Executor reaches a `goto "cleanup"` block but no `label "cleanup"` exists in the macro. Naive implementation either raises an unhandled `KeyError` (Python crash) or silently skips the jump and continues executing the next action (wrong behavior).

**How to avoid:** Validate all goto targets at macro load time, before execution begins. Build a `labels: dict[str, int]` index mapping label names to action indices. If any `goto` references a label not in the index, show an error dialog and refuse to run. This catches the problem at load, not mid-playback.

### Infinite Loop Detection

**What goes wrong:** `goto "loop_start"` at the end of a sequence with no conditional exit creates an infinite loop. The playback thread never terminates. The stop hotkey may not be processed because the playback thread is busy executing actions rapidly (especially if actions are delays of 0ms). The user has to kill the process.

**How to avoid:** Two mechanisms:
1. **Stop flag checked at every action:** The playback loop checks `self._stop_requested` before executing each action, including inside goto jumps. The stop hotkey sets this flag from the pynput listener thread (via signal). This ensures the loop can always be interrupted.
2. **Iteration cap for non-looping detection (optional):** Track `jump_count` per execution run. If it exceeds a configurable threshold (e.g., 10,000 jumps), pause and ask the user "Macro has jumped 10,000 times — is this intentional?". Do not silently terminate; the user may intentionally want an infinite loop.

The stop flag approach is mandatory. The iteration cap is a UX nicety.

---

## Macro File Format Evolution

### Adding New Action Types Without Version Field

**What goes wrong:** Version 1 of the format has action types: `move`, `click`, `scroll`, `key`, `delay`. You add `window_focus` in version 2. A user opens an old macro file after the update. If the executor does not check for unknown action types, it either crashes on `KeyError` or silently skips the new action. If a user opens a version 2 file with an old version of the app, the `window_focus` block is misinterpreted.

**How to avoid:** Include `"version": 1` in every saved macro file from the very first release. On load:
1. Check `data.get("version", 0)` — treat missing version as version 0 (pre-versioning era)
2. If version > `APP_MAX_SUPPORTED_VERSION`: refuse to load with a clear message ("This macro was created with a newer version of Macro Thunder")
3. If version < current: run migration functions in sequence (`migrate_v0_to_v1()`, `migrate_v1_to_v2()`, etc.)

Unknown action types encountered during execution should log a warning and skip the action, not crash. This allows partial forward compatibility.

**Warning signs:**
- Any macro save code that does not include a `"version"` field
- Any executor that does `action_handlers[action["type"]](action)` without a `KeyError` fallback

**Phase to address:** Phase 1 (Macro file format design). Adding versioning after files are in the wild requires a `version: 0` assumption for all existing files — manageable but messier than getting it right from the start.

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| pynput → Qt thread safety (signals only) | Phase 1: Core Recording | Record 30 seconds of fast mouse movement without crash |
| DPI awareness startup sequence | Phase 1: App startup | Test at 125% and 200% system DPI; compare recorded vs replayed positions |
| Playback timing drift | Phase 2: Core Playback | Measure 10-second macro replay wall clock time; must be 10.0 ± 0.1s |
| High-frequency event storage | Phase 1: Core Recording | Verify pixel threshold filters: 5s fast wiggle < 100 stored events |
| Qt widget calls from workers | Phase 1: Architecture | All worker-to-UI communication via signals; code review rule |
| Macro file version field | Phase 1: File format | Every saved file contains `"version"` key |
| goto to nonexistent label | Phase 3: Flow control | Load macro with missing label; verify error dialog, no crash |
| goto infinite loop | Phase 3: Flow control | Create A→A goto loop; verify stop hotkey terminates within 1 second |
| Input suppression in games | Phase 1: Accepted limitation | Document limitation; do not attempt to fix with pynput suppress |

---

## Sources

- [pynput FAQ — threading model, suppress behavior](https://pynput.readthedocs.io/en/latest/faq.html) — HIGH confidence (official docs)
- [pynput Mouse documentation — DPI awareness requirement](https://pynput.readthedocs.io/en/latest/mouse.html) — HIGH confidence (official docs)
- [Microsoft Learn — DPI and device-independent pixels](https://learn.microsoft.com/en-us/windows/win32/learnwin32/dpi-and-device-independent-pixels) — HIGH confidence (official docs)
- [Microsoft Learn — High DPI Desktop Application Development](https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows) — HIGH confidence (official docs)
- [Qt Documentation — Synchronizing Threads](https://doc.qt.io/qt-6/threads-synchronizing.html) — HIGH confidence (official docs)
- [Qt Documentation — QMetaObject](https://doc.qt.io/qt-6/qmetaobject.html) — HIGH confidence (official docs)
- [KDAB — The Eight Rules of Multithreaded Qt](https://www.kdab.com/the-eight-rules-of-multithreaded-qt/) — MEDIUM confidence (authoritative Qt consulting firm)
- [Real Python — Use PyQt's QThread to Prevent Freezing GUIs](https://realpython.com/python-pyqt-qthread/) — MEDIUM confidence (well-established tutorial)
- [Python Tutorials Net — How Accurate is Python's time.sleep()?](https://www.pythontutorials.net/blog/how-accurate-is-python-s-time-sleep/) — MEDIUM confidence (verified against Python stdlib docs)
- [Python stdlib — time.perf_counter()](https://docs.python.org/3/library/time.html) — HIGH confidence (official docs)
- [Feeding Key Presses to Reluctant Games — DirectInput analysis](https://danieldusek.com/feeding-key-presses-to-reluctant-games-in-python.html) — MEDIUM confidence (WebSearch, consistent with pynput GitHub issues)
- [pynput GitHub issue #163 — suppress parameter limitations](https://github.com/moses-palmer/pynput/issues/163) — MEDIUM confidence (maintainer-confirmed behavior in GitHub issues)
- [pynput GitHub issue #230 — not working in game apps](https://github.com/moses-palmer/pynput/issues/230) — MEDIUM confidence (multiple users confirming same behavior)
- [LinkedIn — Custom Qt Signal Resolves PyQt/pynput Thread Conflict](https://www.linkedin.com/pulse/custom-qt-signal-resolves-pyqtpyinput-thread-conflict-jeremy-yabrow-abtqc) — MEDIUM confidence (consistent with Qt official threading docs)
- [Building a High-Precision Mouse Macro Recorder in Python (2026)](https://edvaldoguimaraes.com.br/2026/02/09/building-a-high-precision-mouse-macro-recorder-in-python-gui-hotkeys-repeat-speed/) — MEDIUM confidence (recent, domain-specific, consistent with other sources)

---

*Pitfalls research for: Python Windows desktop macro recorder (Macro Thunder)*
*Researched: 2026-02-25*
