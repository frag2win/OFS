"""Commit management - Load commits from disk.

This module provides utilities for loading commits.
"""

from pathlib import Path
from typing import Optional
import json


def load_commit(commit_id: str, commits_dir: Path) -> Optional[dict]:
    """Load commit by ID.
    
    Args:
        commit_id: Commit ID (e.g., "003")
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        Commit object or None if not found
        
    Example:
        >>> commit = load_commit("003", Path(".ofs/commits"))
        >>> print(commit["message"])
        "Add authentication"
    """
    commit_file = commits_dir / f"{commit_id}.json"
    
    if not commit_file.exists():
        return None
    
    try:
        content = commit_file.read_text()
        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return None


def get_parent_commit(commit_id: str, commits_dir: Path) -> Optional[dict]:
    """Load parent of given commit.
    
    Args:
        commit_id: Commit ID
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        Parent commit object or None
        
    Example:
        >>> parent = get_parent_commit("003", Path(".ofs/commits"))
        >>> print(parent["id"])
        "002"
    """
    commit = load_commit(commit_id, commits_dir)
    
    if not commit or not commit.get("parent"):
        return None
    
    parent_id = commit["parent"]
    return load_commit(parent_id, commits_dir)
