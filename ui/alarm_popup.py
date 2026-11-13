from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class AlarmPopup(QDialog):
    """Modal, always-on-top popup shown when an alarm/timer fires."""
    snoozed = Signal()
    dismissed = Signal()

    def __init__(self, title, message, allow_snooze=True, snooze_minutes=5, center_on=None):
        super().__init__(None, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self._done = False

        card = QFrame()
        card.setObjectName("card")
        t = QLabel(title)
        t.setObjectName("popupTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m = QLabel(message)
        m.setObjectName("popupMsg")
        m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m.setWordWrap(True)

        row = QHBoxLayout()
        if allow_snooze:
            snooze = QPushButton(f"Snooze {snooze_minutes} min")
            snooze.clicked.connect(lambda: self._finish(self.snoozed))
            row.addWidget(snooze)
        dismiss = QPushButton("Dismiss" if allow_snooze else "Stop")
        dismiss.setObjectName("primary")
        dismiss.setDefault(True)
        dismiss.clicked.connect(lambda: self._finish(self.dismissed))
        row.addWidget(dismiss)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setSpacing(14)
        inner.addWidget(t)
        inner.addWidget(m)
        inner.addLayout(row)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)
        self.setMinimumWidth(300)
        self.adjustSize()

        screen = (center_on.screen() if center_on is not None and center_on.isVisible() else None) \
            or QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

    def _finish(self, signal):
        if self._done:
            return
        self._done = True
        signal.emit()
        self.close()

    def reject(self):  # Esc
        self._finish(self.dismissed)

    def closeEvent(self, e):
        if not self._done:  # closed some other way -> treat as dismiss
            self._done = True
            self.dismissed.emit()
        super().closeEvent(e)
