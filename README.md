# FloatClock

Always-on-top floating clock for Windows with a countdown timer and alarms (PySide6).

## Run
```
cd floatclock
py -3.11 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Test by phase
1. **Window + clock** – drag it, double-click to toggle compact/expanded, compare with the taskbar clock, right-click for the menu.
2. **Timer** – Timer tab: press 5m then Start; Pause/Resume/Reset; try 0 min 5 sec to hear the sound + popup + notification (sound loops until you press Stop).
3. **Alarms** – Alarms tab: add an alarm for 2 minutes from now; test Snooze and Dismiss; restart the app and check it persisted (%APPDATA%\FloatClock\alarms.json).
4. **Tray + settings** – ✕ hides to tray; tray icon click toggles; ⚙ opens settings (opacity, 12/24h, seconds, date, sound, hotkey Ctrl+Alt+C, start with Windows). Launch a second copy: it just shows the first.
5. **Package** – run `build.bat` → `dist\FloatClock.exe`.

Note: it shows over normal and borderless-windowed apps, not over exclusive-fullscreen games.
