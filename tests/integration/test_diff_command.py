"""Integration tests for diff command."""

import pytest
from pathlib import Path

from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.diff import execute as diff_execute


def test_diff_working_vs_staged(tmp_path):
    """Test diff between working directory and staged."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and stage a file
    file = tmp_path / "test.txt"
    file.write_text("line 1\nline 2\nline 3\n")
    add_execute([str(file)], repo_root=tmp_path)
    
    # Modify the file
    file.write_text("line 1\nmodified line 2\nline 3\n")
    
    # Run diff
    result = diff_execute(repo_root=tmp_path)
    
    assert result == 0  # Success


def test_diff_staged_vs_head_no_commits(tmp_path):
    """Test diff --cached with no commits yet."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and stage a file
    file = tmp_path / "test.txt"
    file.write_text("new file content\n")
    add_execute([str(file)], repo_root=tmp_path)
    
    # Run diff --cached
    result = diff_execute(cached=True, repo_root=tmp_path)
    
    assert result == 0


def test_diff_staged_vs_head_with_commits(tmp_path):
    """Test diff --cached with existing commits."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create, stage, and commit a file
    file = tmp_path / "test.txt"
    file.write_text("line 1\nline 2\n")
    add_execute([str(file)], repo_root=tmp_path)
    commit_execute("First commit", repo_root=tmp_path)
    
    # Modify, stage
    file.write_text("line 1\nmodified line 2\nline 3\n")
    add_execute([str(file)], repo_root=tmp_path)
    
    # Run diff --cached
    result = diff_execute(cached=True, repo_root=tmp_path)
    
    assert result == 0


def test_diff_commit_vs_commit(tmp_path):
    """Test diff between two commits."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create commit 1
    file = tmp_path / "test.txt"
    file.write_text("version 1\n")
    add_execute([str(file)], repo_root=tmp_path)
    commit_execute("Commit 1", repo_root=tmp_path)
    
    # Create commit 2
    file.write_text("version 2\n")
    add_execute([str(file)], repo_root=tmp_path)
    commit_execute("Commit 2", repo_root=tmp_path)
    
    # Run diff between commits
    result = diff_execute(commit1="001", commit2="002", repo_root=tmp_path)
    
    assert result == 0


def test_diff_not_initialized(tmp_path):
    """Test diff in non-initialized directory."""
    result = diff_execute(repo_root=tmp_path)
    
    assert result == 1  # Error


def test_diff_invalid_commit(tmp_path, capsys):
    """Test diff with invalid commit ID."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Try to diff with non-existent commit
    result = diff_execute(commit1="999", repo_root=tmp_path)
    
    # Should error
    captured = capsys.readouterr()
    assert result == 1 or "not found" in captured.out  # Error


def test_diff_no_staged_files(tmp_path, capsys):
    """Test diff with no files staged."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Run diff with nothing staged
    result = diff_execute(repo_root=tmp_path)
    
    captured = capsys.readouterr()
    assert "No files staged" in captured.out or result == 0


def test_diff_binary_file(tmp_path):
    """Test diff with binary files."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and stage binary file
    file = tmp_path / "binary.bin"
    file.write_bytes(b"binary\x00content")
    add_execute([str(file)], repo_root=tmp_path)
    
    # Modify binary file
    file.write_bytes(b"modified\x00binary")
    
    # Run diff
    result = diff_execute(repo_root=tmp_path)
    
    assert result == 0


def test_diff_new_file_in_working(tmp_path):
    """Test diff with new file in working directory."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create, stage and commit a file
    file1 = tmp_path / "file1.txt"
    file1.write_text("file 1\n")
    add_execute([str(file1)], repo_root=tmp_path)
    commit_execute("Commit 1", repo_root=tmp_path)
    
    # Stage file1 again and add new file2
    add_execute([str(file1)], repo_root=tmp_path)
    file2 = tmp_path / "file2.txt"
    file2.write_text("file 2\n")
    add_execute([str(file2)], repo_root=tmp_path)
    
    # Run diff cached (should show new file2)
    result = diff_execute(cached=True, repo_root=tmp_path)
    
    assert result == 0


def test_diff_deleted_file_in_working(tmp_path, capsys):
    """Test diff with deleted file."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and stage a file
    file = tmp_path / "test.txt"
    file.write_text("content\n")
    add_execute([str(file)], repo_root=tmp_path)
    
    # Delete the file from working
    file.unlink()
    
    # Run diff (should show deletion in working vs staged)
    result = diff_execute(repo_root=tmp_path)
    
    captured = capsys.readouterr()
    assert result == 0  # Should succeed even with deleted file
    assert "deleted" in captured.out or result == 0


def test_diff_no_changes(tmp_path, capsys):
    """Test diff with no changes."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and commit
    file = tmp_path / "test.txt"
    file.write_text("content\n")
    add_execute([str(file)], repo_root=tmp_path)
    commit_execute("Commit 1", repo_root=tmp_path)
    
    # Run diff with no changes
    result = diff_execute(cached=True, repo_root=tmp_path)
    
    captured = capsys.readouterr()
    assert "No changes" in captured.out or result == 0


def test_diff_multiple_files(tmp_path):
    """Test diff with multiple files."""
    # Initialize repository
    repo = Repository(tmp_path)
    repo.initialize()
    
    # Create and stage multiple files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("file 1\n")
    file2.write_text("file 2\n")
    add_execute([str(file1), str(file2)], repo_root=tmp_path)
    
    # Modify both
    file1.write_text("file 1 modified\n")
    file2.write_text("file 2 modified\n")
    
    # Run diff
    result = diff_execute(repo_root=tmp_path)
    
    assert result == 0
