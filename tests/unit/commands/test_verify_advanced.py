"""Additional tests for verify command."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.verify import execute as verify_execute
from ofs.core.verify.integrity import (
    verify_objects,
    verify_index,
    verify_commits,
    verify_refs,
    verify_repository,
)
from ofs.core.commits import clear_commit_cache


class TestVerifyObjects:
    """Tests for verify_objects function."""
    
    def test_verify_empty_objects(self, tmp_path):
        """Empty object store passes verification."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        success, errors = verify_objects(repo)
        assert success is True
        assert errors == []
    
    def test_verify_valid_objects(self, tmp_path):
        """Valid objects pass verification."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        file1 = tmp_path / "test.txt"
        file1.write_text("test content")
        add_execute([str(file1)], tmp_path)
        commit_execute("Test commit", tmp_path)
        clear_commit_cache()
        
        success, errors = verify_objects(repo)
        assert success is True
        assert errors == []


class TestVerifyIndex:
    """Tests for verify_index function."""
    
    def test_verify_no_index(self, tmp_path):
        """Missing index file handles gracefully."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        # Delete index file if exists
        if repo.index_file.exists():
            repo.index_file.unlink()
        
        success, errors = verify_index(repo)
        # Missing index should pass (no entries to verify)
        assert success is True
    
    def test_verify_valid_index(self, tmp_path):
        """Valid index passes verification."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        success, errors = verify_index(repo)
        assert success is True


class TestVerifyCommits:
    """Tests for verify_commits function."""
    
    def test_verify_no_commits(self, tmp_path):
        """Empty commits directory passes."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        success, errors = verify_commits(repo)
        assert success is True
    
    def test_verify_valid_commits(self, tmp_path):
        """Valid commits pass verification."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        file1 = tmp_path / "test.txt"
        file1.write_text("test")
        add_execute([str(file1)], tmp_path)
        commit_execute("Test", tmp_path)
        clear_commit_cache()
        
        success, errors = verify_commits(repo)
        assert success is True


class TestVerifyRefs:
    """Tests for verify_refs function."""
    
    def test_verify_refs_no_commits(self, tmp_path):
        """Refs verification with no commits."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        success, errors = verify_refs(repo)
        assert success is True
    
    def test_verify_refs_with_commits(self, tmp_path):
        """Refs verification with valid commits."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        file1 = tmp_path / "test.txt"
        file1.write_text("test")
        add_execute([str(file1)], tmp_path)
        commit_execute("Test", tmp_path)
        clear_commit_cache()
        
        success, errors = verify_refs(repo)
        assert success is True


class TestVerifyRepository:
    """Tests for verify_repository function."""
    
    def test_verify_empty_repository(self, tmp_path):
        """Empty repository passes all checks."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        success, results = verify_repository(tmp_path)
        assert isinstance(success, bool)
        assert isinstance(results, dict)
        assert "objects" in results
        assert "index" in results
        assert "commits" in results
        assert "refs" in results
    
    def test_verify_repository_with_commits(self, tmp_path):
        """Repository with commits passes verification."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        file1 = tmp_path / "test.txt"
        file1.write_text("test")
        add_execute([str(file1)], tmp_path)
        commit_execute("Test", tmp_path)
        clear_commit_cache()
        
        success, results = verify_repository(tmp_path)
        assert success is True
        # Check all components passed
        for key, result in results.items():
            assert result["success"] is True, f"{key} failed: {result.get('errors')}"


class TestVerifyCommand:
    """Tests for verify command execute."""
    
    def test_verify_command_valid_repo(self, tmp_path, capsys):
        """Verify command succeeds on valid repo."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        file1 = tmp_path / "test.txt"
        file1.write_text("test")
        add_execute([str(file1)], tmp_path)
        commit_execute("Test", tmp_path)
        clear_commit_cache()
        
        result = verify_execute(repo_root=tmp_path)
        assert result == 0
    
    def test_verify_command_not_initialized(self, tmp_path, capsys):
        """Verify command fails on non-repo."""
        result = verify_execute(repo_root=tmp_path)
        assert result == 1
