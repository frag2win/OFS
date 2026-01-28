"""Unit tests for verify_hash function."""

import pytest
from pathlib import Path
from ofs.utils.hash.verify_hash import verify_hash


def test_verify_hash_correct(tmp_path):
    """Test verification with correct hash."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    # Known SHA-256 of "hello"
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    
    assert verify_hash(file_path, expected) is True


def test_verify_hash_incorrect(tmp_path):
    """Test verification with incorrect hash."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    # Wrong hash
    wrong_hash = "0" * 64
    
    assert verify_hash(file_path, wrong_hash) is False


def test_verify_hash_case_insensitive(tmp_path):
    """Test verification is case-insensitive."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    # Uppercase hash
    expected_upper = "2CF24DBA5FB0A30E26E83B2AC5B9E29E1B161E5C1FA7425E73043362938B9824"
    
    assert verify_hash(file_path, expected_upper) is True


def test_verify_hash_invalid_format_short(tmp_path):
    """Test verification with invalid hash format (too short)."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    with pytest.raises(ValueError, match="Invalid hash format"):
        verify_hash(file_path, "abc123")


def test_verify_hash_invalid_format_non_hex(tmp_path):
    """Test verification with invalid hash format (non-hex characters)."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    invalid_hash = "g" * 64  # 'g' is not a hex character
    
    with pytest.raises(ValueError, match="Invalid hash format"):
        verify_hash(file_path, invalid_hash)


def test_verify_hash_file_not_found(tmp_path):
    """Test verification with non-existent file."""
    file_path = tmp_path / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        verify_hash(file_path, "0" * 64)


def test_verify_hash_empty_file(tmp_path):
    """Test verification with empty file."""
    file_path = tmp_path / "empty.txt"
    file_path.write_bytes(b"")
    
    # Known SHA-256 of empty content
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    assert verify_hash(file_path, expected) is True
