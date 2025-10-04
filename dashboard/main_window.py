# file: dashboard/main_window.py (Final version with secret management)

import sys
import os

# Add the project root to Python path so we can import ursafe_sdk
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

from ursafe_sdk.usb_manager import find_usb_drives, verify_stick
from ursafe_sdk.log_manager import add_log_entry
from ursafe_sdk.vault_manager import VaultManager

# --- MOCK_SECRETS (unchanged) ---
MOCK_SECRETS = {
    "1": {"label": "Gmail", "username": "user@gmail.com", "password": "mock_password_1"},
    "2": {"label": "GitHub", "username": "git-user", "password": "mock_password_2"},
}

# --- Simple PIN Verification Dialog ---
class SimplePinDialog(QDialog):
    def __init__(self, parent=None, title="Enter PIN", message="Enter your PIN:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Message label
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        
        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Enter PIN")
        layout.addWidget(self.pin_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Focus on PIN input
        self.pin_input.setFocus()
    
    def get_pin(self):
        return self.pin_input.text()

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
        self.current_vault_manager = None
        self.current_pin = None
        self.current_usb_drive = None

        # Main layout (unchanged)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # UI Elements (unchanged)
        self.usb_selection_layout = QHBoxLayout()
        self.usb_label = QLabel("Select UR Safe Stick:")
        self.usb_combo = QComboBox()
        self.refresh_button = QPushButton(" Refresh Drives")  # Has SVG but keep emoji for visibility
        self.usb_selection_layout.addWidget(self.usb_label)
        self.usb_selection_layout.addWidget(self.usb_combo, 1)
        self.usb_selection_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(self.usb_selection_layout)
        self.action_layout = QHBoxLayout()
        self.pin_label = QLabel("PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Enter your PIN to unlock")
        self.init_button = QPushButton("Initialize New Stick")  # Has SVG icon - no emoji
        self.unlock_button = QPushButton("Unlock Vault")  # Has SVG icon - no emoji
        
        # Apply modern button styling
        self.apply_button_style(self.init_button, "#4CAF50")  # Green
        self.apply_button_style(self.unlock_button, "#2196F3")  # Blue
        self.apply_button_style(self.refresh_button, "#757575")  # Gray
        
        self.action_layout.addWidget(self.pin_label)
        self.action_layout.addWidget(self.pin_input, 1)
        self.action_layout.addWidget(self.init_button)
        self.action_layout.addWidget(self.unlock_button)
        self.main_layout.addLayout(self.action_layout)
        self.secrets_table = QTableWidget()
        self.secrets_table.setColumnCount(4)
        self.secrets_table.setHorizontalHeaderLabels(["Label", "Username", "Password", "Actions"])
        header = self.secrets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Label column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Username column stretches  
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Password column stretches
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Actions column fixed width
        self.secrets_table.setColumnWidth(3, 50)  # Set actions column width for trash button
        self.main_layout.addWidget(self.secrets_table, 1)
        
        # Status information label with proper contrast
        self.status_label = QLabel("Ready - Select USB drive and initialize or unlock vault")
        self.status_label.setStyleSheet("""
            QLabel { 
                background-color: #e3f2fd; 
                color: #1565c0; 
                padding: 12px; 
                border: 2px solid #2196f3; 
                border-radius: 6px; 
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.status_label.setWordWrap(True)
        self.main_layout.addWidget(self.status_label)
        
        self.bottom_action_layout = QHBoxLayout()
        self.delete_data_button = QPushButton("🗑️ Delete All Data")  # Keep emoji - no SVG available
        self.add_secret_button = QPushButton("Add New Secret")  # Has SVG icon - no emoji  
        self.lock_button = QPushButton("Save & Lock Vault")  # Has SVG icon - no emoji
        
        # Apply modern button styling with hover effects
        self.apply_button_style(self.delete_data_button, "#f44336")  # Red
        self.apply_button_style(self.add_secret_button, "#4CAF50")   # Green
        self.apply_button_style(self.lock_button, "#2196F3")         # Blue
        self.bottom_action_layout.addWidget(self.delete_data_button)
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
        self.delete_data_button.clicked.connect(self.handle_delete_data)
        
        self.populate_usb_drives()  # Always populate on startup and update UI state
        self.setup_svg_icons()  # Add SVG icons to buttons
        
        # Setup USB monitoring timer
        self.usb_monitor_timer = QTimer()
        self.usb_monitor_timer.timeout.connect(self.check_usb_status)
        self.usb_monitor_timer.start(2000)  # Check every 2 seconds

    def load_svg_icon(self, svg_path, size=(24, 24)):
        """Load SVG file and convert to QIcon"""
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
        return QIcon()  # Return empty icon on failure

    def setup_svg_icons(self):
        """Apply SVG icons to buttons"""
        # Map buttons to their corresponding SVG files
        icon_mappings = {
            self.refresh_button: "refresh.svg",
            self.unlock_button: "unlock.svg",
            self.lock_button: "lock-in.svg",
            self.init_button: "settings.svg",
            # Add folder icon for add secret button
            self.add_secret_button: "add-folder.svg"
        }
        
        for button, svg_file in icon_mappings.items():
            icon = self.load_svg_icon(os.path.join("assets", svg_file))
            if not icon.isNull():
                button.setIcon(icon)

    def apply_button_style(self, button, base_color):
        """Apply modern button styling with hover effects and disabled states"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 10px 20px;
                border: 2px solid {base_color};
                border-radius: 6px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(base_color, 0.1)};
                border: 2px solid {self.darken_color(base_color, 0.3)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(base_color, 0.3)};
                border: 2px solid {self.darken_color(base_color, 0.4)};
            }}
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #9e9e9e;
                border: 2px solid #cccccc;
            }}
        """)

    def darken_color(self, hex_color, factor=0.2):
        """Darken a hex color by a given factor"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def update_ui_state(self):
        """Enable/disable UI elements based on the vault's lock state and USB connection."""
        has_usb = bool(self.usb_combo.currentText())
        
        # Refresh button should ALWAYS be enabled so user can refresh USB drives
        self.refresh_button.setEnabled(True)
        
        # Main action buttons
        self.init_button.setEnabled(has_usb and not self.is_unlocked)
        self.unlock_button.setEnabled(has_usb and not self.is_unlocked)
        self.pin_input.setEnabled(has_usb and not self.is_unlocked)
        
        # Vault operation buttons (require unlocked vault)
        self.add_secret_button.setEnabled(self.is_unlocked)
        self.lock_button.setEnabled(self.is_unlocked)
        self.secrets_table.setEnabled(self.is_unlocked)
        
        # Delete button (requires USB but not necessarily unlocked)
        self.delete_data_button.setEnabled(has_usb)
        
        # Update status based on state
        if not has_usb:
            self.status_label.setText("🔌 No USB drive detected - Insert USB drive and click 🔄 Refresh Drives")
        elif not self.is_unlocked:
            self.status_label.setText("🔒 Select a USB drive and either Initialize a new vault or Unlock an existing one")
        # Otherwise status is updated by the specific operations

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
                
                # Add delete button for new row
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(40, 30)
                delete_btn.setToolTip("Delete this secret")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: 2px solid #d32f2f;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                        border: 2px solid #b71c1c;
                    }
                    QPushButton:pressed {
                        background-color: #b71c1c;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, r=row_position: self.delete_secret_row(r))
                self.secrets_table.setCellWidget(row_position, 3, delete_btn)
                print(f"Added new secret: {data['label']}")

    def delete_secret_row(self, row):
        """Delete a specific secret row after confirmation"""
        if row >= self.secrets_table.rowCount():
            return
            
        label_item = self.secrets_table.item(row, 0)
        label = label_item.text() if label_item else f"Row {row + 1}"
        
        reply = QMessageBox.question(
            self,
            "Delete Secret",
            f"Are you sure you want to delete the secret '{label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.secrets_table.removeRow(row)
            # Update the row indices for remaining delete buttons
            self.refresh_delete_buttons()

    def refresh_delete_buttons(self):
        """Refresh all delete button connections after row removal"""
        for row in range(self.secrets_table.rowCount()):
            widget = self.secrets_table.cellWidget(row, 3)
            if widget:
                # Disconnect old connection and reconnect with correct row
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
        
        # Verify the stick first
        verification = verify_stick(selected_drive)
        if not verification.get("valid", False):
            QMessageBox.critical(self, "Unlock Error", f"Selected drive is not a valid UR Safe Stick.\nReason: {verification.get('reason', 'Unknown')}")
            return
        
        try:
            # Use our real VaultManager to unlock
            vault_manager = VaultManager(selected_drive)
            vault_data = vault_manager.unlock_vault(pin)
            
            # Clear and populate the table with real data
            self.secrets_table.setRowCount(0)
            for row, (secret_id, secret) in enumerate(vault_data.items()):
                self.secrets_table.insertRow(row)
                self.secrets_table.setItem(row, 0, QTableWidgetItem(secret.get("label", secret_id)))
                self.secrets_table.setItem(row, 1, QTableWidgetItem(secret.get("username", "")))
                self.secrets_table.setItem(row, 2, QTableWidgetItem(secret.get("password", "")))
                
                # Add delete button for this row
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(40, 30)
                delete_btn.setToolTip("Delete this secret")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: 2px solid #d32f2f;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                        border: 2px solid #b71c1c;
                    }
                    QPushButton:pressed {
                        background-color: #b71c1c;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_secret_row(r))
                self.secrets_table.setCellWidget(row, 3, delete_btn)
            
            self.is_unlocked = True
            self.current_vault_manager = vault_manager  # Store for later use
            self.current_pin = pin  # Store for saving
            self.current_usb_drive = selected_drive  # Track current drive for monitoring
            
            # Update status with encryption information
            secret_count = len(vault_data)
            from ursafe_sdk.chunk_manager import get_host_chunk_dir
            import os
            host_chunk_dir = get_host_chunk_dir()
            host_chunks_exist = os.path.exists(host_chunk_dir) and len(os.listdir(host_chunk_dir)) > 0
            
            status_info = (
                f"🔓 VAULT UNLOCKED - {secret_count} secrets loaded\n"
                f"🔐 Encryption: AES-256-GCM with Argon2id key derivation\n"
                f"💾 USB Drive: {selected_drive} | 🖥️ Host Chunks: {'✅ Present' if host_chunks_exist else '❌ Missing'}\n"
                f"🔑 Security: 4-Factor Authentication (USB + PIN + Host + Hardware Fingerprint)"
            )
            self.status_label.setText(status_info)
            self.update_ui_state()
            QMessageBox.information(self, "Success", f"Vault unlocked successfully!\nFound {secret_count} secrets.")
            
        except Exception as e:
            QMessageBox.critical(self, "Unlock Error", f"Failed to unlock vault:\n{str(e)}")
            self.pin_input.clear()

    def handle_lock(self):
        if not hasattr(self, 'current_vault_manager') or not self.current_vault_manager:
            QMessageBox.warning(self, "Lock Error", "No vault is currently unlocked.")
            return
            
        try:
            # Collect data from the table
            new_vault_data = {}
            for row in range(self.secrets_table.rowCount()):
                label = self.secrets_table.item(row, 0).text() if self.secrets_table.item(row, 0) else ""
                username = self.secrets_table.item(row, 1).text() if self.secrets_table.item(row, 1) else ""
                password = self.secrets_table.item(row, 2).text() if self.secrets_table.item(row, 2) else ""
                
                if label:  # Only save entries with labels
                    new_vault_data[label] = {
                        "label": label, 
                        "username": username, 
                        "password": password
                    }
            
            # Show saving status
            self.status_label.setText("💾 Saving vault data with AES-256-GCM encryption...")
            
            # Use our real VaultManager to save
            self.current_vault_manager.save_vault(self.current_pin, new_vault_data)
            
            # Clear UI state
            self.secrets_table.setRowCount(0)
            self.pin_input.clear()
            self.is_unlocked = False
            self.current_vault_manager = None
            self.current_pin = None
            self.current_usb_drive = None
            self.status_label.setText("🔒 Vault locked and secured - Data encrypted and saved")
            self.update_ui_state()
            
            secret_count = len(new_vault_data)
            QMessageBox.information(self, "Locked", f"Vault has been saved and locked.\n{secret_count} secrets saved.")
            
        except Exception as e:
            QMessageBox.critical(self, "Lock Error", f"Failed to save and lock vault:\n{str(e)}")

    def handle_delete_data(self):
        """Delete all vault data and chunks after PIN verification"""
        selected_drive = self.usb_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Delete Error", "No USB drive selected.")
            return
            
        # Check if vault exists
        from ursafe_sdk.vault_manager import VaultManager
        import os
        vault_manager = VaultManager(selected_drive)
        if not os.path.exists(vault_manager.ursafe_dir):
            QMessageBox.information(self, "Delete Error", "No vault data found on this USB drive.")
            return
        
        # Confirm deletion with strong warning
        reply = QMessageBox.question(
            self, 
            "⚠️ PERMANENT DELETION WARNING ⚠️",
            f"This will PERMANENTLY DELETE all data from the vault on {selected_drive}!\n\n"
            "This includes:\n"
            "• All saved passwords and secrets\n"
            "• All host chunks on this computer\n"
            "• All vault encryption keys\n\n"
            "⚠️ THIS CANNOT BE UNDONE! ⚠️\n\n"
            "Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Get PIN for verification
        dialog = SimplePinDialog(self, "Verify PIN", "Enter your current PIN to confirm deletion:")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        pin = dialog.get_pin()
        if not pin:
            QMessageBox.critical(self, "PIN Error", "PIN is required for deletion.")
            return
        
        try:
            # Verify PIN by trying to unlock first
            vault_data = vault_manager.unlock_vault(pin)
            secret_count = len(vault_data)
            
            # Delete vault files
            import shutil
            if os.path.exists(vault_manager.ursafe_dir):
                shutil.rmtree(vault_manager.ursafe_dir)
            
            # Delete host chunks
            from ursafe_sdk.chunk_manager import get_host_chunk_dir
            host_chunk_dir = get_host_chunk_dir()
            if os.path.exists(host_chunk_dir):
                shutil.rmtree(host_chunk_dir)
            
            # Clear UI
            self.secrets_table.setRowCount(0)
            self.pin_input.clear()
            self.is_unlocked = False
            self.current_vault_manager = None
            self.current_pin = None
            self.update_ui_state()
            
            QMessageBox.information(
                self, 
                "Data Deleted", 
                f"Successfully deleted all vault data!\n\n"
                f"• {secret_count} secrets deleted from USB\n"
                f"• Host chunks deleted from computer\n"
                f"• Vault completely removed\n\n"
                f"The USB drive can now be reinitialized."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Failed to delete vault data:\n{str(e)}")

    def handle_initialize(self):
        selected_drive = self.usb_combo.currentText()
        if not selected_drive:
            QMessageBox.warning(self, "Initialization Error", "No USB drive selected.")
            return
            
        # Check if vault already exists
        from ursafe_sdk.vault_manager import VaultManager
        import os
        vault_manager = VaultManager(selected_drive)
        
        if os.path.exists(vault_manager.ursafe_dir):
            reply = QMessageBox.question(
                self, 
                "Vault Already Exists",
                f"A vault already exists on {selected_drive}!\n\n"
                "To initialize a new vault, you must first delete the existing data.\n"
                "Use the 'Delete All Data' button to remove the current vault.\n\n"
                "Do you want to delete the existing vault and create a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.handle_delete_data()
                return
            else:
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
            try:
                # Create new VaultManager for initialization
                vault_manager = VaultManager(selected_drive)
                
                # Initialize vault with PIN only (creates empty vault)
                vault_manager.initialize_vault(pin)
                
                # Optionally save initial empty data (vault starts empty)
                initial_data = {}  # Empty vault to start with
                vault_manager.save_vault(pin, initial_data)
                
                QMessageBox.information(self, "Success", f"UR Safe Stick successfully initialized on {selected_drive}!")
                
            except Exception as e:
                QMessageBox.critical(self, "Failure", f"An unexpected error occurred during initialization:\n{str(e)}")

    def check_usb_status(self):
        """Monitor USB drive status and close if current drive disconnects"""
        try:
            if self.is_unlocked and self.current_usb_drive:
                drives = find_usb_drives()
                drive_paths = [drive['mountpoint'] for drive in drives]
                
                if self.current_usb_drive not in drive_paths:
                    QMessageBox.critical(
                        self, 
                        "USB Drive Disconnected", 
                        f"The USB drive {self.current_usb_drive} has been disconnected!\n"
                        "For security reasons, the application will close."
                    )
                    self.close()
                    return
            
            # Update drive list to detect new/removed drives
            current_selection = self.usb_combo.currentText()
            self.populate_usb_drives()
            
            # Try to restore selection if it still exists
            index = self.usb_combo.findText(current_selection)
            if index >= 0:
                self.usb_combo.setCurrentIndex(index)
            # Note: update_ui_state() is called by populate_usb_drives()
            
        except Exception as e:
            print(f"Error checking USB status: {e}")
            # Continue running even if USB check fails

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
            # Always update UI state after populating drives (or trying to)
            self.update_ui_state()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())