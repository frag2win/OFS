"""Tests for file size validation."""

import pytest
from pathlib import Path
from ofs.utils.validation.file_size import check_file_size, format_file_size, MAX_FILE_SIZE


def test_check_file_size_valid(tmp_path):
    """Test small file passes validation."""
    file_path = tmp_path / "small.txt"
    file_path.write_text("Small content")
    
    is_valid, msg = check_file_size(file_path)
    
    assert is_valid is True
    assert msg == ""


def test_check_file_size_too_large(tmp_path):
    """Test large file fails validation."""
    file_path = tmp_path / "huge.bin"
    # Create file larger than 100MB
    large_content = b"x" * (MAX_FILE_SIZE + 1000)
    file_path.write_bytes(large_content)
    
    is_valid, msg = check_file_size(file_path)
    
    assert is_valid is False
    assert "exceeds maximum" in msg


def test_check_file_size_nonexistent(tmp_path):
    """Test nonexistent file fails validation."""
    file_path = tmp_path / "nonexistent.txt"
    
    is_valid, msg = check_file_size(file_path)
    
    assert is_valid is False
    assert "not found" in msg.lower()


def test_check_file_size_directory(tmp_path):
    """Test directory fails validation."""
    dir_path = tmp_path / "directory"
    dir_path.mkdir()
    
    is_valid, msg = check_file_size(dir_path)
    
    assert is_valid is False
    assert "not a file" in msg.lower()


def test_format_file_size_bytes():
    """Test formatting bytes."""
    assert "500 B" in format_file_size(500)


def test_format_file_size_kb():
    """Test formatting kilobytes."""
    size_str = format_file_size(2048)
    assert "KB" in size_str
    assert "2.0" in size_str


def test_format_file_size_mb():
    """Test formatting megabytes."""
    size_str = format_file_size(5 * 1024 * 1024)
    assert "MB" in size_str
    assert "5.0" in size_str


def test_format_file_size_gb():
    """Test formatting gigabytes."""
    size_str = format_file_size(3 * 1024 * 1024 * 1024)
    assert "GB" in size_str
    assert "3.0" in size_str
