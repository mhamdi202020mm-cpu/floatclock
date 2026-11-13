"""Alarm storage + trigger logic (persisted in %APPDATA%/FloatClock/alarms.json)."""
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, time as dtime

from PySide6.QtCore import QObject, Signal

from .settings import app_dir

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MAX_LATE = timedelta(minutes=10)  # don't ring for alarms missed by more than this (e.g. long sleep)


@dataclass
class Alarm:
    time: str = "07:00"
    label: str = ""
    days: list = field(default_factory=list)  # weekday numbers, Mon=0; empty = once
    enabled: bool = True
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def hm(self):
        h, m = self.time.split(":")
        return int(h), int(m)

    def days_text(self):
        if not self.days:
            return "Once"
        if len(self.days) == 7:
            return "Every day"
        return " ".join(DAY_NAMES[d] for d in sorted(self.days))

    @staticmethod
    def from_dict(d):
        try:
            a = Alarm(time=str(d["time"]), label=str(d.get("label", "")),
                      days=[int(x) for x in d.get("days", []) if 0 <= int(x) <= 6],
                      enabled=bool(d.get("enabled", True)),
                      id=str(d.get("id") or uuid.uuid4().hex))
            a.hm()
            dtime(*a.hm())  # validates range
            return a
        except (KeyError, ValueError, TypeError):
            return None


class AlarmManager(QObject):
    changed = Signal()
    triggered = Signal(object)  # Alarm

    def __init__(self):
        super().__init__()
        self.path = app_dir() / "alarms.json"
        self.alarms = []
        self._snoozes = []  # (due datetime, Alarm)
        self._last = datetime.now()
        self.load()

    # ---- persistence -------------------------------------------------
    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.alarms = [a for a in (Alarm.from_dict(d) for d in raw) if a]
        except (OSError, ValueError, TypeError):
            self.alarms = []

    def save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps([asdict(a) for a in self.alarms], indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    # ---- editing -----------------------------------------------------
    def add(self, alarm):
        self.alarms.append(alarm)
        self._commit()

    def update(self, alarm):
        for i, a in enumerate(self.alarms):
            if a.id == alarm.id:
                self.alarms[i] = alarm
        self._commit()

    def delete(self, alarm_id):
        self.alarms = [a for a in self.alarms if a.id != alarm_id]
        self._snoozes = [(d, a) for d, a in self._snoozes if a.id != alarm_id]
        self._commit()

    def set_enabled(self, alarm_id, enabled):
        for a in self.alarms:
            if a.id == alarm_id and a.enabled != enabled:
                a.enabled = enabled
                self._commit()

    def _commit(self):
        self.alarms.sort(key=lambda a: a.time)
        self.save()
        self.changed.emit()

    # ---- triggering --------------------------------------------------
    def snooze(self, alarm, minutes=5):
        self._snoozes.append((datetime.now() + timedelta(minutes=minutes), alarm))

    def tick(self, now=None):
        """Call about once per second. Fires every alarm whose scheduled moment
        fell inside (previous tick, now] -> exactly once per match, and also
        catches alarms due during a short sleep/resume gap."""
        now = now or datetime.now()
        last = self._last if self._last <= now else now - timedelta(seconds=1)
        self._last = now

        for a in list(self.alarms):
            if not a.enabled:
                continue
            h, m = a.hm()
            for back in (1, 0):  # yesterday, today (gap may span midnight)
                occ = datetime.combine((now - timedelta(days=back)).date(), dtime(h, m))
                if not (last < occ <= now) or now - occ > MAX_LATE:
                    continue
                if a.days and occ.weekday() not in a.days:
                    continue
                if not a.days:  # one-shot -> disable
                    a.enabled = False
                    self._commit()
                self.triggered.emit(a)
                break

        due = [(d, a) for d, a in self._snoozes if d <= now]
        if due:
            self._snoozes = [(d, a) for d, a in self._snoozes if d > now]
            for _, a in due:
                self.triggered.emit(a)
