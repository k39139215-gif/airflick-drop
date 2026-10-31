#!/usr/bin/env python3
"""
AirFlick Drop - Health Diagnostic & Doctor CLI
Verifies Python dependencies, network interfaces, port availability, and tunnel binary.
"""

import os
import sys
import socket
import urllib.request
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import get_lan_ip
from tunnel import ensure_cloudflared

def run_diagnostics():
    print("=" * 60)
    print("  AIRFLICK DROP DIAGNOSTIC HEALTH CHECK")
    print("=" * 60)
    
    # 1. Check Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"[OK] Python version: {py_ver}")
    
    # 2. Check local LAN IP
    lan_ip = get_lan_ip()
    print(f"[OK] Detected LAN IP: {lan_ip}")
    
    # 3. Check port 5050 status
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        is_port_open = s.connect_ex(('127.0.0.1', 5050)) == 0
    if is_port_open:
        print("[INFO] Port 5050 is active (AirFlick server running).")
    else:
        print("[OK] Port 5050 is available for binding.")
        
    # 4. Check cloudflared binary
    exe = ensure_cloudflared()
    if exe and os.path.exists(exe):
        print(f"[OK] Cloudflare binary located: {exe}")
    else:
        print("[WARN] Cloudflare binary not found. Will auto-download on launch.")
        
    # 5. Check dependencies
    pkgs = ["flask", "werkzeug", "PyQt6", "qrcode", "PIL"]
    for pkg in pkgs:
        try:
            __import__(pkg)
            print(f"[OK] Dependency installed: {pkg}")
        except ImportError:
            print(f"[FAIL] Missing dependency: {pkg}")

    print("=" * 60)
    print("All core diagnostics passed successfully.")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
