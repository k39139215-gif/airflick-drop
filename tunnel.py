import os
import sys
import subprocess
import re
import time
import threading
import shutil
import urllib.request

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(PROJECT_DIR, "bin")
EXE_NAME = "cloudflared.exe" if sys.platform == "win32" else "cloudflared"
CLOUDFLARED_EXE = os.path.join(BIN_DIR, EXE_NAME)
URL_CACHE_FILE = os.path.join(PROJECT_DIR, ".tunnel_url")

DOWNLOAD_URLS = {
    "win32": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    "darwin": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64",
    "linux": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
}

def ensure_cloudflared():
    """Ensures cloudflared executable is available. Downloads if missing."""
    # Check if in BIN_DIR
    if os.path.exists(CLOUDFLARED_EXE):
        return CLOUDFLARED_EXE
        
    # Check if in PATH
    path_bin = shutil.which("cloudflared")
    if path_bin:
        return path_bin

    # Auto-download
    os.makedirs(BIN_DIR, exist_ok=True)
    platform_key = sys.platform if sys.platform in DOWNLOAD_URLS else "linux"
    download_url = DOWNLOAD_URLS[platform_key]
    print(f"[Tunnel] Downloading cloudflared for initial setup from {download_url}...")
    try:
        temp_path = CLOUDFLARED_EXE + ".tmp"
        urllib.request.urlretrieve(download_url, temp_path)
        if sys.platform != "win32":
            os.chmod(temp_path, 0o755)
        os.replace(temp_path, CLOUDFLARED_EXE)
        print(f"[Tunnel] cloudflared downloaded successfully to {CLOUDFLARED_EXE}")
        return CLOUDFLARED_EXE
    except Exception as e:
        print(f"[Tunnel] Error downloading cloudflared: {e}")
        return None

GIST_ENDPOINT_ID = "13a26c30b2be5b27f84af379b343397a"

def sync_endpoint_to_gist(url):
    """Silently updates the central Gist endpoint in the background."""
    def _worker():
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            subprocess.run(
                ["gh", "gist", "edit", GIST_ENDPOINT_ID, "-f", "endpoint.txt", "-"],
                input=url.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags
            )
            print(f"[AirFlick Gist Sync] Successfully synced live endpoint to Gist!")
        except Exception as e:
            print(f"[AirFlick Gist Sync] Notice: {e}")
    threading.Thread(target=_worker, daemon=True).start()

class CloudflareTunnel:
    def __init__(self, port=5050):
        self.port = port
        self.process = None
        self.public_url = None
        self.is_running = False
        self._stop_event = threading.Event()
        self.callback_on_url = None

    def start(self, callback_on_url=None):
        self.callback_on_url = callback_on_url
        self._stop_event.clear()

        exe = ensure_cloudflared()
        if not exe or not os.path.exists(exe):
            print(f"[Tunnel] Unable to start tunnel: cloudflared binary missing.")
            return self

        def run_loop():
            url_pattern = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")
            while not self._stop_event.is_set():
                cmd = [exe, "tunnel", "--url", f"http://127.0.0.1:{self.port}"]
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW

                try:
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        bufsize=1,
                        creationflags=creationflags
                    )
                    self.is_running = True

                    for line in iter(self.process.stdout.readline, ''):
                        if self._stop_event.is_set():
                            break
                        if not line:
                            break
                        match = url_pattern.search(line)
                        if match:
                            found_url = match.group(0)
                            if found_url != self.public_url:
                                self.public_url = found_url
                                try:
                                    with open(URL_CACHE_FILE, "w", encoding="utf-8") as f:
                                        f.write(self.public_url)
                                except Exception:
                                    pass
                                print(f"\n[AirFlick Cloudflare Tunnel] Live HTTPS URL: {self.public_url}")
                                sync_endpoint_to_gist(self.public_url)
                                if self.callback_on_url:
                                    self.callback_on_url(self.public_url)
                except Exception as e:
                    print(f"[Tunnel] Process error: {e}")
                finally:
                    self.is_running = False
                    if self.process and self.process.poll() is None:
                        try:
                            self.process.terminate()
                        except Exception:
                            pass

                if not self._stop_event.is_set():
                    time.sleep(3)  # Brief pause before reconnecting if killed

        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        return self

    def stop(self):
        self._stop_event.set()
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.is_running = False
        if os.path.exists(URL_CACHE_FILE):
            try:
                os.remove(URL_CACHE_FILE)
            except Exception:
                pass

if __name__ == "__main__":
    t = CloudflareTunnel(5050)
    t.start(lambda url: print("Tunnel callback:", url))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        t.stop()
