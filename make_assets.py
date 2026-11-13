"""Generates assets/icon.ico and assets/alarm.wav (run once: python make_assets.py)."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtGui import QGuiApplication

from core.sound import PATTERNS, write_wav
from ui.theme import make_icon_pixmap

app = QGuiApplication([])
out = Path(__file__).parent / "assets"
out.mkdir(exist_ok=True)
ok = make_icon_pixmap(256).save(str(out / "icon.ico"), "ICO")
write_wav(out / "alarm.wav", PATTERNS["Classic"])
print("icon.ico:", "ok" if ok else "FAILED", "| alarm.wav: ok")
