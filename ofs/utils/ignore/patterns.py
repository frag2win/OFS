"""Ignore pattern matching for .ofsignore files.

This module provides functionality to match file paths against ignore patterns,
similar to .gitignore but simplified for OFS.

Patterns are pre-compiled to regex for efficient repeated matching.
"""

from pathlib import Path
from typing import List, Tuple
import fnmatch
import re


# Type alias for compiled pattern: (raw_pattern, name_regex, path_regex, is_negation, is_dir_pattern)
CompiledPattern = Tuple[str, re.Pattern, re.Pattern, bool, bool]


def compile_patterns(patterns: List[str]) -> List[CompiledPattern]:
    """Pre-compile ignore patterns to regex for efficient matching.
    
    Args:
        patterns: List of glob-style patterns (supports '!' negation)
        
    Returns:
        List of compiled pattern tuples
    """
    compiled = []
    
    for pattern in patterns:
        if not pattern:
            continue
            
        is_negation = pattern.startswith('!')
        raw = pattern[1:] if is_negation else pattern
        
        # Handle directory patterns (ending with /)
        is_dir_pattern = raw.endswith('/')
        if is_dir_pattern:
            raw = raw[:-1]
        
        # Handle **/ prefix by creating a pattern that matches the basename
        match_raw = raw
        if match_raw.startswith("**/"):
            match_raw = match_raw[3:]
        
        # Compile regex for filename matching
        name_regex = re.compile(fnmatch.translate(match_raw))
        # Compile regex for full path matching
        path_regex = re.compile(fnmatch.translate(raw))
        
        compiled.append((raw, name_regex, path_regex, is_negation, is_dir_pattern))
    
    return compiled


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
    
    # Pre-compile patterns
    compiled = compile_patterns(patterns)
    return should_ignore_compiled(path, compiled, repo_root)


def should_ignore_compiled(path: Path, compiled: List[CompiledPattern], repo_root: Path = None) -> bool:
    """Check if path should be ignored using pre-compiled patterns.
    
    Use this when matching many files against the same pattern set for performance.
    
    Args:
        path: Path to check
        compiled: Pre-compiled patterns from compile_patterns()
        repo_root: Optional repository root for relative path calculation
        
    Returns:
        bool: True if path should be ignored
    """
    # Get path parts for matching
    path_str = str(path).replace("\\", "/")
    path_name = path.name
    
    # Try to get relative path if repo_root provided
    if repo_root:
        try:
            rel_path = path.relative_to(repo_root)
            path_str = str(rel_path).replace("\\", "/")
        except ValueError:
            pass
    
    # Process compiled patterns in order, tracking ignore state
    ignored = False
    
    for raw, name_regex, path_regex, is_negation, is_dir_pattern in compiled:
        matched = _matches_compiled(path_name, path_str, raw, name_regex, path_regex, is_dir_pattern)
        
        if matched:
            if is_negation:
                ignored = False  # Un-ignore
            else:
                ignored = True  # Ignore
    
    return ignored


def _matches_compiled(
    path_name: str, path_str: str, raw: str,
    name_regex: re.Pattern, path_regex: re.Pattern,
    is_dir_pattern: bool
) -> bool:
    """Check if path matches a single compiled pattern.
    
    Args:
        path_name: File/directory name only
        path_str: Full path string (forward slashes)
        raw: Raw pattern string (without ! prefix or trailing /)
        name_regex: Pre-compiled regex for filename matching
        path_regex: Pre-compiled regex for full path matching
        is_dir_pattern: Whether original pattern ended with /
        
    Returns:
        bool: True if matches
    """
    # Handle directory patterns
    if is_dir_pattern:
        if path_str.startswith(raw + '/'):
            return True
        if path_name == raw or path_str == raw:
            return True
    
    # Match on filename
    if name_regex.match(path_name):
        return True
    
    # Match on full path
    if path_regex.match(path_str):
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
