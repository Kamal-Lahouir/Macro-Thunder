"""Tests for LoopHeaderRow, LoopFooterRow, LoopChildRow in view_model.py.

Plan 07-02 TDD tests.
"""
from __future__ import annotations

import pytest
from macro_thunder.models.blocks import (
    LoopStartBlock, LoopEndBlock, DelayBlock,
    MouseMoveBlock, LabelBlock, GotoBlock,
)
from macro_thunder.models.document import MacroDocument


def make_doc(*blocks):
    return MacroDocument(blocks=list(blocks))


class TestLoopRowImports:
    def test_import_loop_header_row(self):
        from macro_thunder.models.view_model import LoopHeaderRow
        assert LoopHeaderRow is not None

    def test_import_loop_footer_row(self):
        from macro_thunder.models.view_model import LoopFooterRow
        assert LoopFooterRow is not None

    def test_import_loop_child_row(self):
        from macro_thunder.models.view_model import LoopChildRow
        assert LoopChildRow is not None


class TestRebuildDisplayRowsLoops:
    def _get_rows(self, *blocks):
        from macro_thunder.models.view_model import BlockTableModel
        doc = make_doc(*blocks)
        model = BlockTableModel(doc)
        return model._display_rows

    def test_loop_region_produces_header_child_footer(self):
        from macro_thunder.models.view_model import LoopHeaderRow, LoopChildRow, LoopFooterRow
        rows = self._get_rows(
            LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock()
        )
        assert len(rows) == 3
        assert isinstance(rows[0], LoopHeaderRow)
        assert rows[0].flat_index == 0
        assert isinstance(rows[1], LoopChildRow)
        assert rows[1].flat_index == 1
        assert rows[1].loop_header_flat_index == 0
        assert isinstance(rows[2], LoopFooterRow)
        assert rows[2].flat_index == 2

    def test_loop_with_surrounding_blocks(self):
        from macro_thunder.models.view_model import (
            BlockRow, LoopHeaderRow, LoopChildRow, LoopFooterRow
        )
        rows = self._get_rows(
            DelayBlock(0.0),
            LoopStartBlock(repeat=2),
            DelayBlock(0.0),
            DelayBlock(0.0),
            LoopEndBlock(),
            DelayBlock(0.0),
        )
        assert isinstance(rows[0], BlockRow) and rows[0].flat_index == 0
        assert isinstance(rows[1], LoopHeaderRow) and rows[1].flat_index == 1
        assert isinstance(rows[2], LoopChildRow) and rows[2].flat_index == 2
        assert isinstance(rows[3], LoopChildRow) and rows[3].flat_index == 3
        assert isinstance(rows[4], LoopFooterRow) and rows[4].flat_index == 4
        assert isinstance(rows[5], BlockRow) and rows[5].flat_index == 5

    def test_orphaned_loop_end_renders_as_block_row(self):
        from macro_thunder.models.view_model import BlockRow
        rows = self._get_rows(DelayBlock(0.0), LoopEndBlock())
        assert isinstance(rows[1], BlockRow)
        assert rows[1].flat_index == 1

    def test_existing_group_rows_still_work(self):
        from macro_thunder.models.view_model import GroupHeaderRow
        rows = self._get_rows(
            MouseMoveBlock(0, 0, 0.0),
            MouseMoveBlock(1, 1, 0.1),
        )
        assert len(rows) == 1
        assert isinstance(rows[0], GroupHeaderRow)

    def test_empty_loop_region(self):
        from macro_thunder.models.view_model import LoopHeaderRow, LoopFooterRow
        rows = self._get_rows(LoopStartBlock(repeat=1), LoopEndBlock())
        assert len(rows) == 2
        assert isinstance(rows[0], LoopHeaderRow)
        assert isinstance(rows[1], LoopFooterRow)


class TestBlockValueLoop:
    def test_loop_start_value(self):
        from macro_thunder.models.view_model import _block_value
        b = LoopStartBlock(repeat=5)
        assert _block_value(b) == "repeat x5"

    def test_loop_end_value(self):
        from macro_thunder.models.view_model import _block_value
        b = LoopEndBlock()
        assert _block_value(b) == "end loop"


