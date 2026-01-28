"""Unit tests for ObjectStore class."""

import pytest
from pathlib import Path
from ofs.core.objects import ObjectStore


def test_store_and_retrieve(tmp_path):
    """Test basic store and retrieve."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"Test content"
    
    # Store
    hash_val = store.store(content)
    
    # Retrieve
    retrieved = store.retrieve(hash_val)
    
    assert retrieved == content


def test_store_returns_hash(tmp_path):
    """Test store returns correct hash."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"hello"
    
    hash_val = store.store(content)
    
    # Known SHA-256 of "hello"
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert hash_val == expected


def test_deduplication(tmp_path):
    """Test same content stored once."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"Same content"
    
    hash1 = store.store(content)
    hash2 = store.store(content)
    
    # Same hash
    assert hash1 == hash2
    
    # Only one file should exist
    obj_path = store._get_path(hash1)
    assert obj_path.exists()


def test_two_level_directory_structure(tmp_path):
    """Test objects stored in ab/cdef... structure."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"test"
    
    hash_val = store.store(content)
    
    # Check directory structure
    expected_path = (
        tmp_path / ".ofs" / "objects" / hash_val[:2] / hash_val[2:]
    )
    assert expected_path.exists()


def test_exists(tmp_path):
    """Test exists check."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"exists test"
    
    hash_val = store.store(content)
    
    assert store.exists(hash_val) is True
    assert store.exists("0" * 64) is False


def test_retrieve_nonexistent(tmp_path):
    """Test retrieving non-existent object."""
    store = ObjectStore(tmp_path / ".ofs")
    
    with pytest.raises(FileNotFoundError):
        store.retrieve("0" * 64)


def test_corruption_detection(tmp_path):
    """Test corruption is detected."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"original content"
    
    hash_val = store.store(content)
    
    # Corrupt the object
    obj_path = store._get_path(hash_val)
    obj_path.write_bytes(b"corrupted")
    
    # Should raise on retrieve
    with pytest.raises(ValueError, match="Corruption detected"):
        store.retrieve(hash_val)


def test_verify_ok(tmp_path):
    """Test verify returns True for valid object."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"verify test"
    
    hash_val = store.store(content)
    
    assert store.verify(hash_val) is True


def test_verify_corrupted(tmp_path):
    """Test verify returns False for corrupted object."""
    store = ObjectStore(tmp_path / ".ofs")
    content = b"original"
    
    hash_val = store.store(content)
    
    # Corrupt
    obj_path = store._get_path(hash_val)
    obj_path.write_bytes(b"corrupted")
    
    assert store.verify(hash_val) is False


def test_verify_nonexistent(tmp_path):
    """Test verify raises for non-existent object."""
    store = ObjectStore(tmp_path / ".ofs")
    
    with pytest.raises(FileNotFoundError):
        store.verify("0" * 64)


def test_store_binary_data(tmp_path):
    """Test storing binary data."""
    store = ObjectStore(tmp_path / ".ofs")
    binary_data = bytes(range(256))
    
    hash_val = store.store(binary_data)
    retrieved = store.retrieve(hash_val)
    
    assert retrieved == binary_data


def test_store_large_data(tmp_path):
    """Test storing 1MB data."""
    store = ObjectStore(tmp_path / ".ofs")
    large_data = b"x" * (1024 * 1024)
    
    hash_val = store.store(large_data)
    retrieved = store.retrieve(hash_val)
    
    assert retrieved == large_data
    assert len(retrieved) == 1024 * 1024


def test_multiple_objects(tmp_path):
    """Test storing multiple different objects."""
    store = ObjectStore(tmp_path / ".ofs")
    
    contents = [b"first", b"second", b"third"]
    hashes = []
    
    for content in contents:
        hash_val = store.store(content)
        hashes.append(hash_val)
    
    # All hashes should be different
    assert len(set(hashes)) == 3
    
    # All should be retrievable
    for content, hash_val in zip(contents, hashes):
        assert store.retrieve(hash_val) == content
