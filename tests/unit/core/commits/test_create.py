"""Tests for commit creation utilities."""

import pytest
from pathlib import Path
from ofs.core.commits.create import (
    generate_commit_id,
    get_file_actions,
    create_commit_object,
    get_author_info,
)


def test_generate_commit_id_first(tmp_path):
    """Test generating first commit ID."""
    commits_dir = tmp_path / "commits"
    
    commit_id = generate_commit_id(commits_dir)
    
    assert commit_id == "001"


def test_generate_commit_id_sequential(tmp_path):
    """Test generating sequential commit IDs."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create some commit files
    (commits_dir / "001.json").write_text("{}")
    (commits_dir / "002.json").write_text("{}")
    
    commit_id = generate_commit_id(commits_dir)
    
    assert commit_id == "003"


def test_generate_commit_id_gaps(tmp_path):
    """Test generating ID with gaps in sequence."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create commits with gaps
    (commits_dir / "001.json").write_text("{}")
    (commits_dir / "005.json").write_text("{}")
    
    commit_id = generate_commit_id(commits_dir)
    
    # Should be max + 1
    assert commit_id == "006"


def test_get_file_actions_first_commit():
    """Test file actions for first commit (no parent)."""
    staged_files = [
        {"path": "file1.txt", "hash": "abc123"},
        {"path": "file2.txt", "hash": "def456"},
    ]
    
    files_with_actions = get_file_actions(staged_files, None)
    
    assert len(files_with_actions) == 2
    assert all(f["action"] == "added" for f in files_with_actions)


def test_get_file_actions_modified():
    """Test detecting modified files."""
    staged_files = [
        {"path": "file1.txt", "hash": "new_hash"},
    ]
    
    parent_commit = {
        "files": [
            {"path": "file1.txt", "hash": "old_hash", "action": "added"}
        ]
    }
    
    files_with_actions = get_file_actions(staged_files, parent_commit)
    
    assert len(files_with_actions) == 1
    assert files_with_actions[0]["action"] == "modified"


def test_get_file_actions_unchanged():
    """Test detecting unchanged files."""
    staged_files = [
        {"path": "file1.txt", "hash": "same_hash"},
    ]
    
    parent_commit = {
        "files": [
            {"path": "file1.txt", "hash": "same_hash", "action": "added"}
        ]
    }
    
    files_with_actions = get_file_actions(staged_files, parent_commit)
    
    assert len(files_with_actions) == 1
    assert files_with_actions[0]["action"] == "unchanged"


def test_get_file_actions_added():
    """Test detecting newly added files."""
    staged_files = [
        {"path": "file1.txt", "hash": "abc123"},
        {"path": "file2.txt", "hash": "def456"},
    ]
    
    parent_commit = {
        "files": [
            {"path": "file1.txt", "hash": "abc123", "action": "added"}
        ]
    }
    
    files_with_actions = get_file_actions(staged_files, parent_commit)
    
    # file1 unchanged, file2 added
    file2 = next(f for f in files_with_actions if f["path"] == "file2.txt")
    assert file2["action"] == "added"


def test_get_file_actions_deleted():
    """Test detecting deleted files."""
    staged_files = [
        {"path": "file1.txt", "hash": "abc123"},
    ]
    
    parent_commit = {
        "files": [
            {"path": "file1.txt", "hash": "abc123", "action": "added"},
            {"path": "file2.txt", "hash": "def456", "action": "added"},
        ]
    }
    
    files_with_actions = get_file_actions(staged_files, parent_commit)
    
    # Should detect file2 as deleted
    deleted_file = next(f for f in files_with_actions if f["path"] == "file2.txt")
    assert deleted_file["action"] == "deleted"


def test_create_commit_object():
    """Test creating commit object."""
    files = [
        {"path": "file1.txt", "hash": "abc123", "size": 100, "action": "added"}
    ]
    
    commit = create_commit_object(
        commit_id="003",
        parent_id="002",
        message="Test commit",
        author="testuser",
        email="test@example.com",
        files=files
    )
    
    assert commit["id"] == "003"
    assert commit["parent"] == "002"
    assert commit["message"] == "Test commit"
    assert commit["author"] == "testuser"
    assert commit["email"] == "test@example.com"
    assert "timestamp" in commit
    assert commit["files"] == files


def test_create_commit_object_first_commit():
    """Test creating first commit (no parent)."""
    commit = create_commit_object(
        commit_id="001",
        parent_id=None,
        message="First commit",
        author="testuser",
        email="test@example.com",
        files=[]
    )
    
    assert commit["id"] == "001"
    assert commit["parent"] is None


def test_get_author_info():
    """Test getting author info from environment."""
    author, email = get_author_info()
    
    # Should return something (from env or defaults)
    assert author
    assert email
    assert "@" in email
