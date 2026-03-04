"""Regression tests for the stale sentinel / amber cursor bug.

When the user presses Stop hotkey during playback, the engine eventually
puts a (-1, -1) sentinel into the progress queue.  The drain loop in
_update_status must NOT call _stop_play again if the state is already IDLE.

We test the guard condition in isolation without instantiating QApplication
by extracting the decision logic into a helper and verifying its behaviour.
"""
from __future__ import annotations

import enum
import queue


# ---------------------------------------------------------------------------
# Minimal stub that mirrors the decision logic in MainWindow._update_status
# ---------------------------------------------------------------------------

class AppState(enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PLAYING = "playing"


def drain_once(state: AppState, sentinel_queue: queue.Queue, stop_play_calls: list) -> AppState:
    """Simulate one pass of the _update_status sentinel drain.

    Returns the resulting state. If sentinel arrives and state is PLAYING,
    calls _stop_play (appends 'stop' to stop_play_calls) and returns IDLE.
    If sentinel arrives and state is not PLAYING, discards it and returns state.
    Progress items (idx >= 0) are always applied.
    """
    while not sentinel_queue.empty():
        try:
            idx, total = sentinel_queue.get_nowait()
        except queue.Empty:
            break
        if idx == -1 and total == -1:
            # FIXED guard: only stop if still playing
            if state == AppState.PLAYING:
                stop_play_calls.append("stop")
                state = AppState.IDLE
            break
        else:
            # Normal progress update — always applied
            stop_play_calls.append(f"progress:{idx}")
    return state


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSentinelGuard:
    """Sentinel (-1,-1) must not clear amber cursor when state is already IDLE."""

    def test_sentinel_does_not_call_stop_play_when_idle(self):
        """Bug scenario: hotkey already stopped playback; stale sentinel arrives."""
        q = queue.Queue()
        q.put((-1, -1))
        calls: list[str] = []

        result_state = drain_once(AppState.IDLE, q, calls)

        assert "stop" not in calls, "stop_play must NOT be called when state is IDLE"
        assert result_state == AppState.IDLE

    def test_sentinel_calls_stop_play_when_playing(self):
        """Normal completion: engine finishes naturally; sentinel should stop playback."""
        q = queue.Queue()
        q.put((-1, -1))
        calls: list[str] = []

        result_state = drain_once(AppState.PLAYING, q, calls)

        assert "stop" in calls, "stop_play MUST be called when state is PLAYING"
        assert result_state == AppState.IDLE

    def test_sentinel_does_not_call_stop_play_when_recording(self):
        """Sentinel arriving during RECORDING state must also be ignored."""
        q = queue.Queue()
        q.put((-1, -1))
        calls: list[str] = []

        result_state = drain_once(AppState.RECORDING, q, calls)

        assert "stop" not in calls
        assert result_state == AppState.RECORDING

    def test_progress_update_always_applied(self):
        """Normal progress items (idx >= 0) are always forwarded regardless of state."""
        q = queue.Queue()
        q.put((3, 10))
        calls: list[str] = []

        drain_once(AppState.PLAYING, q, calls)

        assert "progress:3" in calls

    def test_progress_update_applied_even_when_idle(self):
        """Progress items are forwarded even if somehow state is IDLE."""
        q = queue.Queue()
        q.put((0, 5))
        calls: list[str] = []

        drain_once(AppState.IDLE, q, calls)

        assert "progress:0" in calls
