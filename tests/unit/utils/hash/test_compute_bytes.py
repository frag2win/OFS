"""Unit tests for compute_hash function."""

import pytest
from ofs.utils.hash.compute_bytes import compute_hash


def test_hash_empty_bytes():
    """Test hashing empty bytes."""
    # Known SHA-256 of empty string
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_hash(b"") == expected


def test_hash_hello():
    """Test hashing 'hello'."""
    # Known SHA-256 of "hello"
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert compute_hash(b"hello") == expected


def test_hash_consistency():
    """Test same input produces same hash."""
    data = b"Test data for consistency"
    hash1 = compute_hash(data)
    hash2 = compute_hash(data)
    assert hash1 == hash2


def test_hash_different_data():
    """Test different data produces different hashes."""
    hash1 = compute_hash(b"data1")
    hash2 = compute_hash(b"data2")
    assert hash1 != hash2


def test_hash_length():
    """Test hash is 64 hex characters."""
    hash_val = compute_hash(b"any data")
    assert len(hash_val) == 64
    assert all(c in "0123456789abcdef" for c in hash_val)


def test_hash_binary_data():
    """Test hashing binary data."""
    binary_data = bytes(range(256))
    hash_val = compute_hash(binary_data)
    assert len(hash_val) == 64
    
    # Consistency check
    assert hash_val == compute_hash(binary_data)
