"""Tests for listing commits."""

import pytest
from pathlib import Path
from ofs.core.commits.list import list_commits, get_commit_count
from ofs.core.commits import clear_commit_cache

class TestListCommits:
    """Tests for list_commits function."""
    
    def test_list_nonexistent_dir(self, tmp_path):
        """Nonexistent directory returns empty list."""
        assert list_commits(tmp_path / "missing") == []
    
    def test_list_empty_dir(self, tmp_path):
        """Empty directory returns empty list."""
        commits_dir = tmp_path / "commits"
        commits_dir.mkdir()
        assert list_commits(commits_dir) == []
    
    def test_list_corrupted_commit(self, tmp_path):
        """Corrupted commit files are skipped."""
        commits_dir = tmp_path / "commits"
        commits_dir.mkdir()
        
        # specific bad file
        bad = commits_dir / "001.json"
        bad.write_text("{invalid json")
        
        # valid file
        good = commits_dir / "002.json"
        good.write_text('{"id": "002", "message": "ok"}')
        
        commits = list_commits(commits_dir)
        assert len(commits) == 1
        assert commits[0]["id"] == "002"
    
    def test_list_sorting(self, tmp_path):
        """Commits are sorted by ID descending."""
        commits_dir = tmp_path / "commits"
        commits_dir.mkdir()
        
        (commits_dir / "001.json").write_text('{"id": "001"}')
        (commits_dir / "003.json").write_text('{"id": "003"}')
        (commits_dir / "002.json").write_text('{"id": "002"}')
        
        commits = list_commits(commits_dir)
        assert len(commits) == 3
        assert commits[0]["id"] == "003"
        assert commits[1]["id"] == "002"
        assert commits[2]["id"] == "001"

class TestGetCommitCount:
    """Tests for get_commit_count function."""
    
    def test_count_nonexistent_dir(self, tmp_path):
        """Nonexistent directory returns 0."""
        assert get_commit_count(tmp_path / "missing") == 0
    
    def test_count_files(self, tmp_path):
        """Counts .json files."""
        commits_dir = tmp_path / "commits"
        commits_dir.mkdir()
        
        (commits_dir / "001.json").touch()
        (commits_dir / "002.json").touch()
        (commits_dir / "readme.txt").touch() # Should be ignored
        
        assert get_commit_count(commits_dir) == 2
