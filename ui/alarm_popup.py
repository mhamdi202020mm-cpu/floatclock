from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (QDialog, QFrame, QGraphicsDropShadowEffect, QLabel, QPushButton,
                               QVBoxLayout)

SHADOW_MARGIN = 28  # transparent margin around the card, room for the soft shadow


def _split_icon(title: str):
    """'⏰ 07:30' -> ('⏰', '07:30'); titles without a leading symbol get no icon."""
    head, _, rest = title.partition(" ")
    if rest and not head.isascii():
        return head, rest
    return "", title


class AlarmPopup(QDialog):
    """Modal, always-on-top popup shown when an alarm/timer fires (Apple-style sheet)."""
    snoozed = Signal()
    dismissed = Signal()

    def __init__(self, title, message, allow_snooze=True, snooze_minutes=5, center_on=None):
        super().__init__(None, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setWindowTitle(title)
        self._done = False

        card = QFrame()
        card.setObjectName("popupCard")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(shadow)

        icon_text, title_text = _split_icon(title)
        t = QLabel(title_text)
        t.setObjectName("popupTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setWordWrap(True)
        m = QLabel(message)
        m.setObjectName("popupMsg")
        m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m.setWordWrap(True)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(28, 30, 28, 24)
        inner.setSpacing(0)
        if icon_text:
            icon = QLabel(icon_text)
            icon.setObjectName("popupIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setAccessibleName("Notification")
            inner.addWidget(icon)
            inner.addSpacing(10)
        inner.addWidget(t)
        inner.addSpacing(6)
        inner.addWidget(m)
        inner.addSpacing(26)

        # full-width stacked buttons, primary first (Apple sheet pattern)
        dismiss = QPushButton("Dismiss" if allow_snooze else "Stop")
        dismiss.setObjectName("popupPrimary")
        dismiss.setDefault(True)
        dismiss.clicked.connect(lambda: self._finish(self.dismissed))
        inner.addWidget(dismiss)
        if allow_snooze:
            snooze = QPushButton(f"Snooze {snooze_minutes} min")
            snooze.setObjectName("popupSecondary")
            snooze.clicked.connect(lambda: self._finish(self.snoozed))
            inner.addSpacing(10)
            inner.addWidget(snooze)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN)
        outer.addWidget(card)
        self.setMinimumWidth(340 + 2 * SHADOW_MARGIN)
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
