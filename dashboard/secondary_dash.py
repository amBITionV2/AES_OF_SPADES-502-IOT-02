# file: dashboard/secondary_dash.py (Updated with integrated mockup)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel,
    QTableWidget, QHeaderView, QTableWidgetItem, QTextEdit, QGridLayout
)
from PyQt6.QtCore import QTimer

from dashboard.utils.data_collector import DataCollector
# --- NEW: Import Team 3's refactored UI widget ---
from dashboard.mockup_widget import MockupTabWidget

class SecondaryDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UR Safe Stick - Technical Dashboard")
        self.setGeometry(1100, 100, 800, 550) # Using the smaller height

        self.collector = DataCollector()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._create_live_data_tab()
        # --- THIS LINE IS NOW UPDATED ---
        self._create_dummy_dashboard_tab()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data_displays)
        self.timer.start(3000)
        self.update_data_displays()

    def _create_live_data_tab(self):
        # ... (This method is unchanged)
        tab_widget = QWidget()
        layout = QGridLayout(tab_widget)
        layout.addWidget(QLabel("<b>System Information</b>"), 0, 0)
        self.pc_id_label = QLabel("PC ID: N/A")
        self.hardware_info_text = QTextEdit()
        self.hardware_info_text.setReadOnly(True)
        layout.addWidget(self.pc_id_label, 1, 0)
        layout.addWidget(self.hardware_info_text, 2, 0)
        layout.addWidget(QLabel("<b>USB Information</b>"), 0, 1)
        self.usb_info_text = QTextEdit()
        self.usb_info_text.setReadOnly(True)
        layout.addWidget(self.usb_info_text, 1, 1, 2, 1)
        layout.addWidget(QLabel("<b>Chunk Status (Shamir's Secret Sharing)</b>"), 3, 0)
        self.chunk_status_text = QTextEdit()
        self.chunk_status_text.setReadOnly(True)
        layout.addWidget(self.chunk_status_text, 4, 0, 1, 2)
        layout.addWidget(QLabel("<b>Blockchain Log Chain</b>"), 5, 0)
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Action", "Prev. Hash", "Verified"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.log_table, 6, 0, 1, 2)
        self.tabs.addTab(tab_widget, "📈 Live Technical View")

    # --- THIS METHOD IS NOW UPDATED TO USE TEAM 3'S WIDGET ---
    def _create_dummy_dashboard_tab(self):
        """Integrates the full mockup UI from Team 3."""
        # Instead of a simple QLabel, we now instantiate the entire mockup widget
        mockup_widget = MockupTabWidget()
        self.tabs.addTab(mockup_widget, "UI Visualization")

    def update_data_displays(self):
        # ... (This method is unchanged)
        data = self.collector.fetch_all_data()
        sys_info = data.get("system_info", {})
        self.pc_id_label.setText(f"<b>PC ID:</b> {sys_info.get('pc_id', 'N/A')}")
        hardware_str = "\n".join([f"{k}: {v}" for k, v in sys_info.get('hardware', {}).items()])
        self.hardware_info_text.setText(hardware_str if hardware_str else "Error: SDK function not found.")
        usb_info = data.get("usb_info", {})
        usb_str = "\n".join([f"{k}: {v}" for k, v in usb_info.items()])
        self.usb_info_text.setText(usb_str if usb_str else "No USB connected or error.")
        chunk_info = data.get("chunk_status", {})
        chunk_str = (f"M-of-N: {chunk_info.get('required_shares')}-of-{chunk_info.get('total_shares')}\n"
                     f"Reconstruction Possible: {chunk_info.get('reconstruction_possible')}\n\n"
                     f"Host Chunks ({chunk_info.get('host_available')} found):\n{chunk_info.get('host_location')}\n\n"
                     f"USB Chunks ({chunk_info.get('usb_available')} found):\n{chunk_info.get('usb_location')}")
        self.chunk_status_text.setText(chunk_str)
        logs = data.get("log_chain", [])
        self.log_table.setRowCount(len(logs))
        for row, entry in enumerate(logs):
            self.log_table.setItem(row, 0, QTableWidgetItem(entry.get("timestamp", "")))
            self.log_table.setItem(row, 1, QTableWidgetItem(entry.get("action", "")))
            self.log_table.setItem(row, 2, QTableWidgetItem(str(entry.get("prev_hash", ""))))
            self.log_table.setItem(row, 3, QTableWidgetItem(str(entry.get("verified", "N/A"))))