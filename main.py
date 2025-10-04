# file: main.py (Updated to load stylesheet)
import sys
from PyQt6.QtWidgets import QApplication
from dashboard.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- ADD THIS PART TO LOAD TEAM 3'S STYLES ---
    try:
        with open("dashboard/style.qss", "r") as f:
            style_sheet = f.read()
            app.setStyleSheet(style_sheet)
    except FileNotFoundError:
        print("Stylesheet file not found. Running with default style.")
    # -----------------------------------------------

    window = MainWindow()
    window.show()
    sys.exit(app.exec())