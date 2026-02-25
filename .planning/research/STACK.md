# Stack Research

**Domain:** Python Windows desktop macro recorder and editor
**Researched:** 2026-02-25
**Confidence:** MEDIUM-HIGH (core libraries verified via PyPI; some rationale from WebSearch)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime | 3.11 offers meaningful perf gains over 3.9/3.10; 3.12+ still has packaging friction with some Win32 packages. 3.11 hits the sweet spot of speed, compatibility, and ecosystem maturity as of early 2026. |
| PyQt6 | 6.10.2 | UI framework | The only Python GUI framework with the widget power needed: `QAbstractTableModel` + `QTableView` for the block editor, drag-and-drop reordering, custom delegates for inline editing, dockable panels. CustomTkinter cannot do this without reinventing Qt. PyQt6 is actively maintained (Jan 2026 release), targets Win32 natively, and scales to complex UIs. Personal/GPL-licensed use is free. |
| pynput | 1.8.1 | Mouse and keyboard capture/recording | Clean event-driven API with `Listener` threads for mouse and keyboard independently. `GlobalHotKeys` provides stop-recording hotkey out of the box. v1.8.0 (Mar 2025) added injected event detection — critical for not recording your own playback events. Well-maintained, widely deployed. |
| pywin32 | 311 | Win32 window management | `win32gui.FindWindow`, `win32gui.EnumWindows`, `win32gui.SetForegroundWindow`, `win32gui.GetWindowRect`, `win32gui.SetWindowPos` — the full Window Focus action feature depends on this. pywin32 is the authoritative Python binding for Win32 APIs, not a wrapper around ctypes. |
| json (stdlib) | built-in | Macro file storage | Macros are human-readable structured data with a simple schema. JSON files are trivially editable outside the app, diffable in git, and require zero dependencies. SQLite is overkill for this domain — there are no relational queries, no concurrent writers, and no search across macros at runtime. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyqtdarktheme | 2.1.0 | Dark theme for PyQt6 | Apply once at app startup with `qdarktheme.setup_theme()`. Provides a flat, modern dark palette across all Qt widgets without CSS gymnastics. Use the `PyQtDarkTheme-fork` (2.3.4) if the original goes unmaintained. |
| pyinstaller | 6.19.0 | Packaging to Windows EXE | Single command packaging, native PyQt6 support out of the box, no C toolchain required. For a personal-use tool, startup time and code protection are non-concerns — PyInstaller wins on simplicity. |
| ctypes (stdlib) | built-in | DPI awareness + fallback Win32 | Call `ctypes.windll.shcore.SetProcessDpiAwareness(2)` at startup before any window is created. Also use `ctypes.windll.user32` for any Win32 calls that pywin32 doesn't expose cleanly (rare). |
| threading / queue (stdlib) | built-in | Async event dispatch | pynput listener callbacks run on a system thread. Never block in a callback — dispatch to a `queue.Queue` and consume in a worker thread. Prevents input freeze during recording. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Qt Designer (via pyqt6-tools) | Visual UI layout for main shell | Use for the outer application shell (main window, panels, menus). The block editor itself must be built programmatically with `QAbstractTableModel` — Qt Designer cannot model that. |
| black | Code formatting | `pip install black`. Standard formatter, no config required. |
| pyright | Type checking | Understands PyQt6 stubs. Catches signal/slot mismatches before runtime. `pip install pyright`. |

---

## Installation

