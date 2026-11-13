"""Alarm sounds: QSoundEffect with winsound / beep fallback.

Sounds are synthesized to .wav on demand, so the app works even if
assets/alarm.wav is missing.
"""
import math
import struct
import wave
from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QApplication

from .settings import app_dir, resource_path

try:
    import winsound
except ImportError:  # non-Windows
    winsound = None

RATE = 22050

# name -> list of (frequency Hz, seconds, decay). frequency 0 = silence.
PATTERNS = {
    "Classic": [(880, .15, False), (0, .10, False)] * 3 + [(0, .7, False)],
    "Chime": [(659, .45, True), (784, .45, True), (988, .7, True), (0, .4, False)],
    "Digital": [(1500, .08, False), (0, .08, False)] * 4 + [(0, .7, False)],
}
SOUND_NAMES = list(PATTERNS)


def write_wav(path, pattern):
    frames = bytearray()
    for freq, dur, decay in pattern:
        n = int(RATE * dur)
        for i in range(n):
            if freq == 0:
                s = 0.0
            else:
                t = i / RATE
                env = min(1.0, i / (RATE * .005), (n - i) / (RATE * .005))  # click-free edges
                if decay:
                    env *= math.exp(-3.0 * i / n)
                s = 0.45 * env * math.sin(2 * math.pi * freq * t)
            frames += struct.pack("<h", int(s * 32767))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(frames))


def ensure_sound_file(name: str):
    """Return a path to a playable .wav for `name`, or None."""
    if name not in PATTERNS:
        name = "Classic"
    try:
        if name == "Classic":
            bundled = Path(resource_path("assets/alarm.wav"))
            if bundled.is_file():
                return str(bundled)
        d = app_dir() / "sounds"
        d.mkdir(exist_ok=True)
        p = d / f"{name}.wav"
        if not p.is_file():
            write_wav(p, PATTERNS[name])
        return str(p)
    except Exception:
        return None


class SoundPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._effect = None  # created lazily: avoids touching the audio stack at startup
        self._path = None
        self._loop = False
        self._playing = False

    def start(self, name: str, loop: bool = True):
        self.stop()
        self._playing = True
        self._loop = loop
        self._path = ensure_sound_file(name)
        if not self._path:
            self._fallback()
            return
        if self._effect is None:
            try:
                self._effect = QSoundEffect(self)
                self._effect.statusChanged.connect(self._on_status)
            except Exception:
                self._effect = None
                self._fallback()
                return
        self._effect.setSource(QUrl.fromLocalFile(self._path))
        self._effect.setLoopCount(-2 if loop else 1)  # -2 == QSoundEffect.Infinite
        self._effect.setVolume(1.0)
        self._effect.play()

    def stop(self):
        self._playing = False
        if self._effect is not None:
            self._effect.stop()
        if winsound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    def _on_status(self):
        if self._playing and self._effect is not None and self._effect.status() == QSoundEffect.Status.Error:
            self._fallback()

    def _fallback(self):
        if winsound and self._path:
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if self._loop:
                flags |= winsound.SND_LOOP
            try:
                winsound.PlaySound(self._path, flags)
                return
            except Exception:
                pass
        if winsound:
            try:
                winsound.MessageBeep()
                return
            except Exception:
                pass
        QApplication.beep()
