import sys
import os
import winsound
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QApplication

class AirFlickOverlayCard(QWidget):
    """
    Transparent, frameless floating card that swoops in from the bottom
    of the Windows desktop with the received photo/files, drops it, and fades out.
    """
    def __init__(self, file_path, file_name, file_count=1, already_existed=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = file_name
        self.file_count = file_count
        self.already_existed = already_existed

        # Window Flags: Frameless, Always on Top, Click-through / Non-activating
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.card_width = 320
        self.card_height = 420
        self.setFixedSize(self.card_width + 40, self.card_height + 40) # margin for shadow

        self._init_ui()

    def _init_ui(self):
        # Container widget for styling
        self.container = QWidget(self)
        self.container.setGeometry(20, 20, self.card_width, self.card_height)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(12, 12, 14, 248);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 45);
            }
        """)

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 210))
        shadow.setOffset(0, 16)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Badge
        header_layout = QHBoxLayout()
        badge_dot = QLabel("●", self)
        dot_color = "#fbbf24" if self.already_existed else "#34d399"
        badge_dot.setStyleSheet(f"color: {dot_color}; font-size: 11px; background: transparent; border: none;")
        
        if self.already_existed:
            badge_text = "⚡ AirFlick • Exists! Bumped to Top"
        elif self.file_count > 1:
            badge_text = f"AirFlick • Dropped {self.file_count} Files from Android"
        else:
            badge_text = "AirFlick • Dropped from Android"
            
        badge_title = QLabel(badge_text, self)
        badge_title.setStyleSheet("color: #a1a1aa; font-size: 12px; font-weight: 600; letter-spacing: -0.2px; background: transparent; border: none;")
        
        header_layout.addWidget(badge_dot)
        header_layout.addWidget(badge_title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Photo Preview
        self.image_label = QLabel(self)
        self.image_label.setFixedHeight(270)
        self.image_label.setStyleSheet("background-color: #000000; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 15);")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load and scale photo with rounded corners
        if os.path.exists(self.file_path):
            original_pix = QPixmap(self.file_path)
            if not original_pix.isNull():
                scaled = original_pix.scaled(
                    self.card_width - 36, 270,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Crop to exact dimensions
                target_w = self.card_width - 36
                target_h = 270
                cropped = scaled.copy((scaled.width() - target_w) // 2, (scaled.height() - target_h) // 2, target_w, target_h)

                # Round corners on the pixmap
                rounded = QPixmap(target_w, target_h)
                rounded.fill(Qt.GlobalColor.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, target_w, target_h, 20, 20)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, cropped)
                painter.end()

                self.image_label.setPixmap(rounded)
            else:
                self.image_label.setText("📄 " + self.file_name)
                self.image_label.setStyleSheet("color: white; font-size: 16px; background-color: #18181b; border-radius: 20px;")
        
        layout.addWidget(self.image_label)

        # Footer Info
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(2)

        name_label = QLabel(self.file_name, self)
        name_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 600; letter-spacing: -0.2px; background: transparent; border: none;")
        
        if self.already_existed:
            status_text = "Timestamp updated to NOW • Jumped to Top ✓"
        elif self.file_count > 1:
            status_text = f"All {self.file_count} Files Saved to Desktop ✓"
        else:
            status_text = "Saved to Desktop ✓"

        status_label = QLabel(status_text, self)
        status_label.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 500; background: transparent; border: none;")

        footer_layout.addWidget(name_label)
        footer_layout.addWidget(status_label)
        layout.addLayout(footer_layout)
        footer_layout.setSpacing(2)

        name_label = QLabel(self.file_name, self)
        name_label.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        
        status_label = QLabel("Saved to Desktop ✓", self)
        status_label.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 500; background: transparent; border: none;")

        footer_layout.addWidget(name_label)
        footer_layout.addWidget(status_label)
        layout.addLayout(footer_layout)

    def play_entrance(self):
        # Find screen geometry
        screen = QApplication.primaryScreen().geometry()
        
        # Target position: Bottom center or bottom right
        target_x = (screen.width() - self.width()) // 2
        target_y = screen.height() - self.height() - 40 # 40px above taskbar

        # Start position: Off screen below
        start_x = target_x
        start_y = screen.height() + 50

        self.move(start_x, start_y)
        self.setWindowOpacity(1.0)
        self.show()

        # Play arrival chime
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        # Spring Fly-in Animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(650)
        self.anim.setStartValue(QPoint(start_x, start_y))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

        # Timer to start fade out after 3.2 seconds
        QTimer.singleShot(3200, self.play_exit)

    def play_exit(self):
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(450)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_anim.finished.connect(self.close)
        self.fade_anim.start()
