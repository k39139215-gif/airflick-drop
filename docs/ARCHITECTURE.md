# AirFlick Drop Architecture

## System Overview

AirFlick Drop provides high-velocity, cross-platform file transfers between mobile devices (iOS Safari, Android Chrome) and desktop computers (Windows, macOS, Linux).

```
   [Mobile Phone] (Browser)
          │
          ├── (Mode 1: Cloudflare HTTPS Tunnel) ──> Cloudflare Edge ──> [127.0.0.1:5050 Laptop Flask]
          │                                                                      │
          └── (Mode 2: Local Wi-Fi / Hotspot) ─────> [10.x.x.x / 192.168.x.x LAN]─┘
                                                                                 │
                                                                         [Desktop Target]
                                                                      (Silent bump-to-top)
```

## Key Modules

1. **`server.py`**:
   - Streaming receiver handling 4MB chunks up to 15 GB without memory saturation.
   - Non-blocking `os.utime()` timestamp bump to bring transferred files to the top of desktop view.
   - `/api/tunnel_info` synchronization endpoint.

2. **`tunnel.py`**:
   - Manages official `cloudflared` binary with automated background download if missing.
   - Spawns silent background tunnel process with `CREATE_NO_WINDOW`.
   - Extracts live HTTPS domain via regex and triggers callback.

3. **`main_window.py`**:
   - PyQt6 desktop companion.
   - Dual-mode connection toggle: Cloudflare HTTPS vs Local LAN.
   - Single-instance IPC socket lock (`QLocalServer`).
   - Native system tray integration (`QSystemTrayIcon`).

4. **`autostart.py`**:
   - Automated registration on user machine startup (Windows `shell:startup`, macOS LaunchAgent, Linux desktop entry).
