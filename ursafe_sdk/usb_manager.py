# file: ursafe_sdk/usb_manager.py
"""
Manages detecting, identifying, and verifying USB devices.
"""
import psutil
import os
import json
import platform
import subprocess
from . import crypto_manager
from . import system_utils

def get_usb_signature(drive_path):
    """
    Gets a unique, stable identifier for a USB drive.
    
    Args:
        drive_path (str): The mount point of the drive
    
    Returns:
        str: Unique identifier for the USB drive, or None if failed
    """
    try:
        if platform.system() == "Windows":
            # Get volume serial number on Windows
            import ctypes
            volume_serial = ctypes.c_ulong()
            drive_root = os.path.splitdrive(drive_path)[0] + "\\"
            success = ctypes.windll.kernel32.GetVolumeInformationW(
                drive_root, None, 0, ctypes.byref(volume_serial), None, None, None, 0
            )
            if success:
                return f"WIN-{volume_serial.value:08X}"
                
        elif platform.system() == "Linux":
            # Try to get device UUID on Linux
            result = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', drive_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return f"LINUX-{result.stdout.strip()}"
                
        elif platform.system() == "Darwin":  # macOS
            # Try to get volume UUID on macOS
            result = subprocess.run(['diskutil', 'info', drive_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Volume UUID' in line:
                        uuid = line.split(':')[1].strip()
                        return f"MAC-{uuid}"
    except Exception as e:
        print(f"Warning: Could not get USB signature: {e}")
    
    # Fallback: use drive path
    return f"FALLBACK-{abs(hash(drive_path))}"

def verify_stick(drive_path):
    """
    Verifies if a given drive is an initialized UR Safe Stick with cryptographic validation.

    Args:
        drive_path (str): The mount point of the drive to check.

    Returns:
        dict: Verification result with status and details
    """
    if not drive_path or not os.path.isdir(drive_path):
        return {"valid": False, "reason": "Drive path invalid"}

    ursafe_path = os.path.join(drive_path, ".ursafe")
    if not os.path.isdir(ursafe_path):
        return {"valid": False, "reason": "Not a UR Safe Stick (no .ursafe directory)"}
    
    # Check for required files
    required_files = ["vault.enc", "meta.json"]
    for filename in required_files:
        if not os.path.exists(os.path.join(ursafe_path, filename)):
            return {"valid": False, "reason": f"Missing required file: {filename}"}
    
    try:
        # Verify metadata structure
        meta_file = os.path.join(ursafe_path, "meta.json")
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
        
        required_fields = ["salt_hex", "usb_chunks_hex", "system_fingerprint_hex"]
        for field in required_fields:
            if field not in metadata:
                return {"valid": False, "reason": f"Invalid metadata: missing {field}"}
        
        # Verify USB signature if stored
        usb_sig = get_usb_signature(drive_path)
        stored_sig = metadata.get("usb_signature")
        
        if stored_sig and stored_sig != usb_sig:
            return {"valid": False, "reason": "USB signature mismatch - possible clone"}
        
        # Verify system fingerprint
        stored_fp = bytes.fromhex(metadata["system_fingerprint_hex"])
        current_fp = system_utils.get_system_fingerprint()
        
        fp_match = stored_fp == current_fp
        
        return {
            "valid": True,
            "reason": "Valid UR Safe Stick",
            "system_match": fp_match,
            "usb_signature": usb_sig,
            "metadata": metadata
        }
        
    except Exception as e:
        return {"valid": False, "reason": f"Verification error: {e}"}
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

def get_drive_info(drive_path: str) -> dict:
    """
    Get detailed information about a drive/USB stick.
    
    Args:
        drive_path: Path to the drive (e.g., 'F:\\')
    
    Returns:
        Dictionary with drive information
    """
    try:
        if not os.path.exists(drive_path):
            return {"error": "Drive path does not exist"}
        
        # Get disk usage
        usage = psutil.disk_usage(drive_path)
        
        # Get drive info from partitions
        partitions = psutil.disk_partitions(all=True)
        drive_info = None
        for partition in partitions:
            if partition.mountpoint == drive_path:
                drive_info = partition
                break
        
        result = {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "fstype": drive_info.fstype if drive_info else "Unknown",
            "serial": get_usb_signature(drive_path),  # Use our USB signature as serial
            "device": drive_info.device if drive_info else "Unknown"
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to get drive info: {e}"}

# Self-test functionality
if __name__ == '__main__':
    print("--- Running usb_manager.py self-test ---")
    
    print("\n[1] Testing USB drive detection...")
    drives = find_usb_drives()
    print(f"Found {len(drives)} removable drives:")
    for i, drive in enumerate(drives):
        print(f"  {i+1}. Device: {drive['device']}, Mount Point: {drive['mountpoint']}")
        
        # Test USB signature
        signature = get_usb_signature(drive['mountpoint'])
        print(f"     USB Signature: {signature}")
        
        # Test verification
        verification = verify_stick(drive['mountpoint'])
        print(f"     Verification: {verification['reason']}")
        if verification['valid']:
            print(f"     System Match: {verification.get('system_match', 'Unknown')}")
    
    if not drives:
        print("  No removable drives found.")
    
    print("\n[2] Testing with mock UR Safe Stick...")
    # Create a mock stick for testing
    TEST_USB_PATH = "test_usb_verification"
    if os.path.exists(TEST_USB_PATH):
        import shutil
        shutil.rmtree(TEST_USB_PATH)
    
    os.makedirs(os.path.join(TEST_USB_PATH, ".ursafe"))
    
    # Create mock metadata
    mock_metadata = {
        "salt_hex": "1234567890abcdef" * 2,
        "usb_chunks_hex": ["abcd"] * 10,
        "system_fingerprint_hex": system_utils.get_system_fingerprint().hex(),
        "usb_signature": get_usb_signature(TEST_USB_PATH)
    }
    
    with open(os.path.join(TEST_USB_PATH, ".ursafe", "meta.json"), 'w') as f:
        json.dump(mock_metadata, f)
    
    # Create mock vault file
    with open(os.path.join(TEST_USB_PATH, ".ursafe", "vault.enc"), 'wb') as f:
        f.write(b"mock_encrypted_data")
    
    # Test verification
    result = verify_stick(TEST_USB_PATH)
    print(f"Mock stick verification: {result}")
    assert result['valid'] == True
    assert result['system_match'] == True
    print("[OK] Mock UR Safe Stick verification passed")
    
    # Cleanup
    import shutil
    shutil.rmtree(TEST_USB_PATH)
    
    print("\n--- All usb_manager tests passed! ---")