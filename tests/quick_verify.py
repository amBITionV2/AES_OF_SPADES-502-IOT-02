#!/usr/bin/env python3
"""
UR Safe Stick - Quick Project Verification
Performs essential checks to verify the project is working
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_verification():
    """Quick verification of essential components"""
    print("=" * 60)
    print("🔒 UR Safe Stick - Quick Project Verification")
    print("=" * 60)
    
    # Check 1: Module imports
    print("\n1️⃣ Testing Module Imports...")
    try:
        from ursafe_sdk.vault_manager import VaultManager
        from ursafe_sdk.crypto_manager import encrypt_aes_gcm, decrypt_aes_gcm
        from ursafe_sdk.usb_manager import find_usb_drives
        print("✅ All core modules import successfully!")
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False
    
    # Check 2: Crypto functions
    print("\n2️⃣ Testing Basic Cryptography...")
    try:
        from ursafe_sdk.crypto_manager import derive_key_argon2
        
        # Quick crypto test
        test_key = b"0123456789abcdef" * 2  # 32 bytes
        test_data = b"Hello UR Safe Stick!"
        
        nonce, encrypted = encrypt_aes_gcm(test_key, test_data)
        decrypted = decrypt_aes_gcm(test_key, nonce, encrypted)
        
        if decrypted == test_data:
            print("✅ Basic encryption/decryption works!")
        else:
            print("❌ Crypto test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Crypto test failed: {e}")
        return False
    
    # Check 3: USB detection
    print("\n3️⃣ Testing USB Detection...")
    try:
        drives = find_usb_drives()
        print(f"✅ USB detection works! Found {len(drives)} removable drives")
        
        for drive in drives[:3]:  # Show max 3 drives
            label = drive.get('label', 'Unlabeled')
            size = drive.get('size', 'Unknown size')
            print(f"   💾 {drive['mountpoint']} - {label} ({size})")
            
    except Exception as e:
        print(f"❌ USB detection failed: {e}")
        return False
    
    # Check 4: GUI components
    print("\n4️⃣ Testing GUI Components...")
    try:
        from PyQt6.QtWidgets import QApplication
        from dashboard.main_window import MainWindow
        print("✅ PyQt6 GUI components load successfully!")
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False
    
    # Check 5: File structure
    print("\n5️⃣ Checking Project Files...")
    essential_files = [
        "ursafe_sdk/crypto_manager.py",
        "ursafe_sdk/vault_manager.py", 
        "ursafe_sdk/usb_manager.py",
        "dashboard/main_window.py",
        "main.py",
        "requirements.txt"
    ]
    
    all_present = True
    for file_path in essential_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size} bytes)")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_present = False
    
    if not all_present:
        return False
    
    print("\n" + "=" * 60)
    print("🎉 PROJECT VERIFICATION PASSED!")
    print("🚀 UR Safe Stick is ready to run!")
    print("=" * 60)
    print("\n💡 To launch the application:")
    print("   python main.py")
    print("\n💡 To test with real operations:")
    print("   python test_integration.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = quick_verification()
    sys.exit(0 if success else 1)