"""Tests for ofs add command."""

import pytest
from pathlib import Path
from ofs.commands.add import execute
from ofs.core.repository.init import Repository
from ofs.core.index.manager import Index


def test_add_single_file(tmp_repo):
    """Test adding a single file."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create a test file
    test_file = tmp_repo / "test.txt"
    test_file.write_text("Hello World")
    
    # Add the file
    exit_code = execute(["test.txt"], tmp_repo)
    
    assert exit_code == 0
    
    # Verify file is in index
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"


def test_add_directory(tmp_repo):
    """Test adding a directory recursively."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create a directory with files
    src_dir = tmp_repo / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "utils.py").write_text("def helper(): pass")
    
    # Add the directory
    exit_code = execute(["src"], tmp_repo)
    
    assert exit_code == 0
    
    # Verify files are in index
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    paths = {entry["path"] for entry in entries}
    
    assert "src/main.py" in paths or "src\\main.py" in paths
    assert "src/utils.py" in paths or "src\\utils.py" in paths


def test_add_respects_ignore_patterns(tmp_repo):
    """Test that ignored files are not added."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create files, some should be ignored
    (tmp_repo / "code.py").write_text("code")
    (tmp_repo / "temp.tmp").write_text("temp")  # Should be ignored
    (tmp_repo / "backup.swp").write_text("backup")  # Should be ignored
    
    # Add all files
    exit_code = execute(["."], tmp_repo)
    
    assert exit_code == 0
    
    # Verify only non-ignored file is in index
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    paths = {entry["path"] for entry in entries}
    
    assert "code.py" in paths
    assert "temp.tmp" not in paths
    assert "backup.swp" not in paths


def test_add_nonexistent_file(tmp_repo):
    """Test adding a file that doesn't exist."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Try to add non-existent file
    exit_code = execute(["nonexistent.txt"], tmp_repo)
    
    # Should exit with error code (no files added)
    assert exit_code == 1
    
    # Verify index is empty
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    assert len(entries) == 0


def test_add_without_repo(tmp_path):
    """Test adding when not in a repository."""
    # Don't initialize repository
    
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")
    
    # Try to add the file
    exit_code = execute(["test.txt"], tmp_path)
    
    assert exit_code == 1  # Should fail


def test_add_updates_existing_entry(tmp_repo):
    """Test that adding a file again updates the index entry."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create and add a file
    test_file = tmp_repo / "test.txt"
    test_file.write_text("Version 1")
    execute(["test.txt"], tmp_repo)
    
    # Modify and add again
    test_file.write_text("Version 2")
    exit_code = execute(["test.txt"], tmp_repo)
    
    assert exit_code == 0
    
    # Verify only one entry in index
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"
