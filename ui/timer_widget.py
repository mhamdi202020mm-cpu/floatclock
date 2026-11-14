import math
import time

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

PRESETS = [5, 10, 25, 60]


def fmt(seconds: int) -> str:
    h, rem = divmod(max(0, seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class TimerWidget(QWidget):
    """Countdown based on an absolute end timestamp (wall clock), so it stays
    correct across UI lag and system sleep."""
    finished = Signal()
    display_changed = Signal(object, float, bool)  # text|None, progress 0..1, paused

    IDLE, RUNNING, PAUSED = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = self.IDLE
        self._total = 0
        self._end = 0.0
        self._remaining = 0.0

        self.display = QLabel("05:00")
        self.display.setObjectName("timerDisplay")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Timer progress")
        self.display.setAccessibleName("Time remaining")

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 999)
        self.min_spin.setValue(5)
        self.min_spin.setSuffix(" min")
        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)
        self.sec_spin.setSuffix(" sec")
        self.min_spin.valueChanged.connect(self._input_changed)
        self.sec_spin.valueChanged.connect(self._input_changed)

        inputs = QHBoxLayout()
        inputs.addStretch(1)
        inputs.addWidget(self.min_spin)
        inputs.addWidget(self.sec_spin)
        inputs.addStretch(1)

        presets = QHBoxLayout()
        for m in PRESETS:
            b = QPushButton(f"{m}m")
            b.clicked.connect(lambda _=False, m=m: self.set_preset(m))
            presets.addWidget(b)

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.toggle)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset)
        buttons = QHBoxLayout()
        buttons.addWidget(self.start_btn, 2)
        buttons.addWidget(self.reset_btn, 1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(8)
        lay.addWidget(self.display)
        lay.addWidget(self.progress)
        lay.addLayout(inputs)
        lay.addLayout(presets)
        lay.addLayout(buttons)
        lay.addStretch(1)

        self._ticker = QTimer(self)
        self._ticker.setInterval(200)
        self._ticker.timeout.connect(self._tick)

    # ---- helpers ------------------------------------------------------
    def _input_seconds(self):
        return self.min_spin.value() * 60 + self.sec_spin.value()

    def _input_changed(self):
        if self.state == self.IDLE:
            self.display.setText(fmt(self._input_seconds()))

    def _emit_display(self, rem=None):
        if self.state == self.IDLE:
            self.display_changed.emit(None, 0.0, False)
            return
        if rem is None:
            rem = self._remaining
        prog = (1 - rem / self._total) if self._total else 0.0
        self.display_changed.emit(fmt(math.ceil(rem)), max(0.0, min(1.0, prog)),
                                  self.state == self.PAUSED)

    def _set_inputs_enabled(self, on):
        self.min_spin.setEnabled(on)
        self.sec_spin.setEnabled(on)

    # ---- public actions -----------------------------------------------
    def set_preset(self, minutes):
        self.reset()
        self.min_spin.setValue(minutes)
        self.sec_spin.setValue(0)

    def toggle(self):
        if self.state == self.IDLE:
            self._total = self._input_seconds()
            if self._total <= 0:
                return
            self._end = time.time() + self._total
            self._begin()
        elif self.state == self.PAUSED:
            self._end = time.time() + self._remaining
            self._begin()
        else:  # running -> pause
            self._remaining = max(0.0, self._end - time.time())
            self.state = self.PAUSED
            self._ticker.stop()
            self.start_btn.setText("Resume")
            self._emit_display()

    def _begin(self):
        self.state = self.RUNNING
        self.start_btn.setText("Pause")
        self._set_inputs_enabled(False)
        self._ticker.start()
        self._tick()

    def reset(self):
        self._ticker.stop()
        self.state = self.IDLE
        self.start_btn.setText("Start")
        self._set_inputs_enabled(True)
        self.progress.setValue(0)
        self.display.setText(fmt(self._input_seconds()))
        self._emit_display()

    def _tick(self):
        if self.state != self.RUNNING:
            return
        rem = self._end - time.time()
        if rem <= 0:
            self._ticker.stop()
            self.state = self.IDLE
            self.start_btn.setText("Start")
            self._set_inputs_enabled(True)
            self.display.setText("00:00")
            self.progress.setValue(1000)
            self._emit_display()
            self.finished.emit()
            return
        self.display.setText(fmt(math.ceil(rem)))
        if self._total:
            self.progress.setValue(int(1000 * (1 - rem / self._total)))
        self._emit_display(rem)
