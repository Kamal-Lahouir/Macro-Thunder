"""UI tests for the block editor using pytest-qt.

Exercises the full editor stack (BlockTableModel + EditorPanel) without
launching MainWindow or touching pynput/hotkeys.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QAbstractItemView

from macro_thunder.models.blocks import (
    KeyPressBlock,
    MouseMoveBlock,
    DelayBlock,
)
from macro_thunder.models.document import MacroDocument
from macro_thunder.ui.editor_panel import EditorPanel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(*blocks):
    return MacroDocument(blocks=list(blocks))


def _kp(t=0.0, key="a"):
    return KeyPressBlock(key=key, direction="down", timestamp=t)


def _mv(x=0, y=0, t=0.0):
    return MouseMoveBlock(x=x, y=y, timestamp=t)


def _make_panel(qtbot, doc: MacroDocument) -> EditorPanel:
    panel = EditorPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.load_document(doc)
    return panel


# ---------------------------------------------------------------------------
# Delay block: edit duration via inline editor (regression for "too fast")
# ---------------------------------------------------------------------------

class TestDelayBlockEdit:
    def test_delay_duration_edit_bare_number(self, qtbot):
        """Editing the duration cell with a bare number (e.g. '3') updates block."""
        doc = _doc(_kp(0.0), DelayBlock(duration=0.5), _kp(1.0))
        panel = _make_panel(qtbot, doc)
        model = panel._model

        # Row 1 is the DelayBlock
        delay_index = model.index(1, 1)  # COL_VALUE = 1

        # EditRole should return bare "0.500", not "0.500s"
        edit_val = model.data(delay_index, Qt.ItemDataRole.EditRole)
        assert edit_val == "0.500", f"EditRole returned {edit_val!r}, expected bare number"

        # setData with a bare number
        ok = model.setData(delay_index, "3.0", Qt.ItemDataRole.EditRole)
        assert ok, "setData returned False"
        assert doc.blocks[1].duration == pytest.approx(3.0)

    def test_delay_duration_edit_with_s_suffix(self, qtbot):
        """Editing with an 's' suffix (e.g. '5.0s') still parses correctly."""
        doc = _doc(DelayBlock(duration=0.5))
        panel = _make_panel(qtbot, doc)
        model = panel._model

        delay_index = model.index(0, 1)
        ok = model.setData(delay_index, "5.0s", Qt.ItemDataRole.EditRole)
        assert ok
        assert doc.blocks[0].duration == pytest.approx(5.0)

    def test_delay_setdata_emits_dataChanged_not_reset(self, qtbot):
        """setData must emit dataChanged, NOT beginResetModel, so the editor survives."""
        doc = _doc(DelayBlock(duration=0.5))
        panel = _make_panel(qtbot, doc)
        model = panel._model

        reset_called = []
        model.modelReset.connect(lambda: reset_called.append(1))

        changed = []
        model.dataChanged.connect(lambda *_: changed.append(1))

        model.setData(model.index(0, 1), "2.0", Qt.ItemDataRole.EditRole)

        assert not reset_called, "setData must not call beginResetModel/endResetModel"
        assert changed, "setData must emit dataChanged"

    def test_each_insert_gets_fresh_delay_instance(self, qtbot):
        """Two inserted DelayBlocks must be independent objects."""
        from macro_thunder.ui.block_type_dialog import _BLOCK_TYPES
        import copy

        # Simulate what BlockTypeDialog._selected_block does (with copy.copy fix)
        _, proto = next(t for t in _BLOCK_TYPES if t[0] == "Delay")
        b1 = copy.copy(proto)
        b2 = copy.copy(proto)
        b1.duration = 10.0
        assert b2.duration != 10.0, "copy.copy must produce independent instances"


# ---------------------------------------------------------------------------
# Engine: DelayBlock timing (no crash, duration respected)
# ---------------------------------------------------------------------------

class TestEngineDelay:
    def test_delay_block_does_not_crash(self, qtbot):
        """PlaybackEngine must not raise AttributeError on DelayBlock."""
        import time
        from macro_thunder.engine import PlaybackEngine
        from unittest.mock import MagicMock

        mouse_ctrl = MagicMock()
        kb_ctrl = MagicMock()
        progress = []

        engine = PlaybackEngine(
            mouse_ctrl=mouse_ctrl,
            kb_ctrl=kb_ctrl,
            on_progress=lambda i, t: progress.append((i, t)),
        )

        blocks = [
            _kp(0.0, "a"),
            DelayBlock(duration=0.05),  # 50 ms — fast enough for a test
            _kp(0.1, "b"),
        ]
        engine.start(blocks, speed=1.0)
        engine._thread.join(timeout=2.0)

        assert not engine._thread.is_alive(), "Playback should finish within 2 s"
        assert len(progress) == 3, f"Expected 3 progress events, got {progress}"

    def test_delay_shifts_subsequent_blocks(self, qtbot):
        """Blocks after a delay fire at the right wall-clock time."""
        import time
        from macro_thunder.engine import PlaybackEngine
        from unittest.mock import MagicMock

        timestamps: list[float] = []

        def on_progress(i, total):
            timestamps.append(time.perf_counter())

        engine = PlaybackEngine(
            mouse_ctrl=MagicMock(),
            kb_ctrl=MagicMock(),
            on_progress=on_progress,
        )

        delay_s = 0.1  # 100 ms delay
        blocks = [
            _kp(0.0, "a"),           # fires at t0+0
            DelayBlock(duration=delay_s),
            _kp(0.05, "b"),          # should fire ~delay_s after previous
        ]
        engine.start(blocks, speed=1.0)
        engine._thread.join(timeout=3.0)

        assert len(timestamps) == 3
        gap = timestamps[2] - timestamps[0]  # total gap: ~0 + delay + 0.05
        assert gap >= delay_s * 0.8, f"Gap {gap:.3f}s too short — delay not respected"


# ---------------------------------------------------------------------------
# Editor panel: add / delete / move
# ---------------------------------------------------------------------------

class TestEditorPanelOperations:
    def test_add_block_inserts_after_selection(self, qtbot):
        doc = _doc(_kp(0.0), _kp(1.0))
        panel = _make_panel(qtbot, doc)

        # Select row 0, then insert a DelayBlock after it
        panel._table.selectRow(0)
        panel._model.insert_block(0, DelayBlock(duration=1.0))

        assert len(doc.blocks) == 3
        assert isinstance(doc.blocks[1], DelayBlock)

    def test_delete_selected_row(self, qtbot):
        doc = _doc(_kp(0.0), _kp(1.0), _kp(2.0))
        panel = _make_panel(qtbot, doc)

        panel._table.selectRow(1)
        panel._on_delete()

        assert len(doc.blocks) == 2
        assert doc.blocks[0].timestamp == pytest.approx(0.0)
        assert doc.blocks[1].timestamp == pytest.approx(2.0)

    def test_move_up(self, qtbot):
        doc = _doc(_kp(0.0, "a"), _kp(1.0, "b"), _kp(2.0, "c"))
        panel = _make_panel(qtbot, doc)

        panel._table.selectRow(1)
        panel._on_move_up()

        assert doc.blocks[0].key == "b"
        assert doc.blocks[1].key == "a"

    def test_move_down(self, qtbot):
        doc = _doc(_kp(0.0, "a"), _kp(1.0, "b"), _kp(2.0, "c"))
        panel = _make_panel(qtbot, doc)

        panel._table.selectRow(1)
        panel._on_move_down()

        assert doc.blocks[1].key == "c"
        assert doc.blocks[2].key == "b"

    def test_document_modified_emitted_on_delete(self, qtbot):
        doc = _doc(_kp(0.0), _kp(1.0))
        panel = _make_panel(qtbot, doc)

        with qtbot.waitSignal(panel.document_modified, timeout=1000):
            panel._table.selectRow(0)
            panel._on_delete()

    def test_record_here_signal_carries_flat_index(self, qtbot):
        doc = _doc(_kp(0.0), _kp(1.0), _kp(2.0))
        panel = _make_panel(qtbot, doc)

        panel._table.selectRow(1)

        with qtbot.waitSignal(panel.record_here_requested, timeout=1000) as blocker:
            panel._btn_record_here.click()

        flat_idx = blocker.args[0]
        assert flat_idx == 1  # row 1 → flat index 1


# ---------------------------------------------------------------------------
# Mouse-move group: expand / collapse
# ---------------------------------------------------------------------------

class TestGroupToggle:
    def test_group_collapses_to_one_row(self, qtbot):
        moves = [_mv(i, i, t=i * 0.01) for i in range(5)]
        doc = _doc(*moves)
        panel = _make_panel(qtbot, doc)
        model = panel._model

        # Should start collapsed: 5 moves → 1 group header row
        assert model.rowCount() == 1

    def test_expand_shows_child_rows(self, qtbot):
        moves = [_mv(i, i, t=i * 0.01) for i in range(4)]
        doc = _doc(*moves)
        panel = _make_panel(qtbot, doc)
        model = panel._model

        model.toggle_group(0)  # expand
        assert model.rowCount() == 1 + 4  # header + 4 children

    def test_collapse_hides_children(self, qtbot):
        moves = [_mv(i, i, t=i * 0.01) for i in range(4)]
        doc = _doc(*moves)
        panel = _make_panel(qtbot, doc)
        model = panel._model

        model.toggle_group(0)   # expand
        model.toggle_group(0)   # collapse
        assert model.rowCount() == 1
