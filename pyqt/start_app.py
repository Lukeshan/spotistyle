import sys
import webbrowser
import requests
from io import BytesIO

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, Qt, QTimer, QEvent
from PyQt6.QtGui import QPalette, QColor, QPixmap, QFontDatabase, QFont
from PIL import Image
import numpy as np
import cv2

from app_ui import Ui_MainWindow  # your generated UI file

BACKEND_URL = "http://localhost:8000" # Should add to env vars

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        font_id = QFontDatabase.addApplicationFont("font.otf")  # or "MyFont.otf"
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        app.setFont(QFont(font_family, 10))  # 10 is the default size

        self.ui.songDetailsLabel.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: rgba(255, 255, 255, 180);
            }
        """)



        self.ui.songDetailsLabel.setFont(QFont(font_family, 32))

        self._bg_color = QColor("blue")
        self.setAutoFillBackground(True)
        self.update_bg()

        self.access_token = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_for_token)

        self.track_timer = QTimer()
        self.track_timer.timeout.connect(self.get_current_track)

        self.ui.loginButton.clicked.connect(self.login)
        self.ui.bgColorButton.clicked.connect(self.animate_color)
        self.ui.updateButton_2.clicked.connect(self.get_current_track)

    def update_bg(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self._bg_color)
        self.setPalette(palette)

    def get_bg_color(self):
        return self._bg_color
    
    def set_bg_color(self, color):
        self._bg_color = color
        self.update_bg()

    bg_color = pyqtProperty(QColor, fget=get_bg_color, fset=set_bg_color)


    def get_dominant_rgb(self, url, n_colors = 5):

        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((200, 200))
        pixels = np.array(img).reshape((-1, 3)).astype(np.float32)

        # Apply KMeans clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Reconstruct quantized image
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        quantized_image = quantized.reshape((200, 200, 3))

        # Find dominant color
        label_counts = np.bincount(labels.flatten())
        dominant_index = np.argmax(label_counts)
        dominant_color = centers[dominant_index]
        r, g, b = map(int, dominant_color)
        return r, g, b

    def animate_color(self, r=0,b=255,g=0):
        self.anim = QPropertyAnimation(self, b"bg_color")
        self.anim.setDuration(1000)
        self.anim.setStartValue(self._bg_color)
        self.anim.setEndValue(QColor(r,g,b))
        self.anim.start()

    def login(self):
        try:
            response = requests.get(f"{BACKEND_URL}/login")
            auth_url = response.json()["auth_url"]
            webbrowser.open(auth_url)
            self.ui.songDetailsLabel.setText("Login in browser...")
            self.poll_timer.start(1250)  # Poll every 2 seconds
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Login failed: {e}")

    def poll_for_token(self):
        try:
            response = requests.get(f"{BACKEND_URL}/track")
            if response.status_code == 401:
                return  # Still not authenticated
            self.poll_timer.stop()
            self.access_token = response.json().get("access_token")
            self.ui.songDetailsLabel.setText("Login successful!")
            self.get_current_track()
            self.track_timer.start(10000) 
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Polling error: {e}")

    def get_current_track(self):
        try:
            response = requests.get(f"{BACKEND_URL}/track")
            data = response.json()
            track = data.get("name", "Unknown")
            artist = data.get("artist", "Unknown")
            image_url = data.get("image")
            new_track = True if self.ui.songDetailsLabel.text() != f"{track} — {artist}" else False

            if not new_track:
                return

            self.ui.songDetailsLabel.setText(f"{track} — {artist}")

            if image_url:
                img_data = requests.get(image_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                scaled = pixmap.scaled(self.ui.albumArtLabel.width(), self.ui.albumArtLabel.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.ui.albumArtLabel.setPixmap(scaled)
                r,g,b = self.get_dominant_rgb(url=image_url, n_colors=16)
                d_f = 0.96 # Darkening Factor
                r = round(r*d_f); g = round(g*d_f); b = round(b*d_f)
                self.animate_color(r=r,g=g,b=b)
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Error fetching track: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
