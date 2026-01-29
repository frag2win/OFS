"""Tests for working tree utilities."""

import pytest
from pathlib import Path
from ofs.core.working_tree.scan import scan_working_tree
from ofs.core.working_tree.compare import has_file_changed


def test_scan_working_tree_basic(tmp_path):
    """Test scanning working tree finds files."""
    # Create files
    (tmp_path / "file1.txt").write_text("Content 1")
    (tmp_path / "file2.txt").write_text("Content 2")
    
    # Scan
    files = scan_working_tree(tmp_path, [])
    
    assert len(files) >= 2
    assert Path("file1.txt") in files
    assert Path("file2.txt") in files


def test_scan_working_tree_with_ignore(tmp_path):
    """Test scanning respects ignore patterns."""
    # Create files
    (tmp_path / "keep.txt").write_text("Keep")
    (tmp_path / "ignore.tmp").write_text("Ignore")
    
    # Scan with ignore pattern
    patterns = ["*.tmp"]
    files = scan_working_tree(tmp_path, patterns)
    
    assert Path("keep.txt") in files
    assert Path("ignore.tmp") not in files


def test_has_file_changed_no_change(tmp_path):
    """Test detecting when file hasn't changed."""
    from ofs.utils.hash.compute_file import compute_file_hash
    
    file_path = tmp_path / "file.txt"
    file_path.write_text("Original content")
    
    expected_hash = compute_file_hash(file_path)
    
    # File hasn't changed
    changed = has_file_changed(file_path, expected_hash)
    
    assert changed is False


def test_has_file_changed_modified(tmp_path):
    """Test detecting when file has changed."""
    file_path = tmp_path / "file.txt"
    file_path.write_text("Original content")
    
    # Use wrong hash
    wrong_hash = "0" * 64
    
    # File has changed
    changed = has_file_changed(file_path, wrong_hash)
    
    assert changed is True


def test_has_file_changed_deleted(tmp_path):
    """Test detecting when file is deleted."""
    file_path = tmp_path / "nonexistent.txt"
    
    # File doesn't exist
    changed = has_file_changed(file_path, "somehash")
    
    assert changed is True
