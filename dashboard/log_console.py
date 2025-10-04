# file: dashboard/log_console.py
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QColor, QTextCharFormat, QFont
from PyQt6.QtCore import QDateTime

class SecurityLogConsole(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logConsole")
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 10))
        self.log_message("INFO", "Security Log Console Initialized.")

    def log_message(self, level, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        if level.upper() == "SUCCESS":
            color = QColor("#2ecc71") # Green
            level_icon = "✔"
        elif level.upper() == "ERROR":
            color = QColor("#e74c3c") # Red
            level_icon = "✖"
        elif level.upper() == "WARN":
            color = QColor("#f39c12") # Yellow
            level_icon = "⚠"
        else: # INFO
            color = QColor("#3498db") # Blue
            level_icon = "ℹ"

        log_format = QTextCharFormat()
        log_format.setForeground(color)

        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Insert Timestamp
        cursor.insertText(f"[{timestamp}] ", log_format)
        
        # Insert Level
        cursor.insertText(f"{level_icon} [{level.upper()}]: ", log_format)

        # Insert Message
        log_format.setForeground(QColor("#abb2bf")) # Standard text color
        cursor.insertText(message + "\n", log_format)
        
        self.ensureCursorVisible()