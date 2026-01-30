"""Integration tests for commit workflow."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.log import execute as log_execute
from ofs.commands.status import execute as status_execute


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository."""
    repo = Repository(tmp_path)
    repo.initialize()
    return tmp_path


def test_commit_basic_workflow(test_repo, capsys):
    """Test basic commit workflow: add -> commit -> log."""
    # Create a file
    test_file = test_repo / "test.txt"
    test_file.write_text("Hello world")
    
    # Add file
    result = add_execute([str(test_file)], test_repo)
    assert result == 0
    
    # Commit
    result = commit_execute("First commit", test_repo)
    assert result == 0
    
    captured = capsys.readouterr()
    assert "[main 001]" in captured.out
    assert "First commit" in captured.out
    
    # View log
    result = log_execute(repo_root=test_repo)
    assert result == 0
    
    captured = capsys.readouterr()
    assert "Commit 001" in captured.out
    assert "First commit" in captured.out


def test_commit_empty_index(test_repo, capsys):
    """Test committing with empty index fails."""
    result = commit_execute("Empty commit", test_repo)
    
    assert result == 1
    captured = capsys.readouterr()
    assert "Nothing to commit" in captured.out


def test_commit_short_message(test_repo, capsys):
    """Test committing with too-short message fails."""
    # Add a file first
    test_file = test_repo / "test.txt"
    test_file.write_text("Content")
    add_execute([str(test_file)], test_repo)
    
    result = commit_execute("ab", test_repo)
    
    assert result == 1
    captured = capsys.readouterr()
    assert "too short" in captured.out


def test_commit_clears_index(test_repo):
    """Test that commit clears the index."""
    # Create and add file
    test_file = test_repo / "test.txt"
    test_file.write_text("Content")
    add_execute([str(test_file)], test_repo)
    
    # Commit
    commit_execute("First commit", test_repo)
    
    # Check index is cleared
    from ofs.core.index.manager import Index
    repo = Repository(test_repo)
    index = Index(repo.index_file)
    
    assert not index.has_changes()


def test_multiple_commits(test_repo, capsys):
    """Test creating multiple commits."""
    # First commit
    file1 = test_repo / "file1.txt"
    file1.write_text("First")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Second commit
    file2 = test_repo / "file2.txt"
    file2.write_text("Second")
    add_execute([str(file2)], test_repo)
    commit_execute("Second commit", test_repo)
    
    # Third commit
    file3 = test_repo / "file3.txt"
    file3.write_text("Third")
    add_execute([str(file3)], test_repo)
    commit_execute("Third commit", test_repo)
    
    # Check log shows all commits
    log_execute(repo_root=test_repo)
    captured = capsys.readouterr()
    
    assert "Commit 001" in captured.out
    assert "Commit 002" in captured.out
    assert "Commit 003" in captured.out
    assert "First commit" in captured.out
    assert "Second commit" in captured.out
    assert "Third commit" in captured.out


def test_log_with_limit(test_repo, capsys):
    """Test log with -n limit."""
    # Create 3 commits
    for i in range(1, 4):
        file = test_repo / f"file{i}.txt"
        file.write_text(f"Content {i}")
        add_execute([str(file)], test_repo)
        commit_execute(f"Commit {i}", test_repo)
    
    # Get only last 2 commits
    log_execute(limit=2, repo_root=test_repo)
    captured = capsys.readouterr()
    
    assert "Commit 003" in captured.out
    assert "Commit 002" in captured.out
    assert "Commit 001" not in captured.out


def test_log_oneline(test_repo, capsys):
    """Test log --oneline format."""
    # Create a commit
    file1 = test_repo / "file1.txt"
    file1.write_text("Content")
    add_execute([str(file1)], test_repo)
    commit_execute("Test commit", test_repo)
    
    # Get oneline log
    log_execute(oneline=True, repo_root=test_repo)
    captured = capsys.readouterr()
    
    # Should be compact format (one line per commit)
    output = captured.out.strip()
    assert "001" in output
    assert "Test commit" in output
    # Should not contain multi-line commit format
    assert "Commit 001" not in output


def test_commit_updates_head(test_repo):
    """Test that commit updates HEAD."""
    from ofs.core.refs import resolve_head
    
    # Create commit
    file1 = test_repo / "file1.txt"
    file1.write_text("Content")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Check HEAD
    repo = Repository(test_repo)
    commit_id = resolve_head(repo.ofs_dir)
    
    assert commit_id == "001"
    
    # Create second commit
    file2 = test_repo / "file2.txt"
    file2.write_text("Content 2")
    add_execute([str(file2)], test_repo)
    commit_execute("Second commit", test_repo)
    
    # HEAD should be updated
    commit_id = resolve_head(repo.ofs_dir)
    assert commit_id == "002"


def test_commit_file_actions(test_repo, capsys):
    """Test that commits track file actions correctly."""
    # First commit - add file
    file1 = test_repo / "file1.txt"
    file1.write_text("Original")
    add_execute([str(file1)], test_repo)
    commit_execute("Add file1", test_repo)
    
    # Second commit - modify file
    file1.write_text("Modified")
    add_execute([str(file1)], test_repo)
    commit_execute("Modify file1", test_repo)
    
    # Check log shows actions
    log_execute(repo_root=test_repo)
    captured = capsys.readouterr()
    
    # First commit should show "added"
    assert "+ file1.txt" in captured.out or "added" in captured.out.lower()
    
    # Second commit should show "modified"
    assert "M file1.txt" in captured.out or "modified" in captured.out.lower()
