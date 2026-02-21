"""Commit tree state reconstruction.

This module provides utilities for reconstructing the complete file tree
at any given commit by traversing the parent chain.
"""

from pathlib import Path
from typing import Dict

from ofs.core.commits.load import load_commit


def build_tree_state(commit_id: str, commits_dir: Path) -> Dict[str, dict]:
    """Build complete file tree state at a given commit.
    
    Uses parent-chain traversal: walks from target commit back to root
    via parent pointers, then applies commits oldest-first to build
    the complete tree.
    
    Complexity: O(D × F_avg) where D = chain depth, F_avg = avg files per commit.
    Uses commit cache via load_commit() to avoid redundant JSON parsing.
    
    Args:
        commit_id: Target commit ID
        commits_dir: Path to commits directory
        
    Returns:
        Dictionary mapping path -> file_entry (with hash, action, etc.)
    """
    # Walk parent chain from target back to root
    chain = []
    current_id = commit_id
    
    while current_id:
        commit = load_commit(current_id, commits_dir)
        if not commit:
            break
        chain.append(commit)
        current_id = commit.get('parent')
    
    # Apply commits from oldest to newest (reverse the chain)
    tree_state = {}  # path -> file_entry
    
    for commit in reversed(chain):
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
