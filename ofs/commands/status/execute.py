"""ofs status command implementation.

This module implements the 'ofs status' command to show repository status.
"""

from pathlib import Path
from typing import List, Set, Dict

from ofs.core.repository.init import Repository
from ofs.core.index.manager import Index
from ofs.core.working_tree.scan import scan_working_tree
from ofs.core.working_tree.compare import has_file_changed
from ofs.utils.ignore.patterns import load_ignore_patterns


def execute(repo_root: Path = None) -> int:
    """Execute the 'ofs status' command.
    
    Args:
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
    
    # Load index
    index = Index(repo.index_file)
    staged_entries = index.get_entries()
    
    # Get all files in working directory
    ignore_patterns = load_ignore_patterns(repo_root)
    working_files = scan_working_tree(repo_root, ignore_patterns)
    
    # Build sets for comparison
    staged_paths = {Path(entry["path"]) for entry in staged_entries}
    
    # Categorize files
    staged: List[Path] = []
    modified: List[Path] = []
    untracked: List[Path] = []
    
    # Check staged files
    for entry in staged_entries:
        file_path = Path(entry["path"])
        staged.append(file_path)
        
        # Check if staged file has been modified
        abs_path = repo_root / file_path
        if abs_path.exists():
            if has_file_changed(abs_path, entry["hash"]):
                modified.append(file_path)
    
    # Find untracked files
    for file_path in working_files:
        if file_path not in staged_paths:
            untracked.append(file_path)
    
    # Print status
    _print_status(staged, modified, untracked)
    
    return 0


def _print_status(staged: List[Path], modified: List[Path], untracked: List[Path]):
    """Print formatted status output.
    
    Args:
        staged: List of staged files (new or updated)
        modified: List of staged files that have been modified since staging
        untracked: List of files not staged
    """
    from ofs.utils.ui.color import green, red
    
    has_changes = bool(staged or modified or untracked)
    
    if not has_changes:
        print("Nothing to commit, working tree clean")
        return
    
    # Staged files (ready to commit)
    if staged:
        print("Changes to be committed:")
        print("  (use \"ofs reset <file>...\" to unstage)")
        print()
        for file_path in sorted(staged):
            # Check if file was modified after staging
            if file_path in modified:
                print(green(f"  modified:   {file_path}"))
            else:
                print(green(f"  new file:   {file_path}"))
        print()
    
    # Modified files (staged but changed since)
    if modified:
        print("Changes not staged for commit:")
        print("  (use \"ofs add <file>...\" to update what will be committed)")
        print()
        for file_path in sorted(modified):
            print(red(f"  modified:   {file_path}"))
        print()
    
    # Untracked files
    if untracked:
        print("Untracked files:")
        print("  (use \"ofs add <file>...\" to include in what will be committed)")
        print()
        for file_path in sorted(untracked):
            print(red(f"  {file_path}"))
        print()
