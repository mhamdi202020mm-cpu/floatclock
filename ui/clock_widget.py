from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


def format_time(dt: datetime, use_24h: bool, show_seconds: bool):
    """Returns (time_text, suffix) e.g. ('3:07:09', 'PM')."""
    if use_24h:
        t = f"{dt.hour:02d}:{dt.minute:02d}"
        suffix = ""
    else:
        t = f"{dt.hour % 12 or 12}:{dt.minute:02d}"
        suffix = "AM" if dt.hour < 12 else "PM"
    if show_seconds:
        t += f":{dt.second:02d}"
    return t, suffix


class ClockWidget(QWidget):
    def __init__(self, settings, compact=False, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.compact = compact
        self.time_label = QLabel()
        self.time_label.setObjectName("timeCompact" if compact else "time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label = QLabel()
        self.date_label.setObjectName("date")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label = QLabel()
        self.timer_label.setObjectName("timerCompact")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_progress = QProgressBar()
        self.timer_progress.setRange(0, 1000)
        self.timer_progress.setTextVisible(False)
        self.timer_label.hide()
        self.timer_progress.hide()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addStretch(1)
        lay.addWidget(self.time_label)
        if compact:
            lay.addWidget(self.timer_label)
            lay.addWidget(self.timer_progress)
        if not compact:
            lay.addWidget(self.date_label)
        lay.addStretch(1)
        self.refresh(datetime.now())

    def set_timer(self, text, progress=0.0, paused=False):
        """Compact mode: show the running timer instead of the clock (text=None -> clock)."""
        if not self.compact:
            return
        active = text is not None
        self.time_label.setVisible(not active)
        self.timer_label.setVisible(active)
        self.timer_progress.setVisible(active)
        if active:
            self.timer_label.setText(("⏸ " if paused else "") + text)
            self.timer_label.setProperty("paused", paused)
            self.timer_label.style().unpolish(self.timer_label)
            self.timer_label.style().polish(self.timer_label)
            self.timer_progress.setValue(int(progress * 1000))

    def refresh(self, now: datetime):
        s = self.settings
        t, suffix = format_time(now, s.get("use_24h"), s.get("show_seconds"))
        if suffix:
            small = "10pt" if self.compact else "14pt"
            self.time_label.setText(f'{t}<span style="font-size:{small}"> {suffix}</span>')
        else:
            self.time_label.setText(t)
        if not self.compact:
            self.date_label.setVisible(bool(s.get("show_date")))
            self.date_label.setText(now.strftime("%A, %d %B %Y"))
