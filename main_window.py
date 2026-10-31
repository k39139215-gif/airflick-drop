import socket
import os
import sys
import threading
import subprocess
import io
import json
import urllib.request
import qrcode
from PIL import Image

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def open_desktop_folder(path):
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        pass

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QIcon, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame, QApplication,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from server import run_server, get_lan_ip, DESKTOP_DIR
from tunnel import CloudflareTunnel, URL_CACHE_FILE

LOCAL_SERVER_NAME = "airflick_drop_single_instance_lock"

class ServerBridge(QObject):
    file_received = pyqtSignal(str, str, int, bool)
    tunnel_url_updated = pyqtSignal(str)

class AirFlickMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirFlick Drop • Mobile to Desktop")
        self.setFixedSize(500, 720)
        
        icon_path = os.path.join(os.path.dirname(__file__), "web", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.lan_ip = get_lan_ip()
        self.port = 5050
        self.lan_url = f"http://{self.lan_ip}:{self.port}"
        self.tunnel_url = None
        self.current_mode = "cloudflare"  # "cloudflare" or "lan"
        self.server_url = self.lan_url
        self.local_tunnel = None
        
        # Check if cached tunnel URL exists
        if os.path.exists(URL_CACHE_FILE):
            try:
                with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
                    cached = f.read().strip()
                    if cached.startswith("https://"):
                        self.tunnel_url = cached
                        self.server_url = self.tunnel_url
            except Exception:
                pass

        self.bridge = ServerBridge()
        self.bridge.file_received.connect(self.on_file_received)
        self.bridge.tunnel_url_updated.connect(self.on_tunnel_url_updated)

        self.is_quitting = False

        self._init_single_instance_server()
        self._init_ui()
        self._init_tray()
        self._start_server_and_tunnel()

    def _init_single_instance_server(self):
        self.local_server = QLocalServer(self)
        self.local_server.removeServer(LOCAL_SERVER_NAME)
        self.local_server.listen(LOCAL_SERVER_NAME)
        self.local_server.newConnection.connect(self._on_single_instance_activated)

    def _on_single_instance_activated(self):
        client = self.local_server.nextPendingConnection()
        if client:
            client.close()
        self.show_and_activate()

    def _init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #090d16;
            }
            QWidget {
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            }
            QFrame#card {
                background: #131b2e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
            }
            QPushButton.mode-pill {
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton.mode-pill:hover {
                background: #334155;
                color: #ffffff;
            }
            QPushButton.mode-pill-active {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                color: #ffffff;
                border: 1px solid #818cf8;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton.primary-btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                color: white;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 12px;
                padding: 12px 20px;
            }
            QPushButton.primary-btn:hover {
                background: #4f46e5;
            }
            QPushButton.secondary-btn {
                background: #1e293b;
                color: #cbd5e1;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 12px 16px;
            }
            QPushButton.secondary-btn:hover {
                background: #334155;
                color: #ffffff;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: #1a2236;
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 6px;
                color: #cbd5e1;
                font-size: 13px;
            }
        """)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header_title = QLabel("AirFlick Drop ⚡", self)
        header_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        
        self.status_badge = QLabel("● Active", self)
        self.status_badge.setStyleSheet("color: #10b981; font-weight: 600; font-size: 12px; background: rgba(16, 185, 129, 0.12); padding: 4px 10px; border-radius: 20px;")
        
        header.addWidget(header_title)
        header.addStretch()
        header.addWidget(self.status_badge)
        layout.addLayout(header)

        # Mode Selection Row (Cloudflare vs Local LAN)
        mode_box = QHBoxLayout()
        mode_box.setSpacing(8)

        self.btn_cf_mode = QPushButton("🌐 Cloudflare HTTPS (Universal)", self)
        self.btn_cf_mode.setProperty("class", "mode-pill-active")
        self.btn_cf_mode.clicked.connect(lambda: self.switch_mode("cloudflare"))
        mode_box.addWidget(self.btn_cf_mode)

        self.btn_lan_mode = QPushButton("📶 Local Wi-Fi / Hotspot", self)
        self.btn_lan_mode.setProperty("class", "mode-pill")
        self.btn_lan_mode.clicked.connect(lambda: self.switch_mode("lan"))
        mode_box.addWidget(self.btn_lan_mode)

        layout.addLayout(mode_box)

        # Instructions / QR Card
        qr_card = QFrame(self)
        qr_card.setObjectName("card")
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(18, 16, 18, 16)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.setSpacing(10)

        self.mode_info_badge = QLabel("● HTTPS Secure • Works Across All Networks", self)
        self.mode_info_badge.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; background: rgba(16, 185, 129, 0.10); padding: 3px 10px; border-radius: 12px;")
        qr_layout.addWidget(self.mode_info_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        instr = QLabel("Scan with iPhone or Android Camera to connect:", self)
        instr.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        qr_layout.addWidget(instr, alignment=Qt.AlignmentFlag.AlignCenter)

        # QR Code Display
        self.qr_label = QLabel(self)
        self.qr_label.setFixedSize(175, 175)
        self.qr_label.setStyleSheet("background: white; border-radius: 12px; padding: 6px;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # URL and Action Row
        url_box = QHBoxLayout()
        url_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        url_box.setSpacing(6)

        self.url_label = QLabel("Connecting secure tunnel...", self)
        self.url_label.setStyleSheet("color: #818cf8; font-size: 14px; font-weight: 600; background: rgba(99, 102, 241, 0.12); padding: 6px 12px; border-radius: 8px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_box.addWidget(self.url_label)

        copy_btn = QPushButton("📋", self)
        copy_btn.setToolTip("Copy URL to Clipboard")
        copy_btn.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #ffffff; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        copy_btn.clicked.connect(self.copy_url_to_clipboard)
        url_box.addWidget(copy_btn)

        refresh_btn = QPushButton("🔄", self)
        refresh_btn.setToolTip("Refresh connection and auto-detect IP")
        refresh_btn.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #ffffff; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        refresh_btn.clicked.connect(self.refresh_all_connections)
        url_box.addWidget(refresh_btn)

        qr_layout.addLayout(url_box)

        self.hint_label = QLabel("Works on any Wi-Fi, Hotspot, or Mobile Data • Zero white screen!", self)
        self.hint_label.setStyleSheet("color: #64748b; font-size: 11px;")
        qr_layout.addWidget(self.hint_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(qr_card)

        # Buttons Row
        btn_row = QHBoxLayout()
        test_btn = QPushButton("✨ Test Flick Animation", self)
        test_btn.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
            color: white; font-weight: 600; font-size: 13px; border: none; border-radius: 12px; padding: 11px 18px;
        """)
        test_btn.clicked.connect(self.trigger_demo_flick)
        btn_row.addWidget(test_btn)

        open_folder_btn = QPushButton("📂 Open Desktop", self)
        open_folder_btn.setStyleSheet("""
            background: #1e293b; color: #cbd5e1; font-weight: 600; font-size: 13px; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 11px 16px;
        """)
        open_folder_btn.clicked.connect(lambda: open_desktop_folder(DESKTOP_DIR))
        btn_row.addWidget(open_folder_btn)

        layout.addLayout(btn_row)

        # Activity List
        activity_title = QLabel("Recent AirFlick Drops", self)
        activity_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #94a3b8; margin-top: 2px;")
        layout.addWidget(activity_title)

        self.history_list = QListWidget(self)
        self.history_list.setFixedHeight(110)
        layout.addWidget(self.history_list)

        init_item = QListWidgetItem("Ready for files. Flick from iPhone or Android anytime!")
        self.history_list.addItem(init_item)

        # Initial render of QR
        self.update_active_view()

        # Background polling timer
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(3000)
        self.sync_timer.timeout.connect(self.periodic_sync)
        self.sync_timer.start()

    def switch_mode(self, mode):
        self.current_mode = mode
        if mode == "cloudflare":
            self.btn_cf_mode.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                color: #ffffff; border: 1px solid #818cf8; border-radius: 10px; padding: 8px 14px; font-size: 12px; font-weight: 700;
            """)
            self.btn_lan_mode.setStyleSheet("""
                background: #1e293b; color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 8px 14px; font-size: 12px; font-weight: 600;
            """)
            self.mode_info_badge.setText("● HTTPS Secure • Works Across All Networks")
            self.mode_info_badge.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; background: rgba(16, 185, 129, 0.10); padding: 3px 10px; border-radius: 12px;")
            self.hint_label.setText("Works on any Wi-Fi, Hotspot, or Mobile Data • Zero white screen!")
        else:
            self.btn_lan_mode.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                color: #ffffff; border: 1px solid #818cf8; border-radius: 10px; padding: 8px 14px; font-size: 12px; font-weight: 700;
            """)
            self.btn_cf_mode.setStyleSheet("""
                background: #1e293b; color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 8px 14px; font-size: 12px; font-weight: 600;
            """)
            self.mode_info_badge.setText("● Local LAN Mode • High Speed Wi-Fi")
            self.mode_info_badge.setStyleSheet("color: #3b82f6; font-size: 12px; font-weight: 600; background: rgba(59, 130, 246, 0.10); padding: 3px 10px; border-radius: 12px;")
            self.hint_label.setText("Connect phone to the same Wi-Fi or Hotspot.")
        
        self.update_active_view()

    def update_active_view(self):
        if self.current_mode == "cloudflare":
            if self.tunnel_url:
                self.server_url = self.tunnel_url
                self.url_label.setText(self.tunnel_url)
                self._generate_qr_code(self.tunnel_url)
            else:
                self.url_label.setText("Connecting secure tunnel...")
                # Temporarily show LAN QR until tunnel connects
                self._generate_qr_code(self.lan_url)
        else:
            self.server_url = self.lan_url
            self.url_label.setText(self.lan_url)
            self._generate_qr_code(self.lan_url)

        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.setToolTip(f"AirFlick Drop • Ready\n{self.server_url}")

    def _generate_qr_code(self, target_url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)
        pix = QPixmap()
        pix.loadFromData(buffer.getvalue())
        self.qr_label.setPixmap(pix)

    def on_tunnel_url_updated(self, url):
        self.tunnel_url = url
        print(f"[AirFlick GUI] Cloudflare HTTPS Tunnel Connected: {url}")
        if self.current_mode == "cloudflare":
            self.update_active_view()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(
                "AirFlick Drop",
                f"Cloudflare Tunnel Ready! Flick from anywhere.",
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )

    def periodic_sync(self):
        # 1. Check if LAN IP has changed
        current_ip = get_lan_ip()
        if current_ip and current_ip != self.lan_ip:
            print(f"[AirFlick] Network change detected: {self.lan_ip} -> {current_ip}")
            self.lan_ip = current_ip
            self.lan_url = f"http://{self.lan_ip}:{self.port}"
            if self.current_mode == "lan":
                self.update_active_view()

        # 2. Check tunnel status via server API or cache file if tunnel_url not yet set
        if not self.tunnel_url:
            self._query_server_tunnel_info()

    def _query_server_tunnel_info(self):
        def query():
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/tunnel_info", headers={'User-Agent': 'AirFlickGUI'})
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        t_url = data.get("tunnel_url")
                        if t_url and t_url != self.tunnel_url:
                            self.bridge.tunnel_url_updated.emit(t_url)
            except Exception:
                # Check cache file
                if os.path.exists(URL_CACHE_FILE):
                    try:
                        with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
                            t_url = f.read().strip()
                            if t_url.startswith("https://") and t_url != self.tunnel_url:
                                self.bridge.tunnel_url_updated.emit(t_url)
                    except Exception:
                        pass
        t = threading.Thread(target=query, daemon=True)
        t.start()

    def _start_server_and_tunnel(self):
        # Check if server is already running
        server_alive = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', self.port)) == 0:
                server_alive = True

        if server_alive:
            print(f"[AirFlick GUI] Server already alive on port {self.port}. Attached cleanly.")
            self._query_server_tunnel_info()
            # If server is running but no tunnel is cached, start tunnel companion
            if not self.tunnel_url:
                self.local_tunnel = CloudflareTunnel(self.port)
                self.local_tunnel.start(lambda url: self.bridge.tunnel_url_updated.emit(url))
        else:
            def server_callback(path, name, count=1, existed=False):
                self.bridge.file_received.emit(path, name, count, existed)

            # Start server (which automatically launches CloudflareTunnel)
            t = threading.Thread(
                target=run_server, 
                args=(server_callback, self.port, True), 
                daemon=True
            )
            t.start()
            
            # Start tunnel callback listener
            def check_tunnel_loop():
                for _ in range(30):
                    if self.tunnel_url:
                        break
                    if os.path.exists(URL_CACHE_FILE):
                        try:
                            with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
                                u = f.read().strip()
                                if u.startswith("https://"):
                                    self.bridge.tunnel_url_updated.emit(u)
                                    break
                        except Exception:
                            pass
                    threading.Event().wait(1)
            
            t_watcher = threading.Thread(target=check_tunnel_loop, daemon=True)
            t_watcher.start()

    def refresh_all_connections(self):
        self.lan_ip = get_lan_ip()
        self.lan_url = f"http://{self.lan_ip}:{self.port}"
        self._query_server_tunnel_info()
        self.update_active_view()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage("AirFlick", "Connections refreshed!", QSystemTrayIcon.MessageIcon.Information, 1000)

    def on_file_received(self, file_path, file_name, file_count=1, already_existed=False):
        prefix = "⚡ [BUMPED TO TOP]" if already_existed else "📁"
        item = QListWidgetItem(f"{prefix} {file_name} → Desktop")
        self.history_list.insertItem(0, item)

        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(
                "AirFlick Drop",
                f"Received {file_name} on Desktop",
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )

    def trigger_demo_flick(self):
        demo_path = os.path.join(os.path.dirname(__file__), "web", "demo_sample.jpg")
        if not os.path.exists(demo_path):
            img = Image.new("RGB", (600, 800), color=(99, 102, 241))
            img.save(demo_path)

        self.on_file_received(demo_path, "Demo_AirFlick_Photo.jpg", 1, True)

    def _init_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), "web", "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(f"AirFlick Drop • Ready\n{self.server_url}")

        tray_menu = QMenu()
        show_action = QAction("Open AirFlick (QR Code)", self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)

        copy_cf_action = QAction("Copy Cloudflare URL (HTTPS)", self)
        copy_cf_action.triggered.connect(lambda: self.copy_specific_url(self.tunnel_url or self.server_url))
        tray_menu.addAction(copy_cf_action)

        copy_lan_action = QAction("Copy Local Wi-Fi URL", self)
        copy_lan_action.triggered.connect(lambda: self.copy_specific_url(self.lan_url))
        tray_menu.addAction(copy_lan_action)

        open_folder_action = QAction("Open Desktop Folder", self)
        open_folder_action.triggered.connect(lambda: open_desktop_folder(DESKTOP_DIR))
        tray_menu.addAction(open_folder_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit AirFlick", self)
        quit_action.triggered.connect(self.force_quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def show_and_activate(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()

    def copy_url_to_clipboard(self):
        QApplication.clipboard().setText(self.server_url)
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage("AirFlick", "Mobile URL copied to clipboard!", QSystemTrayIcon.MessageIcon.Information, 1500)

    def copy_specific_url(self, url):
        if url:
            QApplication.clipboard().setText(url)
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage("AirFlick", f"Copied: {url}", QSystemTrayIcon.MessageIcon.Information, 1500)

    def closeEvent(self, event):
        if self.is_quitting:
            event.accept()
        else:
            event.ignore()
            self.hide()
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(
                    "AirFlick Drop",
                    "Running silently in the background. Ready to receive files anytime!",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

    def force_quit(self):
        self.is_quitting = True
        if self.local_tunnel:
            self.local_tunnel.stop()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Check single instance
    check_socket = QLocalSocket()
    check_socket.connectToServer(LOCAL_SERVER_NAME)
    if check_socket.waitForConnected(400):
        # Already running: the active instance is now brought to front
        sys.exit(0)

    window = AirFlickMainWindow()
    if "--minimized" in sys.argv or "--startup" in sys.argv:
        pass
    else:
        window.show()
    sys.exit(app.exec())
