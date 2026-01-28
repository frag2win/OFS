"""Compute SHA-256 hash of bytes in memory."""

import hashlib


def compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data.
    
    Args:
        data: Bytes to hash
        
    Returns:
        Hex digest of SHA-256 hash (64 characters)
        
    Example:
        >>> compute_hash(b"hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
        
    Note:
        Uses SHA-256 which provides cryptographic strength and is FIPS 140-2 approved.
        Hash collisions are practically impossible (2^256 space).
    """
    return hashlib.sha256(data).hexdigest()
