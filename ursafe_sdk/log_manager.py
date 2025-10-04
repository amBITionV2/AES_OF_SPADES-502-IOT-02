# file: ursafe_sdk/log_manager.py
"""
Manages the blockchain-style, tamper-evident usage log.
"""
import json
import os
from datetime import datetime

# NOTE: For now, we are writing the log in plain text for easy debugging.
# Once Team 1's crypto_manager is ready, we will integrate encryption.
LOG_FILENAME = "logchain.json"
URSAFE_DIR = ".ursafe"

def add_log_entry(drive_path, action_description):
    """
    Creates a new log entry and appends it to the logchain file on the USB.

    Args:
        drive_path (str): The mount point of the USB stick (e.g., 'E:\\').
        action_description (str): A human-readable string of the action performed.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    log_file_path = os.path.join(drive_path, URSAFE_DIR, LOG_FILENAME)

    # For this to work, the .ursafe directory must exist.
    # The initialization process (done by Team 1's vault_manager) will create it.
    # For our testing, we can create it manually on our test USB.
    if not os.path.isdir(os.path.join(drive_path, URSAFE_DIR)):
        print(f"Error: UR Safe directory not found at {drive_path}")
        # In a real scenario, we might create it here if appropriate,
        # but for now, we assume it's created during initialization.
        return False

    # For now, we just create a simple entry. The "prev_hash" and "signature"
    # will be added once Team 1 provides the crypto functions.
    new_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action_description,
        "prev_hash": "placeholder_previous_hash", # Placeholder
        "signature": "placeholder_ed25519_signature" # Placeholder
    }

    try:
        # 'a' means append mode. We add one JSON object per line.
        with open(log_file_path, 'a') as f:
            f.write(json.dumps(new_entry) + "\n")
        print(f"Successfully logged action: '{action_description}'")
        return True
    except Exception as e:
        print(f"Error writing to log file: {e}")
        return False

# You can run this file directly to test its functionality
if __name__ == '__main__':
    # To test this, create a folder named ".ursafe" on your USB drive.
    # Replace 'E:\\' with your actual USB drive letter or mount point.
    test_drive_path = 'E:\\' 
    print(f"Testing log manager with drive: {test_drive_path}")
    if os.path.exists(test_drive_path):
        add_log_entry(test_drive_path, "Test Action: Manual Log Entry")
    else:
        print(f"Test drive {test_drive_path} not found. Please update the path.")