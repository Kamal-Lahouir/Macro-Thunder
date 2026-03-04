from __future__ import annotations

import json
import dataclasses
from pathlib import Path

from macro_thunder.models.blocks import block_from_dict
from macro_thunder.models.document import MacroDocument, CURRENT_VERSION


def save(doc: MacroDocument, path: Path) -> None:
    """Write a MacroDocument to a JSON file with 2-space indentation."""
    data = {
        "version": doc.version,
        "name": doc.name,
        "blocks": [dataclasses.asdict(b) for b in doc.blocks],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(path: Path) -> MacroDocument:
    """Load a MacroDocument from a JSON file."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" not in data:
        raise ValueError(f"Missing 'version' field in {path}")
    blocks = [block_from_dict(b) for b in data.get("blocks", [])]
    return MacroDocument(
        name=data.get("name", path.stem),
        version=data["version"],
        blocks=blocks,
    )


def rename_macro(old_path: Path, new_name: str) -> Path:
    """Rename macro file on disk and update doc.name inside the JSON.
    Returns the new Path."""
    old_path = Path(old_path)
    new_path = old_path.parent / f"{new_name}.json"
    # Update doc.name field inside JSON
    data = json.loads(old_path.read_text(encoding="utf-8"))
    data["name"] = new_name
    new_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if new_path != old_path:
        old_path.unlink()
    return new_path


def default_macro_dir() -> Path:
    """Returns ~/Documents/Althar/, creating it if needed."""
    p = Path.home() / "Documents" / "Althar"
    p.mkdir(parents=True, exist_ok=True)
    return p
