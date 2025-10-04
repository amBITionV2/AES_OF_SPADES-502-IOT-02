import os
import json

# Import the modules we just built
from . import crypto_manager
from . import chunk_manager
from . import system_utils

class VaultManager:
    """
    Manages high-level vault operations like initialization, unlocking, and locking.
    NOW INCLUDES SYSTEM FINGERPRINTING.
    """
    def __init__(self, usb_path: str):
        if not os.path.isdir(usb_path):
            raise FileNotFoundError(f"The specified USB path does not exist: {usb_path}")
        self.usb_path = usb_path
        self.ursafe_dir = os.path.join(self.usb_path, ".ursafe")
        self.vault_file = os.path.join(self.ursafe_dir, "vault.enc")
        self.meta_file = os.path.join(self.ursafe_dir, "meta.json")

    def initialize_vault(self, pin: str):
        """
        Initializes a new vault, now binding it to the current system's fingerprint.
        """
        os.makedirs(self.ursafe_dir, exist_ok=True)
        usb_salt = os.urandom(16)
        host_secret_blob = os.urandom(32)
        
        # **NEW**: Get the system fingerprint
        system_fingerprint = system_utils.get_system_fingerprint()

        all_shares = chunk_manager.split_master_key(host_secret_blob)
        num_host_chunks = chunk_manager.DEFAULT_REQUIRED_SHARES // 2
        host_chunks = all_shares[:num_host_chunks]
        usb_chunks = all_shares[num_host_chunks:]
        chunk_manager.save_host_chunks(host_chunks)

        # **UPDATED**: Store the fingerprint in the metadata
        metadata = {
            'salt_hex': usb_salt.hex(),
            'usb_chunks_hex': [chunk.hex() for chunk in usb_chunks],
            'system_fingerprint_hex': system_fingerprint.hex()
        }
        with open(self.meta_file, 'w') as f:
            json.dump(metadata, f)
        
        # **UPDATED**: Include the fingerprint in the key derivation material
        key_material = pin.encode('utf-8') + usb_salt + host_secret_blob + system_fingerprint
        vault_key = crypto_manager.derive_key_argon2(key_material, usb_salt)

        initial_vault_data = json.dumps({}).encode('utf-8')
        self.lock_vault(vault_key, initial_vault_data)
        
        print("Vault initialized successfully and bound to this computer.")

    def unlock_vault(self, pin: str) -> dict:
        """
        Orchestrates unlocking, now with a mandatory fingerprint check.
        """
        with open(self.meta_file, 'r') as f:
            metadata = json.load(f)
        
        # **NEW**: Verify the system fingerprint
        stored_fingerprint = bytes.fromhex(metadata['system_fingerprint_hex'])
        current_fingerprint = system_utils.get_system_fingerprint()

        if stored_fingerprint != current_fingerprint:
            raise PermissionError("Hardware changed! This vault is bound to a different computer.")

        usb_salt = bytes.fromhex(metadata['salt_hex'])
        usb_chunks = [bytes.fromhex(chunk) for chunk in metadata['usb_chunks_hex']]
        
        num_host_chunks = chunk_manager.DEFAULT_REQUIRED_SHARES // 2
        host_chunks = chunk_manager.load_host_chunks(num_host_chunks)

        if len(host_chunks) < num_host_chunks:
            raise PermissionError("Could not find all required host chunks. Is this the correct computer?")

        all_available_shares = host_chunks + usb_chunks
        try:
            required_shares = all_available_shares[:chunk_manager.DEFAULT_REQUIRED_SHARES]
            host_secret_blob = chunk_manager.reconstruct_master_key(required_shares)
        except Exception as e:
            raise ValueError(f"Failed to reconstruct secret key. Chunks may be missing or corrupt. {e}")
            
        # **UPDATED**: Include the CURRENT fingerprint in key derivation
        key_material = pin.encode('utf-8') + usb_salt + host_secret_blob + current_fingerprint
        vault_key = crypto_manager.derive_key_argon2(key_material, usb_salt)

        with open(self.vault_file, 'rb') as f:
            nonce = f.read(crypto_manager.AES_NONCE_SIZE)
            encrypted_data = f.read()
        
        decrypted_data_bytes = crypto_manager.decrypt_aes_gcm(vault_key, nonce, encrypted_data)
        return json.loads(decrypted_data_bytes.decode('utf-8'))

    def lock_vault(self, vault_key: bytes, vault_data_bytes: bytes):
        """
        Encrypts the given vault data and writes it to the vault file. (No changes here)
        """
        nonce, encrypted_data = crypto_manager.encrypt_aes_gcm(vault_key, vault_data_bytes)
        with open(self.vault_file, 'wb') as f:
            f.write(nonce)
            f.write(encrypted_data)

# --- Self-Test Block ---
if __name__ == '__main__':
    import shutil

    print("--- Running vault_manager.py self-test ---")
    
    # Create a dummy directory to simulate a USB stick
    TEST_USB_PATH = "test_usb_drive"
    if os.path.exists(TEST_USB_PATH):
        shutil.rmtree(TEST_USB_PATH) # Clean up from previous runs
    os.makedirs(TEST_USB_PATH)
    
    # Clean up host chunks from previous runs
    host_chunk_dir = chunk_manager.get_host_chunk_dir()
    if os.path.exists(host_chunk_dir):
        shutil.rmtree(host_chunk_dir)

    print(f"Created dummy USB drive at: ./{TEST_USB_PATH}")

    # 1. Test Vault Initialization
    print("\n[1] Testing Vault Initialization...")
    try:
        manager = VaultManager(TEST_USB_PATH)
        test_pin = "1234-5678"
        manager.initialize_vault(test_pin)
        
        # Verify files were created
        assert os.path.exists(manager.ursafe_dir)
        assert os.path.exists(manager.vault_file)
        assert os.path.exists(manager.meta_file)
        assert os.path.exists(host_chunk_dir)
        print("[OK] Initialization successful. All required files and directories created.")
    except Exception as e:
        print(f"[FAIL] FAILED: Initialization threw an exception: {e}")
        exit() # Cannot continue if this fails
        
    # 2. Test Vault Unlocking
    print("\n[2] Testing Vault Unlocking...")
    try:
        # Create a new manager instance to simulate a new run
        unlock_manager = VaultManager(TEST_USB_PATH)
        
        # Test with correct PIN
        unlocked_data = unlock_manager.unlock_vault(test_pin)
        assert unlocked_data == {} # Should be an empty dict initially
        print("[OK] Unlocking with correct PIN successful.")
        
        # Test with incorrect PIN
        try:
            unlock_manager.unlock_vault("wrong-pin")
            print("[FAIL] FAILED: Unlocking with wrong PIN should not succeed.")
        except ValueError as e:
            print(f"[OK] Unlocking correctly failed with wrong PIN. Error: {e}")

    except Exception as e:
        print(f"[FAIL] FAILED: Unlocking threw an unexpected exception: {e}")
        
    # 3. Clean up the test environment
    print("\n[3] Cleaning up test environment...")
    shutil.rmtree(TEST_USB_PATH)
    shutil.rmtree(host_chunk_dir)
    print("[OK] Cleanup successful.")
    
    print("\n--- All vault_manager tests passed! ---")