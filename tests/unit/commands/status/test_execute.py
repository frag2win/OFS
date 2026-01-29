"""Tests for ofs status command."""

import pytest
from pathlib import Path
from ofs.commands.status import execute
from ofs.commands.add import execute as add_execute
from ofs.core.repository.init import Repository


def test_status_clean_repository(tmp_repo):
    """Test status in a clean repository."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Run status
    exit_code = execute(tmp_repo)
    
    assert exit_code == 0


def test_status_with_staged_files(tmp_repo, capsys):
    """Test status shows staged files."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create and add a file
    test_file = tmp_repo / "test.txt"
    test_file.write_text("Hello")
    add_execute(["test.txt"], tmp_repo)
    
    # Run status
    exit_code = execute(tmp_repo)
    
    assert exit_code == 0
    
    # Check output
    captured = capsys.readouterr()
    assert "Changes to be committed" in captured.out
    assert "test.txt" in captured.out


def test_status_with_modified_files(tmp_repo, capsys):
    """Test status detects modified files."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create and add a file
    test_file = tmp_repo / "test.txt"
    test_file.write_text("Version 1")
    add_execute(["test.txt"], tmp_repo)
    
    # Modify the file
    test_file.write_text("Version 2")
    
    # Run status
    exit_code = execute(tmp_repo)
    
    assert exit_code == 0
    
    # Check output
    captured = capsys.readouterr()
    assert "Changes not staged" in captured.out or "modified" in captured.out


def test_status_with_untracked_files(tmp_repo, capsys):
    """Test status shows untracked files."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create a file but don't add it
    test_file = tmp_repo / "untracked.txt"
    test_file.write_text("Untracked")
    
    # Run status
    exit_code = execute(tmp_repo)
    
    assert exit_code == 0
    
    # Check output
    captured = capsys.readouterr()
    assert "Untracked files" in captured.out
    assert "untracked.txt" in captured.out


def test_status_without_repo(tmp_path):
    """Test status when not in a repository."""
    # Don't initialize repository
    
    # Run status
    exit_code = execute(tmp_path)
    
    assert exit_code == 1  # Should fail


def test_status_mixed_states(tmp_repo, capsys):
    """Test status with files in different states."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create different files
    staged_file = tmp_repo / "staged.txt"
    staged_file.write_text("Staged")
    add_execute(["staged.txt"], tmp_repo)
    
    modified_file = tmp_repo / "modified.txt"
    modified_file.write_text("Version 1")
    add_execute(["modified.txt"], tmp_repo)
    modified_file.write_text("Version 2")  # Modify after staging
    
    untracked_file = tmp_repo / "untracked.txt"
    untracked_file.write_text("Untracked")
    
    # Run status
    exit_code = execute(tmp_repo)
    
    assert exit_code == 0
    
    # Check output contains all categories
    captured = capsys.readouterr()
    assert "staged.txt" in captured.out
    assert "modified.txt" in captured.out
    assert "untracked.txt" in captured.out
