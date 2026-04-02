@echo off
echo Building FlowNote.exe with PyInstaller...
cd /d "%~dp0"

:: Install PyInstaller if missing
pip show pyinstaller >nul 2>&1 || pip install pyinstaller

pyinstaller ^
  --name FlowNote ^
  --onefile ^
  --windowed ^
  --add-data "config;config" ^
  --hidden-import PyQt5.sip ^
  --hidden-import keyboard ^
  --hidden-import pyperclip ^
  run.py

echo.
if exist "dist\FlowNote.exe" (
    echo SUCCESS: dist\FlowNote.exe created
) else (
    echo FAILED: check build output above
)
pause
