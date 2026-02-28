from __future__ import annotations
import dataclasses
import json
import pathlib

SETTINGS_DIR = pathlib.Path.home() / "Documents" / "MacroThunder"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


@dataclasses.dataclass
class AppSettings:
    hotkey_start_record: str = "<f9>"
    hotkey_stop_record: str = "<f10>"
    hotkey_start_play: str = "<f6>"
    hotkey_stop_play: str = "<f8>"
    mouse_threshold_px: int = 3

    @classmethod
    def load(cls) -> "AppSettings":
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            fields = {f.name for f in dataclasses.fields(cls)}
            return cls(**{k: v for k, v in data.items() if k in fields})
        return cls()

    def save(self) -> None:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(dataclasses.asdict(self), indent=2),
            encoding="utf-8",
        )
