# file: dashboard/wizard.py
from PyQt6.QtWidgets import QWizard, QWizardPage, QVBoxLayout, QLabel, QComboBox, QLineEdit, QMessageBox

class InitializationWizard(QWizard):
    def __init__(self, usb_drives, parent=None):
        super().__init__(parent)
        self.usb_drives = usb_drives
        self.setWindowTitle("UR Safe Stick Initialization Wizard")

        # Add the pages to the wizard
        self.addPage(self.create_intro_page())
        self.addPage(self.create_pin_page())
        self.addPage(self.create_confirmation_page())

    def create_intro_page(self):
        page = QWizardPage()
        page.setTitle("Step 1: Select Your USB Drive")
        page.setSubTitle("Choose the USB drive you want to transform into a UR Safe Stick. "
                        "WARNING: Any existing data on the selected drive might be affected.")

        layout = QVBoxLayout()
        drive_label = QLabel("Available USB Drives:")
        self.drive_combo = QComboBox()
        self.drive_combo.addItems([f"{drive[0]} ({drive[1]})" for drive in self.usb_drives])

        layout.addWidget(drive_label)
        layout.addWidget(self.drive_combo)
        page.setLayout(layout)

        # Register the field so we can access it later
        page.registerField("selected_drive*", self.drive_combo)
        return page

    def create_pin_page(self):
        page = QWizardPage()
        page.setTitle("Step 2: Set Your Master PIN")
        page.setSubTitle("This PIN is crucial for unlocking your vault. Choose something strong and memorable.")

        layout = QVBoxLayout()
        pin_label = QLabel("Enter a new PIN (6-12 digits recommended):")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        confirm_pin_label = QLabel("Confirm your PIN:")
        self.confirm_pin_input = QLineEdit()
        self.confirm_pin_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(pin_label)
        layout.addWidget(self.pin_input)
        layout.addWidget(confirm_pin_label)
        layout.addWidget(self.confirm_pin_input)
        page.setLayout(layout)

        # Register fields
        page.registerField("pin*", self.pin_input)
        page.registerField("confirm_pin*", self.confirm_pin_input)
        return page

    def create_confirmation_page(self):
        page = QWizardPage()
        page.setTitle("Step 3: Ready to Initialize")
        page.setSubTitle("The setup is complete. Click 'Finish' to create your secure UR Safe Stick.")
        
        layout = QVBoxLayout()
        label = QLabel("You are about to initialize the selected USB drive. This process is irreversible.")
        label.setWordWrap(True)
        layout.addWidget(label)
        page.setLayout(layout)
        return page
    
    def validateCurrentPage(self):
        # This function is called when the user clicks "Next"
        if self.currentPage().title() == "Step 2: Set Your Master PIN":
            pin = self.field("pin")
            confirm_pin = self.field("confirm_pin")
            if len(pin) < 4:
                QMessageBox.warning(self, "Weak PIN", "Your PIN should be at least 4 characters long.")
                return False
            if pin != confirm_pin:
                QMessageBox.warning(self, "PIN Mismatch", "The PINs you entered do not match.")
                return False
        return True