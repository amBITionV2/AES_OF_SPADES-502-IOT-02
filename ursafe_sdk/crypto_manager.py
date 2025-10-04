import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
import argon2

# --- Constants from Project Spec ---
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 65536  # 64 MiB
ARGON2_PARALLELISM = 2
AES_KEY_SIZE = 32  # 32 bytes = 256 bits
AES_NONCE_SIZE = 12 # 12 bytes = 96 bits

# --- Symmetric Encryption: AES-256-GCM ---

def encrypt_aes_gcm(key: bytes, data: bytes) -> tuple:
    """
    Encrypts data using AES-256-GCM.
    Returns a tuple of (nonce, ciphertext_with_tag).
    """
    if len(key) != AES_KEY_SIZE:
        raise ValueError("Invalid AES key size.")
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(AES_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, data, None) # None for additional authenticated data
    return (nonce, ciphertext)

def decrypt_aes_gcm(key: bytes, nonce: bytes, encrypted_data: bytes) -> bytes:
    """
    Decrypts data using AES-256-GCM.
    Returns the original plaintext data or raises an exception on failure.
    """
    if len(key) != AES_KEY_SIZE:
        raise ValueError("Invalid AES key size.")
    
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, encrypted_data, None)
        return plaintext
    except Exception as e:
        # This will fail if the key is wrong or the data is tampered with (tag mismatch)
        raise ValueError(f"Decryption failed. Data may be corrupt or key is incorrect. Details: {e}")

# --- Key Derivation Function: Argon2id ---

def derive_key_argon2(password: bytes, salt: bytes) -> bytes:
    """
    Derives a 32-byte key from a password and salt using Argon2id.
    """
    ph = argon2.PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=AES_KEY_SIZE,
        salt_len=len(salt)
    )
    # Use low-level hash function to get raw bytes instead of encoded string
    key = argon2.low_level.hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=AES_KEY_SIZE,
        type=argon2.Type.ID
    )
    return key

# --- Digital Signatures: Ed25519 ---

def generate_ed25519_keys() -> tuple:
    """
    Generates a new Ed25519 private/public key pair.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return (private_key, public_key)

def sign_data(private_key: ed25519.Ed25519PrivateKey, data: bytes) -> bytes:
    """
    Signs data using an Ed25519 private key.
    """
    return private_key.sign(data)

def verify_signature(public_key: ed25519.Ed25519PublicKey, signature: bytes, data: bytes) -> bool:
    """
    Verifies a signature using an Ed25519 public key.
    Returns True if valid, False otherwise.
    """
    try:
        public_key.verify(signature, data)
        return True
    except Exception:
        return False

# --- Hashing: SHA-256 ---

def hash_sha256(data: bytes) -> bytes:
    """
    Computes the SHA-256 hash of the given data.
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()

# --- Self-Test Block ---
if __name__ == '__main__':
    print("--- Running crypto_manager.py self-test ---")

    # 1. Test Key Derivation
    print("\n[1] Testing Argon2id Key Derivation...")
    password = b"my-super-secret-pin-1234"
    salt = os.urandom(16)
    derived_key = derive_key_argon2(password, salt)
    print(f"Salt (hex): {salt.hex()}")
    print(f"Derived Key (hex): {derived_key.hex()}")
    assert len(derived_key) == AES_KEY_SIZE
    print("[OK] Key Derivation Successful.")

    # 2. Test AES-GCM Encryption/Decryption
    print("\n[2] Testing AES-GCM Encryption & Decryption...")
    original_data = b'{"account": "github", "password": "super_secure_password!"}'
    nonce, encrypted_data = encrypt_aes_gcm(derived_key, original_data)
    
    decrypted_data = decrypt_aes_gcm(derived_key, nonce, encrypted_data)
    print(f"Original Data: {original_data.decode()}")
    print(f"Decrypted Data: {decrypted_data.decode()}")
    assert original_data == decrypted_data
    print("[OK] Encryption & Decryption Successful.")

    # Test for decryption failure with wrong key
    wrong_key = os.urandom(32)
    try:
        decrypt_aes_gcm(wrong_key, nonce, encrypted_data)
        print("[FAIL] FAILED: Decryption with wrong key should not succeed.")
    except ValueError:
        print("[OK] Decryption correctly failed with wrong key.")

    # 3. Test Ed25519 Digital Signatures
    print("\n[3] Testing Ed25519 Digital Signatures...")
    priv_key, pub_key = generate_ed25519_keys()
    data_to_sign = b"This is a manifest file for the vault."
    
    signature = sign_data(priv_key, data_to_sign)
    is_valid = verify_signature(pub_key, signature, data_to_sign)
    print(f"Signature valid with correct key: {is_valid}")
    assert is_valid
    print("[OK] Signature Verification Successful.")

    # Test for verification failure with wrong key/data
    other_priv_key, _ = generate_ed25519_keys()
    wrong_signature = sign_data(other_priv_key, data_to_sign)
    is_valid_wrong_key = verify_signature(pub_key, wrong_signature, data_to_sign)
    is_valid_wrong_data = verify_signature(pub_key, signature, b"tampered data")
    print(f"Signature valid with wrong key: {is_valid_wrong_key}")
    print(f"Signature valid with wrong data: {is_valid_wrong_data}")
    assert not is_valid_wrong_key
    assert not is_valid_wrong_data
    print("[OK] Signature verification correctly failed for invalid cases.")
    
    # 4. Test SHA-256 Hashing
    print("\n[4] Testing SHA-256 Hashing...")
    hash_result = hash_sha256(b"hello world")
    print(f"SHA-256 of 'hello world': {hash_result.hex()}")
    assert hash_result.hex() == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    print("[OK] Hashing Successful.")

    print("\n--- All crypto_manager tests passed! ---")