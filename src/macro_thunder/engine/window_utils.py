"""Win32 window management helpers for the playback engine.

Pure-Python helpers (_title_matches) are unit-testable without a live Windows
session.  ctypes helpers (_find_window, _activate_window, _set_window_rect,
_hwnd_from_point, _get_window_info) require a real Windows desktop session and
are tested manually via the human-verify checkpoint.

All ctypes patterns taken from 04-RESEARCH.md verified code examples.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import os

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------
SW_RESTORE = 9
SW_SHOW = 5
GA_ROOT = 2
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# ---------------------------------------------------------------------------
# ctypes setup
# ---------------------------------------------------------------------------
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
)


# ---------------------------------------------------------------------------
# Pure-Python helper — fully unit-testable
# ---------------------------------------------------------------------------

def _title_matches(title_query: str, window_title: str, match_mode: str) -> bool:
    """Return True if window_title matches title_query under the given mode.

    All comparisons are case-insensitive.

    match_mode values:
        "Contains"   — title_query is a substring of window_title
        "Exact"      — title_query equals window_title
        "Starts With"— window_title starts with title_query
        (any other)  — falls back to Contains
    """
    q = title_query.lower()
    t = window_title.lower()
    if match_mode == "Exact":
        return q == t
    elif match_mode == "Starts With":
        return t.startswith(q)
    else:
        # Contains (default / fallback)
        return q in t


# ---------------------------------------------------------------------------
# ctypes helpers — require live Windows session
# ---------------------------------------------------------------------------

def _get_visible_windows() -> list[tuple[int, str, str]]:
    """Return list of (hwnd, exe_basename, title) for visible top-level windows."""
    results: list[tuple[int, str, str]] = []

    def _cb(hwnd: int, _: int) -> bool:
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
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
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


def _find_window(executable: str, title: str, match_mode: str) -> int | None:
    """Return hwnd of the first matching visible window, or None.

    executable is matched as a case-insensitive substring of the process's
    executable basename (empty string matches any executable).
    title is matched using _title_matches with match_mode.
    """
    exe_lower = executable.lower()
    for hwnd, exe, win_title in _get_visible_windows():
        exe_match = (not exe_lower) or (exe_lower in exe.lower())
        if exe_match and _title_matches(title, win_title, match_mode):
            return hwnd
    return None


def _activate_window(hwnd: int) -> None:
    """Bring hwnd to the foreground using the AttachThreadInput reliable pattern.

    See 04-RESEARCH.md Pitfall 1 for why bare SetForegroundWindow is unreliable.
    """
    # Only restore if minimized — don't un-maximize a fullscreen window
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)
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


def _set_window_rect(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    """Reposition and resize hwnd without changing Z-order or activation."""
    user32.SetWindowPos(hwnd, 0, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)


def _hwnd_from_point(x: int, y: int) -> int:
    """Return the root (top-level) HWND at screen coordinates (x, y).

    Uses GetAncestor(GA_ROOT) to walk up from child HWNDs to the top-level
    window, avoiding the Pitfall 2 issue of capturing child widget HWNDs.
    """
    pt = ctypes.wintypes.POINT(x, y)
    hwnd = user32.WindowFromPoint(pt)
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return root if root else hwnd


def _get_window_info(hwnd: int) -> tuple[str, str]:
    """Return (title, exe_basename) for the given hwnd."""
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    title = buf.value

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if h:
        size = ctypes.wintypes.DWORD(512)
        path_buf = ctypes.create_unicode_buffer(512)
        if kernel32.QueryFullProcessImageNameW(h, 0, path_buf, ctypes.byref(size)):
            exe = os.path.basename(path_buf.value)
        kernel32.CloseHandle(h)
    return title, exe
