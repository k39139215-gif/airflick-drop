# ⚡ AirFlick Drop

> **Cross-Platform Flick-to-Send File Transfer: iPhone & Android ➔ Windows & Mac**  
> Inspired by Apple AirDrop and Instagram Reels interactions. Transfer files up to **15 GB** lag-free with zero-RAM chunked streaming, pure dark Apple OLED UI, 3D physics gestures, and Smart Bump-to-top on Desktop.

<p align="center">
  <img src="qr_code.png" width="220" alt="AirFlick Live QR Code" style="border-radius: 16px; border: 4px solid #6366f1;" />
  <br />
  <sub>Scan with your phone's camera (iPhone or Android) to connect directly over local Wi-Fi or Hotspot</sub>
</p>

---

## 🌟 The Cross-Ecosystem Solution

Apple AirDrop is great inside the Apple walled garden, but breaks down completely across different operating systems:
- ❌ **iPhone ➔ Windows**: AirDrop doesn't exist on Windows.
- ❌ **Android ➔ Mac**: Quick Share / AirDrop doesn't work on macOS.

**AirFlick Drop fixes both permanently:**
- 📱 **Send from any Phone**: iPhone (Safari), iPad, Android (Chrome/Samsung Internet) — with zero apps to install!
- 💻 **Receive on any Computer**: Windows 10/11, macOS (MacBook, iMac), and Linux!

---

## 🚀 Key Features

- **📱 Flick-to-Screen Gestures**: Drag the card and flick upward toward your computer screen with realistic 3D tilt perspective, Web Audio synthesized whoosh effects, and haptic feedback.
- **🍎 iPhone & Android Ready**: Works directly inside iOS Safari and Android Chrome with instant system file/photo pickers.
- **🖼️ Full-Fit Visual Previews**: Supports full-bleed previews for landscape certificates, widescreen photos, and vertical documents without any awkward cropping (`object-fit: contain` with dynamic aspect ratio preservation).
- **⚡ Huge Files (Up to 15 GB)**: Uses 4MB chunked streaming over local HTTP. Files stream directly to disk without bloating mobile or laptop RAM.
- **⏸ Pause, Resume & Cancel**: Real-time Transfer HUD with live MB/s speed, progress bar, `⏸ Pause` / `▶ Resume`, and `✕ Cancel` (with automatic partial file cleanup).
- **🚀 Smart Bump-to-Top**: When a file is transferred and already exists on Desktop, AirFlick refreshes its `LastWriteTime` and `CreationTime` to the exact current second and auto-highlights it in Windows Explorer or macOS Finder.
- **🌐 100% Offline Ready**: Works with **0 KB Internet**. Connect both devices to the same local Wi-Fi router (no internet needed) or connect your laptop to your phone's Personal Hotspot.
- **🖥️ Desktop Companion**: Native desktop GUI (PyQt6) with an auto-updating QR code, network change auto-detection (switches between Wi-Fi and Hotspot automatically), and floating incoming file notification cards.
- **📁 Multi-File Selection**: Pick single or multiple files (images, 4K videos, ZIPs, APKs) with no limit.

---

## 🔒 Security & Privacy (Zero Data Breach Risk)

1. **Private Local IP Only (RFC 1918)**:  
   The IP addresses used (like `10.x.x.x` or `192.168.x.x`) are non-routable private intranet addresses. **They cannot be accessed from anywhere on the internet.** Even if someone has your URL or QR code, it will not open outside your own local Wi-Fi or personal hotspot.
2. **Ingestion-Only Architecture**:  
   The server only exposes upload endpoints (`/upload`, `/api/upload_chunk`). There are **no file-browsing, listing, or download endpoints**. Nobody can inspect or download any files stored on your laptop.
3. **Zero Cloud, Zero Third-Party Servers**:  
   All files travel 100% peer-to-peer over your local wireless waves directly between your phone and laptop. Zero bytes are uploaded to the cloud or external servers.

---

## 🛠️ Architecture

```
airflick-drop/
├── main_window.py      # PyQt6 companion app (QR code, network listener, history)
├── server.py           # Flask HTTP server (cross-platform streaming, bump-to-top)
├── overlay.py          # Floating drop card overlay animation
├── Start_AirFlick.bat  # 1-click launcher for Windows
├── start_silent.vbs    # Silent background startup launcher (zero CMD popup)
├── start_airflick.sh   # 1-click launcher for macOS & Linux
├── requirements.txt    # Python dependencies
├── qr_code.png         # Project QR Code asset
├── web/                # Mobile client web app
│   ├── index.html      # Responsive Apple OLED dark UI with 3D flick physics & full-fit preview
│   ├── qr.png          # High-res QR code
│   ├── manifest.json   # Web app manifest
│   ├── icon.png        # App icon
│   └── sw.js           # Cache management
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Windows 10/11, macOS, or Linux
- Any modern mobile browser (iOS Safari, Android Chrome, Samsung Internet)

### 2. Installation
```bash
git clone https://github.com/k39139215-gif/airflick-drop.git
cd airflick-drop
pip install -r requirements.txt
```

### 3. Run AirFlick
**On Windows:**
Double-click `Start_AirFlick.bat` or run:
```bash
python main_window.py
```

**On macOS / Linux:**
Run:
```bash
chmod +x start_airflick.sh
./start_airflick.sh
```

1. The companion window will open displaying a QR code and local URL.
2. Scan the QR code with your iPhone or Android camera.
3. Pick any photo, document, or huge 4K video, and **flick it up towards your computer screen**!

---

## 📄 License
MIT License. Free for personal and commercial use.
