"""Tests for file size validation."""

import pytest
from pathlib import Path
from ofs.utils.validation.file_size import (
    check_file_size,
    format_file_size,
    MAX_FILE_SIZE,
)


class TestCheckFileSize:
    """Tests for check_file_size function."""
    
    def test_small_file_valid(self, tmp_path):
        """Small file passes validation."""
        file = tmp_path / "small.txt"
        file.write_text("small content")
        
        is_valid, msg = check_file_size(file)
        assert is_valid is True
        assert msg == ""
    
    def test_file_exceeds_limit(self, tmp_path):
        """File exceeding limit fails validation."""
        file = tmp_path / "large.txt"
        file.write_text("x" * 100)  # 100 bytes
        
        # With 50 byte limit, should fail
        is_valid, msg = check_file_size(file, max_size=50)
        assert is_valid is False
        assert "exceeds" in msg
    
    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file fails validation."""
        nonexistent = tmp_path / "nonexistent.txt"
        is_valid, msg = check_file_size(nonexistent)
        assert is_valid is False
        assert "not found" in msg.lower()

    def test_check_file_size_exception(self, tmp_path, monkeypatch):
        """Test exception handling in check_file_size."""
        file = tmp_path / "test.txt"
        file.write_text("content")
        
        # Mock Path.stat to raise exception
        def mock_stat(*args, **kwargs):
            raise OSError("Mock error")
            
        monkeypatch.setattr(Path, "stat", mock_stat)
        
        is_valid, msg = check_file_size(file)
        assert is_valid is False
        assert "Error checking file size" in msg
    
    def test_directory_not_file(self, tmp_path):
        """Directory fails validation."""
        is_valid, msg = check_file_size(tmp_path)
        assert is_valid is False
        assert "Not a file" in msg
    
    def test_custom_limit_pass(self, tmp_path):
        """Custom size limit works when passing."""
        file = tmp_path / "test.txt"
        file.write_text("x" * 100)  # 100 bytes
        
        is_valid, msg = check_file_size(file, max_size=200)
        assert is_valid is True
    
    def test_exact_limit(self, tmp_path):
        """File at exact limit passes."""
        file = tmp_path / "exact.txt"
        file.write_bytes(b"x" * 100)  # Exactly 100 bytes
        
        is_valid, msg = check_file_size(file, max_size=100)
        assert is_valid is True
    
    def test_over_limit_by_one(self, tmp_path):
        """File over limit by one byte fails."""
        file = tmp_path / "over.txt"
        file.write_bytes(b"x" * 101)  # 101 bytes
        
        is_valid, msg = check_file_size(file, max_size=100)
        assert is_valid is False


class TestFormatFileSize:
    """Tests for format_file_size function."""
    
    def test_format_bytes(self):
        """Format bytes."""
        assert format_file_size(100) == "100 B"
    
    def test_format_kilobytes(self):
        """Format kilobytes."""
        result = format_file_size(1024)
        assert "KB" in result
    
    def test_format_megabytes(self):
        """Format megabytes."""
        result = format_file_size(1024 * 1024)
        assert "MB" in result
    
    def test_format_gigabytes(self):
        """Format gigabytes."""
        result = format_file_size(1024 * 1024 * 1024)
        assert "GB" in result
    
    def test_format_zero(self):
        """Format zero bytes."""
        assert format_file_size(0) == "0 B"
    
    def test_format_1500_bytes(self):
        """Format 1500 bytes (1.5 KB)."""
        result = format_file_size(1536)
        assert "1.5" in result
        assert "KB" in result


class TestMaxFileSize:
    """Tests for MAX_FILE_SIZE constant."""
    
    def test_max_file_size_defined(self):
        """MAX_FILE_SIZE constant is defined."""
        assert MAX_FILE_SIZE > 0
    
    def test_max_file_size_is_100mb(self):
        """MAX_FILE_SIZE is 100MB."""
        assert MAX_FILE_SIZE == 100 * 1024 * 1024
