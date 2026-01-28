"""Verify hash matches expected value."""

from pathlib import Path
from .compute_file import compute_file_hash


def verify_hash(path: Path, expected_hash: str) -> bool:
    """Verify file hash matches expected value.
    
    Args:
        path: Path to file to verify
        expected_hash: Expected SHA-256 hash (64 hex characters)
        
    Returns:
        True if hash matches, False otherwise
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If expected_hash is not valid format
        
    Example:
        >>> from pathlib import Path
        >>> path = Path("test.txt")
        >>> path.write_text("hello")
        5
        >>> verify_hash(path, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
        True
        >>> verify_hash(path, "0" * 64)
        False
        
    Note:
        This is used for corruption detection throughout OFS.
        Every file retrieved from object store is verified.
    """
    # Validate expected hash format
    if len(expected_hash) != 64 or not all(c in "0123456789abcdef" for c in expected_hash.lower()):
        raise ValueError(f"Invalid hash format: {expected_hash}")
    
    actual_hash = compute_file_hash(path)
    return actual_hash.lower() == expected_hash.lower()
