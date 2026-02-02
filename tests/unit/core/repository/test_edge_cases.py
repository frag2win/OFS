"""Edge case tests for Repository class."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository

class TestRepositoryEdgeCases:
    """Edge cases for Repository."""
    
    def test_initialize_exception(self, tmp_path, monkeypatch):
        """initialize handles exceptions and cleans up."""
        repo = Repository(tmp_path)
        
        # Mock mkdir to raise exception
        def mock_mkdir(*args, **kwargs):
            raise OSError("Mock error")
            
        monkeypatch.setattr(Path, "mkdir", mock_mkdir)
        
        # Should return False and print error (captured by pytest)
        assert repo.initialize() is False
        
        # Should clean up
        assert not (tmp_path / ".ofs").exists()

    def test_initialize_already_exists(self, tmp_path):
        """initialize returns False if already initialized."""
        repo = Repository(tmp_path)
        assert repo.initialize() is True
        assert repo.initialize() is False
    
    def test_get_config_not_initialized(self, tmp_path):
        """get_config raises FileNotFoundError if not initialized."""
        repo = Repository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.get_config()

    def test_set_config_not_initialized(self, tmp_path):
        """set_config raises FileNotFoundError if not initialized."""
        repo = Repository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.set_config("key", "value")

    def test_set_config_updates(self, tmp_path):
        """set_config updates configuration."""
        repo = Repository(tmp_path)
        repo.initialize()
        
        repo.set_config("user.email", "test@example.com")
        config = repo.get_config()
        assert config["user.email"] == "test@example.com"
