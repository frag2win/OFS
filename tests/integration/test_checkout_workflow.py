"""Integration tests for checkout workflow."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.checkout import execute as checkout_execute


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository with some commits."""
    # Clear commit cache to avoid cross-test pollution
    from ofs.core.commits import clear_commit_cache
    clear_commit_cache()
    
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create first commit - only file1
    file1 = tmp_path / "file1.txt"
    file1.write_text("First version")
    add_execute([str(file1)], tmp_path)
    commit_execute("First commit", tmp_path)
    clear_commit_cache()  # Clear between commits
    
    # Create second commit - add file2, keep file1
    file2 = tmp_path / "file2.txt"
    file2.write_text("Second file")
    # Stage BOTH files to indicate file1 is still there
    add_execute([str(file1), str(file2)], tmp_path)
    commit_execute("Second commit", tmp_path)
    clear_commit_cache()  # Clear between commits
    
    # Create third commit - modify file1, keep file2
    file1.write_text("Modified version")
    # Stage BOTH files to indicate file2 is still there
    add_execute([str(file1), str(file2)], tmp_path)
    commit_execute("Third commit", tmp_path)
    
    # Clear cache to ensure fresh reads
    clear_commit_cache()
    
    return tmp_path


def test_checkout_to_previous_commit(test_repo):
    """Test checking out to a previous commit."""
    # Clear cache at start of test
    from ofs.core.commits import clear_commit_cache
    clear_commit_cache()
    
    # Checkout to commit 001
    result = checkout_execute("001", force=True, repo_root=test_repo)
    
    assert result == 0
    
    # Verify files are restored
    file1 = test_repo / "file1.txt"
    assert file1.exists()
    assert file1.read_text() == "First version"
    
    # file2 should not exist (added in commit 002)
    file2 = test_repo / "file2.txt"
    assert not file2.exists()


def test_checkout_restores_files(test_repo):
    """Test that checkout restores all files correctly."""
    # Checkout to commit 002
    result = checkout_execute("002", force=True, repo_root=test_repo)
    
    assert result == 0
    
    # Both files should exist
    file1 = test_repo / "file1.txt"
    file2 = test_repo / "file2.txt"
    
    assert file1.exists()
    assert file2.exists()
    assert file1.read_text() == "First version"  # Not modified yet
    assert file2.read_text() == "Second file"


def test_checkout_updates_head(test_repo):
    """Test that checkout updates HEAD."""
    from ofs.core.refs import read_head
    
    # Checkout to commit 001
    checkout_execute("001", force=True, repo_root=test_repo)
    
    # HEAD should be detached at 001
    repo = Repository(test_repo)
    head = read_head(repo.ofs_dir)
    
    assert head == "001"


def test_checkout_nonexistent_commit(test_repo, capsys):
    """Test checking out to nonexistent commit fails."""
    result = checkout_execute("999", force=True, repo_root=test_repo)
    
    assert result == 1
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower() or "Error" in captured.out


def test_checkout_back_and_forth(test_repo):
    """Test checking out between commits multiple times."""
    # Go to 001
    checkout_execute("001", force=True, repo_root=test_repo)
    file1 = test_repo / "file1.txt"
    assert file1.read_text() == "First version"
    
    # Go to 003
    checkout_execute("003", force=True, repo_root=test_repo)
    assert file1.read_text() == "Modified version"
    
    # Back to 002
    checkout_execute("002", force=True, repo_root=test_repo)
    assert file1.read_text() == "First version"
    file2 = test_repo / "file2.txt"
    assert file2.exists()


def test_checkout_with_uncommitted_changes(test_repo, monkeypatch):
    """Test checkout warns about uncommitted changes."""
    # Add a new file to index
    newfile = test_repo / "uncommitted.txt"
    newfile.write_text("Uncommitted")
    add_execute([str(newfile)], test_repo)
    
    # Simulate user saying "no" to checkout
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    result = checkout_execute("001", force=False, repo_root=test_repo)
    
    # Should cancel
    assert result == 1


def test_checkout_force_ignores_changes(test_repo):
    """Test checkout --force ignores uncommitted changes."""
    # Add a new file to index
    newfile = test_repo / "uncommitted.txt"
    newfile.write_text("Uncommitted")
    add_execute([str(newfile)], test_repo)
    
    # Force checkout should proceed without asking
    result = checkout_execute("001", force=True, repo_root=test_repo)
    
    assert result == 0
    
    # Should be at commit 001
    file1 = test_repo / "file1.txt"
    assert file1.read_text() == "First version"
