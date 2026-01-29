"""Working tree comparison utility.

This module provides functionality to compare working directory files
with staged/committed versions.
"""

from pathlib import Path
from ofs.utils.hash.compute_file import compute_file_hash


def has_file_changed(file_path: Path, expected_hash: str) -> bool:
    """Check if file has changed from expected hash.
    
    Args:
        file_path: Path to file
        expected_hash: Expected SHA-256 hash
        
    Returns:
        bool: True if file has changed (hash mismatch)
        
    Example:
        >>> from pathlib import Path
        >>> has_file_changed(Path("file.txt"), "abc123...")
        False  # File unchanged
        >>> # User modifies file
        >>> has_file_changed(Path("file.txt"), "abc123...")
        True  # File changed
    """
    if not file_path.exists():
        return True  # File deleted counts as changed
    
    try:
        current_hash = compute_file_hash(file_path)
        return current_hash != expected_hash
    except Exception:
        return True  # Error reading file counts as changed
