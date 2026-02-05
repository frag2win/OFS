"""ofs diff command implementation.

This module implements the 'ofs diff' command to show changes between different states.
"""

from pathlib import Path
from typing import Optional, Dict

from ofs.core.repository.init import Repository
from ofs.core.index.manager import Index
from ofs.core.objects.store import ObjectStore
from ofs.core.commits import load_commit, list_commits
from ofs.core.refs import resolve_head
from ofs.utils.diff import compute_file_diff, format_diff_header, is_binary
from ofs.commands.checkout.execute import build_tree_state


def execute(
    commit1: Optional[str] = None,
    commit2: Optional[str] = None,
    cached: bool = False,
    repo_root: Path = None
) -> int:
    """Execute the 'ofs diff' command.
    
    Scenarios:
    - No args: working dir vs staged (unstaged changes)
    - --cached: staged vs HEAD (staged changes)
    - <commit>: working dir vs commit
    - <commit1> <commit2>: commit vs commit
    
    Args:
        commit1: First commit ID (optional)
        commit2: Second commit ID (optional)
        cached: Show staged changes vs HEAD
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
    
    # Determine diff scenario and execute
    try:
        if commit1 and commit2:
            # Commit vs commit
            return _diff_commits(repo, commit1, commit2)
        elif commit1:
            # Working vs commit
            return _diff_working_vs_commit(repo, commit1, repo_root)
        elif cached:
            # Staged vs HEAD
            return _diff_staged_vs_head(repo, repo_root)
        else:
            # Working vs staged (default)
            return _diff_working_vs_staged(repo, repo_root)
            
    except Exception as e:
        print(f"Error computing diff: {e}")
        return 1


def _diff_working_vs_staged(repo: Repository, repo_root: Path) -> int:
    """Show unstaged changes (working directory vs staging area).
    
    Args:
        repo: Repository instance
        repo_root: Repository root path
        
    Returns:
        Exit code
    """
    index = Index(repo.index_file)
    staged_entries = {e['path']: e for e in index.get_entries()}
    
    if not staged_entries:
        print("No files staged. Use 'ofs add <file>' to stage changes.")
        return 0
    
    object_store = ObjectStore(repo.ofs_dir)
    has_changes = False
    
    # Check staged files for modifications
    for path, entry in staged_entries.items():
        file_path = repo_root / path
        
        # File exists in working directory
        if file_path.exists():
            working_content = file_path.read_bytes()
            staged_content = object_store.retrieve(entry['hash'])
            
            if working_content != staged_content:
                has_changes = True
                _print_file_diff(
                    staged_content,
                    working_content,
                    path,
                    path,
                    "modified"
                )
        else:
            # File deleted in working directory
            has_changes = True
            print(f"diff --ofs a/{path} b/{path}")
            print(f"deleted file: {path}")
            print()
    
    if not has_changes:
        print("No unstaged changes")
    
    return 0


def _diff_staged_vs_head(repo: Repository, repo_root: Path) -> int:
    """Show staged changes (staging area vs HEAD commit).
    
    Args:
        repo: Repository instance
        repo_root: Repository root path
        
    Returns:
        Exit code
    """
    # Get HEAD commit
    head_commit_id = resolve_head(repo.ofs_dir)
    
    if not head_commit_id:
        # No commits yet, show all staged files as new
        index = Index(repo.index_file)
        staged_entries = index.get_entries()
        
        if not staged_entries:
            print("No changes staged for commit")
            return 0
        
        object_store = ObjectStore(repo.ofs_dir)
        for entry in staged_entries:
            content = object_store.retrieve(entry['hash'])
            _print_file_diff(
                b'',  # No old content
                content,
                entry['path'],
                entry['path'],
                "new"
            )
        return 0
    
    # Compare staged vs HEAD commit
    head_tree = build_tree_state(head_commit_id, repo.commits_dir)
    index = Index(repo.index_file)
    staged_entries = {e['path']: e for e in index.get_entries()}
    
    object_store = ObjectStore(repo.ofs_dir)
    has_changes = False
    
    # Check for modifications and additions
    for path, staged_entry in staged_entries.items():
        if path in head_tree:
            # File exists in HEAD, check if modified
            head_entry = head_tree[path]
            if staged_entry['hash'] != head_entry['hash']:
                has_changes = True
                head_content = object_store.retrieve(head_entry['hash'])
                staged_content = object_store.retrieve(staged_entry['hash'])
                _print_file_diff(
                    head_content,
                    staged_content,
                    path,
                    path,
                    "modified"
                )
        else:
            # New file in staged
            has_changes = True
            staged_content = object_store.retrieve(staged_entry['hash'])
            _print_file_diff(
                b'',
                staged_content,
                path,
                path,
                "new"
            )
    
    # Check for deletions (in HEAD but not staged)
    for path in head_tree:
        if path not in staged_entries:
            has_changes = True
            print(f"diff --ofs a/{path} b/{path}")
            print(f"deleted file: {path}")
            print()
    
    if not has_changes:
        print("No changes staged for commit")
    
    return 0


def _diff_working_vs_commit(repo: Repository, commit_id: str, repo_root: Path) -> int:
    """Show changes between working directory and a commit.
    
    Args:
        repo: Repository instance
        commit_id: Commit ID to compare against
        repo_root: Repository root path
        
    Returns:
        Exit code
    """
    # Load commit
    commit = load_commit(commit_id, repo.commits_dir)
    if not commit:
        print(f"Error: Commit '{commit_id}' not found")
        return 1
    
    # Build tree state from commit
    commit_tree = build_tree_state(commit_id, repo.commits_dir)
    object_store = ObjectStore(repo.ofs_dir)
    
    # Collect all paths (from commit and working directory)
    all_paths = set(commit_tree.keys())
    
    # Add working directory files (excluding ignored)
    from ofs.core.working_tree.scan import scan_working_tree
    working_files = scan_working_tree(repo_root, repo)
    all_paths.update(f.relative_to(repo_root).as_posix() for f in working_files)
    
    has_changes = False
    
    for path in sorted(all_paths):
        file_path = repo_root / path
        in_commit = path in commit_tree
        in_working = file_path.exists()
        
        if in_commit and in_working:
            # Check if modified
            commit_content = object_store.retrieve(commit_tree[path]['hash'])
            working_content = file_path.read_bytes()
            
            if commit_content != working_content:
                has_changes = True
                _print_file_diff(
                    commit_content,
                    working_content,
                    path,
                    path,
                    "modified"
                )
        elif in_commit and not in_working:
            # Deleted in working
            has_changes = True
            print(f"diff --ofs a/{path} b/{path}")
            print(f"deleted file: {path}")
            print()
        elif not in_commit and in_working:
            # New in working
            has_changes = True
            working_content = file_path.read_bytes()
            _print_file_diff(
                b'',
                working_content,
                path,
                path,
                "new"
            )
    
    if not has_changes:
        print(f"No differences between working directory and commit {commit_id}")
    
    return 0


def _diff_commits(repo: Repository, commit1: str, commit2: str) -> int:
    """Show changes between two commits.
    
    Args:
        repo: Repository instance
        commit1: First commit ID
        commit2: Second commit ID
        
    Returns:
        Exit code
    """
    # Load commits
    c1 = load_commit(commit1, repo.commits_dir)
    c2 = load_commit(commit2, repo.commits_dir)
    
    if not c1:
        print(f"Error: Commit '{commit1}' not found")
        return 1
    if not c2:
        print(f"Error: Commit '{commit2}' not found")
        return 1
    
    # Build tree states
    tree1 = build_tree_state(commit1, repo.commits_dir)
    tree2 = build_tree_state(commit2, repo.commits_dir)
    
    # Collect all paths
    all_paths = set(tree1.keys()) | set(tree2.keys())
    
    object_store = ObjectStore(repo.ofs_dir)
    has_changes = False
    
    for path in sorted(all_paths):
        in_tree1 = path in tree1
        in_tree2 = path in tree2
        
        if in_tree1 and in_tree2:
            # Check if modified
            if tree1[path]['hash'] != tree2[path]['hash']:
                has_changes = True
                content1 = object_store.retrieve(tree1[path]['hash'])
                content2 = object_store.retrieve(tree2[path]['hash'])
                _print_file_diff(
                    content1,
                    content2,
                    path,
                    path,
                    "modified"
                )
        elif in_tree1 and not in_tree2:
            # Deleted in tree2
            has_changes = True
            print(f"diff --ofs a/{path} b/{path}")
            print(f"deleted file: {path}")
            print()
        elif not in_tree1 and in_tree2:
            # New in tree2
            has_changes = True
            content2 = object_store.retrieve(tree2[path]['hash'])
            _print_file_diff(
                b'',
                content2,
                path,
                path,
                "new"
            )
    
    if not has_changes:
        print(f"No differences between commits {commit1} and {commit2}")
    
    return 0


def _print_file_diff(
    old_content: bytes,
    new_content: bytes,
    old_path: str,
    new_path: str,
    action: str = None
):
    """Print diff for a single file.
    
    Args:
        old_content: Old file content
        new_content: New file content
        old_path: Old file path
        new_path: New file path
        action: Action (new, deleted, modified)
    """
    # Print header
    header = format_diff_header(old_path, new_path, action)
    for line in header:
        print(line)
    
    # Compute and print diff
    diff_lines = compute_file_diff(
        old_content,
        new_content,
        f"a/{old_path}",
        f"b/{new_path}"
    )
    
    for line in diff_lines:
        print(line)
    
    print()  # Empty line between files
