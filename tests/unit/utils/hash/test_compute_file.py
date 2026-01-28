"""Unit tests for compute_file_hash function."""

import pytest
from pathlib import Path
from ofs.utils.hash.compute_file import compute_file_hash


def test_hash_file_empty(tmp_path):
    """Test hashing empty file."""
    file_path = tmp_path / "empty.txt"
    file_path.write_bytes(b"")
    
    # Known SHA-256 of empty content
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_file_hash(file_path) == expected


def test_hash_file_text(tmp_path):
    """Test hashing text file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    # Known SHA-256 of "hello"
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert compute_file_hash(file_path) == expected


def test_hash_file_binary(tmp_path):
    """Test hashing binary file."""
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(bytes(range(256)))
    
    hash1 = compute_file_hash(file_path)
    
    # Verify consistency
    hash2 = compute_file_hash(file_path)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_hash_file_large(tmp_path):
    """Test hashing large file (streaming)."""
    file_path = tmp_path / "large.bin"
    
    # Create 1MB file
    data = b"x" * (1024 * 1024)
    file_path.write_bytes(data)
    
    hash1 = compute_file_hash(file_path)
    
    # Verify it matches direct hash
    from ofs.utils.hash.compute_bytes import compute_hash
    hash2 = compute_hash(data)
    
    assert hash1 == hash2


def test_hash_file_not_found(tmp_path):
    """Test hashing non-existent file."""
    file_path = tmp_path / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_file_hash(file_path)


def test_hash_file_consistency(tmp_path):
    """Test multiple reads produce same hash."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("consistent data")
    
    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)
    hash3 = compute_file_hash(file_path)
    
    assert hash1 == hash2 == hash3
