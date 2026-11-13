from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QKeySequenceEdit,
                               QLabel, QMessageBox, QPushButton, QSlider, QVBoxLayout)

from core import startup
from core.sound import SOUND_NAMES, SoundPlayer


class SettingsDialog(QDialog):
    """Changes apply immediately; there is no OK/Cancel."""

    def __init__(self, settings, sound: SoundPlayer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FloatClock settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.s = settings
        self.sound = sound

        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(30, 100)
        self.opacity.setValue(int(settings.get("opacity") * 100))
        self.opacity.valueChanged.connect(lambda v: settings.set("opacity", v / 100))

        self.fmt = QComboBox()
        self.fmt.addItems(["12-hour", "24-hour"])
        self.fmt.setCurrentIndex(1 if settings.get("use_24h") else 0)
        self.fmt.currentIndexChanged.connect(lambda i: settings.set("use_24h", i == 1))

        self.seconds = QCheckBox("Show seconds")
        self.seconds.setChecked(settings.get("show_seconds"))
        self.seconds.toggled.connect(lambda v: settings.set("show_seconds", v))
        self.date = QCheckBox("Show date and weekday")
        self.date.setChecked(settings.get("show_date"))
        self.date.toggled.connect(lambda v: settings.set("show_date", v))

        self.sound_box = QComboBox()
        self.sound_box.addItems(SOUND_NAMES)
        self.sound_box.setCurrentText(settings.get("sound"))
        self.sound_box.currentTextChanged.connect(lambda t: settings.set("sound", t))
        test = QPushButton("Test")
        test.clicked.connect(lambda: sound.start(settings.get("sound"), loop=False))
        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_box, 1)
        sound_row.addWidget(test)

        self.hk_enabled = QCheckBox("Global hotkey to show/hide")
        self.hk_enabled.setChecked(settings.get("hotkey_enabled"))
        self.hk_enabled.toggled.connect(lambda v: settings.set("hotkey_enabled", v))
        self.hk_edit = QKeySequenceEdit(QKeySequence(settings.get("hotkey").replace("windows", "meta")))
        if hasattr(self.hk_edit, "setMaximumSequenceLength"):
            self.hk_edit.setMaximumSequenceLength(1)
        self.hk_edit.editingFinished.connect(self._hotkey_changed)

        self.autostart = QCheckBox("Start with Windows")
        self.autostart.setChecked(startup.is_enabled())
        self.autostart.setEnabled(startup.is_supported())
        self.autostart.toggled.connect(self._autostart_toggled)

        form = QFormLayout()
        form.addRow("Opacity", self.opacity)
        form.addRow("Time format", self.fmt)
        form.addRow("", self.seconds)
        form.addRow("", self.date)
        form.addRow("Alarm sound", sound_row)
        form.addRow("", self.hk_enabled)
        form.addRow("Hotkey", self.hk_edit)
        form.addRow("", self.autostart)
        close = QPushButton("Close")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(close)
        self.setMinimumWidth(340)

    def _hotkey_changed(self):
        seq = self.hk_edit.keySequence().toString()
        if seq:
            self.s.set("hotkey", seq.lower().replace("meta", "windows").replace(" ", ""))

    def _autostart_toggled(self, on):
        if not startup.set_enabled(on):
            QMessageBox.warning(self, "FloatClock", "Could not update the Windows startup entry.")
            self.autostart.blockSignals(True)
            self.autostart.setChecked(startup.is_enabled())
            self.autostart.blockSignals(False)

    def done(self, r):
        self.sound.stop()
        super().done(r)
