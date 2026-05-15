@echo off
cd /d "%~dp0"
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" "%~dp0launcher.py"
) else (
    start "" pythonw "%~dp0launcher.py"
)
