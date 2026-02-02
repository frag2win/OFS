"""Commit management - Load commits from disk.

This module provides utilities for loading commits.
Includes LRU caching for improved performance on repeated accesses.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
from functools import lru_cache
import json

# Cache for loaded commits: (commit_id, commits_dir_str) -> commit_dict
_commit_cache: Dict[Tuple[str, str], Optional[dict]] = {}
_CACHE_MAX_SIZE = 128


def _load_commit_from_disk(commit_id: str, commits_dir: Path) -> Optional[dict]:
    """Load commit directly from disk (no caching).
    
    Args:
        commit_id: Commit ID (e.g., "003")
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        Commit object or None if not found
    """
    commit_file = commits_dir / f"{commit_id}.json"
    
    if not commit_file.exists():
        return None
    
    try:
        content = commit_file.read_text()
        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return None


def load_commit(commit_id: str, commits_dir: Path) -> Optional[dict]:
    """Load commit by ID with caching.
    
    Uses an LRU cache to avoid repeated disk reads for the same commit.
    
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
    global _commit_cache
    
    # Create cache key
    cache_key = (commit_id, str(commits_dir.resolve()))
    
    # Check cache first
    if cache_key in _commit_cache:
        # Return a copy to prevent mutation
        cached = _commit_cache[cache_key]
        return dict(cached) if cached else None
    
    # Load from disk
    result = _load_commit_from_disk(commit_id, commits_dir)
    
    # Manage cache size (simple LRU: evict oldest if full)
    if len(_commit_cache) >= _CACHE_MAX_SIZE:
        # Remove oldest entry (first key)
        oldest_key = next(iter(_commit_cache))
        del _commit_cache[oldest_key]
    
    # Store in cache
    _commit_cache[cache_key] = result
    
    # Return a copy to prevent mutation
    return dict(result) if result else None


def clear_commit_cache() -> None:
    """Clear the commit cache.
    
    Call this after modifying commits on disk to ensure
    fresh data is loaded.
    """
    global _commit_cache
    _commit_cache.clear()


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
