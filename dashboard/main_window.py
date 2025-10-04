# file: dashboard/main_window.py
from PyQt6.QtWidgets import QMainWindow, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Safe Stick Dashboard")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        # A central widget to show a welcome message
        central_widget = QLabel("UR Safe Stick Project - Blueprint Initialized!")
        central_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set a simple style for visibility
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 24px;
                font-family: Arial, sans-serif;
            }
        """)

        self.setCentralWidget(central_widget)