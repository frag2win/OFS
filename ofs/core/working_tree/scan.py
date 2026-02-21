"""Working tree scanning utility.

This module provides functionality to scan the working directory and
identify files for status reporting.
"""

from pathlib import Path
from typing import List, Set
from ofs.utils.filesystem.walk_directory import walk_directory
from ofs.utils.ignore.patterns import load_ignore_patterns, compile_patterns, should_ignore_compiled


def scan_working_tree(repo_root: Path, ignore_patterns: List[str] = None) -> Set[Path]:
    """Scan working directory and return all non-ignored files.
    
    Pre-compiles ignore patterns once and reuses them for every file,
    avoiding repeated pattern parsing.
    
    Args:
        repo_root: Repository root directory
        ignore_patterns: Optional list of ignore patterns
        
    Returns:
        Set[Path]: Set of file paths (relative to repo root)
        
    Example:
        >>> from pathlib import Path
        >>> files = scan_working_tree(Path("/repo"))
        >>> "src/main.py" in files
        True
    """
    if ignore_patterns is None:
        ignore_patterns = load_ignore_patterns(repo_root)
    
    # Pre-compile patterns once for all files
    compiled = compile_patterns(ignore_patterns)
    
    files = set()
    
    for file_path in walk_directory(repo_root, lambda p: should_ignore_compiled(p, compiled, repo_root)):
        try:
            rel_path = file_path.relative_to(repo_root)
            files.add(rel_path)
        except ValueError:
            # File is outside repo root, skip
            continue
    
    return files
