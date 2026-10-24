import os
import sys
import socket
import logging
import time
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Suppress Flask default request logging to keep console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(PROJECT_DIR, "web")
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")

app = Flask(__name__, static_folder=WEB_DIR)
# 15 GB max file transfer over local Wi-Fi / hotspot
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 * 1024  

# Callback to notify PyQt GUI
on_file_dropped_callback = None

def bump_file_timestamp(filepath):
    """Refreshes Modified and Created time to NOW so file jumps to the absolute top of Desktop (cross-platform)."""
    try:
        now = time.time()
        os.utime(filepath, (now, now))
        if sys.platform == 'win32':
            ps_cmd = f"(Get-Item -LiteralPath '{filepath}').LastWriteTime = Get-Date; (Get-Item -LiteralPath '{filepath}').CreationTime = Get-Date"
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=2)
        elif sys.platform == 'darwin':
            subprocess.run(["touch", "-m", filepath], capture_output=True, timeout=2)
        else:
            subprocess.run(["touch", filepath], capture_output=True, timeout=2)
    except Exception:
        pass

def reveal_in_file_manager(filepath):
    """Highlights received file in Windows Explorer, macOS Finder, or Linux file manager."""
    try:
        if sys.platform == 'win32':
            subprocess.Popen(['explorer.exe', f'/select,{filepath}'])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', filepath])
        else:
            subprocess.Popen(['xdg-open', os.path.dirname(filepath)])
    except Exception:
        pass

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")

@app.route("/<path:filename>")
def static_assets(filename):
    return send_from_directory(WEB_DIR, filename)

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Receives files from Mobile -> Laptop (Desktop).
    Supports multi-file up to 15 GB, 4MB chunked streaming, and Smart Bump-to-top.
    """
    files = request.files.getlist('file') or request.files.getlist('files[]')
    if not files:
        return jsonify({"error": "No file part"}), 400

    saved_info = []
    first_path = None
    any_existed = False

    for f in files:
        if not f or f.filename == '':
            continue

        raw_filename = secure_filename(f.filename) or "airflick_file"
        base, ext = os.path.splitext(raw_filename)
        if not ext:
            ext = ".bin"

        target_path = os.path.join(DESKTOP_DIR, f"{base}{ext}")
        already_existed = os.path.exists(target_path)
        if already_existed:
            any_existed = True

        # Stream in 4MB chunks for zero-RAM overhead on files up to 15 GB
        with open(target_path, 'wb') as dst:
            while True:
                chunk = f.stream.read(4 * 1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

        # Smart Bump-to-Top: Force timestamp to exact current second!
        bump_file_timestamp(target_path)

        final_filename = os.path.basename(target_path)
        saved_info.append({
            "name": final_filename,
            "path": target_path,
            "existed": already_existed
        })
        if not first_path:
            first_path = target_path

    if not saved_info:
        return jsonify({"error": "No valid files received"}), 400

    print(f"\n[AirFlick Server] [OK] Received & Bumped {len(saved_info)} file(s) to Top of Desktop (Existing: {any_existed})")

    # If already existed, auto-highlight in File Manager
    if any_existed and first_path:
        reveal_in_file_manager(first_path)

    # Trigger GUI callback
    if on_file_dropped_callback and first_path:
        if len(saved_info) == 1:
            on_file_dropped_callback(first_path, saved_info[0]["name"], 1, any_existed)
        else:
            summary = f"{len(saved_info)} Files ({saved_info[0]['name']}, ...)"
            on_file_dropped_callback(first_path, summary, len(saved_info), any_existed)

    return jsonify({
        "status": "success",
        "count": len(saved_info),
        "bumped": any_existed,
        "files": [item["name"] for item in saved_info],
        "filename": saved_info[0]["name"]
    })

@app.route("/api/upload_chunk", methods=["POST"])
def upload_chunk_api():
    """
    Receives chunked slices of a file. Supports 15 GB files, Pause/Resume and Cancel.
    """
    transfer_id = request.form.get("transfer_id")
    filename = request.form.get("filename")
    chunk_index = int(request.form.get("chunk_index", 0))
    total_chunks = int(request.form.get("total_chunks", 1))
    chunk_file = request.files.get("chunk")
    
    if not transfer_id or not filename or not chunk_file:
        return jsonify({"error": "Missing parameters"}), 400

    raw_filename = secure_filename(filename) or "airflick_file.bin"
    base, ext = os.path.splitext(raw_filename)
    if not ext:
        ext = ".bin"

    temp_part_path = os.path.join(DESKTOP_DIR, f".{transfer_id}_{base}{ext}.part")
    
    mode = "wb" if chunk_index == 0 else "ab"
    with open(temp_part_path, mode) as dst:
        while True:
            buf = chunk_file.stream.read(4 * 1024 * 1024)
            if not buf:
                break
            dst.write(buf)

    if chunk_index == total_chunks - 1:
        # All chunks received! Finalize file on Desktop
        target_path = os.path.join(DESKTOP_DIR, f"{base}{ext}")
        already_existed = os.path.exists(target_path)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass
        os.rename(temp_part_path, target_path)
        bump_file_timestamp(target_path)

        if already_existed:
            reveal_in_file_manager(target_path)

        if on_file_dropped_callback:
            on_file_dropped_callback(target_path, os.path.basename(target_path), 1, already_existed)

        print(f"\n[AirFlick Server] [COMPLETE] Finished {filename} ({total_chunks} chunks). Bumped: {already_existed}")
        return jsonify({
            "status": "completed",
            "bumped": already_existed,
            "filename": os.path.basename(target_path),
            "count": 1
        })

    return jsonify({"status": "chunk_saved", "chunk_index": chunk_index})

@app.route("/api/upload_cancel", methods=["POST"])
def upload_cancel_api():
    """Cancels in-progress upload and cleans up temporary partial files."""
    data = request.get_json(force=True) or {}
    transfer_id = data.get("transfer_id")
    filename = data.get("filename")
    if transfer_id and filename:
        raw_filename = secure_filename(filename) or "airflick_file.bin"
        base, ext = os.path.splitext(raw_filename)
        temp_part_path = os.path.join(DESKTOP_DIR, f".{transfer_id}_{base}{ext}.part")
        if os.path.exists(temp_part_path):
            try:
                os.remove(temp_part_path)
                print(f"[AirFlick Server] [CANCELLED] Deleted partial file: {temp_part_path}")
            except Exception:
                pass
    return jsonify({"status": "cancelled"})

def run_server(callback=None, port=5050):
    global on_file_dropped_callback
    on_file_dropped_callback = callback
    lan_ip = get_lan_ip()
    print(f"AirFlick HTTP Server running on http://{lan_ip}:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    run_server()
