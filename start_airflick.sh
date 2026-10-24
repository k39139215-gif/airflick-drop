#!/usr/bin/env bash
# AirFlick Drop - macOS & Linux Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=============================================================="
echo "  AIRFLICK DROP • iPhone / Android to Mac / Windows / Linux"
echo "=============================================================="
echo ""
echo "Starting AirFlick companion server..."
python3 main_window.py
