"""Ignore pattern matching for .ofsignore files.

This module provides functionality to match file paths against ignore patterns,
similar to .gitignore but simplified for OFS.
"""

from pathlib import Path
from typing import List
import fnmatch


def should_ignore(path: Path, patterns: List[str], repo_root: Path = None) -> bool:
    """Check if path should be ignored based on patterns.
    
    Args:
        path: Path to check
        patterns: List of ignore patterns (glob style)
        repo_root: Optional repository root for relative path calculation
        
    Returns:
        bool: True if path should be ignored
        
    Example:
        >>> from pathlib import Path
        >>> patterns = ["*.tmp", "*.log", "__pycache__"]
        >>> should_ignore(Path("file.tmp"), patterns)
        True
        >>> should_ignore(Path("file.py"), patterns)
        False
    """
    if not patterns:
        return False
    
    # Get path parts for matching
    path_str = str(path)
    path_name = path.name
    
    # Try to get relative path if repo_root provided
    if repo_root:
        try:
            rel_path = path.relative_to(repo_root)
            path_str = str(rel_path)
        except ValueError:
            pass
    
    # Check each pattern
    for pattern in patterns:
        # Direct match on filename
        if fnmatch.fnmatch(path_name, pattern):
            return True
        
        # Match on full path (for directory patterns)
        if fnmatch.fnmatch(path_str, pattern):
            return True
        
        # Match on path parts (for **/pattern style)
        if pattern.startswith("**/"):
            pattern_without_prefix = pattern[3:]
            if fnmatch.fnmatch(path_name, pattern_without_prefix):
                return True
                
    return False


def load_ignore_patterns(repo_root: Path) -> List[str]:
    """Load ignore patterns from .ofsignore and config.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        List[str]: List of ignore patterns
    """
    patterns = []
    
    # Default patterns (always ignored)
    default_patterns = [
        ".ofs",
        ".ofs/**",
        "*.tmp",
        "*.swp",
        "__pycache__",
        ".DS_Store"
    ]
    patterns.extend(default_patterns)
    
    # Load from .ofsignore if it exists
    ofsignore = repo_root / ".ofsignore"
    if ofsignore.exists():
        try:
            content = ofsignore.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
        except Exception:
            # Silently ignore errors reading .ofsignore
            pass
    
    return patterns
