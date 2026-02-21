"""File size validation utility.

This module provides functionality to validate file sizes against configured limits.
"""

from pathlib import Path


# Maximum file size in bytes (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def check_file_size(file_path: Path, max_size: int = MAX_FILE_SIZE) -> tuple[bool, str]:
    """Check if file size is within limits.
    
    Args:
        file_path: Path to file to check
        max_size: Maximum allowed file size in bytes (default: 100MB)
        
    Returns:
        tuple: (is_valid, error_message)
            - is_valid: True if file size is OK
            - error_message: Empty string if valid, error description if not
            
    Example:
        >>> from pathlib import Path
        >>> is_valid, msg = check_file_size(Path("small.txt"))
        >>> is_valid
        True
        >>> is_valid, msg = check_file_size(Path("huge.bin"))
        >>> is_valid
        False
        >>> msg
        'File size 150MB exceeds maximum of 100MB'
    """
    try:
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        file_size = file_path.stat().st_size
        
        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            return False, f"File size {size_mb:.1f}MB exceeds maximum of {max_mb:.0f}MB"
        
        return True, ""
        
    except OSError as e:
        return False, f"Error checking file size: {str(e)}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
        
    Example:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
