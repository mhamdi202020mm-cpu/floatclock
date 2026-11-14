from datetime import datetime

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                               QMenu, QSizeGrip, QStackedWidget, QSystemTrayIcon, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from core.hotkey import HotkeyManager
from .alarm_popup import AlarmPopup
from .alarms_widget import AlarmsWidget
from .clock_widget import ClockWidget
from .settings_dialog import SettingsDialog
from .theme import make_app_icon
from .timer_widget import TimerWidget

MARGIN = 12  # transparent margin around the card (room for the shadow)
COMPACT_SIZE = (190 + 2 * MARGIN, 66 + 2 * MARGIN)
EXPANDED_MIN = (320, 360)
QWIDGETSIZE_MAX = 16777215
MIN_OPACITY = 0.6  # lower values break text contrast


class MainWindow(QWidget):
    def __init__(self, settings, alarm_manager, sound):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                         Qt.WindowType.Tool)
        self.settings = settings
        self.alarm_manager = alarm_manager
        self.sound = sound
        self._quitting = False
        self._drag = None
        self._popups = set()
        self._last_tick = None
        self._flash_left = 0
        self._compact = bool(settings.get("compact"))

        self.setWindowTitle("FloatClock")
        self.setWindowIcon(make_app_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._build_tray()
        self._shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self._shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcut.activated.connect(lambda: self.set_compact(not self._compact))

        # hotkey
        self.hotkey = HotkeyManager(self)
        self.hotkey.triggered.connect(self.toggle_visibility)
        self._apply_hotkey()

        # signals
        settings.changed.connect(self._on_setting)
        alarm_manager.triggered.connect(self._on_alarm)
        self.timer_widget.finished.connect(self._on_timer_finished)
        self.timer_widget.display_changed.connect(self.clock_compact.set_timer)
        app = QGuiApplication.instance()
        try:  # Windows logoff/shutdown must not be blocked by our hide-to-tray closeEvent
            app.commitDataRequest.connect(self._on_session_end, Qt.ConnectionType.DirectConnection)
        except Exception:
            pass
        for sig in (app.screenAdded, app.screenRemoved, app.primaryScreenChanged):
            sig.connect(lambda *_: QTimer.singleShot(600, self.ensure_on_screen))

        # timers
        self._tick_timer = QTimer(self)
        self._tick_timer.setSingleShot(True)
        self._tick_timer.timeout.connect(self._tick)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._save_geometry)
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._flash_step)

        self.setWindowOpacity(max(MIN_OPACITY, settings.get("opacity")))
        self._apply_mode(initial=True)
        self._place_initially()
        self._tick()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        self.card = QFrame()
        self.card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(10, 6, 10, 6)
        self.stack = QStackedWidget()
        card_lay.addWidget(self.stack)

        # page 0: compact
        self.clock_compact = ClockWidget(self.settings, compact=True)
        self.stack.addWidget(self.clock_compact)

        # page 1: expanded
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        header = QHBoxLayout()
        title = QLabel("FLOATCLOCK")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch(1)
        for text, tip, fn in (("⚙", "Settings", self.open_settings),
                              ("▭", "Compact mode (Ctrl+Shift+C)", lambda: self.set_compact(True)),
                              ("✕", "Hide to tray", self.hide)):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setAccessibleName(tip.split(" (")[0])
            b.clicked.connect(fn)
            header.addWidget(b)
        pl.addLayout(header)

        self.clock_full = ClockWidget(self.settings)
        self.timer_widget = TimerWidget()
        self.alarms_widget = AlarmsWidget(self.alarm_manager, self.settings)
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("FloatClock sections")
        self.tabs.addTab(self.clock_full, "Clock")
        self.tabs.addTab(self.timer_widget, "Timer")
        self.tabs.addTab(self.alarms_widget, "Alarms")
        pl.addWidget(self.tabs, 1)
        grip_row = QHBoxLayout()
        grip_row.addStretch(1)
        grip_row.addWidget(QSizeGrip(page))
        pl.addLayout(grip_row)
        self.stack.addWidget(page)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        self.tray.setToolTip("FloatClock")
        menu = QMenu()
        self.act_toggle = QAction("Hide", menu)
        self.act_toggle.triggered.connect(self.toggle_visibility)
        self.act_compact = QAction("Compact mode", menu, checkable=True)
        self.act_compact.setChecked(self._compact)
        self.act_compact.toggled.connect(self.set_compact)
        act_settings = QAction("Settings…", menu)
        act_settings.triggered.connect(self.open_settings)
        act_exit = QAction("Exit", menu)
        act_exit.triggered.connect(self.quit_app)
        for a in (self.act_toggle, self.act_compact, act_settings):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(act_exit)
        self._tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.toggle_visibility() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self._tray_ok = QSystemTrayIcon.isSystemTrayAvailable()
        if self._tray_ok:
            self.tray.show()

    # ---------------------------------------------------------- mode/size
    def set_compact(self, compact: bool):
        if compact == self._compact:
            return
        self._compact = compact
        self.settings.set("compact", compact)
        self._apply_mode()

    def _apply_mode(self, initial=False):
        self.act_compact.blockSignals(True)
        self.act_compact.setChecked(self._compact)
        self.act_compact.blockSignals(False)
        if self._compact:
            self.stack.setCurrentIndex(0)
            self.setMinimumSize(0, 0)
            self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
            # grow with the system font size instead of clipping (stack hint covers both pages, so
            # measure the compact page alone)
            hint = self.clock_compact.sizeHint()
            self.setFixedSize(max(COMPACT_SIZE[0], hint.width() + 20 + 2 * MARGIN),
                              max(COMPACT_SIZE[1], hint.height() + 12 + 2 * MARGIN))
        else:
            self.stack.setCurrentIndex(1)
            self.setMinimumSize(*EXPANDED_MIN)
            self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
            self.resize(max(EXPANDED_MIN[0], self.settings.get("expanded_w")),
                        max(EXPANDED_MIN[1], self.settings.get("expanded_h")))
        if not initial:
            self.ensure_on_screen()

    def _place_initially(self):
        x, y = self.settings.get("x"), self.settings.get("y")
        if x is None or y is None:
            geo = QGuiApplication.primaryScreen().availableGeometry()
            x = geo.right() - self.width() - 20
            y = geo.top() + 20
        self.move(int(x), int(y))
        self.ensure_on_screen()

    def ensure_on_screen(self):
        """Keep the window fully inside an existing monitor (handles unplugged displays)."""
        g = self.frameGeometry()
        screen = QGuiApplication.screenAt(g.center()) or QGuiApplication.primaryScreen()
        a = screen.availableGeometry()
        x = max(a.left(), min(g.x(), a.right() - g.width() + 1))
        y = max(a.top(), min(g.y(), a.bottom() - g.height() + 1))
        if (x, y) != (g.x(), g.y()):
            self.move(x, y)

    def _save_geometry(self):
        self.settings.set("x", self.x())
        self.settings.set("y", self.y())
        if not self._compact:
            self.settings.set("expanded_w", self.width())
            self.settings.set("expanded_h", self.height())

    def moveEvent(self, e):
        super().moveEvent(e)
        self._save_timer.start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._save_timer.start()

    # ------------------------------------------------------------- events
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            self._drag = None
            self.ensure_on_screen()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.set_compact(not self._compact)

    def contextMenuEvent(self, e):
        m = QMenu(self)
        m.addAction("Expand" if self._compact else "Compact mode",
                    lambda: self.set_compact(not self._compact))
        m.addAction("Settings…", self.open_settings)
        m.addAction("Hide", self.hide)
        m.addSeparator()
        m.addAction("Exit", self.quit_app)
        m.exec(e.globalPos())

    def showEvent(self, e):
        super().showEvent(e)
        self.act_toggle.setText("Hide")

    def hideEvent(self, e):
        super().hideEvent(e)
        self.act_toggle.setText("Show")

    def closeEvent(self, e):
        if self._quitting:
            self._save_geometry()
            self.hotkey.stop()
            e.accept()
        elif not self._tray_ok:  # no tray to restore from -> closing really exits
            self._quitting = True
            self._save_geometry()
            self.hotkey.stop()
            e.accept()
            QApplication.exit(0)
        else:
            e.ignore()
            self.hide()

    # ---------------------------------------------------------- behaviour
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_and_raise()

    def show_and_raise(self):
        self.show()
        self.ensure_on_screen()
        self.raise_()
        self.activateWindow()

    def _on_session_end(self, *_):
        self._quitting = True

    def quit_app(self):
        self._quitting = True
        self.tray.hide()
        self._save_geometry()
        self.hotkey.stop()
        for p in list(self._popups):
            p.close()
        QApplication.exit(0)

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self.sound, self if self.isVisible() else None)
        dlg.exec()

    def _on_setting(self, key):
        if key == "opacity":
            self.setWindowOpacity(max(MIN_OPACITY, self.settings.get("opacity")))
        elif key in ("use_24h", "show_seconds", "show_date"):
            self._refresh_clocks(datetime.now())
        elif key in ("hotkey", "hotkey_enabled"):
            self._apply_hotkey()

    def _apply_hotkey(self):
        if self.settings.get("hotkey_enabled"):
            if not self.hotkey.start(self.settings.get("hotkey")):
                self.tray.setToolTip("FloatClock (global hotkey unavailable)")
        else:
            self.hotkey.stop()

    # -------------------------------------------------------------- clock
    def _refresh_clocks(self, now):
        self.clock_compact.refresh(now)
        self.clock_full.refresh(now)

    def _tick(self):
        now = datetime.now()
        if self._last_tick is not None:
            gap = (now - self._last_tick).total_seconds()
            if abs(gap - 1) > 2.5:  # system slept / clock changed -> resync
                self.ensure_on_screen()
        self._last_tick = now
        self._refresh_clocks(now)
        self.alarm_manager.tick(now)
        # align the next tick to the start of the next second
        self._tick_timer.start(max(20, 1000 - datetime.now().microsecond // 1000 + 5))

    # ----------------------------------------------------- alarms / timer
    def _on_alarm(self, alarm):
        mins = self.settings.get("snooze_minutes")
        self._ring(f" {alarm.time}", alarm.label or "Alarm", True, mins,
                   on_snooze=lambda: self.alarm_manager.snooze(alarm, mins))

    def _on_timer_finished(self):
        self._ring(" Timer finished", "Time's up!", False)

    def _ring(self, title, message, allow_snooze, snooze_minutes=5, on_snooze=None):
        self.show_and_raise()
        self.flash()
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 10000)
        self.sound.start(self.settings.get("sound"), loop=True)

        popup = AlarmPopup(title, message, allow_snooze, snooze_minutes, center_on=self)
        self._popups.add(popup)

        def finish(snoozed):
            if snoozed and on_snooze:
                on_snooze()
            self._popups.discard(popup)
            if not self._popups:
                self.sound.stop()
            popup.deleteLater()

        popup.snoozed.connect(lambda: finish(True))
        popup.dismissed.connect(lambda: finish(False))
        popup.show()
        popup.raise_()
        popup.activateWindow()

    def flash(self):
        QApplication.alert(self, 0)
        self._flash_left = 10
        self._flash_timer.start(300)

    def _flash_step(self):
        if self._flash_left <= 0:
            self._flash_timer.stop()
            self._set_flash(False)
            return
        self._set_flash(self._flash_left % 2 == 1)
        self._flash_left -= 1

    def _set_flash(self, on):
        self.card.setProperty("flash", on)
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)
