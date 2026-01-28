"""Unit tests for Index class."""

import pytest
from pathlib import Path
import json
from ofs.core.index import Index


def test_add_entry(tmp_path):
    """Test adding entry to index."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    entries = index.get_entries()
    
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"
    assert entries[0]["hash"] == "abc123"
    assert entries[0]["size"] == 100


def test_add_updates_existing(tmp_path):
    """Test adding same path updates entry."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    index.add("test.txt", "def456", {"size": 200})
    entries = index.get_entries()
    
    # Should have only one entry (updated)
    assert len(entries) == 1
    assert entries[0]["hash"] == "def456"
    assert entries[0]["size"] == 200


def test_remove_entry(tmp_path):
    """Test removing entry from index."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    assert index.remove("test.txt") is True
    
    entries = index.get_entries()
    assert len(entries) == 0


def test_remove_nonexistent(tmp_path):
    """Test removing non-existent entry."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    assert index.remove("nonexistent.txt") is False


def test_get_entries_empty(tmp_path):
    """Test getting entries from empty index."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    entries = index.get_entries()
    assert entries == []


def test_get_entries_returns_copy(tmp_path):
    """Test get_entries returns copy, not reference."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    entries1 = index.get_entries()
    entries2 = index.get_entries()
    
    # Should be separate lists
    assert entries1 is not entries2
    assert entries1 == entries2


def test_clear(tmp_path):
    """Test clearing index."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("file1.txt", "abc123", {"size": 100})
    index.add("file2.txt", "def456", {"size": 200})
    
    index.clear()
    
    assert index.get_entries() == []
    assert index.has_changes() is False


def test_has_changes_true(tmp_path):
    """Test has_changes returns True when entries exist."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    
    assert index.has_changes() is True


def test_has_changes_false(tmp_path):
    """Test has_changes returns False when empty."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    assert index.has_changes() is False


def test_find_entry_exists(tmp_path):
    """Test finding existing entry."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    
    entry = index.find_entry("test.txt")
    
    assert entry is not None
    assert entry["path"] == "test.txt"
    assert entry["hash"] == "abc123"


def test_find_entry_not_found(tmp_path):
    """Test finding non-existent entry."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    entry = index.find_entry("nonexistent.txt")
    
    assert entry is None


def test_persistence(tmp_path):
    """Test index persists across instances."""
    index_file = tmp_path / "index.json"
    
    # Create and add entry
    index1 = Index(index_file)
    index1.add("test.txt", "abc123", {"size": 100})
    
    # Load in new instance
    index2 = Index(index_file)
    entries = index2.get_entries()
    
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"


def test_atomic_save(tmp_path):
    """Test saves are atomic (no partial writes)."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("test.txt", "abc123", {"size": 100})
    
    # File should be valid JSON
    content = index_file.read_text()
    data = json.loads(content)
    
    assert isinstance(data, list)
    assert len(data) == 1


def test_corrupt_index_handled(tmp_path):
    """Test corrupt index file is handled gracefully."""
    index_file = tmp_path / "index.json"
    index_file.write_text("invalid json{")
    
    # Should not crash, should use empty index
    index = Index(index_file)
    entries = index.get_entries()
    
    assert entries == []


def test_multiple_files(tmp_path):
    """Test managing multiple files."""
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add("file1.txt", "hash1", {"size": 100})
    index.add("file2.txt", "hash2", {"size": 200})
    index.add("file3.txt", "hash3", {"size": 300})
    
    entries = index.get_entries()
    
    assert len(entries) == 3
    paths = [e["path"] for e in entries]
    assert "file1.txt" in paths
    assert "file2.txt" in paths
    assert "file3.txt" in paths
