"""Reference management - Update references atomically.

This module provides utilities for updating HEAD and branch references.
"""

from pathlib import Path


def update_ref(ref_path: Path, value: str):
    """Update a reference file atomically.
    
    Uses temp file + rename for atomicity.
    
    Args:
        ref_path: Path to reference file
        value: New value (commit ID or symbolic ref)
        
    Example:
        >>> update_ref(Path(".ofs/refs/heads/main"), "003")
    """
    # Ensure parent directory exists
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write: temp file + rename
    # Use parent directory for temp file to ensure atomic rename
    temp_path = ref_path.parent / f"{ref_path.name}.tmp"
    temp_path.write_text(value.strip() + "\n")
    
    # Replace existing file atomically
    if temp_path.exists():
        temp_path.replace(ref_path)


def update_head(ofs_dir: Path, commit_id: str, detached: bool = False):
    """Update HEAD to point to a commit.
    
    Args:
        ofs_dir: Path to .ofs directory
        commit_id: Target commit ID
        detached: If True, set detached HEAD. If False, update the current branch.
        
    Example:
        >>> # Update current branch
        >>> update_head(Path(".ofs"), "003")
        
        >>> # Detached HEAD
        >>> update_head(Path(".ofs"), "002", detached=True)
    """
    head_file = ofs_dir / "HEAD"
    
    if detached:
        # Set HEAD directly to commit ID
        update_ref(head_file, commit_id)
    else:
        # Read current HEAD to find which branch to update
        if not head_file.exists():
            # No HEAD yet, default to main
            head_content = "ref: refs/heads/main"
        else:
            head_content = head_file.read_text().strip()
        
        if head_content.startswith("ref: "):
            # Update the branch that HEAD points to
            ref_path_str = head_content[5:]  # Remove "ref: "
            ref_file = ofs_dir / ref_path_str
            update_ref(ref_file, commit_id)
        else:
            # Detached HEAD, just update HEAD directly
            update_ref(head_file, commit_id)


def init_head(ofs_dir: Path, branch: str = "main"):
    """Initialize HEAD to point to a branch (no commits yet).
    
    Args:
        ofs_dir: Path to .ofs directory
        branch: Branch name (default: "main")
        
    Example:
        >>> init_head(Path(".ofs"))
        # Creates HEAD file with "ref: refs/heads/main"
    """
    head_file = ofs_dir / "HEAD"
    update_ref(head_file, f"ref: refs/heads/{branch}")
