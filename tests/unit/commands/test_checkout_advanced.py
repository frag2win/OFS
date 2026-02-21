"""Additional tests for checkout functionality."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.checkout import execute as checkout_execute
from ofs.core.commits.tree import build_tree_state
from ofs.core.commits import clear_commit_cache


class TestBuildTreeState:
    """Tests for build_tree_state function."""
    
    @pytest.fixture
    def repo_with_commits(self, tmp_path):
        """Create a repository with commits."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        # Commit 1 - file1 only
        file1 = tmp_path / "file1.txt"
        file1.write_text("v1")
        add_execute([str(file1)], tmp_path)
        commit_execute("Commit 1", tmp_path)
        clear_commit_cache()
        
        # Commit 2 - add file2
        file2 = tmp_path / "file2.txt"
        file2.write_text("v1")
        add_execute([str(file1), str(file2)], tmp_path)
        commit_execute("Commit 2", tmp_path)
        clear_commit_cache()
        
        return repo
    
    def test_build_tree_state_first_commit(self, repo_with_commits):
        """Tree state at first commit has one file."""
        tree = build_tree_state("001", repo_with_commits.commits_dir)
        assert "file1.txt" in tree
        assert len(tree) == 1
    
    def test_build_tree_state_second_commit(self, repo_with_commits):
        """Tree state at second commit has two files."""
        tree = build_tree_state("002", repo_with_commits.commits_dir)
        assert "file1.txt" in tree
        assert "file2.txt" in tree
        assert len(tree) == 2
    
    def test_build_tree_state_returns_file_entries(self, repo_with_commits):
        """Tree state entries have required fields."""
        tree = build_tree_state("001", repo_with_commits.commits_dir)
        entry = tree.get("file1.txt")
        assert entry is not None
        assert "hash" in entry
        assert "path" in entry


class TestCheckoutEdgeCases:
    """Edge case tests for checkout."""
    
    def test_checkout_not_initialized(self, tmp_path):
        """Checkout fails on uninitialized repo."""
        result = checkout_execute("001", force=True, repo_root=tmp_path)
        assert result == 1
    
    def test_checkout_invalid_commit(self, tmp_path):
        """Checkout fails with invalid commit ID."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        result = checkout_execute("999", force=True, repo_root=tmp_path)
        assert result == 1
    
    def test_checkout_file_restoration(self, tmp_path):
        """Checkout restores file contents correctly."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        # Create and commit file
        file1 = tmp_path / "test.txt"
        file1.write_text("original content")
        add_execute([str(file1)], tmp_path)
        commit_execute("Initial", tmp_path)
        clear_commit_cache()
        
        # Modify and commit
        file1.write_text("modified content")
        add_execute([str(file1)], tmp_path)
        commit_execute("Modified", tmp_path)
        clear_commit_cache()
        
        # Checkout back to first
        result = checkout_execute("001", force=True, repo_root=tmp_path)
        assert result == 0
        assert file1.read_text() == "original content"


class TestCheckoutWithDeletions:
    """Tests for checkout handling file deletions."""
    
    def test_checkout_removes_new_files(self, tmp_path):
        """Checkout removes files not in target commit."""
        clear_commit_cache()
        repo = Repository(tmp_path)
        repo.initialize()
        
        # Commit 1 - only file1
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        add_execute([str(file1)], tmp_path)
        commit_execute("First", tmp_path)
        clear_commit_cache()
        
        # Commit 2 - add file2
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        add_execute([str(file1), str(file2)], tmp_path)
        commit_execute("Second", tmp_path)
        clear_commit_cache()
        
        # Checkout to first commit
        result = checkout_execute("001", force=True, repo_root=tmp_path)
        assert result == 0
        
        # file2 should be removed
        assert not file2.exists()
        assert file1.exists()
