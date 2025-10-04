# file: dashboard/main_app_window.py

from PyQt6.QtWidgets import QMainWindow
from dashboard.main_window import MainAppTab

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Safe Stick - User Vault")
        self.setGeometry(100, 100, 950, 680)

        # Create an instance of our main application widget
        self.main_app_widget = MainAppTab()

        # Set it as the central widget for this window
        self.setCentralWidget(self.main_app_widget)