"""Tests for filesystem utilities."""

import pytest
from pathlib import Path
from ofs.utils.filesystem.walk_directory import walk_directory
from ofs.utils.filesystem.normalize_path import normalize_path, get_relative_path


def test_walk_directory_simple(tmp_path):
    """Test walking a simple directory."""
    # Create files
    (tmp_path / "file1.txt").write_text("File 1")
    (tmp_path / "file2.txt").write_text("File 2")
    
    # Walk directory
    files = list(walk_directory(tmp_path))
    
    assert len(files) == 2
    assert tmp_path / "file1.txt" in files
    assert tmp_path / "file2.txt" in files


def test_walk_directory_recursive(tmp_path):
    """Test walking directory recursively."""
    # Create nested structure
    (tmp_path / "file1.txt").write_text("File 1")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("File 2")
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "file3.txt").write_text("File 3")
    
    # Walk directory
    files = list(walk_directory(tmp_path))
    
    assert len(files) == 3


def test_walk_directory_with_ignore(tmp_path):
    """Test walking directory with ignore function."""
    # Create files
    (tmp_path / "keep.txt").write_text("Keep")
    (tmp_path / "ignore.tmp").write_text("Ignore")
    
    # Walk with ignore function
    files = list(walk_directory(tmp_path, lambda p: p.suffix == ".tmp"))
    
    assert len(files) == 1
    assert tmp_path / "keep.txt" in files


def test_normalize_path(tmp_path):
    """Test path normalization."""
    # Create a file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test")
    
    # Normalize
    normalized = normalize_path(test_file)
    
    assert normalized.is_absolute()
    assert normalized.exists()


def test_get_relative_path(tmp_path):
    """Test getting relative path."""
    base = tmp_path
    file_path = tmp_path / "src" / "main.py"
    file_path.parent.mkdir()
    file_path.write_text("Code")
    
    # Get relative path
    rel_path = get_relative_path(file_path, base)
    
    assert str(rel_path) == "src/main.py" or str(rel_path) == "src\\main.py"


def test_get_relative_path_outside_base(tmp_path):
    """Test getting relative path for file outside base."""
    base = tmp_path / "repo"
    base.mkdir()
    file_path = tmp_path / "outside.txt"
    file_path.write_text("Outside")
    
    # Should raise ValueError
    with pytest.raises(ValueError):
        get_relative_path(file_path, base)
