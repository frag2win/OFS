"""Edge case tests for ObjectStore."""

import pytest
from pathlib import Path
from ofs.core.objects.store import ObjectStore

class TestObjectStoreEdgeCases:
    """Tests for ObjectStore edge cases."""
    
    def test_retrieve_not_found(self, tmp_path):
        """retrieve raises FileNotFoundError if object missing."""
        ofs_dir = tmp_path / ".ofs"
        store = ObjectStore(ofs_dir)
        
        with pytest.raises(FileNotFoundError):
            store.retrieve("abc123456789")

    def test_verify_corruption(self, tmp_path):
        """verify returns False if content doesn't match hash."""
        ofs_dir = tmp_path / ".ofs"
        store = ObjectStore(ofs_dir)
        
        # Manually create corrupted object
        hash_val = "abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
        obj_path = store._get_path(hash_val)
        obj_path.parent.mkdir(parents=True)
        obj_path.write_text("wrong content")
        
        assert store.verify(hash_val) is False

    def test_verify_not_found(self, tmp_path):
        """verify raises FileNotFoundError if object missing."""
        ofs_dir = tmp_path / ".ofs"
        store = ObjectStore(ofs_dir)
        
        with pytest.raises(FileNotFoundError):
            store.verify("missinghash")
