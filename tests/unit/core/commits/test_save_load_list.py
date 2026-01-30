"""Tests for commit save/load utilities."""

import pytest
from pathlib import Path
import json
from ofs.core.commits.save import save_commit
from ofs.core.commits.load import load_commit, get_parent_commit
from ofs.core.commits.list import list_commits, get_commit_count


def test_save_commit(tmp_path):
    """Test saving commit to disk."""
    commits_dir = tmp_path / "commits"
    
    commit_obj = {
        "id": "003",
        "parent": "002",
        "message": "Test commit",
        "author": "testuser",
        "files": []
    }
    
    save_commit(commit_obj, commits_dir)
    
    commit_file = commits_dir / "003.json"
    assert commit_file.exists()
    
    # Verify content
    saved_data = json.loads(commit_file.read_text())
    assert saved_data["id"] == "003"
    assert saved_data["message"] == "Test commit"


def test_load_commit(tmp_path):
    """Test loading commit from disk."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create commit file
    commit_data = {
        "id": "002",
        "parent": "001",
        "message": "Second commit"
    }
    (commits_dir / "002.json").write_text(json.dumps(commit_data))
    
    commit = load_commit("002", commits_dir)
    
    assert commit is not None
    assert commit["id"] == "002"
    assert commit["message"] == "Second commit"


def test_load_commit_not_found(tmp_path):
    """Test loading non-existent commit."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    commit = load_commit("999", commits_dir)
    
    assert commit is None


def test_load_commit_corrupted(tmp_path):
    """Test loading corrupted commit file."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create invalid JSON
    (commits_dir / "003.json").write_text("invalid json{")
    
    commit = load_commit("003", commits_dir)
    
    assert commit is None


def test_get_parent_commit(tmp_path):
    """Test getting parent commit."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create parent commit
    parent_data = {"id": "001", "parent": None, "message": "First"}
    (commits_dir / "001.json").write_text(json.dumps(parent_data))
    
    # Create child commit
    child_data = {"id": "002", "parent": "001", "message": "Second"}
    (commits_dir / "002.json").write_text(json.dumps(child_data))
    
    parent = get_parent_commit("002", commits_dir)
    
    assert parent is not None
    assert parent["id"] == "001"


def test_get_parent_commit_first_commit(tmp_path):
    """Test getting parent of first commit (no parent)."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    commit_data = {"id": "001", "parent": None}
    (commits_dir / "001.json").write_text(json.dumps(commit_data))
    
    parent = get_parent_commit("001", commits_dir)
    
    assert parent is None


def test_list_commits(tmp_path):
    """Test listing all commits."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create multiple commits
    for i in range(1, 4):
        commit_data = {"id": f"00{i}", "message": f"Commit {i}"}
        (commits_dir / f"00{i}.json").write_text(json.dumps(commit_data))
    
    commits = list_commits(commits_dir)
    
    assert len(commits) == 3
    # Should be in reverse chronological order
    assert commits[0]["id"] == "003"
    assert commits[1]["id"] == "002"
    assert commits[2]["id"] == "001"


def test_list_commits_empty(tmp_path):
    """Test listing commits when none exist."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    commits = list_commits(commits_dir)
    
    assert commits == []


def test_get_commit_count(tmp_path):
    """Test getting commit count."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    # Create commits
    (commits_dir / "001.json").write_text("{}")
    (commits_dir / "002.json").write_text("{}")
    
    count = get_commit_count(commits_dir)
    
    assert count == 2


def test_get_commit_count_zero(tmp_path):
    """Test commit count when no commits exist."""
    commits_dir = tmp_path / "commits"
    commits_dir.mkdir()
    
    count = get_commit_count(commits_dir)
    
    assert count == 0
