# ⚡ AirFlick Drop

> **Flick-to-Send File Transfer from Mobile to Windows Desktop**  
> Inspired by Apple AirDrop and Instagram Reels interactions. Transfer files up to **15 GB** lag-free with zero-RAM chunked streaming, pure dark Apple OLED UI, 3D physics gestures, and Smart Bump-to-top on Windows Desktop.

---

## 🌟 Key Features

- **📱 Flick-to-Screen Gestures**: Drag the card and flick upward toward your laptop screen with realistic 3D tilt perspective, Web Audio synthesized whoosh effects, and haptic feedback.
- **⚡ Huge Files (Up to 15 GB)**: Uses 4MB chunked streaming over local HTTP. Files stream directly to disk without bloating mobile or laptop RAM.
- **⏸ Pause, Resume & Cancel**: Real-time Transfer HUD with live MB/s speed, progress bar, `⏸ Pause` / `▶ Resume`, and `✕ Cancel` (with automatic partial file cleanup).
- **🚀 Smart Bump-to-Top**: When a file is transferred and already exists on Windows Desktop, AirFlick refreshes its `LastWriteTime` and `CreationTime` to the exact current second and auto-highlights it in Windows Explorer so it stays at the top of your Desktop sorted by date.
- **🌐 100% Offline Ready**: Works with **0 KB Internet**. Connect both devices to the same local Wi-Fi router (no internet needed) or connect your laptop to your phone's Personal Hotspot.
- **🖥️ PyQt6 Desktop Companion**: Native Windows desktop GUI with an auto-updating QR code, network change auto-detection (switches between Wi-Fi and Hotspot automatically), and floating incoming file notification cards.
- **📁 Multi-File Selection**: Pick single or multiple files (images, 4K videos, ZIPs, APKs) with no limit.

---

## 🛠️ Architecture

```
airflick-drop/
├── main_window.py      # PyQt6 companion app (QR code, network listener, history)
├── server.py           # Flask HTTP server (chunked streaming, pause/cancel, bump-to-top)
├── overlay.py          # Windows floating drop card overlay animation
├── Start_AirFlick.bat  # 1-click launcher for Windows
├── requirements.txt    # Python dependencies
├── web/                # Mobile client web app
│   ├── index.html      # Responsive Apple OLED dark UI with 3D flick physics
│   ├── manifest.json   # Web app manifest
│   ├── icon.png        # App icon
│   └── sw.js           # Cache management
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Windows 10/11 (for the desktop companion)
- Any modern mobile browser (Android Chrome, Samsung Internet, iOS Safari)

### 2. Installation
```bash
git clone https://github.com/k39139215-gif/airflick-drop.git
cd airflick-drop
pip install -r requirements.txt
```

### 3. Run AirFlick
Double click `Start_AirFlick.bat` or run:
```bash
python main_window.py
```

1. The companion window will open displaying a QR code and local URL (e.g., `http://192.168.1.15:5050`).
2. Scan the QR code with your mobile camera or open the URL in Chrome/Safari.
3. Tap **"Files"** or the center card to pick files, drag the card upward, and **flick towards your laptop screen**!

---

## 🔒 Offline Setup (No Internet)

1. Turn **Mobile Data OFF** on your phone.
2. Turn **Personal Hotspot ON** on your phone.
3. Connect your laptop's Wi-Fi to your phone's hotspot.
4. The AirFlick Desktop app will auto-detect the hotspot IP and refresh the QR code immediately.
5. Scan or open the URL on mobile and enjoy ultra-fast offline transfers!

---

## 📄 License
MIT License. Free for personal and commercial use.
