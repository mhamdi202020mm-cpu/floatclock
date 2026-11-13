"""Global hotkey using `keyboard` (fallback: `pynput`)."""
from PySide6.QtCore import QObject, Signal


class HotkeyManager(QObject):
    triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kb = None
        self._handle = None
        self._listener = None

    def start(self, combo: str) -> bool:
        self.stop()
        combo = (combo or "").strip().lower()
        if not combo:
            return False
        try:
            import keyboard
            self._handle = keyboard.add_hotkey(combo, self.triggered.emit)
            self._kb = keyboard
            return True
        except Exception:
            pass
        try:
            from pynput import keyboard as pk
            names = {"windows": "cmd", "win": "cmd", "meta": "cmd", "control": "ctrl"}
            parts = []
            for p in combo.split("+"):
                p = names.get(p.strip(), p.strip())
                parts.append(f"<{p}>" if len(p) > 1 else p)
            self._listener = pk.GlobalHotKeys({"+".join(parts): self.triggered.emit})
            self._listener.start()
            return True
        except Exception:
            self._listener = None
            return False

    def stop(self):
        if self._kb is not None and self._handle is not None:
            try:
                self._kb.remove_hotkey(self._handle)
            except Exception:
                pass
        self._kb = self._handle = None
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
