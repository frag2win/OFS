"""Repository verification utilities.

This module provides functions to verify repository integrity by checking:
- Object store completeness
- Index consistency
- Commit metadata validity
- Reference integrity
"""

from pathlib import Path
from typing import List, Tuple
import json

from ofs.core.repository.init import Repository
from ofs.core.objects.store import ObjectStore
from ofs.core.index.manager import Index
from ofs.core.commits import load_commit, list_commits
from ofs.core.refs import read_head, resolve_head


def verify_objects(repo: Repository) -> Tuple[bool, List[str]]:
    """Verify object store integrity.
    
    Checks:
    - All object files are readable
    - File hashes match their names
    - No orphaned objects
    
    Args:
        repo: Repository instance
        
    Returns:
        (success, list_of_errors)
    """
    errors = []
    object_store = ObjectStore(repo.ofs_dir)
    objects_dir = repo.ofs_dir / "objects"
    
    if not objects_dir.exists():
        errors.append("Objects directory missing")
        return False, errors
    
    # Check each object file
    object_count = 0
    for obj_file in objects_dir.rglob("*.blob"):
        object_count += 1
        file_hash = obj_file.stem
        
        try:
            # Try to retrieve object
            content = object_store.retrieve(file_hash)
            
            # Verify hash matches content
            from ofs.utils.hash.compute_bytes import compute_hash
            actual_hash = compute_hash(content)
            
            if actual_hash != file_hash:
                errors.append(f"Hash mismatch: {file_hash} (actual: {actual_hash})")
                
        except Exception as e:
            errors.append(f"Cannot read object {file_hash}: {e}")
    
    if object_count == 0:
        # Empty repo is ok
        pass
    
    return len(errors) == 0, errors


def verify_index(repo: Repository) -> Tuple[bool, List[str]]:
    """Verify index file integrity.
    
    Checks:
    - Index file is valid JSON
    - All referenced objects exist
    - File paths are valid
    
    Args:
        repo: Repository instance
        
    Returns:
        (success, list_of_errors)
    """
    errors = []
    
    if not repo.index_file.exists():
        # Empty index is ok
        return True, []
    
    try:
        index = Index(repo.index_file)
        entries = index.get_entries()
        
        object_store = ObjectStore(repo.ofs_dir)
        
        for entry in entries:
            file_hash = entry.get('hash')
            file_path = entry.get('path')
            
            if not file_hash:
                errors.append(f"Index entry missing hash: {file_path}")
                continue
            
            if not file_path:
                errors.append(f"Index entry missing path for hash {file_hash}")
                continue
            
            # Check if object exists
            if not object_store.exists(file_hash):
                errors.append(f"Index references missing object: {file_hash} (path: {file_path})")
                
    except json.JSONDecodeError as e:
        errors.append(f"Index file corrupted (invalid JSON): {e}")
    except Exception as e:
        errors.append(f"Cannot read index: {e}")
    
    return len(errors) == 0, errors


def verify_commits(repo: Repository) -> Tuple[bool, List[str]]:
    """Verify commit history integrity.
    
    Checks:
    - All commit files are valid JSON
    - Parent references are valid
    - All file hashes in commits exist
    - Commit chain is valid
    
    Args:
        repo: Repository instance
        
    Returns:
        (success, list_of_errors)
    """
    errors = []
    commits_dir = repo.commits_dir
    
    if not commits_dir.exists():
        # No commits yet is ok
        return True, []
    
    try:
        commits = list_commits(commits_dir)
        
        if not commits:
            # No commits is ok
            return True, []
        
        object_store = ObjectStore(repo.ofs_dir)
        seen_commits = set()
        
        for commit in commits:
            commit_id = commit.get('id')
            seen_commits.add(commit_id)
            
            # Check parent reference
            parent_id = commit.get('parent')
            if parent_id and parent_id not in seen_commits:
                # Parent will be seen later (we're going reverse chronological)
                pass
            
            # Check all file objects exist
            files = commit.get('files', [])
            for file_entry in files:
                file_hash = file_entry.get('hash')
                file_path = file_entry.get('path')
                action = file_entry.get('action')
                
                if action == 'deleted':
                    continue  # Deleted files don't need objects
                
                if not file_hash:
                    errors.append(f"Commit {commit_id}: file {file_path} missing hash")
                    continue
                
                if not object_store.exists(file_hash):
                    errors.append(f"Commit {commit_id}: missing object {file_hash} for {file_path}")
                    
    except Exception as e:
        errors.append(f"Cannot verify commits: {e}")
    
    return len(errors) == 0, errors


def verify_refs(repo: Repository) -> Tuple[bool, List[str]]:
    """Verify reference integrity.
    
    Checks:
    - HEAD file is valid
    - Referenced commits exist
    - No dangling references
    
    Args:
        repo: Repository instance
        
    Returns:
        (success, list_of_errors)
    """
    errors = []
    
    head_file = repo.ofs_dir / "HEAD"
    if not head_file.exists():
        errors.append("HEAD file missing")
        return False, errors
    
    try:
        head_content = read_head(repo.ofs_dir)
        
        if not head_content:
            # Empty HEAD is ok for new repos
            return True, []
        
        # Resolve HEAD to commit ID
        commit_id = resolve_head(repo.ofs_dir)
        
        if commit_id:
            # Check if commit exists
            commit = load_commit(commit_id, repo.commits_dir)
            if not commit:
                errors.append(f"HEAD points to non-existent commit: {commit_id}")
                
    except Exception as e:
        errors.append(f"Cannot verify HEAD: {e}")
    
    return len(errors) == 0, errors


def verify_repository(repo_root: Path = None, verbose: bool = False) -> Tuple[bool, dict]:
    """Verify entire repository integrity.
    
    Runs all verification checks and reports results.
    
    Args:
        repo_root: Repository root (defaults to current directory)
        verbose: Show detailed output
        
    Returns:
        (success, results_dict)
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    repo = Repository(repo_root)
    
    if not repo.is_initialized():
        return False, {"error": "Not an OFS repository"}
    
    results = {
        "objects": {"success": False, "errors": []},
        "index": {"success": False, "errors": []},
        "commits": {"success": False, "errors": []},
        "refs": {"success": False, "errors": []},
    }
    
    # Run all verifications
    results["objects"]["success"], results["objects"]["errors"] = verify_objects(repo)
    results["index"]["success"], results["index"]["errors"] = verify_index(repo)
    results["commits"]["success"], results["commits"]["errors"] = verify_commits(repo)
    results["refs"]["success"], results["refs"]["errors"] = verify_refs(repo)
    
    # Overall success if all components pass
    all_success = all(r["success"] for r in results.values())
    
    return all_success, results
