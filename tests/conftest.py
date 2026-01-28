"""Pytest configuration and fixtures for OFS tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary directory for testing repository operations.
    
    Args:
        tmp_path: Pytest's built-in temporary directory fixture
        
    Yields:
        Path: Temporary directory path
        
    Cleanup:
        Automatically cleaned up after test
    """
    yield tmp_path


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample text file for testing.
    
    Args:
        tmp_path: Pytest's built-in temporary directory fixture
        
    Returns:
        Path: Path to created file
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Sample content for testing")
    return file_path


@pytest.fixture
def sample_binary_file(tmp_path):
    """Create a sample binary file for testing.
    
    Args:
        tmp_path: Pytest's built-in temporary directory fixture
        
    Returns:
        Path: Path to created binary file
    """
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")
    return file_path


@pytest.fixture
def sample_directory(tmp_path):
    """Create a directory with multiple files for testing.
    
    Args:
        tmp_path: Pytest's built-in temporary directory fixture
        
    Returns:
        Path: Path to created directory
    """
    dir_path = tmp_path / "sample_dir"
    dir_path.mkdir()
    
    (dir_path / "file1.txt").write_text("File 1")
    (dir_path / "file2.txt").write_text("File 2")
    (dir_path / "subdir").mkdir()
    (dir_path / "subdir" / "file3.txt").write_text("File 3")
    
    return dir_path