class TestPlaybackHighlightLoopRows:
    def _make_model(self, *blocks):
        from macro_thunder.models.view_model import BlockTableModel
        doc = make_doc(*blocks)
        return BlockTableModel(doc)

    def test_playback_on_loop_header(self):
        model = self._make_model(LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock())
        model.set_playback_flat_index(0)
        assert model._playback_flat_index == 0

    def test_playback_on_loop_child(self):
        model = self._make_model(LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock())
        model.set_playback_flat_index(1)
        assert model._playback_flat_index == 1

    def test_playback_on_loop_footer(self):
        model = self._make_model(LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock())
        model.set_playback_flat_index(2)
        assert model._playback_flat_index == 2


class TestDeleteLoopRows:
    def _make_model(self, *blocks):
        from macro_thunder.models.view_model import BlockTableModel
        doc = make_doc(*blocks)
        return BlockTableModel(doc)

    def test_delete_loop_header_removes_only_boundaries_not_children(self):
        """Bug 1 regression: pair-delete of LoopHeader must NOT remove children."""
        from macro_thunder.models.view_model import LoopHeaderRow, BlockRow
        model = self._make_model(
            DelayBlock(0.0),         # flat 0 — outside, stays
            LoopStartBlock(repeat=2), # flat 1 — header → deleted
            DelayBlock(0.0),         # flat 2 — child → becomes normal block
            LoopEndBlock(),          # flat 3 — footer → deleted
            DelayBlock(0.0),         # flat 4 — outside, stays
        )
        assert isinstance(model._display_rows[1], LoopHeaderRow)
        model.delete_rows([1])
        # Only boundaries removed; 3 Delay blocks remain
        assert len(model._doc.blocks) == 3
        assert all(isinstance(b, DelayBlock) for b in model._doc.blocks)
        # After rebuild, all rows are plain BlockRows (no loop rows)
        assert all(isinstance(r, BlockRow) for r in model._display_rows)

    def test_delete_loop_footer_removes_only_boundaries_not_children(self):
        """Bug 1 regression: pair-delete of LoopFooter must NOT remove children."""
        from macro_thunder.models.view_model import LoopFooterRow, BlockRow
        model = self._make_model(
            LoopStartBlock(repeat=2), # flat 0 — header → deleted
            DelayBlock(0.0),         # flat 1 — child → becomes normal block
            DelayBlock(0.0),         # flat 2 — child → becomes normal block
            LoopEndBlock(),          # flat 3 — footer → deleted
            DelayBlock(0.0),         # flat 4 — outside, stays
        )
        assert isinstance(model._display_rows[3], LoopFooterRow)
        model.delete_rows([3])
        # Only boundaries removed; 3 Delay blocks remain
        assert len(model._doc.blocks) == 3
        assert all(isinstance(b, DelayBlock) for b in model._doc.blocks)
        # After rebuild, all rows are plain BlockRows (no loop rows)
        assert all(isinstance(r, BlockRow) for r in model._display_rows)

    def test_loop_child_type_label_is_block_type_not_loop_body(self):
        """Bug 2 regression: LoopChildRow COL_TYPE must show actual block type."""
        from macro_thunder.models.view_model import BlockTableModel, LoopChildRow, COL_TYPE
        from PyQt6.QtCore import Qt
        doc = make_doc(LoopStartBlock(repeat=2), DelayBlock(0.0), LoopEndBlock())
        model = BlockTableModel(doc)
        # Row 1 is the LoopChildRow for the DelayBlock
        assert isinstance(model._display_rows[1], LoopChildRow)
        label = model.data(model.index(1, COL_TYPE), Qt.ItemDataRole.DisplayRole)
        # Must show the actual type, not "Loop Body"
        assert "delay" in label.lower() or "Delay" in label
        assert "loop" not in label.lower() or "Loop Body" not in label

    def test_loop_child_type_label_for_key_press(self):
        """Bug 2 regression: KeyPressBlock inside loop shows its own type."""
        from macro_thunder.models.view_model import BlockTableModel, LoopChildRow, COL_TYPE
        from macro_thunder.models.blocks import KeyPressBlock
        from PyQt6.QtCore import Qt
        kp = KeyPressBlock(key="a", direction="down", timestamp=0.0)
        doc = make_doc(LoopStartBlock(repeat=1), kp, LoopEndBlock())
        model = BlockTableModel(doc)
        assert isinstance(model._display_rows[1], LoopChildRow)
        label = model.data(model.index(1, COL_TYPE), Qt.ItemDataRole.DisplayRole)
        assert "key" in label.lower() or "Key" in label
        assert "Loop Body" not in label
