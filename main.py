# file: main.py

import sys
import os
from PyQt6.QtWidgets import QApplication

# Cleanly add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import our two new, separate main window classes
from dashboard.main_app_window import MainAppWindow
from dashboard.secondary_dash import SecondaryDashboard

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load stylesheet for the entire application
    try:
        with open("dashboard/style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Stylesheet file not found. Running with default style.")

    # Create and show the primary user vault window
    main_app_window = MainAppWindow()
    main_app_window.show()

    # Create and show the secondary technical dashboard window
    secondary_dash_window = SecondaryDashboard()
    secondary_dash_window.show()

    sys.exit(app.exec())