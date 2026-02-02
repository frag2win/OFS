"""Tests for working tree operations."""

import pytest
from pathlib import Path
from ofs.core.working_tree.compare import has_file_changed
from ofs.core.working_tree.scan import scan_working_tree
from ofs.utils.hash.compute_file import compute_file_hash


class TestHasFileChanged:
    """Tests for has_file_changed function."""
    
    def test_unchanged_file(self, tmp_path):
        """File with same hash returns False."""
        file = tmp_path / "test.txt"
        file.write_text("test content")
        
        file_hash = compute_file_hash(file)
        assert not has_file_changed(file, file_hash)
    
    def test_changed_file(self, tmp_path):
        """File with different hash returns True."""
        file = tmp_path / "test.txt"
        file.write_text("test content")
        
        # Use wrong hash
        assert has_file_changed(file, "wrong_hash_value")
    
    def test_deleted_file(self, tmp_path):
        """Deleted file returns True."""
        nonexistent = tmp_path / "nonexistent.txt"
        assert has_file_changed(nonexistent, "any_hash")
    
    def test_modified_file(self, tmp_path):
        """Modified file content returns True."""
        file = tmp_path / "test.txt"
        file.write_text("original content")
        original_hash = compute_file_hash(file)
        
        # Modify file
        file.write_text("modified content")
        assert has_file_changed(file, original_hash)


class TestScanWorkingTree:
    """Tests for scan_working_tree function."""
    
    def test_scan_finds_files(self, tmp_path):
        """Scan finds all files."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        result = scan_working_tree(tmp_path, [])
        paths = [str(p) for p in result]
        assert "file1.txt" in paths
        assert "file2.txt" in paths
    
    def test_scan_ignores_patterns(self, tmp_path):
        """Scan respects ignore patterns."""
        (tmp_path / "file.txt").write_text("keep")
        (tmp_path / "file.log").write_text("ignore")
        
        result = scan_working_tree(tmp_path, ["*.log"])
        paths = [str(p) for p in result]
        assert "file.txt" in paths
        assert "file.log" not in paths
    
    def test_scan_recursive(self, tmp_path):
        """Scan is recursive."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")
        (tmp_path / "root.txt").write_text("root")
        
        result = scan_working_tree(tmp_path, [])
        assert len(result) == 2
    
    def test_scan_default_patterns(self, tmp_path):
        """Scan loads default patterns if none provided."""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "file.tmp").write_text("temp")  # Should be ignored by default
        
        result = scan_working_tree(tmp_path)  # No patterns = use defaults
        paths = [str(p) for p in result]
        assert "file.txt" in paths
    
    def test_scan_empty_directory(self, tmp_path):
        """Empty directory returns empty set."""
        result = scan_working_tree(tmp_path, [])
        assert result == set()
    
    def test_scan_returns_relative_paths(self, tmp_path):
        """Returned paths are relative to repo root."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "main.py").write_text("code")
        
        result = scan_working_tree(tmp_path, [])
        paths = [str(p) for p in result]
        assert "src\\main.py" in paths or "src/main.py" in paths
