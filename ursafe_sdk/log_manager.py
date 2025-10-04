# file: ursafe_sdk/log_manager.py
"""
Manages the blockchain-style, tamper-evident usage log.
Integrates with crypto_manager for proper hashing and signatures.
"""
import json
import os
from datetime import datetime
from . import crypto_manager

LOG_FILENAME = "logchain.json"
URSAFE_DIR = ".ursafe"

def get_previous_hash(log_file_path):
    """
    Gets the hash of the last log entry for blockchain chaining.
    
    Returns:
        str: Hex string of previous entry hash, or "genesis" for first entry
    """
    if not os.path.exists(log_file_path):
        return "genesis"
    
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            if not lines:
                return "genesis"
            
            # Get the last entry and hash it
            last_entry = lines[-1].strip()
            if last_entry:
                last_hash = crypto_manager.hash_sha256(last_entry.encode('utf-8'))
                return last_hash.hex()
            else:
                return "genesis"
    except Exception:
        return "genesis"

def add_log_entry(drive_path, action_description, signing_key=None):
    """
    Creates a new blockchain-style log entry with proper hashing and signatures.

    Args:
        drive_path (str): The mount point of the USB stick (e.g., 'E:\\').
        action_description (str): A human-readable string of the action performed.
        signing_key: Ed25519 private key for signing (optional for now)
    
    Returns:
        bool: True if successful, False otherwise.
    """
    log_file_path = os.path.join(drive_path, URSAFE_DIR, LOG_FILENAME)

    # Ensure .ursafe directory exists
    ursafe_dir = os.path.join(drive_path, URSAFE_DIR)
    if not os.path.isdir(ursafe_dir):
        print(f"Error: UR Safe directory not found at {drive_path}")
        return False

    # Get previous hash for blockchain chaining
    prev_hash = get_previous_hash(log_file_path)
    
    # Create the log entry
    timestamp = datetime.utcnow().isoformat()
    entry_data = {
        "timestamp": timestamp,
        "action": action_description,
        "prev_hash": prev_hash
    }
    
    # Convert to JSON for hashing and signing
    entry_json = json.dumps(entry_data, sort_keys=True)
    entry_bytes = entry_json.encode('utf-8')
    
    # Calculate current entry hash
    current_hash = crypto_manager.hash_sha256(entry_bytes)
    
    # Add signature if signing key is provided
    if signing_key:
        try:
            signature = crypto_manager.sign_data(signing_key, entry_bytes)
            entry_data["signature"] = signature.hex()
        except Exception as e:
            print(f"Warning: Could not sign log entry: {e}")
            entry_data["signature"] = "unsigned"
    else:
        entry_data["signature"] = "unsigned"
    
    # Add the current hash to the entry
    entry_data["current_hash"] = current_hash.hex()

    try:
        # Append to log file (one JSON object per line)
        with open(log_file_path, 'a') as f:
            f.write(json.dumps(entry_data) + "\n")
        print(f"Successfully logged action: '{action_description}'")
        return True
    except Exception as e:
        print(f"Error writing to log file: {e}")
        return False

def verify_log_chain(drive_path):
    """
    Verifies the integrity of the entire log chain.
    
    Returns:
        bool: True if chain is valid, False otherwise
    """
    log_file_path = os.path.join(drive_path, URSAFE_DIR, LOG_FILENAME)
    
    if not os.path.exists(log_file_path):
        return True  # Empty log is valid
    
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
        
        previous_hash = "genesis"
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            entry = json.loads(line.strip())
            
            # Verify the previous hash matches
            if entry.get("prev_hash") != previous_hash:
                print(f"Log chain broken at entry {i}: prev_hash mismatch")
                return False
            
            # Verify the current hash
            entry_for_hash = {k: v for k, v in entry.items() if k not in ["signature", "current_hash"]}
            entry_bytes = json.dumps(entry_for_hash, sort_keys=True).encode('utf-8')
            calculated_hash = crypto_manager.hash_sha256(entry_bytes).hex()
            
            if entry.get("current_hash") != calculated_hash:
                print(f"Log entry {i} has invalid hash")
                return False
            
            # Update for next iteration
            previous_hash = calculated_hash
        
        print(f"Log chain verified: {len(lines)} entries valid")
        return True
        
    except Exception as e:
        print(f"Error verifying log chain: {e}")
        return False

def get_log_entries(drive_path):
    """
    Retrieves all log entries from the chain.
    
    Returns:
        list: List of log entry dictionaries
    """
    log_file_path = os.path.join(drive_path, URSAFE_DIR, LOG_FILENAME)
    
    if not os.path.exists(log_file_path):
        return []
    
    try:
        entries = []
        with open(log_file_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))
        return entries
    except Exception as e:
        print(f"Error reading log entries: {e}")
        return []

# Self-test functionality
if __name__ == '__main__':
    print("--- Running log_manager.py self-test ---")
    
    # Create a test directory to simulate USB
    TEST_USB_PATH = "test_log_usb"
    if os.path.exists(TEST_USB_PATH):
        import shutil
        shutil.rmtree(TEST_USB_PATH)
    os.makedirs(os.path.join(TEST_USB_PATH, URSAFE_DIR))
    
    print(f"Testing log manager with drive: {TEST_USB_PATH}")
    
    # Test adding entries
    print("\n[1] Testing log entry creation...")
    assert add_log_entry(TEST_USB_PATH, "Test Action: Vault Initialized")
    assert add_log_entry(TEST_USB_PATH, "Test Action: Vault Unlocked")
    assert add_log_entry(TEST_USB_PATH, "Test Action: Secret Added")
    print("[OK] Log entries created successfully")
    
    # Test chain verification
    print("\n[2] Testing log chain verification...")
    assert verify_log_chain(TEST_USB_PATH)
    print("[OK] Log chain verification passed")
    
    # Test retrieving entries
    print("\n[3] Testing log entry retrieval...")
    entries = get_log_entries(TEST_USB_PATH)
    assert len(entries) == 3
    assert entries[0]["action"] == "Test Action: Vault Initialized"
    assert entries[0]["prev_hash"] == "genesis"
    print(f"[OK] Retrieved {len(entries)} log entries")
    
    # Display the log entries
    print("\n[4] Log Chain Contents:")
    for i, entry in enumerate(entries):
        print(f"   Entry {i+1}: {entry['action']}")
        print(f"   Timestamp: {entry['timestamp']}")
        print(f"   Hash: {entry['current_hash'][:16]}...")
    
    # Cleanup
    import shutil
    shutil.rmtree(TEST_USB_PATH)
    print("\n--- All log_manager tests passed! ---")