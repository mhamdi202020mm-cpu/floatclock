@echo off
REM Build FloatClock.exe  (run from the floatclock folder)
python -m pip install -r requirements.txt pyinstaller || goto :err
python make_assets.py || goto :err
python -m PyInstaller --noconsole --onefile --name FloatClock ^
  --icon assets\icon.ico ^
  --add-data "assets;assets" ^
  --hidden-import keyboard --hidden-import pynput.keyboard._win32 ^
  main.py || goto :err
echo.
echo Done: dist\FloatClock.exe
exit /b 0
:err
echo Build failed.
exit /b 1
