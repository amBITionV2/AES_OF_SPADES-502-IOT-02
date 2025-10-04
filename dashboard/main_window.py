# file: dashboard/main_window.py (Corrected and Complete)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

# Import our USB manager
from ursafe_sdk.usb_manager import find_usb_drives

# --- Placeholder Data (Simulating what we'll get from the backend) ---
MOCK_SECRETS = {
    "1": {"label": "Gmail", "username": "user@gmail.com", "password": "mock_password_1"},
    "2": {"label": "GitHub", "username": "git-user", "password": "mock_password_2"},
    "3": {"label": "Bank Portal", "username": "customer123", "password": "mock_password_3"},
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Safe Stick Dashboard")
        self.setGeometry(100, 100, 900, 700)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Top Section: USB Selection ---
        self.usb_selection_layout = QHBoxLayout()
        self.usb_label = QLabel("Select UR Safe Stick:")
        self.usb_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Drives")

        self.usb_selection_layout.addWidget(self.usb_label)
        self.usb_selection_layout.addWidget(self.usb_combo, 1)
        self.usb_selection_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(self.usb_selection_layout)

        # --- Middle Section: PIN and Actions ---
        self.action_layout = QHBoxLayout()
        self.pin_label = QLabel("PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Enter your PIN to unlock")

        self.init_button = QPushButton("Initialize New Stick")
        self.unlock_button = QPushButton("Unlock Vault")

        self.action_layout.addWidget(self.pin_label)
        self.action_layout.addWidget(self.pin_input, 1)
        self.action_layout.addWidget(self.init_button)
        self.action_layout.addWidget(self.unlock_button)
        self.main_layout.addLayout(self.action_layout)

        # --- Bottom Section: Secrets Table ---
        self.secrets_table = QTableWidget()
        self.secrets_table.setColumnCount(3)
        self.secrets_table.setHorizontalHeaderLabels(["Label", "Username", "Password"])
        self.secrets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.secrets_table, 1)

        # --- Final Actions ---
        self.bottom_action_layout = QHBoxLayout()
        self.add_secret_button = QPushButton("Add New Secret")
        self.lock_button = QPushButton("Save & Lock Vault")
        self.bottom_action_layout.addStretch()
        self.bottom_action_layout.addWidget(self.add_secret_button)
        self.bottom_action_layout.addWidget(self.lock_button)
        self.main_layout.addLayout(self.bottom_action_layout)
        
        # --- Connect Signals to Slots ---
        self.unlock_button.clicked.connect(self.handle_unlock)
        self.lock_button.clicked.connect(self.handle_lock)
        self.refresh_button.clicked.connect(self.populate_usb_drives)

        # Populate drives on startup
        self.populate_usb_drives()

    def populate_usb_drives(self):
        """
        Finds all connected USB drives and populates the combo box.
        """
        print("Refreshing USB drive list...")
        self.usb_combo.clear()
        drives = find_usb_drives()
        if drives:
            for drive in drives:
                self.usb_combo.addItem(drive['mountpoint'])
            print(f"Found drives: {[d['mountpoint'] for d in drives]}")
        else:
            print("No removable drives found.")

    def handle_unlock(self):
        """
        This is a placeholder. For now, it just loads mock data into the table.
        """
        print("Unlock button clicked! Populating with MOCK data.")
        pin = self.pin_input.text()
        if not pin:
            print("PIN is empty. In a real scenario, we'd show an error.")
            return

        self.secrets_table.setRowCount(0)

        for row, secret in enumerate(MOCK_SECRETS.values()):
            self.secrets_table.insertRow(row)
            self.secrets_table.setItem(row, 0, QTableWidgetItem(secret["label"]))
            self.secrets_table.setItem(row, 1, QTableWidgetItem(secret["username"]))
            self.secrets_table.setItem(row, 2, QTableWidgetItem(secret["password"]))
        print("Mock secrets displayed.")

    def handle_lock(self):
        """
        This is a placeholder. For now, it just clears the table and the PIN field.
        """
        print("Lock button clicked! Clearing UI.")
        self.secrets_table.setRowCount(0)
        self.pin_input.clear()
        print("UI is now locked.")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())