# tests/test_serializer.py
import json
import pytest
from pathlib import Path
from macro_thunder.models.blocks import (
    MouseMoveBlock, MouseClickBlock, MouseScrollBlock, KeyPressBlock,
    DelayBlock, WindowFocusBlock, LabelBlock, GotoBlock,
    ActionBlock, block_from_dict,
)
from macro_thunder.models.document import MacroDocument, CURRENT_VERSION
from macro_thunder.persistence.serializer import save, load


# --- block_from_dict tests ---

def test_block_from_dict_mouse_move():
    block = block_from_dict({"type": "MouseMove", "x": 100, "y": 200, "timestamp": 0.5})
    assert isinstance(block, MouseMoveBlock)
    assert block.x == 100
    assert block.y == 200
    assert block.timestamp == 0.5

def test_block_from_dict_all_types():
    """All 8 block types can be round-tripped through block_from_dict."""
    import dataclasses
    samples = [
        MouseMoveBlock(x=10, y=20, timestamp=0.1),
        MouseClickBlock(x=50, y=60, button="left", direction="down", timestamp=0.2),
        MouseScrollBlock(x=0, y=0, dx=0, dy=-3, timestamp=0.3),
        KeyPressBlock(key="a", direction="down", timestamp=0.4),
        DelayBlock(duration=1.0),
        WindowFocusBlock(executable="game.exe", title="Game", match_mode="Contains"),
        LabelBlock(name="loop_start"),
        GotoBlock(target="loop_start"),
    ]
    for original in samples:
        d = dataclasses.asdict(original)
        reconstructed = block_from_dict(d)
        assert dataclasses.asdict(reconstructed) == d, f"Round-trip failed for {original.type}"

def test_block_from_dict_unknown_type_raises():
    with pytest.raises(KeyError):
        block_from_dict({"type": "UnknownType", "x": 0})

def test_block_type_field_is_not_init_param():
    """type field must not be accepted as constructor argument."""
    # This verifies field(default="MouseMove", init=False) is used
    with pytest.raises(TypeError):
        MouseMoveBlock(type="MouseMove", x=0, y=0, timestamp=0.0)


# --- save/load tests ---

def test_save_creates_file_with_version(tmp_path):
    doc = MacroDocument(name="test_macro", blocks=[MouseMoveBlock(x=1, y=2, timestamp=0.0)])
    path = tmp_path / "test.json"
    save(doc, path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "version" in data
    assert data["version"] == CURRENT_VERSION

def test_save_pretty_printed(tmp_path):
    doc = MacroDocument(name="pretty_test")
    path = tmp_path / "pretty.json"
    save(doc, path)
    raw = path.read_text(encoding="utf-8")
    # 2-space indent means we'll have leading spaces on second line
    assert "  " in raw

def test_save_load_round_trip(tmp_path):
    import dataclasses
    blocks = [
        MouseMoveBlock(x=10, y=20, timestamp=0.0),
        MouseClickBlock(x=50, y=60, button="right", direction="up", timestamp=0.1),
        MouseScrollBlock(x=0, y=0, dx=0, dy=1, timestamp=0.2),
        KeyPressBlock(key="Key.shift", direction="down", timestamp=0.3),
        DelayBlock(duration=0.5),
        WindowFocusBlock(executable="app.exe", title="App", match_mode="Exact"),
        LabelBlock(name="end"),
        GotoBlock(target="end"),
    ]
    doc = MacroDocument(name="full_roundtrip", blocks=blocks)
    path = tmp_path / "full.json"
    save(doc, path)
    loaded = load(path)
    assert loaded.name == doc.name
    assert loaded.version == doc.version
    assert len(loaded.blocks) == len(doc.blocks)
    for orig, restored in zip(doc.blocks, loaded.blocks):
        assert dataclasses.asdict(orig) == dataclasses.asdict(restored)

def test_load_missing_version_raises(tmp_path):
    path = tmp_path / "no_version.json"
    path.write_text(json.dumps({"name": "bad", "blocks": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        load(path)

def test_load_empty_blocks(tmp_path):
    doc = MacroDocument(name="empty")
    path = tmp_path / "empty.json"
    save(doc, path)
    loaded = load(path)
    assert loaded.blocks == []
    assert loaded.name == "empty"
