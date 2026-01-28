"""Compute SHA-256 hash of files using streaming."""

import hashlib
from pathlib import Path


def compute_file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA-256 hash of file contents.
    
    Uses streaming to handle large files without loading entire content into memory.
    
    Args:
        path: Path to file to hash
        chunk_size: Size of chunks to read (default 8KB)
        
    Returns:
        Hex digest of SHA-256 hash (64 characters)
        
    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        
    Example:
        >>> from pathlib import Path
        >>> path = Path("test.txt")
        >>> path.write_text("hello")
        5
        >>> compute_file_hash(path)
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
        
    Note:
        Reads file in chunks for memory efficiency with large files (up to 100MB).
        Binary mode ensures consistent hashing across text and binary files.
    """
    hasher = hashlib.sha256()
    
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    
    return hasher.hexdigest()
