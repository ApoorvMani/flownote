@echo off
cd /d "%~dp0"

:: Check for venv
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" run.py %*
) else (
    python run.py %*
)
