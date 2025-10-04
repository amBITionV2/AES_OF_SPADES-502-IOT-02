"""
System Utilities - Hardware Fingerprinting
==========================================

Provides system fingerprinting capabilities for the UR Safe Stick.
Generates stable hardware identifiers for device authentication.
"""

import os
import platform
import hashlib
import subprocess
from . import crypto_manager

def get_system_fingerprint() -> bytes:
    """
    Generate a stable hardware fingerprint for the current system.
    
    This combines various hardware identifiers into a single hash.
    WARNING: Hardware changes may cause lockout - implement recovery!
    
    Returns:
        32-byte SHA-256 hash of system characteristics
    """
    fingerprint_data = []
    
    # Platform information
    fingerprint_data.append(platform.system().encode())
    fingerprint_data.append(platform.machine().encode())
    
    try:
        # CPU information (cross-platform)
        if platform.system() == "Windows":
            # Windows-specific identifiers
            try:
                # Get processor ID
                proc_id = subprocess.check_output(
                    'wmic cpu get processorid /value', 
                    shell=True, stderr=subprocess.DEVNULL
                ).decode().strip()
                if "ProcessorId=" in proc_id:
                    fingerprint_data.append(proc_id.split("=")[1].encode())
                
                # Get motherboard serial
                mb_serial = subprocess.check_output(
                    'wmic baseboard get serialnumber /value',
                    shell=True, stderr=subprocess.DEVNULL
                ).decode().strip()
                if "SerialNumber=" in mb_serial:
                    fingerprint_data.append(mb_serial.split("=")[1].encode())
                    
            except (subprocess.CalledProcessError, Exception):
                # Fallback to username if hardware info fails
                fingerprint_data.append(os.getenv('USERNAME', 'unknown').encode())
                
        elif platform.system() == "Linux":
            # Linux-specific identifiers
            try:
                # Machine ID
                with open('/etc/machine-id', 'r') as f:
                    fingerprint_data.append(f.read().strip().encode())
            except (FileNotFoundError, PermissionError):
                try:
                    # Alternative: DMI product UUID
                    with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                        fingerprint_data.append(f.read().strip().encode())
                except (FileNotFoundError, PermissionError):
                    # Fallback to hostname
                    fingerprint_data.append(platform.node().encode())
                    
        elif platform.system() == "Darwin":  # macOS
            try:
                # Hardware UUID
                hw_uuid = subprocess.check_output(
                    ['system_profiler', 'SPHardwareDataType'],
                    stderr=subprocess.DEVNULL
                ).decode()
                for line in hw_uuid.split('\n'):
                    if 'Hardware UUID' in line:
                        uuid = line.split(':')[1].strip()
                        fingerprint_data.append(uuid.encode())
                        break
            except (subprocess.CalledProcessError, Exception):
                # Fallback to hostname
                fingerprint_data.append(platform.node().encode())
                
    except Exception as e:
        # Ultimate fallback: use username + hostname
        fingerprint_data.append(os.getenv('USER', os.getenv('USERNAME', 'unknown')).encode())
        fingerprint_data.append(platform.node().encode())
        print(f"[WARN] Hardware fingerprinting fallback used: {e}")
    
    # Combine all fingerprint data
    combined_data = b'|'.join(fingerprint_data)
    
    # Hash to create stable 32-byte fingerprint
    return crypto_manager.hash_sha256(combined_data)

def get_system_info() -> dict:
    """
    Get human-readable system information for debugging/display.
    
    Returns:
        Dictionary with system information
    """
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'python_version': platform.python_version(),
    }

def verify_system_fingerprint(stored_fingerprint: bytes) -> bool:
    """
    Verify if the current system matches the stored fingerprint.
    
    Args:
        stored_fingerprint: The previously stored fingerprint
    
    Returns:
        True if fingerprints match, False otherwise
    """
    current_fingerprint = get_system_fingerprint()
    return current_fingerprint == stored_fingerprint

# --- Self-Test Block ---
if __name__ == '__main__':
    print("--- Running system_utils.py self-test ---")
    
    # 1. Test Fingerprint Generation
    print("\n[1] Testing System Fingerprinting...")
    fingerprint1 = get_system_fingerprint()
    fingerprint2 = get_system_fingerprint()
    
    print(f"Fingerprint 1: {fingerprint1.hex()}")
    print(f"Fingerprint 2: {fingerprint2.hex()}")
    
    # Fingerprints should be consistent
    assert fingerprint1 == fingerprint2
    assert len(fingerprint1) == 32  # SHA-256 is 32 bytes
    print("[OK] Fingerprint generation is consistent and correct length.")
    
    # 2. Test System Info
    print("\n[2] Testing System Information...")
    sys_info = get_system_info()
    print(f"System: {sys_info['platform']} {sys_info['architecture']}")
    print(f"Hostname: {sys_info['hostname']}")
    print(f"Python: {sys_info['python_version']}")
    
    assert 'platform' in sys_info
    assert 'hostname' in sys_info
    print("[OK] System information retrieval successful.")
    
    # 3. Test Fingerprint Verification
    print("\n[3] Testing Fingerprint Verification...")
    
    # Should match itself
    assert verify_system_fingerprint(fingerprint1) == True
    print("[OK] Self-verification successful.")
    
    # Should not match a different fingerprint
    fake_fingerprint = os.urandom(32)
    assert verify_system_fingerprint(fake_fingerprint) == False
    print("[OK] Verification correctly rejected fake fingerprint.")
    
    print("\n--- All system_utils tests passed! ---")
    print(f"\nYour system fingerprint: {fingerprint1.hex()}")
    print("Store this securely for recovery purposes!")