"""Commit management - Create commit objects.

This module provides utilities for creating commit objects from staged changes.
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime
import os


def generate_commit_id(commits_dir: Path) -> str:
    """Generate next sequential commit ID.
    
    Scans .ofs/commits/ for existing commits and returns next ID.
    
    Args:
        commits_dir: Path to .ofs/commits directory
        
    Returns:
        Sequential commit ID: "001", "002", "003", etc.
        
    Example:
        >>> id = generate_commit_id(Path(".ofs/commits"))
        >>> print(id)
        "003"
    """
    if not commits_dir.exists():
        return "001"
    
    # Find all .json files
    commit_files = list(commits_dir.glob("*.json"))
    
    if not commit_files:
        return "001"
    
    # Extract IDs and find max
    ids = []
    for file in commit_files:
        try:
            # Extract ID from filename (e.g., "003.json" -> "003")
            commit_id = file.stem
            if commit_id.isdigit():
                ids.append(int(commit_id))
        except Exception:
            continue
    
    if not ids:
        return "001"
    
    # Next ID is max + 1, formatted with leading zeros
    next_id = max(ids) + 1
    return f"{next_id:03d}"


def get_file_actions(
    staged_files: List[dict],
    parent_commit: Optional[dict],
    commits_dir: Path = None
) -> List[dict]:
    """Determine action for each staged file (added/modified/deleted).
    
    Compares staged files with FULL tree state at parent commit
    to correctly determine actions.
    
    Args:
        staged_files: List of staged file entries from index
        parent_commit: Parent commit object (None for first commit)
        commits_dir: Path to commits directory (needed for tree traversal)
        
    Returns:
        List of file entries with "action" field added
        
    Example:
        >>> files = get_file_actions(staged, parent, commits_dir)
        >>> files[0]["action"]
        "added"
    """
    files_with_actions = []
    
    # Build map of FULL tree state at parent for comparison
    parent_files = {}
    if parent_commit and commits_dir:
        # Import here to avoid circular dependency
        from ofs.commands.checkout.execute import build_tree_state
        parent_tree = build_tree_state(parent_commit.get('id'), commits_dir)
        parent_files = parent_tree
    elif parent_commit:
        # Fallback to just parent commit files if commits_dir not provided
        for file in parent_commit.get("files", []):
            if file.get("action") != "deleted":
                parent_files[file["path"]] = file
    
    # Determine action for each staged file
    for staged_file in staged_files:
        file_entry = staged_file.copy()
        path = staged_file["path"]
        
        if path not in parent_files:
            # New file
            file_entry["action"] = "added"
        elif parent_files[path].get("hash") != staged_file.get("hash"):
            # File exists but hash changed
            file_entry["action"] = "modified"
        else:
            # File unchanged (same hash)
            file_entry["action"] = "unchanged"
        
        files_with_actions.append(file_entry)
    
    # Check for deleted files (in parent tree but not in staged)
    if parent_files:
        staged_paths = {f["path"] for f in staged_files}
        for path, parent_file in parent_files.items():
            if path not in staged_paths:
                deleted_entry = parent_file.copy()
                deleted_entry["action"] = "deleted"
                files_with_actions.append(deleted_entry)
    
    return files_with_actions


def create_commit_object(
    commit_id: str,
    parent_id: Optional[str],
    message: str,
    author: str,
    email: str,
    files: List[dict]
) -> dict:
    """Build commit object with metadata.
    
    Args:
        commit_id: Sequential commit ID (e.g., "003")
        parent_id: Parent commit ID (None for first commit)
        message: Commit message
        author: Author name
        email: Author email
        files: List of file entries with actions
        
    Returns:
        Complete commit object ready to save
        
    Example:
        >>> commit = create_commit_object(
        ...     "003", "002", "Add auth", "jsmith", "js@example.com", files
        ... )
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    commit_obj = {
        "id": commit_id,
        "parent": parent_id,
        "message": message,
        "author": author,
        "email": email,
        "timestamp": timestamp,
        "files": files
    }
    
    return commit_obj


def get_author_info() -> tuple[str, str]:
    """Get author name and email from environment or defaults.
    
    Returns:
        Tuple of (author_name, email)
        
    Example:
        >>> name, email = get_author_info()
        >>> print(name)
        "jsmith"
    """
    author = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    email = os.environ.get("EMAIL") or f"{author}@localhost"
    
    return author, email
