@echo off
echo ====================================================
echo Starting FastAPI Indian Stock Market Backend Server
echo ====================================================
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    echo Using Virtual Environment Python (.venv)...
    .venv\Scripts\python.exe main.py
) else if exist "Scripts\python.exe" (
    echo Using Virtual Environment Python...
    Scripts\python.exe main.py
) else (
    echo Error: Python virtual environment not found (.venv\Scripts\python.exe).
    pause
)
