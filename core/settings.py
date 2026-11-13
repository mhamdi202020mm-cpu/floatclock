"""JSON settings stored in %APPDATA%/FloatClock/settings.json."""
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal

APP_NAME = "FloatClock"


def app_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def resource_path(rel: str) -> str:
    """Path to a bundled resource (works from source and from PyInstaller)."""
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent.parent
    return str(Path(base) / rel)


DEFAULTS = {
    "x": None,
    "y": None,
    "expanded_w": 340,
    "expanded_h": 380,
    "compact": False,
    "opacity": 0.95,
    "use_24h": False,
    "show_seconds": True,
    "show_date": True,
    "sound": "Classic",
    "hotkey_enabled": True,
    "hotkey": "ctrl+alt+c",
    "snooze_minutes": 5,
}


class Settings(QObject):
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.path = app_dir() / "settings.json"
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, default in DEFAULTS.items():
                    if k in raw and (default is None or isinstance(raw[k], type(default))
                                     or (isinstance(default, float) and isinstance(raw[k], int))):
                        self.data[k] = raw[k]
        except (OSError, ValueError):
            pass  # missing or corrupt file -> defaults

    def save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    def get(self, key):
        return self.data.get(key, DEFAULTS[key])

    def set(self, key, value):
        if self.data.get(key) == value:
            return
        self.data[key] = value
        self.save()
        self.changed.emit(key)
