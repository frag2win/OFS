"""Ignore pattern matching for .ofsignore files.

This module provides functionality to match file paths against ignore patterns,
similar to .gitignore but simplified for OFS.
"""

from pathlib import Path
from typing import List
import fnmatch


def should_ignore(path: Path, patterns: List[str], repo_root: Path = None) -> bool:
    """Check if path should be ignored based on patterns.
    
    Processes patterns in order. Negation patterns (starting with '!') 
    un-ignore previously ignored files.
    
    Args:
        path: Path to check
        patterns: List of ignore patterns (glob style, '!' for negation)
        repo_root: Optional repository root for relative path calculation
        
    Returns:
        bool: True if path should be ignored
        
    Example:
        >>> from pathlib import Path
        >>> patterns = ["*.log", "!important.log"]
        >>> should_ignore(Path("test.log"), patterns)
        True
        >>> should_ignore(Path("important.log"), patterns)
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
    
    # Process patterns in order, tracking ignore state
    ignored = False
    
    for pattern in patterns:
        # Handle negation patterns
        if pattern.startswith('!'):
            negate_pattern = pattern[1:]
            if _matches_pattern(path_name, path_str, negate_pattern):
                ignored = False  # Un-ignore
        else:
            if _matches_pattern(path_name, path_str, pattern):
                ignored = True  # Ignore
    
    return ignored


def _matches_pattern(path_name: str, path_str: str, pattern: str) -> bool:
    """Check if path matches a single pattern.
    
    Args:
        path_name: File/directory name only
        path_str: Full path string
        pattern: Pattern to match
        
    Returns:
        bool: True if matches
    """
    # Handle directory patterns (ending with /)
    if pattern.endswith('/'):
        dir_pattern = pattern[:-1]  # Remove trailing slash
        # Check if path starts with this directory
        if path_str.startswith(dir_pattern + '/') or path_str.startswith(dir_pattern + '\\'):
            return True
        if path_name == dir_pattern or path_str == dir_pattern:
            return True
    
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
