"""Diff computation utilities.

This module provides functions to compute differences between file versions.
"""

from typing import List, Tuple, Optional
from difflib import unified_diff


def is_binary(content: bytes) -> bool:
    """Check if content is binary.
    
    A file is considered binary if it contains null bytes in the first 8KB.
    
    Args:
        content: File content as bytes
        
    Returns:
        bool: True if content appears to be binary
    """
    # Check first 8KB for null bytes
    sample = content[:8192]
    return b'\x00' in sample


def compute_file_diff(
    old_content: bytes,
    new_content: bytes,
    old_path: str,
    new_path: str,
    context_lines: int = 3
) -> List[str]:
    """Compute unified diff between two file versions.
    
    Args:
        old_content: Original file content
        new_content: New file content
        old_path: Path for "old" file in diff header
        new_path: Path for "new" file in diff header
        context_lines: Number of context lines (default: 3)
        
    Returns:
        List of diff lines (unified diff format)
    """
    # Handle binary files
    if is_binary(old_content) or is_binary(new_content):
        if old_content == new_content:
            return []  # Binary files are identical
        return [f"Binary files {old_path} and {new_path} differ"]
    
    # Convert to text lines
    try:
        old_lines = old_content.decode('utf-8', errors='replace').splitlines(keepends=True)
        new_lines = new_content.decode('utf-8', errors='replace').splitlines(keepends=True)
    except Exception:
        # If decoding fails, treat as binary
        return [f"Binary files {old_path} and {new_path} differ"]
    
    # Compute unified diff
    diff_lines = list(unified_diff(
        old_lines,
        new_lines,
        fromfile=old_path,
        tofile=new_path,
        lineterm='',
        n=context_lines
    ))
    
    return diff_lines


def format_diff_header(old_path: str, new_path: str, action: str = None) -> List[str]:
    """Format diff header for a file.
    
    Args:
        old_path: Old file path
        new_path: New file path
        action: Optional action (new, deleted, modified)
        
    Returns:
        List of header lines
    """
    header = [f"diff --ofs a/{old_path} b/{new_path}"]
    
    if action == "new":
        header.append(f"new file: {new_path}")
    elif action == "deleted":
        header.append(f"deleted file: {old_path}")
    
    return header


def compute_diff_stats(diff_lines: List[str]) -> Tuple[int, int]:
    """Compute statistics from diff lines.
    
    Args:
        diff_lines: Unified diff lines
        
    Returns:
        Tuple of (additions, deletions)
    """
    additions = 0
    deletions = 0
    
    for line in diff_lines:
        if line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
    
    return additions, deletions
