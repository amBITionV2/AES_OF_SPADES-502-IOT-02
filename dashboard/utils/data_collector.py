# file: dashboard/utils/data_collector.py (Corrected)

import os
import sys
import glob
import json

# --- THIS IS THE FIX ---
# This block tells Python to look for modules in the project's root directory
# by adding it to the system path.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.insert(0, project_root)
# ---------------------

from ursafe_sdk import (
    system_utils,
    usb_manager,
    chunk_manager,
    log_manager
)

class DataCollector:
    """
    A class dedicated to collecting all live technical data from the
    UR Safe Stick SDK for the secondary technical dashboard.
    """
    def __init__(self):
        pass

    def get_system_info(self) -> dict:
        """Fetches the hardware fingerprint and its components."""
        try:
            fingerprint_hash = system_utils.get_system_fingerprint().hex()
            hardware_details = system_utils.get_hardware_info()
            return {
                "pc_id": fingerprint_hash,
                "hardware": hardware_details,
                "fingerprint_hash": fingerprint_hash
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return {}

    def get_usb_info(self, drive_path: str) -> dict:
        """Fetches detailed information for a specific USB drive."""
        if not drive_path:
            return {}
        try:
            # Assuming usb_manager.get_drive_info exists and returns a dict
            drive = usb_manager.get_drive_info(drive_path)
            total_gb = drive.get('total', 0) / (1024**3)
            free_gb = drive.get('free', 0) / (1024**3)
            return {
                "drive_path": drive_path,
                "serial_number": drive.get('serial', 'N/A'),
                "total_space": f"{total_gb:.1f} GB",
                "free_space": f"{free_gb:.1f} GB",
                "file_system": drive.get('fstype', 'N/A'),
                "vault_present": usb_manager.verify_stick(drive_path)
            }
        except Exception as e:
            print(f"Error getting USB info for {drive_path}: {e}")
            return {"drive_path": drive_path, "error": str(e)}

    def get_chunk_status(self, drive_path: str) -> dict:
        """Calculates the current distribution and status of Shamir shares."""
        host_dir = chunk_manager.get_host_chunk_dir()
        usb_dir = os.path.join(drive_path, ".ursafe", "chunks") if drive_path else ""

        try:
            host_files = glob.glob(os.path.join(host_dir, ".c_*"))
            usb_files = glob.glob(os.path.join(usb_dir, ".c_*")) if drive_path else []
            
            host_available = len(host_files)
            usb_available = len(usb_files)
            total_available = host_available + usb_available
            
            return {
                "total_shares": chunk_manager.DEFAULT_TOTAL_SHARES,
                "required_shares": chunk_manager.DEFAULT_REQUIRED_SHARES,
                "host_location": host_dir,
                "host_available": host_available,
                "host_files": [os.path.basename(f) for f in host_files],
                "usb_location": usb_dir,
                "usb_available": usb_available,
                "usb_files": [os.path.basename(f) for f in usb_files],
                "reconstruction_possible": total_available >= chunk_manager.DEFAULT_REQUIRED_SHARES
            }
        except Exception as e:
            print(f"Error getting chunk status: {e}")
            return {}

    def get_log_chain(self, drive_path: str) -> list:
        """Fetches and verifies the entire log chain from the USB."""
        if not drive_path or not usb_manager.verify_stick(drive_path):
            return []
        try:
            logs = log_manager.get_log_chain(drive_path)
            is_valid = log_manager.verify_log_chain(drive_path)
            
            for entry in logs:
                entry['verified'] = is_valid
            return logs
        except Exception as e:
            print(f"Error getting log chain: {e}")
            return []

    def fetch_all_data(self) -> dict:
        """
        Fetches all data points required for the secondary dashboard.
        """
        active_usb_list = usb_manager.find_usb_drives()
        drive_path = active_usb_list[0]['mountpoint'] if active_usb_list else None

        all_data = {
            "system_info": self.get_system_info(),
            "usb_info": self.get_usb_info(drive_path),
            "chunk_status": self.get_chunk_status(drive_path),
            "log_chain": self.get_log_chain(drive_path)
        }
        return all_data

# The test block remains the same
if __name__ == '__main__':
    print("--- Running Data Collector Test ---")
    collector = DataCollector()
    live_data = collector.fetch_all_data()
    print(json.dumps(live_data, indent=4))
    print("\n--- Test Complete ---")
    # ... (rest of the test script)