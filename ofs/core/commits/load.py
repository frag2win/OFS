"""Commit management - Load commits from disk.

This module provides utilities for loading commits.
Includes scoped LRU caching for improved performance on repeated accesses.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
import json


class _CommitCache:
    """Scoped commit cache with bounded size.
    
    Cache keys use (commit_id, resolved_commits_dir) tuples to ensure
    per-repository isolation. The cache is bounded to prevent unbounded
    memory growth.
    """
    __slots__ = ('_store', '_max_size')
    
    def __init__(self, max_size: int = 128):
        self._store: Dict[Tuple[str, str], Optional[dict]] = {}
        self._max_size = max_size
    
    def get(self, key: Tuple[str, str]) -> Tuple[bool, Optional[dict]]:
        """Get a cached commit. Returns (found, value)."""
        if key in self._store:
            cached = self._store[key]
            return True, dict(cached) if cached else None
        return False, None
    
    def put(self, key: Tuple[str, str], value: Optional[dict]) -> None:
        """Store a commit in cache, evicting oldest if full."""
        if len(self._store) >= self._max_size:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        self._store[key] = value
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()


# Module-level cache instance — cleared via clear_commit_cache()
_cache = _CommitCache()


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
    
    Uses a scoped LRU cache to avoid repeated disk reads for the same commit.
    Cache keys include the resolved commits_dir path for per-repo isolation.
    
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
    cache_key = (commit_id, str(commits_dir.resolve()))
    
    # Check cache first
    found, cached_value = _cache.get(cache_key)
    if found:
        return cached_value
    
    # Load from disk
    result = _load_commit_from_disk(commit_id, commits_dir)
    
    # Store in cache
    _cache.put(cache_key, result)
    
    # Return a copy to prevent mutation
    return dict(result) if result else None


def clear_commit_cache() -> None:
    """Clear the commit cache.
    
    Call this after modifying commits on disk to ensure
    fresh data is loaded. Also called between tests
    to prevent cross-test contamination.
    """
    _cache.clear()


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
