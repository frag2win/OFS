"""Reference management - Read HEAD pointer.

This module provides utilities for reading and resolving the HEAD pointer.
"""

from pathlib import Path
from typing import Optional


def read_head(ofs_dir: Path) -> Optional[str]:
    """Read HEAD file and return its content.
    
    Args:
        ofs_dir: Path to .ofs directory
        
    Returns:
        - "ref: refs/heads/main" if symbolic ref
        - "003" if detached HEAD (direct commit ID)
        - None if HEAD doesn't exist or is empty
        
    Example:
        >>> head = read_head(Path(".ofs"))
        >>> print(head)
        "ref: refs/heads/main"
    """
    head_file = ofs_dir / "HEAD"
    
    if not head_file.exists():
        return None
    
    try:
        content = head_file.read_text().strip()
        return content if content else None
    except Exception:
        return None


def resolve_head(ofs_dir: Path) -> Optional[str]:
    """Resolve HEAD to actual commit ID.
    
    Follows symbolic refs to get the final commit ID.
    
    Args:
        ofs_dir: Path to .ofs directory
        
    Returns:
        Commit ID string (e.g., "003") or None if no commits yet
        
    Example:
        >>> commit_id = resolve_head(Path(".ofs"))
        >>> print(commit_id)
        "003"
    """
    head_content = read_head(ofs_dir)
    
    if not head_content:
        return None
    
    # Check if symbolic ref (starts with "ref: ")
    if head_content.startswith("ref: "):
        ref_path_str = head_content[5:]  # Remove "ref: " prefix
        ref_file = ofs_dir / ref_path_str
        
        if not ref_file.exists():
            return None  # No commits yet on this branch
        
        try:
            commit_id = ref_file.read_text().strip()
            return commit_id if commit_id else None
        except Exception:
            return None
    
    # Already a commit ID (detached HEAD)
    return head_content


def is_detached_head(ofs_dir: Path) -> bool:
    """Check if HEAD is detached (points directly to commit).
    
    Args:
        ofs_dir: Path to .ofs directory
        
    Returns:
        True if detached HEAD, False if symbolic ref
        
    Example:
        >>> is_detached_head(Path(".ofs"))
        False
    """
    head_content = read_head(ofs_dir)
    
    if not head_content:
        return False
    
    # Detached HEAD doesn't start with "ref: "
    return not head_content.startswith("ref: ")
