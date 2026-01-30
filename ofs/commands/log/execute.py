"""ofs log command implementation.

This module implements the 'ofs log' command to view commit history.
"""

from pathlib import Path
from typing import Optional

from ofs.core.repository.init import Repository
from ofs.core.commits import list_commits


def execute(
    limit: Optional[int] = None,
    oneline: bool = False,
    repo_root: Path = None
) -> int:
    """Execute the 'ofs log' command.
    
    Args:
        limit: Maximum number of commits to show
        oneline: Use compact format
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
    
    # Load commits
    commits = list_commits(repo.commits_dir)
    
    # Check if any commits exist
    if not commits:
        print("No commits yet")
        print("Hint: Use 'ofs commit -m \"message\"' to create your first commit")
        return 0
    
    # Apply limit if specified
    if limit and limit > 0:
        commits = commits[:limit]
    
    # Display commits
    if oneline:
        _print_oneline(commits)
    else:
        _print_full(commits)
    
    return 0


def _print_full(commits: list):
    """Print commits in full format.
    
    Args:
        commits: List of commit objects
    """
    for i, commit in enumerate(commits):
        print(f"Commit {commit['id']}")
        print(f"Author: {commit.get('author', 'unknown')}")
        
        # Parse timestamp
        timestamp = commit.get('timestamp', '')
        if timestamp:
            # Format: 2026-01-30T20:30:45.123456Z -> 2026-01-30 20:30:45
            date_part = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
            time_part = timestamp.split('T')[1][:8] if 'T' in timestamp else ''
            print(f"Date:   {date_part} {time_part}")
        
        print()
        print(f"    {commit.get('message', '')}")
        print()
        
        # Show file changes
        files = commit.get('files', [])
        if files:
            print("    Changes:")
            for file in files:
                action = file.get('action', 'unknown')
                path = file.get('path', '')
                size = file.get('size', 0)
                
                # Action symbol
                symbol = {
                    'added': '+',
                    'modified': 'M',
                    'deleted': '-'
                }.get(action, '?')
                
                print(f"      {symbol} {path} ({size} bytes)")
            print()
        
        # Add separator between commits (except last)
        if i < len(commits) - 1:
            print()


def _print_oneline(commits: list):
    """Print commits in oneline format.
    
    Args:
        commits: List of commit objects
    """
    for commit in commits:
        commit_id = commit['id']
        timestamp = commit.get('timestamp', '')
        author = commit.get('author', 'unknown')
        message = commit.get('message', '')
        
        # Format timestamp: 2026-01-30T20:30:45.123456Z -> 2026-01-30 20:30
        if timestamp and 'T' in timestamp:
            date_part = timestamp.split('T')[0]
            time_part = timestamp.split('T')[1][:5]  # HH:MM
            short_timestamp = f"{date_part} {time_part}"
        else:
            short_timestamp = timestamp[:16] if len(timestamp) >= 16 else timestamp
        
        # Format: 003 2026-01-30 20:30 jsmith  Add authentication
        print(f"{commit_id} {short_timestamp} {author:<10} {message}")
