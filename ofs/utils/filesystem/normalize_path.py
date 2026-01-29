"""Path normalization utility for cross-platform compatibility.

This module provides functionality to normalize file paths for consistent
handling across Windows, Linux, and macOS.
"""

from pathlib import Path


def normalize_path(path: Path, base: Path = None) -> Path:
    """Normalize path for cross-platform compatibility.
    
    Args:
        path: Path to normalize
        base: Optional base path to resolve against
        
    Returns:
        Path: Normalized absolute path
        
    Example:
        >>> from pathlib import Path
        >>> normalize_path(Path("../src/main.py"))
        Path('/absolute/path/to/src/main.py')
    """
    # Resolve to absolute path
    if base:
        normalized = (base / path).resolve()
    else:
        normalized = path.resolve()
    
    return normalized


def get_relative_path(path: Path, base: Path) -> Path:
    """Get path relative to base directory.
    
    Args:
        path: Path to make relative
        base: Base directory
        
    Returns:
        Path: Relative path
        
    Raises:
        ValueError: If path is not within base directory
        
    Example:
        >>> from pathlib import Path
        >>> get_relative_path(Path("/repo/src/main.py"), Path("/repo"))
        Path('src/main.py')
    """
    try:
        return path.relative_to(base)
    except ValueError as e:
        raise ValueError(f"Path {path} is not within {base}") from e