```bash
# Core runtime dependencies
pip install PyQt6==6.10.2
pip install pynput==1.8.1
pip install pywin32==311
pip install pyqtdarktheme==2.1.0

# Packaging
pip install pyinstaller==6.19.0

# Dev tools
pip install pyqt6-tools black pyright
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PyQt6 | CustomTkinter 5.2.2 | Only if the app is a simple utility with no complex data views. CustomTkinter has no equivalent to `QAbstractTableModel`; building the block editor would require writing a custom canvas widget from scratch. Additionally, CustomTkinter's last PyPI release was Jan 2024 — it is effectively unmaintained as of early 2026. Do not use it. |
| PyQt6 | wxPython | wxPython uses native Win32 controls which gives a more "Windows-native" look, but its Python API is verbose and its theming story is poor. Dark mode requires platform hacks. Not worth it when PyQt6 achieves dark theme cleanly. |
| PyQt6 | tkinter (stdlib) | tkinter is adequate for toy apps. It has no model/view architecture, no native drag-and-drop for list reordering, and dark theming is a hack. Eliminated immediately for this use case. |
| pynput | pyWin32 raw hooks | pywin32 can install low-level `SetWindowsHookEx` hooks directly, but this requires a Windows message pump running on the correct thread, produces significantly more boilerplate, and the callback restrictions are identical to pynput's (don't block the hook thread). pynput wraps all of this cleanly. Only drop to raw pywin32 hooks if you need to suppress game inputs (e.g., block a key from reaching a game process) — pynput's `suppress=True` is unreliable for games due to driver-level input in DirectInput/RawInput games. |
| pynput | keyboard + mouse (pip) | These packages have less active maintenance, less complete documentation, and pynput's combined listener model is cleaner for a recorder that needs both simultaneously. |
| JSON files | SQLite | Use SQLite only if the macro library grows to hundreds of macros and you add search/filter features. For the current scope (named macro files, load one at a time), JSON is the right choice — it's human-readable, git-friendly, and requires no schema migration story. |
| PyInstaller | Nuitka | Nuitka requires a C toolchain (MSVC or MinGW), significantly longer build times, and produces larger output for PyQt6 apps (which already bundle Qt DLLs). Performance gains from Nuitka are irrelevant for a UI-bound macro tool. For personal distribution, PyInstaller is correct. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| CustomTkinter | Last released Jan 2024, no model/view architecture, cannot build a row-based block editor without massive custom work | PyQt6 |
| tkinter (plain) | No dark theme without hacks, no drag-and-drop reorder, no `QAbstractItemModel` equivalent | PyQt6 |
| PyAutoGUI | Designed for playback-only automation, not recording. No event listener model. API is a collection of functions, not a foundation for an editor. | pynput for recording, pywin32 for Win32 calls |
| PyUserInput | Abandoned (last commit 2015), archived on GitHub | pynput |
| Electron/Tauri with Python backend | Extreme overkill, adds 150MB+ to distribution, complicates Win32 API access, introduces a JS/web layer with no benefit for this use case | PyQt6 native |
| pickle for macro storage | Not human-readable, not diffable, security risk (arbitrary code execution on load), version fragile | JSON |
| Binary custom format | Needless complexity for a macro recorder; no tooling for debugging corrupted files | JSON |

---

## Stack Patterns by Variant

**If game inputs need to be suppressed from reaching a DirectInput/RawInput game during recording:**
- pynput's `suppress=True` will NOT work reliably for DirectInput games
- Research `Interception` driver or `SendInput` with `LLMHF_INJECTED` flag detection
- This is a deferred concern — not in current scope

**If packaging for distribution to other users (not personal use only):**
- PyQt6's GPL license requires open-sourcing the application OR purchasing a commercial license from Riverbank Computing
- Switch to PySide6 (LGPL, same Qt6 API, drop-in compatible with minor import changes) to avoid GPL obligations
- PySide6 latest: 6.8.x (Jan 2026)

**If the macro library needs to scale beyond ~100 macros with search:**
- Migrate storage to SQLite with `sqlite3` stdlib
- Keep JSON as the export/import format for individual macros (portability)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| PyQt6 6.10.x | Python 3.9–3.14 | Tested. Requires Python >= 3.9. |
| pynput 1.8.1 | Python 3.x | No specific upper bound noted. Works on Windows 10/11. |
| pywin32 311 | Python 3.8–3.14 | Build wheels available for all current CPython versions. |
| pyqtdarktheme 2.1.0 | PyQt6, PySide6, PyQt5 | Call `qdarktheme.setup_theme()` after `QApplication` is created, before any windows are shown. |
| PyInstaller 6.19.0 | Python 3.8–3.14, PyQt6 | PyQt6 is explicitly listed as supported out of the box. Use `--windowed` flag to suppress the console on Windows. |

---

## DPI Awareness — Required Startup Sequence

DPI awareness must be set before creating the `QApplication`, and also before pynput starts recording (otherwise mouse coordinates will be wrong on high-DPI displays):

```python
import ctypes
# Must be called before QApplication() and before any pynput listener starts
ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
```

Both pynput and PyQt6 document this requirement. Failure to set it causes incorrect mouse coordinate capture on 125%/150%/200% display scaling — a near-universal issue on modern Windows laptops.

---

## Sources

- [pynput PyPI](https://pypi.org/project/pynput/) — version 1.8.1, Mar 17 2025, LGPL-3.0. HIGH confidence.
- [PyQt6 PyPI](https://pypi.org/project/PyQt6/) — version 6.10.2, Jan 8 2026, GPL v3. HIGH confidence.
- [pywin32 PyPI](https://pypi.org/project/pywin32/) — version 311, Jul 14 2025, PSF license. HIGH confidence.
- [customtkinter PyPI](https://pypi.org/project/customtkinter/) — version 5.2.2, Jan 10 2024, confirmed inactive as of early 2026. HIGH confidence on "do not use" recommendation.
- [PyInstaller PyPI / docs](https://pyinstaller.org/en/stable/installation.html) — version 6.19.0, PyQt6 explicitly supported. HIGH confidence.
- [pyqtdarktheme PyPI](https://pypi.org/project/pyqtdarktheme/) — version 2.1.0. MEDIUM confidence (original repo maintenance status unclear; fork available).
- [pynput GlobalHotKeys / suppress docs](https://pynput.readthedocs.io/en/latest/keyboard.html) — threading constraints, suppress behavior. HIGH confidence.
- [pythonguis.com QAbstractTableModel PyQt6](https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/) — model/view pattern confirmation. MEDIUM confidence (tutorial, not official Qt docs).
- [sqlite.org - When to Use SQLite](https://sqlite.org/whentouse.html) — confirms SQLite for desktop file format. HIGH confidence.
- WebSearch: PyInstaller vs Nuitka comparison — MEDIUM confidence (multiple sources agree on ease-of-use tradeoff).
- WebSearch: pynput suppress=True unreliable for games — MEDIUM confidence (GitHub issues confirm, not official docs).

---

*Stack research for: Python Windows desktop macro recorder (Macro Thunder)*
*Researched: 2026-02-25*
