# file: dashboard/main_window.py (Final version with secret management)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout
)
from PyQt6.QtCore import Qt

from ursafe_sdk.usb_manager import find_usb_drives, verify_stick
from ursafe_sdk.log_manager import add_log_entry
from ursafe_sdk.vault_manager import initialize_vault_placeholder

# --- MOCK_SECRETS (unchanged) ---
MOCK_SECRETS = {
    "1": {"label": "Gmail", "username": "user@gmail.com", "password": "mock_password_1"},
    "2": {"label": "GitHub", "username": "git-user", "password": "mock_password_2"},
}

# --- PinDialog (unchanged) ---
class PinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Vault PIN")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pin_input = QLineEdit()
        self.confirm_pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout = QFormLayout()
        form_layout.addRow("New PIN:", self.pin_input)
        form_layout.addRow("Confirm PIN:", self.confirm_pin_input)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def get_pin(self):
        pin1 = self.pin_input.text()
        pin2 = self.confirm_pin_input.text()
        if pin1 and pin1 == pin2: return pin1
        return None

# --- NEW: Secret Input Dialog ---
class SecretDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Secret")
        self.label_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        if data:
            self.label_input.setText(data.get("label", ""))
            self.username_input.setText(data.get("username", ""))
            self.password_input.setText(data.get("password", ""))
        form_layout = QFormLayout()
        form_layout.addRow("Label:", self.label_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def get_data(self):
        if self.label_input.text():
            return {
                "label": self.label_input.text(),
                "username": self.username_input.text(),
                "password": self.password_input.text(),
            }
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Safe Stick Dashboard")
        self.setGeometry(100, 100, 900, 700)
        self.is_unlocked = False # --- NEW: State variable to track vault status

        # Main layout (unchanged)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # UI Elements (unchanged)
        self.usb_selection_layout = QHBoxLayout()
        self.usb_label = QLabel("Select UR Safe Stick:")
        self.usb_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Drives")
        self.usb_selection_layout.addWidget(self.usb_label)
        self.usb_selection_layout.addWidget(self.usb_combo, 1)
        self.usb_selection_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(self.usb_selection_layout)
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
        self.secrets_table = QTableWidget()
        self.secrets_table.setColumnCount(3)
        self.secrets_table.setHorizontalHeaderLabels(["Label", "Username", "Password"])
        self.secrets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.secrets_table, 1)
        self.bottom_action_layout = QHBoxLayout()
        self.add_secret_button = QPushButton("Add New Secret")
        self.lock_button = QPushButton("Save & Lock Vault")
        self.bottom_action_layout.addStretch()
        self.bottom_action_layout.addWidget(self.add_secret_button)
        self.bottom_action_layout.addWidget(self.lock_button)
        self.main_layout.addLayout(self.bottom_action_layout)
        
        # Connect Signals to Slots
        self.init_button.clicked.connect(self.handle_initialize)
        self.unlock_button.clicked.connect(self.handle_unlock)
        self.lock_button.clicked.connect(self.handle_lock)
        self.refresh_button.clicked.connect(self.populate_usb_drives)
        self.add_secret_button.clicked.connect(self.handle_add_secret) # <-- Connect new button
        
        self.populate_usb_drives()
        self.update_ui_state() # <-- Call new method to set initial state

    def update_ui_state(self):
        """Enable/disable UI elements based on the vault's lock state."""
        self.add_secret_button.setEnabled(self.is_unlocked)
        self.secrets_table.setEnabled(self.is_unlocked)
        self.lock_button.setEnabled(self.is_unlocked)
        self.unlock_button.setEnabled(not self.is_unlocked)
        self.pin_input.setEnabled(not self.is_unlocked)

    def handle_add_secret(self):
        """Opens the SecretDialog and adds a new row to the table."""
        if not self.is_unlocked: return
        
        dialog = SecretDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                row_position = self.secrets_table.rowCount()
                self.secrets_table.insertRow(row_position)
                self.secrets_table.setItem(row_position, 0, QTableWidgetItem(data["label"]))
                self.secrets_table.setItem(row_position, 1, QTableWidgetItem(data["username"]))
                self.secrets_table.setItem(row_position, 2, QTableWidgetItem(data["password"]))
                print(f"Added new secret: {data['label']}")

    def handle_unlock(self):
        selected_drive = self.usb_combo.currentText()
        if not selected_drive or not verify_stick(selected_drive):
            QMessageBox.critical(self, "Unlock Error", "Selected drive is not a valid UR Safe Stick.")
            return
        # --- (Unlock logic as before, now with state changes) ---
        add_log_entry(selected_drive, "EVENT: Vault Unlock Succeeded")
        self.secrets_table.setRowCount(0)
        for row, secret in enumerate(MOCK_SECRETS.values()):
            self.secrets_table.insertRow(row)
            self.secrets_table.setItem(row, 0, QTableWidgetItem(secret["label"]))
            self.secrets_table.setItem(row, 1, QTableWidgetItem(secret["username"]))
            self.secrets_table.setItem(row, 2, QTableWidgetItem(secret["password"]))
        
        self.is_unlocked = True
        self.update_ui_state()
        QMessageBox.information(self, "Success", "Vault unlocked successfully!")

    def handle_lock(self):
        selected_drive = self.usb_combo.currentText()
        
        # --- NEW: Simulate saving data from the table ---
        new_vault_data = {}
        for row in range(self.secrets_table.rowCount()):
            label = self.secrets_table.item(row, 0).text()
            username = self.secrets_table.item(row, 1).text()
            password = self.secrets_table.item(row, 2).text()
            new_vault_data[label] = {"label": label, "username": username, "password": password}
        
        print("--- Simulating Save ---")
        print("Data that would be encrypted and saved to the vault:")
        print(new_vault_data)
        print("-----------------------")
        
        if verify_stick(selected_drive):
            add_log_entry(selected_drive, "EVENT: Vault Locked (Changes Saved)")
        
        self.secrets_table.setRowCount(0)
        self.pin_input.clear()
        self.is_unlocked = False
        self.update_ui_state()
        QMessageBox.information(self, "Locked", "Vault has been saved and locked.")

    # --- (handle_initialize and populate_usb_drives are unchanged) ---
    def handle_initialize(self):
        selected_drive = self.usb_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Initialization Error", "No USB drive selected.")
            return
        reply = QMessageBox.question(self, "Confirm Initialization",
                                     f"Are you sure you want to initialize the drive at {selected_drive}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return
        dialog = PinDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pin = dialog.get_pin()
            if not pin:
                QMessageBox.critical(self, "PIN Error", "PINs did not match or were empty.")
                return
            success = initialize_vault_placeholder(selected_drive, pin)
            if success:
                add_log_entry(selected_drive, "EVENT: Vault Initialized")
                QMessageBox.information(self, "Success", f"UR Safe Stick successfully initialized on {selected_drive}!")
            else:
                QMessageBox.critical(self, "Failure", "An unexpected error occurred during initialization.")

    def populate_usb_drives(self):
        self.usb_combo.clear()
        drives = find_usb_drives()
        if drives:
            for drive in drives: self.usb_combo.addItem(drive['mountpoint'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())