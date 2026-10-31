@echo off
title AirFlick Drop - Mobile to Desktop
cd /d "%~dp0"

echo ==============================================================
echo   AIRFLICK DROP - Mobile to PC Gesture File Transfer
echo ==============================================================
echo.

:: Automatically verify and install dependencies if missing
python -c "import flask, werkzeug, PyQt6, qrcode, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AirFlick] First time run detected! Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please ensure Python is installed.
        pause
        exit /b 1
    )
)

:: Automatically install silent startup on this computer
python -c "import autostart; autostart.enable_autostart()" >nul 2>&1

:: Launch companion app
echo [AirFlick] Starting AirFlick companion...
start "" pythonw main_window.py
exit
