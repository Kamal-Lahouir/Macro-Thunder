# Project Research Summary

**Project:** Macro Thunder
**Domain:** Python Windows desktop macro recorder and editor (game automation focus)
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

Macro Thunder is a Windows desktop macro recorder and editor built with Python, targeting game automation users who need to record mouse and keyboard actions, edit them visually, and replay them with timing precision. Research across five comparable products (Macro Recorder, Jitbit, PyMacroRecord, Pulover's Macro Creator, AutoIt) confirms that the core user expectation is a visual block editor — not a scripting environment — with mouse movement auto-grouping as the single most important editing feature. Without grouping, a 2-second recorded mouse path produces 200–400 rows in the editor, making the tool unusable. This is the feature that separates products users actually adopt from prototypes they abandon.

The recommended stack is PyQt6 + pynput + pywin32 on Python 3.11. PyQt6 is the only Python GUI framework capable of building the required model/view block editor without massive custom widget work. CustomTkinter (the obvious alternative) is effectively abandoned since January 2024 and lacks QAbstractTableModel equivalents entirely. The architecture separates into four clear layers: data model (pure Python dataclasses), engines (pynput recording, QThread playback), controllers (lifecycle + configuration), and UI (PyQt6 widgets). Communication across threads uses Qt signals exclusively — the single biggest technical risk is mixing thread boundaries, which causes silent crashes in PyQt6.

The critical risk cluster is thread safety and DPI handling, both of which must be addressed in Phase 1 before any features are built on top. DPI awareness must be set as the first line of the application before any imports of PyQt6 or pynput — failure causes subtly wrong mouse coordinates on every modern laptop and cannot be corrected retroactively without invalidating saved macro files. Playback timing must use absolute `time.perf_counter()` targets rather than per-event `time.sleep()` calls — Windows' 15.6ms scheduler tick means naive sleep accumulates 50–200ms of drift per second of playback. Both pitfalls are well-documented, have clear prevention patterns, and are verified against official Microsoft and pynput documentation.

## Key Findings

### Recommended Stack

PyQt6 is the correct and only viable choice for the UI layer. Its `QAbstractTableModel` + `QTableView` architecture is what makes the block editor possible — custom delegates for inline editing, drag-and-drop reordering, and thousands of rows all work natively. pynput provides the cleanest event-driven recording API and includes `GlobalHotKeys` for stop/record hotkeys out of the box. pywin32 provides the Win32 window management APIs (`FindWindow`, `EnumWindows`, `SetForegroundWindow`) required for the Window Focus action block. JSON is the correct storage format — human-readable, git-diffable, no schema migration burden. PyInstaller handles packaging to a single Windows EXE with no C toolchain required.

**Core technologies:**
- Python 3.11: Runtime — sweet spot of performance, ecosystem compatibility, and stability for Win32 packages
- PyQt6 6.10.2: UI framework — required for QAbstractTableModel block editor; no viable alternative
- pynput 1.8.1: Mouse/keyboard capture — clean Listener API, GlobalHotKeys, v1.8.0 injected event detection prevents recording own playback
- pywin32 311: Win32 APIs — authoritative Python binding for FindWindow, SetForegroundWindow, GetWindowRect
- json (stdlib): Macro storage — human-readable, portable, no dependencies, correct for this scope
- pyqtdarktheme 2.1.0: Dark theme — single setup call, covers all Qt widgets
- PyInstaller 6.19.0: Packaging — native PyQt6 support, simplest distribution path

**What NOT to use:** CustomTkinter (abandoned Jan 2024, no model/view architecture), PyAutoGUI (playback-only, no recording model), pickle (security risk, not human-readable), Electron/Tauri (150MB+ overkill, no benefit over native PyQt6).

See `.planning/research/STACK.md` for full alternatives analysis and version compatibility table.

### Expected Features

Research confirms two tiers of features. The first tier (table stakes) are things every comparable product has — missing them makes the product feel broken. The second tier (differentiators) are where Macro Thunder can stand out, particularly mouse movement auto-grouping and group duration editing, which no open-source Python recorder currently implements well.

**Must have (table stakes — v1):**
- Record mouse moves, clicks, scroll, keyboard — the core function
- Pixel threshold filter — without this, editor shows hundreds of rows per second of recording
- Playback with timing fidelity — macros must replay at recorded speed
- Playback speed multiplier — trivial to implement, immediate user value
- Repeat N times + stop hotkey — these ship as a pair; infinite loop without kill switch is dangerous
- Visual block editor with list view — each action as a structured row, not code
- Delete, reorder, copy/paste action blocks — minimum editing operations
- Mouse move auto-grouping — the core editing insight; consecutive moves collapsed into one row
- Group duration editing with proportional time scaling — the value proposition of grouping
- Save/load macros (JSON) — persistence required; users cannot restart from scratch each session
- Macro library panel — named macro files, load/delete
- Dark theme — non-negotiable for the game automation audience

**Should have (competitive differentiators — v1.x after core loop validated):**
- Label blocks + Goto — enables loops and retry logic without a scripting language
- Window Focus action + Interactive window picker — most requested power feature; prevents coordinate drift
- Set window position/size on focus — natural extension of Window Focus
- Multi-select action blocks — required for large macro editing
- Macro chaining ("Run macro" action) — enables composition of utility macros

**Defer (v2+):**
- Relative-to-window coordinates — high value but high cost; validate demand first
- Conditional goto (pixel color check) — fragile for game rendering; validate before building

**Never build:** Image recognition clicks, EXE compilation, cloud sync, AI integration, cross-platform support, scripting language mode. These are explicit anti-features for this product's scope and audience.

See `.planning/research/FEATURES.md` for full competitor analysis and feature dependency graph.

### Architecture Approach

The architecture follows a strict four-layer separation: data model (pure Python dataclasses, no framework imports), engines (pynput RecorderEngine, QThread PlaybackEngine), controllers (RecorderController, PlaybackController — own lifecycle and configuration), and UI (PyQt6 widgets). The critical design decision is that `MacroDocument.blocks` remains a flat list at all times — mouse move grouping is a view-layer computation in `MacroEditorModel`, not a structural change to the stored data. This keeps JSON serialization trivial and the playback engine simple. The playback engine uses a program counter (`pc`) integer rather than a Python for-loop, enabling goto/label jumps without structural workarounds.

**Major components:**
1. RecorderEngine (pynput thread) — puts raw events into `queue.Queue`, never blocks
2. RecorderController (main thread, QTimer) — drains queue at 10ms, applies pixel threshold filter, assembles MacroDocument
3. PlaybackEngine (QThread) — pc-based interpreter, emits Qt signals for progress, reads MacroDocument as read-only snapshot
4. MacroEditorWidget (main thread) — QAbstractTableModel + QTableView, computes MoveGroup rows at display time
5. MacroRepository (main thread) — JSON load/save only, no Qt or pynput dependencies
6. MainWindow — app shell, menus, toolbar, DPI awareness call, hotkey registration

**Build order:** Data model → Engines → Controllers → UI Foundation → Wire everything (first runnable milestone) → Editor features (grouping, delegates) → Flow control (goto/label, Window Focus).

See `.planning/research/ARCHITECTURE.md` for full threading model, signal map, data flow diagrams, and code patterns.

### Critical Pitfalls

1. **pynput callbacks touching Qt widgets directly** — causes silent crashes in Qt's C++ layer with no Python traceback. Prevention: never touch any Qt object from a pynput callback; use `queue.Queue` + QTimer drain pattern exclusively. Must be correct from the first line of recording code — not retrofittable.

2. **DPI awareness not set before QApplication** — causes wrong mouse coordinates on all modern Windows laptops at 125%/150%/200% scaling. Prevention: `ctypes.windll.shcore.SetProcessDpiAwareness(2)` must be literally the first call in `main.py`, before any imports of PyQt6 or pynput. Changing this after macro files exist risks invalidating stored coordinates.

3. **Playback timing drift from naive time.sleep()** — Windows scheduler at 15.6ms tick makes per-event `sleep(dt)` accumulate 50–200ms drift per second of playback. Prevention: use absolute `time.perf_counter()` targets with coarse sleep + final busy-wait spin. Implement correctly from the start — timing bugs are reported by users as "wrong speed" and require a rewrite to fix.

4. **PyQt6 widget calls from background threads** — identical root cause to pitfall 1 but from PlaybackEngine's QThread. Prevention: all worker-to-UI communication must go through Qt signals; establish as code review rule from project start.

5. **No version field in macro JSON** — adding it after files exist in the wild requires treating all existing files as "version 0". Prevention: include `"version": 1` in every saved file from the first save implementation. Free to add, expensive to retrofit.

See `.planning/research/PITFALLS.md` for goto/label pitfalls, input suppression limitations, and the "looks done but isn't" verification checklist.

## Implications for Roadmap

Based on combined research, the dependency graph from ARCHITECTURE.md and the pitfall-to-phase mapping from PITFALLS.md, the following phase structure is recommended.

### Phase 1: Foundation and Core Recording

**Rationale:** Thread safety, DPI handling, and the data model must be correct before any feature is built on top. These cannot be retrofitted. The pixel threshold filter must be part of recording from day one — without it, the editor is immediately unusable. The macro JSON format must include a version field from the first save.

**Delivers:** Working recording pipeline that captures mouse and keyboard input, filters noise via pixel threshold, and stores a MacroDocument. App shell with dark theme. Correct DPI behavior verified at 125%/150%/200% scaling.

**Addresses:** Record mouse/keyboard, pixel threshold filter, save/load JSON (with version field), dark theme, macro library panel (basic).

**Avoids:** pynput→Qt thread crash (queue pattern), DPI coordinate mismatch, high-frequency event storage, missing version field.

### Phase 2: Core Playback

**Rationale:** Once recording works, playback is the immediate validation of the core loop. The pc-based interpreter must be implemented from the start — not a for-loop that gets rewritten when goto support is added later.

**Delivers:** Macro playback with correct timing, configurable speed multiplier, repeat N times, stop hotkey. First end-to-end working milestone: record → save → load → play.

**Addresses:** Playback with timing fidelity, playback speed multiplier, repeat N times + stop hotkey.

**Avoids:** Timing drift (perf_counter pattern), busy-wait on main thread (QThread required), stop flag checked every action.

### Phase 3: Visual Block Editor

**Rationale:** With record and play working, the editor is what makes the tool usable rather than just a recorder. Mouse move auto-grouping and group duration editing are the primary differentiators — they are sequentially dependent (grouping before duration editing) and both ship in this phase.

**Delivers:** QAbstractTableModel-backed block editor with MoveGroup row computation, inline editing via custom delegates, drag-and-drop reorder, multi-select, delete/copy/paste. Group duration editing with proportional timestamp scaling.

**Addresses:** Visual block editor, delete/reorder/copy actions, mouse move auto-grouping, group duration editing, multi-select action blocks.

**Avoids:** Storing groups in MacroDocument (view-layer pattern only), blocking UI during model update (batch inserts via QTimer).

### Phase 4: Flow Control and Window Management

**Rationale:** Once the core record-edit-play loop is proven with real macros, the next highest-value features are Label/Goto (enables loops within macros) and Window Focus (prevents coordinate drift — the most common failure mode for game automation macros). These are sequentially dependent: Label blocks must exist before Goto and Window Focus can reference them.

**Delivers:** Label blocks, Goto blocks, Window Focus action with title matching modes (contains/exact/starts-with) and failure path to label, Interactive window picker dialog, Set window position/size, Macro chaining (Run macro block).

**Addresses:** Label + Goto flow control, Window Focus action, Interactive window picker, Set window position/size, Macro chaining.

**Avoids:** Jump to nonexistent label (validate at load time), infinite loop without stop (stop flag checked at every action), goto label index rebuilt per-jump (build once before execution).

### Phase Ordering Rationale

- Foundation (Phase 1) must precede everything: the entire threading model and DPI handling are foundational — every other layer assumes they are correct.
- Playback (Phase 2) before editor (Phase 3): the editor is more valuable once you can verify that recorded macros play back correctly. Building a polished editor before validating playback accuracy would waste effort.
- Editor (Phase 3) before flow control (Phase 4): flow control blocks (Label, Goto, Window Focus) must be editable in the block editor — the editor's delegate system must exist first.
- The ARCHITECTURE.md build order (data model → engines → controllers → UI → wire → editor features → flow control) maps cleanly to phases 1–4.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 3 (Block Editor):** QAbstractTableModel with variable-height rows (collapsed MoveGroup vs. expanded sub-rows) and custom delegates per block type is a moderately complex Qt pattern. Consider `/gsd:research-phase` for the delegate and group expansion implementation before coding.
- **Phase 4 (Window Focus):** pywin32 `SetForegroundWindow` has documented limitations (calling process must own foreground; requires `ShowWindow(SW_RESTORE)` first). The Interactive window picker (click-to-capture) requires low-level mouse hook to intercept the click without propagating it to the game. This is non-trivial and warrants research during planning.

Phases with standard patterns (skip research-phase):

- **Phase 1 (Foundation):** DPI awareness call, queue/QTimer threading pattern, JSON serialization with dataclasses are all well-documented patterns with code examples in the research files. Implement directly.
- **Phase 2 (Playback):** pc-based interpreter and perf_counter timing pattern are both specified in detail in ARCHITECTURE.md and PITFALLS.md. Implement directly.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | PyPI versions verified; PyQt6, pynput, pywin32 all have current releases. CustomTkinter "do not use" confirmed via PyPI last-release date. |
| Features | HIGH | Cross-validated across 5 competitor products with documented feature lists. MVP definition is opinionated and grounded in competitor analysis. |
| Architecture | HIGH | Patterns derived from official Qt6 model/view docs, pynput threading docs, and MSDN hook documentation. Code examples are concrete and correct. |
| Pitfalls | HIGH | All critical pitfalls verified against official documentation (Microsoft DPI docs, Qt threading docs, pynput FAQ). Timing pitfall verified against Python stdlib. |

**Overall confidence:** HIGH

### Gaps to Address

- **pyqtdarktheme maintenance status:** Original repo maintenance is unclear; the `PyQtDarkTheme-fork` (2.3.4) exists as a fallback. Monitor during Phase 1 — switch to fork if the original fails to install cleanly on the target Python version.
- **pynput suppress=True for games:** Documented as unreliable for DirectInput/RawInput games. Accepted as a product limitation — document for users, do not attempt to fix. If suppression becomes a hard requirement, it requires a separate kernel-driver research spike (Interception driver).
- **Relative-to-window coordinates:** High user value for preventing coordinate drift when game windows move, but high implementation complexity. Deferred to v2+. Validate demand by shipping Window Focus first and observing user feedback.
- **Macro chaining recursion depth:** RunMacroBlock can create circular chains. ARCHITECTURE.md recommends a depth limit of 10. Validate this limit is surfaced clearly to users before implementing.

## Sources

### Primary (HIGH confidence)
- [PyQt6 PyPI](https://pypi.org/project/PyQt6/) — version 6.10.2, Jan 2026
- [pynput PyPI](https://pypi.org/project/pynput/) — version 1.8.1, Mar 2025; threading constraints, suppress behavior
- [pywin32 PyPI](https://pypi.org/project/pywin32/) — version 311, Jul 2025
- [PyInstaller docs](https://pyinstaller.org/en/stable/) — version 6.19.0, PyQt6 support confirmed
- [Qt6 Model/View Programming](https://doc.qt.io/qt-6/model-view-programming.html) — QAbstractTableModel pattern
- [Qt6 Threads and QObject](https://doc.qt.io/qt-6/threads-qobject.html) — signal queuing across threads
- [pynput docs — threading model](https://pynput.readthedocs.io/en/latest/keyboard.html) — callback constraints
- [Microsoft Learn — DPI and device-independent pixels](https://learn.microsoft.com/en-us/windows/win32/learnwin32/dpi-and-device-independent-pixels)
- [Microsoft Learn — High DPI Desktop Application Development](https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows)
- [Python stdlib — time.perf_counter()](https://docs.python.org/3/library/time.html)
- [AutoIt WinActivate](https://www.autoitscript.com/autoit3/docs/functions/WinActivate.htm) — WinTitleMatchMode patterns

### Secondary (MEDIUM confidence)
- [Macro Recorder (macrorecorder.com)](https://www.macrorecorder.com/) — movement consolidation, flow control features
- [Jitbit Macro Recorder](https://www.jitbit.com/macro-recorder/) — SMART-Rec relative coords, pixel color
- [PyMacroRecord (GitHub)](https://github.com/LOUDO56/PyMacroRecord) — open source Python baseline
- [Pulover's Macro Creator](https://www.macrocreator.com/) — flow control scope
- [pythonguis.com QAbstractTableModel](https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/) — model/view pattern
- [KDAB — Eight Rules of Multithreaded Qt](https://www.kdab.com/the-eight-rules-of-multithreaded-qt/)
- [pynput GitHub issue #163](https://github.com/moses-palmer/pynput/issues/163) — suppress parameter limitations
- [Building a High-Precision Mouse Macro Recorder in Python (2026)](https://edvaldoguimaraes.com.br/2026/02/09/building-a-high-precision-mouse-macro-recorder-in-python-gui-hotkeys-repeat-speed/)

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
