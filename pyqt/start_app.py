import sys
import webbrowser
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QPixmap
from app_ui import Ui_MainWindow  # your generated UI file

BACKEND_URL = "http://localhost:8000"

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

    def animate_color(self):
        self.anim = QPropertyAnimation(self, b"bg_color")
        self.anim.setDuration(1000)
        self.anim.setStartValue(self._bg_color)
        self.anim.setEndValue(QColor(225,122,122))
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
                scaled = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.ui.albumArtLabel.setPixmap(scaled)
        except Exception as e:
            self.ui.songDetailsLabel.setText(f"Error fetching track: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
