# file: dashboard/mockup_widget.py
# This file contains Team 3's UI, refactored into a reusable QWidget.

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTabWidget, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
                             QPlainTextEdit)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt

# --- MOCK DATA (Copied from Team 3's file) ---
MOCK_CHUNK_STATUS = {
    "total_shares": 20, "required_shares": 10,
    "host_location": "C:\\ProgramData\\.ursafe_chunks\\", "host_available": 8,
    "host_files": [".c_1", ".c_3", ".c_4", ".c_7", ".c_8", ".c_10", ".c_11", ".c_15"],
    "usb_location": "F:\\.ursafe\\chunks\\", "usb_available": 3,
    "usb_files": [".c_17", ".c_18", ".c_20"],
    "reconstruction_possible": True
}
# ... (all other MOCK data constants are the same)
MOCK_SYSTEM_INFO = {"pc_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", "cpu_id": "BFEBFBFF000906EA", "mb_serial": "123456789", "mac_addresses": ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"], "platform": "Windows-10-AMD64"}
MOCK_LOG_CHAIN = [{"timestamp": "2025-10-05T10:30:00Z", "action": "Vault Initialized", "prev_hash": "000000", "verified": True}, {"timestamp": "2025-10-05T10:32:15Z", "action": "Vault Unlocked", "prev_hash": "a1b2c3", "verified": True}, {"timestamp": "2025-10-05T10:35:45Z", "action": "Secret 'Gmail' Added", "prev_hash": "d4e5f6", "verified": True}, {"timestamp": "2025-10-05T10:36:00Z", "action": "Vault Locked", "prev_hash": "g7h8i9", "verified": True}]
MOCK_USB_INFO = {"drive_path": "F:\\", "serial": "AA12345678", "total_space": "32.0 GB", "free_space": "31.0 GB", "file_system": "FAT32", "vault_present": True}


# --- CHANGE 1: Class name and inheritance changed ---
class MockupTabWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- CHANGE 2: Create a layout for this QWidget ---
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        # -------------------------------------------------

        # The rest of the code is identical to Team 3's file
        self.tabs.addTab(self.create_chunk_status_tab(), "Chunk Status")
        self.tabs.addTab(self.create_system_info_tab(), "System Fingerprint")
        self.tabs.addTab(self.create_usb_info_tab(), "USB Drive Info")
        self.tabs.addTab(self.create_log_chain_tab(), "Log Chain (Blockchain)")
        self.tabs.addTab(self.create_crypto_primitives_tab(), "Crypto Primitives")
        self.tabs.addTab(self.create_workflow_viz_tab(), "Workflow Visualization")

    # All of Team 3's 'create_*_tab' methods are copied here verbatim
    def create_chunk_status_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        status = "✅ Possible" if MOCK_CHUNK_STATUS['reconstruction_possible'] else "❌ Not Possible"
        layout.addRow(QLabel("<b>Reconstruction Status:</b>"), QLabel(status))
        layout.addRow(QLabel("<b>Shares (Required / Total):</b>"), QLabel(f"{MOCK_CHUNK_STATUS['required_shares']} of {MOCK_CHUNK_STATUS['total_shares']}"))
        layout.addRow(QLabel("<b>Host Chunks Available:</b>"), QLabel(f"{MOCK_CHUNK_STATUS['host_available']} at <code>{MOCK_CHUNK_STATUS['host_location']}</code>"))
        host_files_text = QPlainTextEdit()
        host_files_text.setReadOnly(True)
        host_files_text.setPlainText("\n".join(MOCK_CHUNK_STATUS['host_files']))
        host_files_text.setMaximumHeight(150)
        layout.addRow(QLabel("<b>Host Chunk Files:</b>"), host_files_text)
        layout.addRow(QLabel("<b>USB Chunks Available:</b>"), QLabel(f"{MOCK_CHUNK_STATUS['usb_available']} at <code>{MOCK_CHUNK_STATUS['usb_location']}</code>"))
        return widget

    def create_system_info_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        pc_id_label = QLabel(f"<code>{MOCK_SYSTEM_INFO['pc_id']}</code>")
        pc_id_label.setWordWrap(True)
        layout.addRow(QLabel("<b>Bound PC Fingerprint (Hash):</b>"), pc_id_label)
        layout.addRow(QLabel("<b>Platform:</b>"), QLabel(MOCK_SYSTEM_INFO['platform']))
        layout.addRow(QLabel("<b>CPU ID:</b>"), QLabel(f"<code>{MOCK_SYSTEM_INFO['cpu_id']}</code>"))
        layout.addRow(QLabel("<b>Motherboard Serial:</b>"), QLabel(f"<code>{MOCK_SYSTEM_INFO['mb_serial']}</code>"))
        mac_text = "\n".join(MOCK_SYSTEM_INFO['mac_addresses'])
        layout.addRow(QLabel("<b>MAC Addresses:</b>"), QLabel(f"<code>{mac_text}</code>"))
        return widget

    def create_usb_info_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        vault_status = "✅ Detected" if MOCK_USB_INFO['vault_present'] else "❌ Not Found"
        layout.addRow(QLabel("<b>Vault Status:</b>"), QLabel(vault_status))
        layout.addRow(QLabel("<b>Drive Path:</b>"), QLabel(f"<code>{MOCK_USB_INFO['drive_path']}</code>"))
        layout.addRow(QLabel("<b>Volume Serial:</b>"), QLabel(f"<code>{MOCK_USB_INFO['serial']}</code>"))
        layout.addRow(QLabel("<b>File System:</b>"), QLabel(MOCK_USB_INFO['file_system']))
        layout.addRow(QLabel("<b>Capacity:</b>"), QLabel(f"{MOCK_USB_INFO['total_space']} (Free: {MOCK_USB_INFO['free_space']})"))
        return widget

    def create_log_chain_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Timestamp", "Action", "Previous Hash", "Verified"])
        table.setRowCount(len(MOCK_LOG_CHAIN))
        for row, entry in enumerate(MOCK_LOG_CHAIN):
            table.setItem(row, 0, QTableWidgetItem(entry['timestamp']))
            table.setItem(row, 1, QTableWidgetItem(entry['action']))
            table.setItem(row, 2, QTableWidgetItem(f"<code>{entry['prev_hash']}</code>"))
            verified_item = QTableWidgetItem("✔")
            verified_item.setForeground(QColor("#2ecc71"))
            verified_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 3, verified_item)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(table)
        return widget
        
    def create_crypto_primitives_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.addRow(QLabel("<b>Key Derivation (KDF):</b>"), QLabel("Argon2id (time=2, mem=64MiB, parallelism=2)"))
        layout.addRow(QLabel("<b>Symmetric Encryption:</b>"), QLabel("AES-256-GCM (12-byte nonce, 16-byte tag)"))
        layout.addRow(QLabel("<b>Digital Signatures:</b>"), QLabel("Ed25519"))
        layout.addRow(QLabel("<b>Secret Splitting:</b>"), QLabel("Shamir's Secret Sharing (10-of-20)"))
        layout.addRow(QLabel("<b>Hashing:</b>"), QLabel("SHA-256"))
        return widget

    def create_workflow_viz_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("<b>Unlock Workflow Visualization</b>")
        image_label = QLabel()
        pixmap = QPixmap("assets/workflow.png") 
        if pixmap.isNull():
            image_label.setText("Image not found: Please create assets/workflow.png")
        else:
            image_label.setPixmap(pixmap.scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(image_label)
        return widget