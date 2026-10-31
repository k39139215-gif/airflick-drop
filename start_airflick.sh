#!/usr/bin/env bash
# AirFlick Drop - macOS & Linux Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=============================================================="
echo "  AIRFLICK DROP • iPhone / Android to Mac / Windows / Linux"
echo "=============================================================="
echo ""

# Auto install missing requirements
python3 -c "import flask, werkzeug, PyQt6, qrcode, PIL" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[AirFlick] Installing required dependencies..."
    pip3 install -r requirements.txt
fi

# Enable silent startup
python3 -c "import autostart; autostart.enable_autostart()" >/dev/null 2>&1

echo "[AirFlick] Starting companion..."
python3 main_window.py
