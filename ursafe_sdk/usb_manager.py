# file: ursafe_sdk/usb_manager.py
"""
Manages detecting, identifying, and verifying USB devices.
"""
import psutil
import os
# file: ursafe_sdk/usb_manager.py (add this function)

def verify_stick(drive_path):
    """
    Verifies if a given drive is an initialized UR Safe Stick.

    For now, this is a simple check for the existence of the '.ursafe' directory.
    Later, this will be expanded to check for a valid, signed manifest file.

    Args:
        drive_path (str): The mount point of the drive to check.

    Returns:
        bool: True if the drive is a valid stick, False otherwise.
    """
    if not drive_path or not os.path.isdir(drive_path):
        return False

    ursafe_path = os.path.join(drive_path, ".ursafe")
    return os.path.isdir(ursafe_path)
def find_usb_drives():
    """
    Detects all removable USB storage devices connected to the system.
    
    Returns:
        list: A list of dictionaries, where each dictionary represents a
              removable drive with 'device' and 'mountpoint' keys.
              Example: [{'device': 'E:\\', 'mountpoint': 'E:\\'}]
    """
    removable_drives = []
    partitions = psutil.disk_partitions(all=True)
    for p in partitions:
        # 'removable' is a good indicator on Windows. On Linux/macOS,
        # we can also check if 'opts' contains 'removable' or if the
        # device path includes 'usb'.
        is_removable = 'removable' in p.opts or 'usb' in p.device.lower()
        
        # On Windows, psutil might not always populate 'removable'.
        # A fallback is to check if the drive type is 'removable'.
        # This part is a bit more platform-specific.
        if os.name == 'nt' and 'fixed' not in p.opts:
             is_removable = True # A simplification for our project

        if is_removable and p.mountpoint:
            # We only care about drives that are actually mounted and accessible
            removable_drives.append({
                "device": p.device,
                "mountpoint": p.mountpoint
            })
            
    return removable_drives

# You can run this file directly to test its functionality
if __name__ == '__main__':
    print("Finding removable drives...")
    drives = find_usb_drives()
    if drives:
        print("Found the following drives:")
        for drive in drives:
            print(f"  - Device: {drive['device']}, Mount Point: {drive['mountpoint']}")
    else:
        print("No removable drives found.")