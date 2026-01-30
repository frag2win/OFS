"""Commit management - Save and load commits.

This module provides utilities for persisting commits to disk.
"""

from pathlib import Path
import json


def save_commit(commit_obj: dict, commits_dir: Path):
    """Save commit to disk atomically.
    
    Writes commit to .ofs/commits/<id>.json using atomic write.
    
    Args:
        commit_obj: Commit object with all metadata
        commits_dir: Path to .ofs/commits directory
        
    Example:
        >>> save_commit(commit_obj, Path(".ofs/commits"))
        # Creates .ofs/commits/003.json
    """
    # Ensure commits directory exists
    commits_dir.mkdir(parents=True, exist_ok=True)
    
    commit_id = commit_obj["id"]
    commit_file = commits_dir / f"{commit_id}.json"
    
    # Atomic write: temp file + rename
    temp_file = commit_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(commit_obj, indent=2))
    temp_file.rename(commit_file)
