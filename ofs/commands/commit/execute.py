"""ofs commit command implementation.

This module implements the 'ofs commit' command to create snapshots of staged changes.
"""

from pathlib import Path
from typing import Optional

from ofs.core.repository.init import Repository
from ofs.core.index.manager import Index
from ofs.core.commits import (
    generate_commit_id,
    get_file_actions,
    create_commit_object,
    get_author_info,
    save_commit,
    load_commit,
)
from ofs.core.refs import resolve_head, update_head


def execute(message: str, repo_root: Path = None) -> int:
    """Execute the 'ofs commit' command.
    
    Args:
        message: Commit message
        repo_root: Repository root (defaults to current directory)
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Find repository root
    if repo_root is None:
        repo_root = Path.cwd()
    
    repo = Repository(repo_root)
    
    # Check if repository is initialized
    if not repo.is_initialized():
        print("Error: Not an OFS repository")
        print("Hint: Run 'ofs init' to create a repository")
        return 1
    
    # Validate message
    if not message or len(message.strip()) < 3:
        print("Error: Commit message too short (min 3 characters)")
        print("Usage: ofs commit -m \"Your message here\"")
        return 1
    
    message = message.strip()
    
    # Load index
    index = Index(repo.index_file)
    staged_files = index.get_entries()
    
    # Check if index is empty
    if not staged_files:
        print("Error: Nothing to commit")
        print("Hint: Use 'ofs add <file>' to stage changes")
        return 1
    
    # Generate commit ID
    commit_id = generate_commit_id(repo.commits_dir)
    
    # Get parent commit (if exists)
    parent_id = resolve_head(repo.ofs_dir)
    parent_commit = None
    if parent_id:
        parent_commit = load_commit(parent_id, repo.commits_dir)
    
    # Determine file actions (pass commits_dir for full tree comparison)
    files_with_actions = get_file_actions(staged_files, parent_commit, repo.commits_dir)
    
    # Filter out "unchanged" files (only include added/modified/deleted)
    files_to_commit = [
        f for f in files_with_actions 
        if f.get("action") != "unchanged"
    ]
    
    if not files_to_commit:
        print("Error: No changes to commit (all files unchanged)")
        return 1
    
    # Get author information
    author, email = get_author_info()
    
    # Create commit object
    commit_obj = create_commit_object(
        commit_id=commit_id,
        parent_id=parent_id,
        message=message,
        author=author,
        email=email,
        files=files_to_commit
    )
    
    # Save commit
    try:
        save_commit(commit_obj, repo.commits_dir)
    except Exception as e:
        print(f"Error: Failed to save commit: {e}")
        return 1
    
    # Update HEAD (updates refs/heads/main)
    try:
        update_head(repo.ofs_dir, commit_id)
    except Exception as e:
        print(f"Error: Failed to update HEAD: {e}")
        return 1
    
    # Clear index
    try:
        index.clear()
    except Exception as e:
        print(f"Warning: Failed to clear index: {e}")
        # Don't return error, commit was successful
    
    # Print confirmation
    print(f"[main {commit_id}] {message}")
    
    # Count file changes by action
    added_count = sum(1 for f in files_to_commit if f.get("action") == "added")
    modified_count = sum(1 for f in files_to_commit if f.get("action") == "modified")
    deleted_count = sum(1 for f in files_to_commit if f.get("action") == "deleted")
    
    total_changes = added_count + modified_count + deleted_count
    print(f" {total_changes} file(s) changed")
    
    if added_count > 0:
        print(f" {added_count} file(s) added")
    if modified_count > 0:
        print(f" {modified_count} file(s) modified")
    if deleted_count > 0:
        print(f" {deleted_count} file(s) deleted")
    
    return 0
