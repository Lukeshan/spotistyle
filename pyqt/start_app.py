import sys
import webbrowser
import requests
from io import BytesIO

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QPixmap
from PIL import Image, ImageFilter
import numpy as np
import cv2

from app_ui import Ui_MainWindow  # your generated UI file

BACKEND_URL = "http://localhost:8000" # Should add to env vars

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._bg_color = QColor("blue")
        self.setAutoFillBackground(True)
        self.update_bg()

        self.access_token = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_for_token)

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


    def get_dominant_rgb(self, image_url, crop_margin=0.15, blur_radius=50, min_saturation=50):
        # Load and crop image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        w, h = img.size
        margin_w, margin_h = int(w * crop_margin), int(h * crop_margin)
        img = img.crop((margin_w, margin_h, w - margin_w, h - margin_h))
        img = img.resize((200, 200))

        # Convert to NumPy and OpenCV formats
        pixels = np.array(img)
        img_cv = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)

        # Saliency detection
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
        (success, saliencyMap) = saliency.computeSaliency(img_cv)
        saliencyMap = (saliencyMap * 255).astype(np.uint8)

        # Edge detection
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=5)
        edge_map = np.absolute(edges).astype(np.uint8)

        # Combine saliency and edge maps
        combined_weight = cv2.addWeighted(saliencyMap, 0.6, edge_map, 0.4, 0)
        combined_weight = combined_weight.flatten()

        # Flatten pixels and apply weights
        flat_pixels = pixels.reshape(-1, 3)
        hsv = cv2.cvtColor(flat_pixels.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).reshape(-1, 3)
        mask = hsv[:, 1] >= min_saturation
        filtered_pixels = flat_pixels[mask]
        filtered_weights = combined_weight[mask]

        # Fallback if too few pixels remain
        if len(filtered_pixels) < 10:
            filtered_pixels = flat_pixels
            filtered_weights = combined_weight

        # Weighted average
        weighted_avg = np.average(filtered_pixels, axis=0, weights=filtered_weights)
        r, g, b = map(int, weighted_avg)
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
            self.poll_timer.start(2000)  # Poll every 2 seconds
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
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Polling error: {e}")

    def get_current_track(self):
        try:
            response = requests.get(f"{BACKEND_URL}/track")
            data = response.json()
            track = data.get("name", "Unknown")
            artist = data.get("artist", "Unknown")
            image_url = data.get("image")

            self.ui.songDetailsLabel.setText(f"{track} — {artist}")

            if image_url:
                img_data = requests.get(image_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                scaled = pixmap.scaled(self.ui.albumArtLabel.width(), self.ui.albumArtLabel.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.ui.albumArtLabel.setPixmap(scaled)
                r,g,b = self.get_dominant_rgb(image_url)
                self.animate_color(r,g,b)
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Error fetching track: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
