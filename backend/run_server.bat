@echo off
echo ====================================================
echo Starting FastAPI Indian Stock Market Backend Server
echo ====================================================
cd /d "%~dp0"
if exist "Scripts\python.exe" (
    echo Using Virtual Environment Python...
    Scripts\python.exe main.py
) else (
    echo Error: Scripts\python.exe not found.
    pause
)
