from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QTimeEdit, QVBoxLayout, QWidget)

from core.alarm_manager import Alarm, DAY_NAMES


class AlarmEditDialog(QDialog):
    def __init__(self, alarm: Alarm = None, use_24h=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alarm")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._alarm = alarm or Alarm()

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm" if use_24h else "hh:mm AP")
        h, m = self._alarm.hm()
        self.time_edit.setTime(QTime(h, m))
        self.label_edit = QLineEdit(self._alarm.label)
        self.label_edit.setPlaceholderText("Label (optional)")

        days_row = QHBoxLayout()
        self.day_boxes = []
        for i, name in enumerate(DAY_NAMES):
            cb = QCheckBox(name)
            cb.setChecked(i in self._alarm.days)
            self.day_boxes.append(cb)
            days_row.addWidget(cb)
        hint = QLabel("No days selected = rings once")
        hint.setObjectName("hint")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("Time", self.time_edit)
        form.addRow("Label", self.label_edit)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addLayout(days_row)
        lay.addWidget(hint)
        lay.addWidget(buttons)

    def result_alarm(self) -> Alarm:
        a = self._alarm
        a.time = self.time_edit.time().toString("HH:mm")
        a.label = self.label_edit.text().strip()
        a.days = [i for i, cb in enumerate(self.day_boxes) if cb.isChecked()]
        return a


def _pretty_time(hhmm: str, use_24h: bool) -> str:
    if use_24h:
        return hhmm
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


class AlarmsWidget(QWidget):
    def __init__(self, manager, settings, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        self.list = QListWidget()
        self.list.itemChanged.connect(self._item_changed)
        self.list.itemDoubleClicked.connect(lambda _: self.edit())

        add = QPushButton("+ Add")
        add.setObjectName("primary")
        add.clicked.connect(self.add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Delete")
        delete.clicked.connect(self.delete)
        row = QHBoxLayout()
        row.addWidget(add, 2)
        row.addWidget(edit, 1)
        row.addWidget(delete, 1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.addWidget(self.list, 1)
        lay.addLayout(row)

        manager.changed.connect(self.refresh)
        settings.changed.connect(lambda k: self.refresh() if k == "use_24h" else None)
        self.refresh()

    def refresh(self):
        use24 = self.settings.get("use_24h")
        self.list.blockSignals(True)
        self.list.clear()
        for a in self.manager.alarms:
            text = f"{_pretty_time(a.time, use24)}   {a.label or 'Alarm'}\n{a.days_text()}"
            it = QListWidgetItem(text)
            it.setData(Qt.ItemDataRole.UserRole, a.id)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if a.enabled else Qt.CheckState.Unchecked)
            self.list.addItem(it)
        self.list.blockSignals(False)

    def _selected(self):
        it = self.list.currentItem()
        if not it:
            return None
        aid = it.data(Qt.ItemDataRole.UserRole)
        return next((a for a in self.manager.alarms if a.id == aid), None)

    def _item_changed(self, item):
        self.manager.set_enabled(item.data(Qt.ItemDataRole.UserRole),
                                 item.checkState() == Qt.CheckState.Checked)

    def add(self):
        dlg = AlarmEditDialog(use_24h=self.settings.get("use_24h"), parent=self.window())
        if dlg.exec():
            self.manager.add(dlg.result_alarm())

    def edit(self):
        a = self._selected()
        if not a:
            return
        dlg = AlarmEditDialog(Alarm(**a.__dict__), self.settings.get("use_24h"), self.window())
        if dlg.exec():
            new = dlg.result_alarm()
            new.enabled = True  # re-arm when edited
            self.manager.update(new)

    def delete(self):
        a = self._selected()
        if a and QMessageBox.question(self.window(), "Delete alarm",
                                      f"Delete the {a.time} alarm?") == QMessageBox.StandardButton.Yes:
            self.manager.delete(a.id)
