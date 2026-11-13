"""Dark theme + app icon painting."""
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QBrush

ACCENT = "#7c9cff"
ACCENT_2 = "#b28cff"
GOLD = "#e8c27a"

STYLE = """
* { font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif; color: #eceff8; font-size: 10pt; }
QDialog { background: #14161f; }
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(30, 33, 48, 242), stop:1 rgba(14, 15, 24, 246));
    border: 1px solid rgba(255, 255, 255, 38);
    border-radius: 18px;
}
QFrame#card[flash="true"] { border: 2px solid #e8c27a; }
QLabel { background: transparent; }
QLabel#time { font-size: 38pt; font-weight: 200; letter-spacing: 1px; }
QLabel#timeCompact { font-size: 20pt; font-weight: 300; letter-spacing: 1px; }
QLabel#timerCompact { font-size: 20pt; font-weight: 400; letter-spacing: 1px; color: #9fb6ff; }
QLabel#timerCompact[paused="true"] { color: #e8c27a; }
QLabel#date { color: #8f98b0; font-size: 10pt; letter-spacing: 2px; }
QLabel#title { color: #e8c27a; font-size: 8pt; font-weight: 700; letter-spacing: 4px; }
QLabel#timerDisplay { font-size: 38pt; font-weight: 200; letter-spacing: 1px; }
QLabel#hint { color: #6f788f; font-size: 9pt; }
QLabel#popupTitle { font-size: 13pt; font-weight: 600; }
QLabel#popupMsg { font-size: 11pt; color: #cfd6e6; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: transparent; padding: 7px 16px; color: #7f88a0; font-weight: 600;
               letter-spacing: 1px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #ffffff; border-bottom: 2px solid #7c9cff; }
QTabBar::tab:hover { color: #ffffff; }
QPushButton { background: rgba(255,255,255,16); border: 1px solid rgba(255,255,255,22);
              border-radius: 10px; padding: 7px 14px; }
QPushButton:hover { background: rgba(255,255,255,34); border-color: rgba(255,255,255,50); }
QPushButton:disabled { color: #5d6476; }
QPushButton#primary { border: 0; color: white; font-weight: 600;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6f8cff, stop:1 #a07cff); }
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #86a0ff, stop:1 #b392ff); }
QPushButton#danger { background: #d9534f; border: 0; color: white; }
QToolButton { background: transparent; border: 0; padding: 3px 8px; border-radius: 8px; color: #8f98b0; }
QToolButton:hover { background: rgba(255,255,255,26); color: white; }
QSpinBox, QTimeEdit, QLineEdit, QComboBox, QKeySequenceEdit {
    background: rgba(255,255,255,12); border: 1px solid rgba(255,255,255,26);
    border-radius: 9px; padding: 5px 8px; }
QSpinBox:focus, QTimeEdit:focus, QLineEdit:focus, QComboBox:focus { border-color: #7c9cff; }
QComboBox QAbstractItemView { background: #1d2030; selection-background-color: #5f7dff; border-radius: 6px; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item { padding: 9px; border-radius: 10px; }
QListWidget::item:hover { background: rgba(255,255,255,12); }
QListWidget::item:selected { background: rgba(124,156,255,60); color: white; }
QCheckBox::indicator, QListWidget::indicator { width: 16px; height: 16px; border-radius: 5px;
    border: 1px solid rgba(255,255,255,80); background: rgba(255,255,255,10); }
QCheckBox::indicator:checked, QListWidget::indicator:checked { background: #7c9cff; border-color: #7c9cff; }
QProgressBar { background: rgba(255,255,255,20); border: 0; border-radius: 2px;
               max-height: 4px; min-height: 4px; }
QProgressBar::chunk { border-radius: 2px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c9cff, stop:1 #b28cff); }
QSlider::groove:horizontal { height: 4px; background: rgba(255,255,255,36); border-radius: 2px; }
QSlider::handle:horizontal { background: #e8c27a; width: 14px; margin: -5px 0; border-radius: 7px; }
QMenu { background: #1b1e2c; border: 1px solid rgba(255,255,255,34); padding: 6px; border-radius: 10px; }
QMenu::item { padding: 7px 24px; border-radius: 6px; }
QMenu::item:selected { background: #5f7dff; }
QMenu::separator { height: 1px; background: rgba(255,255,255,28); margin: 5px 8px; }
"""


def make_icon_pixmap(size: int = 64) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(ACCENT)))
    p.setPen(Qt.PenStyle.NoPen)
    m = size * 0.04
    p.drawEllipse(QPointF(size / 2, size / 2), size / 2 - m, size / 2 - m)
    pen = QPen(QColor("white"), size * 0.07, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    c = size / 2
    p.drawLine(QPointF(c, c), QPointF(c, size * 0.22))
    p.drawLine(QPointF(c, c), QPointF(size * 0.7, size * 0.58))
    p.end()
    return pm


def make_app_icon() -> QIcon:
    return QIcon(make_icon_pixmap(64))
