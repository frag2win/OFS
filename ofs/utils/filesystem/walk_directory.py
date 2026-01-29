"""Recursive directory traversal utility.

This module provides functionality to walk through directories recursively,
respecting ignore patterns and yielding file paths.
"""

from pathlib import Path
from typing import Iterator, List, Callable


def walk_directory(
    directory: Path,
    should_ignore: Callable[[Path], bool] = None
) -> Iterator[Path]:
    """Walk directory recursively, yielding file paths.
    
    Args:
        directory: Directory to walk
        should_ignore: Optional function to check if path should be ignored
        
    Yields:
        Path: File paths found in directory
        
    Example:
        >>> from pathlib import Path
        >>> for file_path in walk_directory(Path("src")):
        ...     print(file_path)
        src/main.py
        src/utils.py
        src/subdir/helper.py
    """
    if not directory.exists():
        return
    
    if not directory.is_dir():
        return
    
    for item in directory.iterdir():
        # Skip if should be ignored
        if should_ignore and should_ignore(item):
            continue
            
        if item.is_file():
            yield item
        elif item.is_dir():
            # Recursively walk subdirectories
            yield from walk_directory(item, should_ignore)
