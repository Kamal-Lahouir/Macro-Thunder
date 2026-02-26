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


def default_macro_dir() -> Path:
    """Returns ~/Documents/MacroThunder/, creating it if needed."""
    p = Path.home() / "Documents" / "MacroThunder"
    p.mkdir(parents=True, exist_ok=True)
    return p
