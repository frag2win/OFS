"""Commit management - List commits.

This module provides utilities for listing and querying commits.
"""

from pathlib import Path
from typing import List
import json


def list_commits(commits_dir: Path) -> List[dict]:
    """List all commits in reverse chronological order (newest first).
    
    Args:
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        List of commit objects sorted by ID (descending)
        
    Example:
        >>> commits = list_commits(Path(".ofs/commits"))
        >>> print(commits[0]["id"])  # Most recent
        "003"
    """
    if not commits_dir.exists():
        return []
    
    # Find all commit files
    commit_files = list(commits_dir.glob("*.json"))
    
    if not commit_files:
        return []
    
    # Load and sort commits
    commits = []
    for file in commit_files:
        try:
            content = file.read_text()
            commit = json.loads(content)
            commits.append(commit)
        except (json.JSONDecodeError, Exception):
            # Skip corrupted commits
            continue
    
    # Sort by ID (descending - newest first)
    commits.sort(key=lambda c: c.get("id", ""), reverse=True)
    
    return commits


def get_commit_count(commits_dir: Path) -> int:
    """Get total number of commits.
    
    Args:
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        Number of commits
        
    Example:
        >>> count = get_commit_count(Path(".ofs/commits"))
        >>> print(count)
        3
    """
    if not commits_dir.exists():
        return 0
    
    commit_files = list(commits_dir.glob("*.json"))
    return len(commit_files)
