"""ofs checkout command implementation.

This module implements the 'ofs checkout' command to restore repository to a previous commit.
"""

from pathlib import Path
from typing import Dict

from ofs.core.repository.init import Repository
from ofs.core.commits import load_commit, list_commits
from ofs.core.objects.store import ObjectStore
from ofs.core.index.manager import Index
from ofs.core.refs import update_head
from ofs.utils.hash.compute_file import compute_file_hash


def build_tree_state(commit_id: str, commits_dir: Path) -> Dict[str, dict]:
    """Build complete file tree state at a given commit.
    
    Traverses commit history from beginning to target commit
    to build the complete file state.
    
    Args:
        commit_id: Target commit ID
        commits_dir: Path to commits directory
        
    Returns:
        Dictionary mapping path -> file_entry (with hash, etc.)
    """
    # Get all commits up to and including target
    all_commits = list_commits(commits_dir)
    
    # Find commits to apply (from oldest to target)
    commits_to_apply = []
    for commit in reversed(all_commits):
        commits_to_apply.append(commit)
        if commit.get('id') == commit_id:
            break
    
    # Build tree by applying commits in order
    tree_state = {}  # path -> file_entry
    
    for commit in commits_to_apply:
        for file_entry in commit.get('files', []):
            path = file_entry.get('path')
            action = file_entry.get('action')
            
            if action == 'deleted':
                # Remove from tree
                if path in tree_state:
                    del tree_state[path]
            else:
                # Add or update in tree
                tree_state[path] = file_entry
    
    return tree_state


def execute(
    commit_id: str,
    force: bool = False,
    repo_root: Path = None
) -> int:
    """Execute the 'ofs checkout' command.
    
    Args:
        commit_id: Target commit ID
        force: Overwrite uncommitted changes without warning
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
    
    # Load target commit
    commit = load_commit(commit_id, repo.commits_dir)
    
    if not commit:
        print(f"Error: Commit '{commit_id}' not found")
        print("Hint: Use 'ofs log' to see available commits")
        return 1
    
    # Check for uncommitted changes (unless --force)
    if not force:
        index = Index(repo.index_file)
        if index.has_changes():
            print("[WARNING] You have uncommitted changes in the staging area")
            print("These changes will be LOST if you proceed.")
            print()
            print("Your uncommitted changes:")
            
            # Show what's staged
            entries = index.get_entries()
            for entry in entries[:5]:  # Show first 5
                print(f"  - {entry['path']}")
            if len(entries) > 5:
                print(f"  ... and {len(entries) - 5} more file(s)")
            
            print()
            print("Options:")
            print(f"  1. Commit your changes:  ofs commit -m 'save work'")
            print(f"  2. Force checkout:        ofs checkout --force {commit_id}")
            print()
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Checkout cancelled")
                return 1
            print()
    
    # Initialize object store
    object_store = ObjectStore(repo.ofs_dir)
    
    # Build complete tree state at target commit
    tree_state = build_tree_state(commit_id, repo.commits_dir)
    files_to_restore = list(tree_state.values())
    
    # Verify all file hashes exist in object store
    for file_entry in files_to_restore:
        file_hash = file_entry.get('hash')
        if not file_hash:
            print(f"Error: Commit corrupted (missing hash for {file_entry.get('path')})")
            return 1
        
        if not object_store.exists(file_hash):
            print(f"Error: Object not found: {file_hash}")
            print(f"       Required for: {file_entry.get('path')}")
            return 1
    
    # Build set of files that SHOULD exist after checkout
    target_files = set(tree_state.keys())
    
    # Find files that need to be removed
    # Compare against current HEAD tree state (not the empty index)
    from ofs.core.refs import resolve_head
    current_head = resolve_head(repo.ofs_dir)
    files_to_remove = set()
    
    if current_head:
        # Build current tree state from HEAD
        current_tree_state = build_tree_state(current_head, repo.commits_dir)
        
        for path in current_tree_state.keys():
            if path not in target_files:
                files_to_remove.add(path)
    
    # Restore files
    restored_count = 0
    removed_count = 0
    
    for file_entry in files_to_restore:
        path = file_entry.get('path')
        file_hash = file_entry.get('hash')
        
        if not path or not file_hash:
            continue
        
        file_path = repo_root / path
        
        # Restore file
        try:
            # Retrieve content from object store
            content = object_store.retrieve(file_hash)
            
            # Verify hash
            from ofs.utils.hash.compute_bytes import compute_hash
            actual_hash = compute_hash(content)
            if actual_hash != file_hash:
                print(f"Error: Hash mismatch for {path}")
                return 1
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_bytes(content)
            restored_count += 1
            
        except Exception as e:
            print(f"Error: Failed to restore {path}: {e}")
            return 1
    
    # Remove files that shouldn't exist in target commit
    for path in files_to_remove:
        file_path = repo_root / path
        if file_path.exists():
            try:
                file_path.unlink()
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {path}: {e}")
    
    # Update index to match commit
    try:
        index = Index(repo.index_file)
        index.clear()
        
        # Add all files from tree state to index
        for file_entry in files_to_restore:
            index.add(
                file_entry['path'],
                file_entry['hash'],
                {
                    'size': file_entry.get('size', 0),
                    'mode': file_entry.get('mode', '100644'),
                    'mtime': 0  # Will be updated on next add
                }
            )
    except Exception as e:
        print(f"Warning: Failed to update index: {e}")
    
    # Update HEAD (detached HEAD state)
    try:
        update_head(repo.ofs_dir, commit_id, detached=True)
    except Exception as e:
        print(f"Error: Failed to update HEAD: {e}")
        return 1
    
    # Print confirmation
    message = commit.get('message', '')
    print(f"[OK] Checked out to commit {commit_id} \"{message}\"")
    print(f"  {restored_count} file(s) restored")
    if removed_count > 0:
        print(f"  {removed_count} file(s) removed")
    
    # Show if we discarded uncommitted changes
    if force:
        index = Index(repo.index_file)
        if index.has_changes():
            print(f"  [WARNING] Uncommitted changes were discarded")
    
    return 0
