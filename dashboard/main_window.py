# file: dashboard/main_window.py (Refactored to be a QWidget for tabbing)

import os
import sys

# Add the project root to Python path so we can import ursafe_sdk
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    # --- CHANGE 1: QMainWindow is no longer needed here ---
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

from ursafe_sdk.usb_manager import find_usb_drives, verify_stick
from ursafe_sdk.log_manager import add_log_entry
from ursafe_sdk.vault_manager import VaultManager

# All dialog classes (SimplePinDialog, PinDialog, SecretDialog) remain exactly the same
# ... (Their code is included below for completeness)

class SimplePinDialog(QDialog):
    def __init__(self, parent=None, title="Enter PIN", message="Enter your PIN:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        layout = QVBoxLayout()
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Enter PIN")
        layout.addWidget(self.pin_input)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.pin_input.setFocus()
    
    def get_pin(self):
        return self.pin_input.text()

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

# --- CHANGE 2: The class now inherits from QWidget, not QMainWindow ---
class MainAppTab(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle(...) is removed, as tabs don't have titles

        self.is_unlocked = False
        self.current_vault_manager = None
        self.current_pin = None
        self.current_usb_drive = None

        # --- CHANGE 3: The layout is applied directly to 'self' (the QWidget) ---
        # self.central_widget is removed.
        self.main_layout = QVBoxLayout(self)

        # The rest of the __init__ method and all other methods are IDENTICAL
        # UI Elements
        self.usb_selection_layout = QHBoxLayout()
        self.usb_label = QLabel("Select UR Safe Stick:")
        self.usb_combo = QComboBox()
        self.refresh_button = QPushButton(" Refresh Drives")
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
        
        self.apply_button_style(self.init_button, "#4CAF50")
        self.apply_button_style(self.unlock_button, "#2196F3")
        self.apply_button_style(self.refresh_button, "#757575")
        
        self.action_layout.addWidget(self.pin_label)
        self.action_layout.addWidget(self.pin_input, 1)
        self.action_layout.addWidget(self.init_button)
        self.action_layout.addWidget(self.unlock_button)
        self.main_layout.addLayout(self.action_layout)
        
        self.secrets_table = QTableWidget()
        self.secrets_table.setColumnCount(4)
        self.secrets_table.setHorizontalHeaderLabels(["Label", "Username", "Password", "Actions"])
        header = self.secrets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.secrets_table.setColumnWidth(3, 50)
        self.main_layout.addWidget(self.secrets_table, 1)
        
        self.status_label = QLabel("Ready - Select USB drive and initialize or unlock vault")
        self.status_label.setStyleSheet("""
            QLabel { background-color: #e3f2fd; color: #1565c0; padding: 12px; border: 2px solid #2196f3; border-radius: 6px; font-weight: bold; font-size: 11px; }
        """)
        self.status_label.setWordWrap(True)
        self.main_layout.addWidget(self.status_label)
        
        self.bottom_action_layout = QHBoxLayout()
        self.delete_data_button = QPushButton(" Delete All Data")
        self.add_secret_button = QPushButton("Add New Secret")
        self.lock_button = QPushButton("Save & Lock Vault")
        
        self.apply_button_style(self.delete_data_button, "#f44336")
        self.apply_button_style(self.add_secret_button, "#4CAF50")
        self.apply_button_style(self.lock_button, "#2196F3")
        
        self.bottom_action_layout.addWidget(self.delete_data_button)
        self.bottom_action_layout.addStretch()
        self.bottom_action_layout.addWidget(self.add_secret_button)
        self.bottom_action_layout.addWidget(self.lock_button)
        self.main_layout.addLayout(self.bottom_action_layout)
        
        self.init_button.clicked.connect(self.handle_initialize)
        self.unlock_button.clicked.connect(self.handle_unlock)
        self.lock_button.clicked.connect(self.handle_lock)
        self.refresh_button.clicked.connect(self.populate_usb_drives)
        self.add_secret_button.clicked.connect(self.handle_add_secret)
        self.delete_data_button.clicked.connect(self.handle_delete_data)
        
        self.populate_usb_drives()
        self.setup_svg_icons()
        
        self.usb_monitor_timer = QTimer()
        self.usb_monitor_timer.timeout.connect(self.check_usb_status)
        self.usb_monitor_timer.start(2000)

    # All other methods (load_svg_icon, setup_svg_icons, handle_unlock, etc.) are IDENTICAL.
    # No changes are needed inside them. They are included here for completeness.
    def load_svg_icon(self, svg_path, size=(24, 24)):
        try:
            if os.path.exists(svg_path):
                renderer = QSvgRenderer(svg_path)
                pixmap = QPixmap(size[0], size[1])
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
        except Exception as e:
            print(f"Failed to load SVG {svg_path}: {e}")
        return QIcon()

    def setup_svg_icons(self):
        icon_mappings = {
            self.refresh_button: "refresh.svg", self.unlock_button: "unlock.svg",
            self.lock_button: "lock-in.svg", self.init_button: "settings.svg",
            self.add_secret_button: "add-folder.svg", self.delete_data_button: "trash.svg"
        }
        for button, svg_file in icon_mappings.items():
            icon = self.load_svg_icon(os.path.join("assets", svg_file))
            if not icon.isNull():
                button.setIcon(icon)

    def create_delete_button(self, row):
        """Create a delete button with trash SVG icon"""
        delete_btn = QPushButton()
        delete_btn.setToolTip("Delete this secret")
        # Load trash SVG icon
        trash_icon = self.load_svg_icon(os.path.join("assets", "trash.svg"), size=(16, 16))
        if not trash_icon.isNull():
            delete_btn.setIcon(trash_icon)
        else:
            delete_btn.setText("🗑️")  # Fallback to emoji if SVG fails
        delete_btn.clicked.connect(lambda checked, r=row: self.delete_secret_row(r))
        return delete_btn

    def apply_button_style(self, button, base_color):
        button.setStyleSheet(f"""
            QPushButton {{ background-color: {base_color}; color: white; font-weight: bold; font-size: 12px; padding: 10px 20px; border: 2px solid {base_color}; border-radius: 6px; min-height: 20px; }}
            QPushButton:hover {{ background-color: {self.darken_color(base_color, 0.1)}; border: 2px solid {self.darken_color(base_color, 0.3)}; }}
            QPushButton:pressed {{ background-color: {self.darken_color(base_color, 0.3)}; border: 2px solid {self.darken_color(base_color, 0.4)}; }}
            QPushButton:disabled {{ background-color: #e0e0e0; color: #9e9e9e; border: 2px solid #cccccc; }}
        """)

    def darken_color(self, hex_color, factor=0.2):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def update_ui_state(self):
        has_usb = bool(self.usb_combo.currentText())
        self.refresh_button.setEnabled(True)
        self.init_button.setEnabled(has_usb and not self.is_unlocked)
        self.unlock_button.setEnabled(has_usb and not self.is_unlocked)
        self.pin_input.setEnabled(has_usb and not self.is_unlocked)
        self.add_secret_button.setEnabled(self.is_unlocked)
        self.lock_button.setEnabled(self.is_unlocked)
        self.secrets_table.setEnabled(self.is_unlocked)
        self.delete_data_button.setEnabled(has_usb)
        if not has_usb:
            self.status_label.setText("🔌 No USB drive detected - Insert USB drive and click 🔄 Refresh Drives")
        elif not self.is_unlocked:
            self.status_label.setText("🔒 Select a USB drive and either Initialize a new vault or Unlock an existing one")

    def handle_add_secret(self):
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
                delete_btn = self.create_delete_button(row_position)
                self.secrets_table.setCellWidget(row_position, 3, delete_btn)

    def delete_secret_row(self, row):
        if row >= self.secrets_table.rowCount(): return
        label_item = self.secrets_table.item(row, 0)
        label = label_item.text() if label_item else f"Row {row + 1}"
        reply = QMessageBox.question(self, "Delete Secret", f"Are you sure you want to delete the secret '{label}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.secrets_table.removeRow(row)
            self.refresh_delete_buttons()

    def refresh_delete_buttons(self):
        for row in range(self.secrets_table.rowCount()):
            widget = self.secrets_table.cellWidget(row, 3)
            if widget:
                widget.clicked.disconnect()
                widget.clicked.connect(lambda checked, r=row: self.delete_secret_row(r))

    def handle_unlock(self):
        selected_drive = self.usb_combo.currentText()
        pin = self.pin_input.text()
        if not selected_drive:
            QMessageBox.critical(self, "Unlock Error", "No USB drive selected.")
            return
        if not pin:
            QMessageBox.critical(self, "Unlock Error", "Please enter your PIN.")
            return
        verification = verify_stick(selected_drive)
        if not verification.get("valid", False):
            QMessageBox.critical(self, "Unlock Error", f"Selected drive is not a valid UR Safe Stick.\nReason: {verification.get('reason', 'Unknown')}")
            return
        try:
            vault_manager = VaultManager(selected_drive)
            vault_data = vault_manager.unlock_vault(pin)
            self.secrets_table.setRowCount(0)
            for row, (secret_id, secret) in enumerate(vault_data.items()):
                self.secrets_table.insertRow(row)
                self.secrets_table.setItem(row, 0, QTableWidgetItem(secret.get("label", secret_id)))
                self.secrets_table.setItem(row, 1, QTableWidgetItem(secret.get("username", "")))
                self.secrets_table.setItem(row, 2, QTableWidgetItem(secret.get("password", "")))
                delete_btn = self.create_delete_button(row)
                self.secrets_table.setCellWidget(row, 3, delete_btn)
            self.is_unlocked = True
            self.current_vault_manager = vault_manager
            self.current_pin = pin
            self.current_usb_drive = selected_drive
            from ursafe_sdk.chunk_manager import get_host_chunk_dir
            host_chunk_dir = get_host_chunk_dir()
            host_chunks_exist = os.path.exists(host_chunk_dir) and len(os.listdir(host_chunk_dir)) > 0
            status_info = (
                f"🔓 VAULT UNLOCKED - {len(vault_data)} secrets loaded\n"
                f"🔐 Encryption: AES-256-GCM with Argon2id key derivation\n"
                f"💾 USB Drive: {selected_drive} | 🖥️ Host Chunks: {'✅ Present' if host_chunks_exist else '❌ Missing'}\n"
                f"🔑 Security: 4-Factor Authentication (USB + PIN + Host + Hardware Fingerprint)"
            )
            self.status_label.setText(status_info)
            self.update_ui_state()
            QMessageBox.information(self, "Success", f"Vault unlocked successfully!\nFound {len(vault_data)} secrets.")
        except Exception as e:
            QMessageBox.critical(self, "Unlock Error", f"Failed to unlock vault:\n{str(e)}")
            self.pin_input.clear()

    def handle_lock(self):
        if not hasattr(self, 'current_vault_manager') or not self.current_vault_manager:
            QMessageBox.warning(self, "Lock Error", "No vault is currently unlocked.")
            return
        try:
            new_vault_data = {}
            for row in range(self.secrets_table.rowCount()):
                label = self.secrets_table.item(row, 0).text() if self.secrets_table.item(row, 0) else ""
                if label:
                    new_vault_data[label] = {
                        "label": label, 
                        "username": self.secrets_table.item(row, 1).text() if self.secrets_table.item(row, 1) else "",
                        "password": self.secrets_table.item(row, 2).text() if self.secrets_table.item(row, 2) else ""
                    }
            self.status_label.setText("💾 Saving vault data with AES-256-GCM encryption...")
            self.current_vault_manager.save_vault(self.current_pin, new_vault_data)
            self.secrets_table.setRowCount(0)
            self.pin_input.clear()
            self.is_unlocked = False
            self.current_vault_manager = None
            self.current_pin = None
            self.current_usb_drive = None
            self.status_label.setText("🔒 Vault locked and secured - Data encrypted and saved")
            self.update_ui_state()
            QMessageBox.information(self, "Locked", f"Vault has been saved and locked.\n{len(new_vault_data)} secrets saved.")
        except Exception as e:
            QMessageBox.critical(self, "Lock Error", f"Failed to save and lock vault:\n{str(e)}")

    def handle_delete_data(self):
        selected_drive = self.usb_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Delete Error", "No USB drive selected.")
            return
        vault_manager = VaultManager(selected_drive)
        if not os.path.exists(vault_manager.ursafe_dir):
            QMessageBox.information(self, "Delete Error", "No vault data found on this USB drive.")
            return
        reply = QMessageBox.question(self, "⚠️ PERMANENT DELETION WARNING ⚠️", f"This will PERMANENTLY DELETE all data from the vault on {selected_drive}!\n\nThis includes:\n• All saved passwords and secrets\n• All host chunks on this computer\n• All vault encryption keys\n\n⚠️ THIS CANNOT BE UNDONE! ⚠️\n\nAre you absolutely sure you want to continue?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        dialog = SimplePinDialog(self, "Verify PIN", "Enter your current PIN to confirm deletion:")
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        pin = dialog.get_pin()
        if not pin:
            QMessageBox.critical(self, "PIN Error", "PIN is required for deletion.")
            return
        try:
            secret_count = len(vault_manager.unlock_vault(pin))
            import shutil
            if os.path.exists(vault_manager.ursafe_dir): shutil.rmtree(vault_manager.ursafe_dir)
            from ursafe_sdk.chunk_manager import get_host_chunk_dir
            host_chunk_dir = get_host_chunk_dir()
            if os.path.exists(host_chunk_dir): shutil.rmtree(host_chunk_dir)
            self.secrets_table.setRowCount(0)
            self.pin_input.clear()
            self.is_unlocked = False
            self.current_vault_manager = None
            self.current_pin = None
            self.update_ui_state()
            QMessageBox.information(self, "Data Deleted", f"Successfully deleted all vault data!\n\n• {secret_count} secrets deleted from USB\n• Host chunks deleted from computer\n• Vault completely removed\n\nThe USB drive can now be reinitialized.")
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Failed to delete vault data:\n{str(e)}")

    def handle_initialize(self):
        selected_drive = self.usb_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Initialization Error", "No USB drive selected.")
            return
        vault_manager = VaultManager(selected_drive)
        if os.path.exists(vault_manager.ursafe_dir):
            reply = QMessageBox.question(self, "Vault Already Exists", f"A vault already exists on {selected_drive}!\n\nTo initialize a new vault, you must first delete the existing data.\nUse the 'Delete All Data' button to remove the current vault.\n\nDo you want to delete the existing vault and create a new one?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.handle_delete_data()
                return
            else:
                return
        reply = QMessageBox.question(self, "Confirm Initialization", f"Are you sure you want to initialize the drive at {selected_drive}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return
        dialog = PinDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pin = dialog.get_pin()
            if not pin:
                QMessageBox.critical(self, "PIN Error", "PINs did not match or were empty.")
                return
            try:
                vault_manager = VaultManager(selected_drive)
                vault_manager.initialize_vault(pin)
                vault_manager.save_vault(pin, {})
                QMessageBox.information(self, "Success", f"UR Safe Stick successfully initialized on {selected_drive}!")
            except Exception as e:
                QMessageBox.critical(self, "Failure", f"An unexpected error occurred during initialization:\n{str(e)}")

    def emergency_lock(self):
        """Emergency lock when USB is disconnected - doesn't try to save"""
        try:
            self.secrets_table.setRowCount(0)
            self.pin_input.clear()
            self.is_unlocked = False
            self.current_vault_manager = None
            self.current_pin = None
            self.current_usb_drive = None
            self.status_label.setText("🔒 Emergency lock - USB drive disconnected, data not saved")
            self.update_ui_state()
        except Exception as e:
            print(f"Error during emergency lock: {e}")

    def check_usb_status(self):
        try:
            if self.is_unlocked and self.current_usb_drive:
                drives = find_usb_drives()
                drive_paths = [drive['mountpoint'] for drive in drives]
                if self.current_usb_drive not in drive_paths:
                    # USB disconnected - emergency lock without saving
                    self.emergency_lock()
                    
                    reply = QMessageBox.critical(
                        self, 
                        "USB Drive Disconnected", 
                        f"The USB drive {self.current_usb_drive} has been disconnected!\n\n"
                        "For security reasons, the vault has been locked and the application will close.\n"
                        "Any unsaved changes have been lost.",
                        QMessageBox.StandardButton.Ok
                    )
                    
                    # Close the entire application
                    import sys
                    from PyQt6.QtWidgets import QApplication
                    QApplication.instance().quit()
                    sys.exit(0)
                    
            current_selection = self.usb_combo.currentText()
            self.populate_usb_drives()
            index = self.usb_combo.findText(current_selection)
            if index >= 0:
                self.usb_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error checking USB status: {e}")

    def populate_usb_drives(self):
        try:
            self.usb_combo.clear()
            drives = find_usb_drives()
            if drives:
                for drive in drives: 
                    self.usb_combo.addItem(drive['mountpoint'])
        except Exception as e:
            print(f"Error finding USB drives: {e}")
        finally:
            self.update_ui_state()

# --- CHANGE 4: The __main__ block is removed. ---
# This file is no longer intended to be run directly.