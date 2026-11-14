"""Dark theme + app icon painting."""
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QBrush

# Fog Mode palette
UI_WHITE = "#FAFAFA"
MIST_GRAY = "#E0E0E0"
SILVER_VEIL = "#B5B5B5"
CLOUD_SLATE = "#707070"
INK = "#2B2B2B"        # darker tone derived from Cloud Slate, for primary text
FOCUS = "#2F78B8"      # focus ring / selection accent
WARN = "#9A5B00"       # paused / alarm flash

ACCENT = INK

STYLE = """
* { font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif; color: #2B2B2B; font-size: 10pt; }
QDialog { background: #FAFAFA; }
QToolTip { background: #FAFAFA; color: #2B2B2B; border: 1px solid #707070; padding: 4px; }
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(250, 250, 250, 246), stop:1 rgba(236, 236, 236, 246));
    border: 1px solid #B5B5B5;
    border-radius: 18px;
}
QFrame#card[flash="true"] { border: 3px solid #9A5B00; }
QLabel { background: transparent; }
QLabel#time { font-size: 38pt; font-weight: 200; letter-spacing: 1px; }
QLabel#timeCompact { font-size: 20pt; font-weight: 300; letter-spacing: 1px; }
QLabel#timerCompact { font-size: 20pt; font-weight: 500; letter-spacing: 1px; color: #2B2B2B; }
QLabel#timerCompact[paused="true"] { color: #9A5B00; }
QLabel#date { color: #5F5F5F; font-size: 10pt; letter-spacing: 2px; }
QLabel#title { color: #5F5F5F; font-size: 8pt; font-weight: 700; letter-spacing: 4px; }
QLabel#timerDisplay { font-size: 38pt; font-weight: 200; letter-spacing: 1px; }
QLabel#hint { color: #5F5F5F; font-size: 9pt; }
QLabel#popupTitle { font-size: 13pt; font-weight: 600; }
QLabel#popupMsg { font-size: 11pt; color: #3d3d3d; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: transparent; padding: 7px 16px; color: #5F5F5F; font-weight: 600;
               letter-spacing: 1px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #2B2B2B; border-bottom: 2px solid #2B2B2B; }
QTabBar::tab:hover { color: #2B2B2B; }
QTabBar::tab:focus { border: 2px solid #2F78B8; border-radius: 6px; }
QPushButton { background: #E0E0E0; border: 1px solid #B5B5B5; border-radius: 10px; padding: 7px 14px; }
QPushButton:hover { background: #D2D2D2; border-color: #707070; }
QPushButton:pressed { background: #C6C6C6; }
QPushButton:focus { border: 2px solid #2F78B8; }
QPushButton:disabled { color: #8c8c8c; background: #EDEDED; }
QPushButton#primary { border: 0; color: #FFFFFF; font-weight: 600;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5E5E5E, stop:1 #404040); }
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #707070, stop:1 #4d4d4d); }
QPushButton#primary:focus { border: 2px solid #2F78B8; }
QPushButton#danger { background: #A8322D; border: 0; color: white; }
QToolButton { background: transparent; border: 1px solid transparent; padding: 5px 10px;
              min-width: 18px; min-height: 18px; border-radius: 8px; color: #5F5F5F; }
QToolButton:hover { background: #E0E0E0; color: #2B2B2B; }
QToolButton:focus { border: 2px solid #2F78B8; color: #2B2B2B; }
QSpinBox, QTimeEdit, QLineEdit, QComboBox, QKeySequenceEdit {
    background: #FFFFFF; border: 1px solid #707070; border-radius: 9px; padding: 5px 8px; }
QSpinBox:focus, QTimeEdit:focus, QLineEdit:focus, QComboBox:focus, QKeySequenceEdit:focus {
    border: 2px solid #2F78B8; }
QSpinBox:disabled { color: #8c8c8c; border-color: #B5B5B5; }
QComboBox QAbstractItemView { background: #FAFAFA; selection-background-color: #D6E6F5;
    selection-color: #2B2B2B; border: 1px solid #707070; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget:focus { border: 2px solid #2F78B8; border-radius: 10px; }
QListWidget::item { padding: 9px; border-radius: 10px; }
QListWidget::item:hover { background: #E0E0E0; }
QListWidget::item:selected { background: #D6E6F5; color: #2B2B2B; }
QCheckBox { spacing: 8px; }
QCheckBox:focus { color: #000000; }
QCheckBox::indicator, QListWidget::indicator { width: 16px; height: 16px; border-radius: 5px;
    border: 2px solid #707070; background: #FFFFFF; }
QCheckBox::indicator:focus { border-color: #2F78B8; }
QCheckBox::indicator:checked, QListWidget::indicator:checked { background: #2B2B2B; border-color: #2B2B2B; }
QProgressBar { background: #E0E0E0; border: 1px solid #B5B5B5; border-radius: 3px;
               max-height: 6px; min-height: 6px; }
QProgressBar::chunk { border-radius: 2px; background: #707070; }
QSlider::groove:horizontal { height: 4px; background: #707070; border-radius: 2px; }
QSlider::handle:horizontal { background: #2B2B2B; width: 16px; margin: -6px 0; border-radius: 8px;
    border: 2px solid #FAFAFA; }
QSlider::handle:horizontal:focus { background: #2F78B8; }
QMenu { background: #FAFAFA; border: 1px solid #B5B5B5; padding: 6px; border-radius: 10px; }
QMenu::item { padding: 7px 24px; border-radius: 6px; }
QMenu::item:selected { background: #E0E0E0; color: #2B2B2B; }
QMenu::separator { height: 1px; background: #B5B5B5; margin: 5px 8px; }
"""


def make_icon_pixmap(size: int = 64) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(INK)))
    p.setPen(Qt.PenStyle.NoPen)
    m = size * 0.04
    p.drawEllipse(QPointF(size / 2, size / 2), size / 2 - m, size / 2 - m)
    pen = QPen(QColor(UI_WHITE), size * 0.07, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    c = size / 2
    p.drawLine(QPointF(c, c), QPointF(c, size * 0.22))
    p.drawLine(QPointF(c, c), QPointF(size * 0.7, size * 0.58))
    p.end()
    return pm


def make_app_icon() -> QIcon:
    return QIcon(make_icon_pixmap(64))
