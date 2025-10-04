import os
import platform
from pyshamir import split, combine

# --- Constants ---
# M-of-N strategy: We need M shares to reconstruct the secret out of N total shares.
DEFAULT_REQUIRED_SHARES = 10
DEFAULT_TOTAL_SHARES = 20

# --- Core Shamir's Secret Sharing Logic ---

def split_master_key(master_key: bytes, m: int = DEFAULT_REQUIRED_SHARES, n: int = DEFAULT_TOTAL_SHARES) -> list[bytes]:
    """
    Splits a master key into 'n' shares, with 'm' required for reconstruction.
    
    Args:
        master_key: The secret bytes to split.
        m: The number of shares required to reconstruct.
        n: The total number of shares to generate.

    Returns:
        A list containing 'n' byte strings, where each is a share.
    """
    if len(master_key) == 0:
        raise ValueError("Master key cannot be empty.")
    shares = split(master_key, n, m)
    return shares

def reconstruct_master_key(shares: list[bytes]) -> bytes:
    """
    Recovers the master key from a list of shares.
    
    Args:
        shares: A list of 'm' or more shares.

    Returns:
        The original master key as bytes.
    
    Raises:
        ValueError if reconstruction fails (e.g., not enough shares).
    """
    try:
        master_key = combine(shares)
        # Convert bytearray to bytes if needed
        if isinstance(master_key, bytearray):
            master_key = bytes(master_key)
        return master_key
    except Exception as e:
        raise ValueError(f"Failed to reconstruct secret. Not enough or invalid shares provided. Details: {e}")

# --- Host Chunk File Management ---

def get_host_chunk_dir() -> str:
    """
    Returns the appropriate hidden directory for storing host chunks based on the OS.
    """
    if platform.system() == "Windows":
        # C:\ProgramData is a standard location for application data.
        return os.path.join(os.getenv("ProgramData"), ".ursafe_chunks")
    else:
        # /var/lib is common for persistent app data on Linux/macOS.
        return "/var/lib/.ursafe_chunks"

def save_host_chunks(shares: list[bytes]):
    """
    Saves a list of shares to the hidden host chunk directory.
    Each share is saved in a separate file (e.g., .c_1, .c_2).
    """
    chunk_dir = get_host_chunk_dir()
    try:
        os.makedirs(chunk_dir, exist_ok=True)
        # On non-Windows, we might want to set restrictive permissions
        if platform.system() != "Windows":
            os.chmod(chunk_dir, 0o700) # Only owner can read/write/execute
            
        for i, share in enumerate(shares):
            # Using obscure filenames as per the spec
            chunk_file_path = os.path.join(chunk_dir, f".c_{i+1}")
            with open(chunk_file_path, "wb") as f:
                f.write(share)
    except Exception as e:
        raise IOError(f"Could not save host chunks to '{chunk_dir}'. Check permissions. Details: {e}")

def load_host_chunks(num_chunks: int) -> list[bytes]:
    """
    Loads a specified number of shares from the host chunk directory.
    """
    chunk_dir = get_host_chunk_dir()
    loaded_shares = []
    if not os.path.isdir(chunk_dir):
        return [] # Return empty list if directory doesn't exist

    for i in range(1, num_chunks + 1):
        chunk_file_path = os.path.join(chunk_dir, f".c_{i}")
        if os.path.exists(chunk_file_path):
            with open(chunk_file_path, "rb") as f:
                loaded_shares.append(f.read())
    
    return loaded_shares

# --- Self-Test Block ---
if __name__ == '__main__':
    print("--- Running chunk_manager.py self-test ---")

    # 1. Test Shamir's Splitting and Reconstruction
    print("\n[1] Testing Shamir's Secret Sharing...")
    secret_key = os.urandom(32) # A realistic 256-bit key
    print(f"Original Secret Key (hex): {secret_key.hex()}")
    
    # Split the key into 20 shares, requiring 10 to reconstruct
    all_shares = split_master_key(secret_key, 10, 20)
    print(f"Successfully split key into {len(all_shares)} shares.")
    assert len(all_shares) == 20
    
    # Test reconstruction with the minimum number of shares
    required_shares = all_shares[:10]
    reconstructed_key_min = reconstruct_master_key(required_shares)
    print(f"Reconstructed with 10 shares (hex): {reconstructed_key_min.hex()}")
    assert secret_key == reconstructed_key_min
    print("[OK] Reconstruction with minimum shares successful.")
    
    # Test reconstruction with more than the minimum
    more_shares = all_shares[:15]
    reconstructed_key_more = reconstruct_master_key(more_shares)
    print(f"Reconstructed with 15 shares (hex): {reconstructed_key_more.hex()}")
    assert secret_key == reconstructed_key_more
    print("[OK] Reconstruction with more than minimum shares successful.")
    
    # Test for failure with insufficient shares
    insufficient_shares = all_shares[:9]
    try:
        reconstructed_insufficient = reconstruct_master_key(insufficient_shares)
        if reconstructed_insufficient != secret_key:
            print("[OK] Reconstruction correctly failed with insufficient shares (returned wrong key).")
        else:
            print("[FAIL] FAILED: Reconstruction with insufficient shares should not succeed.")
    except ValueError:
        print("[OK] Reconstruction correctly failed with insufficient shares.")
        
    # 2. Test Host Chunk File Management
    print("\n[2] Testing Host Chunk File Management...")
    host_dir = get_host_chunk_dir()
    print(f"Host chunk directory for this OS: {host_dir}")
    
    # Use the first 10 shares as our "host chunks"
    host_chunks_to_save = all_shares[10:] # The other 10 shares
    
    try:
        save_host_chunks(host_chunks_to_save)
        print(f"Successfully saved {len(host_chunks_to_save)} chunks to disk.")

        loaded_chunks = load_host_chunks(len(host_chunks_to_save))
        print(f"Successfully loaded {len(loaded_chunks)} chunks from disk.")
        assert host_chunks_to_save == loaded_chunks
        print("[OK] Host chunks saved and loaded correctly.")

        # Final test: Reconstruct using a mix of "in-memory" and "loaded from disk" shares
        final_test_shares = all_shares[:5] + loaded_chunks[:5]
        final_reconstructed_key = reconstruct_master_key(final_test_shares)
        assert secret_key == final_reconstructed_key
        print("[OK] Final reconstruction test with loaded chunks successful.")

    except (IOError, PermissionError) as e:
        print(f"\n[WARN] WARNING: Could not test file saving/loading. This is common if you are not running with admin/sudo privileges.")
        print(f"   Error details: {e}")
        print("   Skipping file management tests, but the core logic tests passed.")
    
    print("\n--- chunk_manager tests completed! ---")