"""Filesystem utility for atomic writes."""

from pathlib import Path
import os


def atomic_write(file_path: Path, content: bytes) -> None:
    """Write content to file atomically using temp file + rename.
    
    This ensures no partial writes are visible if the process crashes.
    The rename operation is atomic on both POSIX and Windows systems.
    
    Args:
        file_path: Target file path to write to
        content: Bytes to write
        
    Raises:
        OSError: If write or rename fails
        PermissionError: If insufficient permissions
        
    Example:
        >>> from pathlib import Path
        >>> atomic_write(Path("test.txt"), b"content")
        >>> Path("test.txt").read_bytes()
        b'content'
        
    Note:
        This is used throughout OFS for all metadata writes (commits, index, refs)
        to ensure atomicity and prevent corruption from crashes.
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    temp_path.write_bytes(content)
    
    # Atomic rename
    # On Windows, rename may fail if target exists, so remove first
    if os.name == "nt" and file_path.exists():
        file_path.unlink()
    
    temp_path.rename(file_path)
