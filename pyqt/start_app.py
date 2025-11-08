import sys
import webbrowser
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QInputDialog
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, Qt
from PyQt6.QtGui import QPalette, QColor
from app_ui import Ui_MainWindow  # your generated UI file

BACKEND_URL = "http://localhost:8000"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._bg_color = QColor("white")
        self.setAutoFillBackground(True)
        self.update_bg()

        self.access_token = None

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
        self.anim.setDuration(1000)  # 1 second
        self.anim.setStartValue(self._bg_color)
        self.anim.setEndValue(QColor(225,122,122))  # target color
        self.anim.start()

    def login(self):
        # Step 1: Get Spotify login URL from backend
        try:
            response = requests.get(f"{BACKEND_URL}/login")
            login_url = response.json()["url"]
            webbrowser.open(login_url)
            self.ui.label.setText("Login in browser...")
        except Exception as e:
            self.ui.label.setText(f"Login failed: {e}")
            return

        # Step 2: Wait for user to complete login and paste code
        code, ok = QInputDialog.getText(self, "Spotify Login", "Paste the code from the URL:")
        if not ok or not code:
            self.ui.label.setText("Login cancelled.")
            return

        # Step 3: Exchange code for access token
        try:
            token_response = requests.get(f"{BACKEND_URL}/callback", params={"code": code})
            self.access_token = token_response.json()["access_token"]
            self.ui.label.setText("Login successful!")
            self.get_current_track()
        except Exception as e:
            self.ui.label.setText(f"Token exchange failed: {e}")

    def get_current_track(self):
        if not self.access_token:
            self.ui.label.setText("Not authenticated.")
            return

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BACKEND_URL}/track", headers=headers)
            data = response.json()
            track = data.get("name", "Unknown")
            artist = data.get("artist", "Unknown")
            self.ui.label.setText(f"{track} — {artist}")
        except Exception as e:
            self.ui.label.setText(f"Error fetching track: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
