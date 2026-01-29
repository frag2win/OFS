"""ofs add command implementation.

This module implements the 'ofs add' command to stage files for commit.
"""

from pathlib import Path
from typing import List
import sys

from ofs.core.repository.init import Repository
from ofs.core.objects.store import ObjectStore
from ofs.core.index.manager import Index
from ofs.utils.filesystem.walk_directory import walk_directory
from ofs.utils.filesystem.normalize_path import normalize_path, get_relative_path
from ofs.utils.ignore.patterns import should_ignore, load_ignore_patterns
from ofs.utils.validation.file_size import check_file_size
from ofs.utils.hash.compute_file import compute_file_hash


def execute(paths: List[str], repo_root: Path = None) -> int:
    """Execute the 'ofs add' command.
    
    Args:
        paths: List of file/directory paths to add
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
    
    # Load ignore patterns
    ignore_patterns = load_ignore_patterns(repo_root)
    
    # Expand paths to list of files
    files_to_add = []
    for path_str in paths:
        path = Path(path_str)
        
        # Normalize to absolute path
        abs_path = normalize_path(path, repo_root) if not path.is_absolute() else path
        
        if not abs_path.exists():
            print(f"Warning: Path does not exist: {path_str}")
            continue
        
        if abs_path.is_file():
            # Single file
            if not should_ignore(abs_path, ignore_patterns, repo_root):
                files_to_add.append(abs_path)
            else:
                print(f"Ignored: {path_str}")
        elif abs_path.is_dir():
            # Directory - walk recursively
            for file_path in walk_directory(abs_path, lambda p: should_ignore(p, ignore_patterns, repo_root)):
                files_to_add.append(file_path)
    
    if not files_to_add:
        print("No files to add")
        return 1  # Return error when no files found
    
    # Initialize object store and index
    object_store = ObjectStore(repo.ofs_dir)
    index = Index(repo.index_file)
    
    # Stage each file
    staged_count = 0
    skipped_count = 0
    
    for file_path in files_to_add:
        try:
            # Validate file size
            is_valid, error_msg = check_file_size(file_path)
            if not is_valid:
                print(f"Skipping {file_path.name}: {error_msg}")
                skipped_count += 1
                continue
            
            # Read and hash file
            content = file_path.read_bytes()
            file_hash = compute_file_hash(file_path)
            
            # Store in object store
            object_store.store(content)
            
            # Get relative path for index
            try:
                rel_path = get_relative_path(file_path, repo_root)
            except ValueError:
                print(f"Warning: {file_path} is outside repository, skipping")
                skipped_count += 1
                continue
            
            # Add to index
            metadata = {
                "size": len(content),
                "mode": "100644",  # Regular file
                "mtime": file_path.stat().st_mtime
            }
            index.add(str(rel_path), file_hash, metadata)
            
            staged_count += 1
            
        except Exception as e:
            print(f"Error adding {file_path.name}: {str(e)}")
            skipped_count += 1
            continue
    
    # Print summary
    if staged_count > 0:
        print(f"Staged {staged_count} file(s)")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} file(s)")
    
    return 0 if staged_count > 0 else 1
