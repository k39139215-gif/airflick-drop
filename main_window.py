import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import threading
import subprocess
import io
import qrcode
from PIL import Image

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
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame, QApplication
)

from overlay import AirFlickOverlayCard
from server import run_server, get_lan_ip, DESKTOP_DIR

class ServerBridge(QObject):
    file_received = pyqtSignal(str, str, int, bool)

class AirFlickMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirFlick Drop • Mobile to Desktop")
        self.setFixedSize(480, 680)
        
        self.lan_ip = get_lan_ip()
        self.port = 5050
        self.server_url = f"http://{self.lan_ip}:{self.port}"
        
        self.bridge = ServerBridge()
        self.bridge.file_received.connect(self.on_file_received)

        self.active_overlays = []

        self._init_ui()
        self._start_server_thread()

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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header_title = QLabel("AirFlick Drop ⚡", self)
        header_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        
        status_badge = QLabel("● Active", self)
        status_badge.setStyleSheet("color: #10b981; font-weight: 600; font-size: 13px; background: rgba(16, 185, 129, 0.12); padding: 4px 10px; border-radius: 20px;")
        
        header.addWidget(header_title)
        header.addStretch()
        header.addWidget(status_badge)
        layout.addLayout(header)

        # Instructions / QR Card
        qr_card = QFrame(self)
        qr_card.setObjectName("card")
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.setSpacing(12)

        instr = QLabel("Scan with iPhone or Android Camera to connect:", self)
        instr.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        qr_layout.addWidget(instr, alignment=Qt.AlignmentFlag.AlignCenter)

        # QR Code Display
        self.qr_label = QLabel(self)
        self.qr_label.setFixedSize(180, 180)
        self.qr_label.setStyleSheet("background: white; border-radius: 12px; padding: 6px;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._generate_qr_code()
        qr_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # URL and Refresh Row
        url_box = QHBoxLayout()
        url_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_label = QLabel(self.server_url, self)
        self.url_label.setStyleSheet("color: #818cf8; font-size: 15px; font-weight: 600; background: rgba(99, 102, 241, 0.12); padding: 6px 14px; border-radius: 8px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_box.addWidget(self.url_label)

        refresh_ip_btn = QPushButton("🔄", self)
        refresh_ip_btn.setToolTip("Auto-detect IP change (Wi-Fi or Hotspot)")
        refresh_ip_btn.setStyleSheet("background: rgba(255, 255, 255, 0.08); color: #ffffff; border-radius: 8px; padding: 6px 10px; font-size: 13px;")
        refresh_ip_btn.clicked.connect(self.check_ip_update)
        url_box.addWidget(refresh_ip_btn)
        qr_layout.addLayout(url_box)

        hint = QLabel("Offline Ready • Connect phone to same Wi-Fi or Hotspot", self)
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        qr_layout.addWidget(hint, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(qr_card)

        # IP polling timer (detects Hotspot / Wi-Fi network switch automatically)
        self.ip_timer = QTimer(self)
        self.ip_timer.setInterval(3000)
        self.ip_timer.timeout.connect(self.check_ip_update)
        self.ip_timer.start()

        # Buttons Row
        btn_row = QHBoxLayout()
        test_btn = QPushButton("✨ Test Flick Animation", self)
        test_btn.setProperty("class", "primary-btn")
        test_btn.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
            color: white; font-weight: 600; font-size: 13px; border: none; border-radius: 12px; padding: 12px 20px;
        """)
        test_btn.clicked.connect(self.trigger_demo_flick)
        btn_row.addWidget(test_btn)

        open_folder_btn = QPushButton("📂 Open Desktop", self)
        open_folder_btn.setStyleSheet("""
            background: #1e293b; color: #cbd5e1; font-weight: 600; font-size: 13px; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px 16px;
        """)
        open_folder_btn.clicked.connect(lambda: open_desktop_folder(DESKTOP_DIR))
        btn_row.addWidget(open_folder_btn)

        layout.addLayout(btn_row)

        # Activity List
        activity_title = QLabel("Recent AirFlick Drops", self)
        activity_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #94a3b8; margin-top: 4px;")
        layout.addWidget(activity_title)

        self.history_list = QListWidget(self)
        self.history_list.setFixedHeight(120)
        layout.addWidget(self.history_list)

        # Add initial item
        init_item = QListWidgetItem("Ready for files. Flick from iPhone or Android anytime!")
        self.history_list.addItem(init_item)

    def _generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(self.server_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)
        pix = QPixmap()
        pix.loadFromData(buffer.getvalue())
        self.qr_label.setPixmap(pix)

    def check_ip_update(self):
        new_ip = get_lan_ip()
        if new_ip and new_ip != self.lan_ip:
            print(f"[AirFlick] Network change detected: {self.lan_ip} -> {new_ip}")
            self.lan_ip = new_ip
            self.server_url = f"http://{self.lan_ip}:{self.port}"
            self.url_label.setText(self.server_url)
            self._generate_qr_code()

    def _start_server_thread(self):
        def server_callback(path, name, count=1, existed=False):
            self.bridge.file_received.emit(path, name, count, existed)

        t = threading.Thread(target=run_server, args=(server_callback, self.port), daemon=True)
        t.start()

    def on_file_received(self, file_path, file_name, file_count=1, already_existed=False):
        prefix = "⚡ [BUMPED TO TOP]" if already_existed else "📁"
        item = QListWidgetItem(f"{prefix} {file_name} → Desktop")
        self.history_list.insertItem(0, item)

        # Launch floating overlay card
        overlay = AirFlickOverlayCard(file_path, file_name, file_count, already_existed)
        self.active_overlays.append(overlay)
        overlay.play_entrance()

    def trigger_demo_flick(self):
        demo_path = os.path.join(os.path.dirname(__file__), "web", "demo_sample.jpg")
        if not os.path.exists(demo_path):
            img = Image.new("RGB", (600, 800), color=(99, 102, 241))
            img.save(demo_path)

        self.on_file_received(demo_path, "Demo_AirFlick_Photo.jpg", 1, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirFlickMainWindow()
    window.show()
    sys.exit(app.exec())
