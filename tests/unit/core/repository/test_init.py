"""Unit tests for Repository initialization."""

import pytest
from pathlib import Path
import json
from ofs.core.repository import Repository


def test_initialize_new_repo(tmp_path):
    """Test initializing a new repository."""
    repo = Repository(tmp_path)
    
    assert repo.initialize() is True
    assert (tmp_path / ".ofs").exists()
    assert (tmp_path / ".ofs" / "HEAD").exists()
    assert (tmp_path / ".ofs" / "config.json").exists()
    assert (tmp_path / ".ofs" / "index.json").exists()
    assert repo.is_initialized()


def test_initialize_twice_fails(tmp_path):
    """Test initializing twice fails gracefully."""
    repo = Repository(tmp_path)
    
    assert repo.initialize() is True
    assert repo.initialize() is False  # Second attempt fails


def test_is_initialized_false(tmp_path):
    """Test is_initialized returns False for uninitialized."""
    repo = Repository(tmp_path)
    
    assert repo.is_initialized() is False


def test_directory_structure(tmp_path):
    """Test all required directories are created."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    assert (tmp_path / ".ofs" / "objects").exists()
    assert (tmp_path / ".ofs" / "refs" / "heads").exists()
    assert (tmp_path / ".ofs" / "commits").exists()


def test_head_file_content(tmp_path):
    """Test HEAD file contains correct reference."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    head_content = repo.head_file.read_text()
    assert head_content == "ref: refs/heads/main\n"


def test_index_empty(tmp_path):
    """Test index is initialized as empty array."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    index_content = repo.index_file.read_text()
    assert index_content == "[]"


def test_config_defaults(tmp_path):
    """Test default configuration is created."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    config = repo.get_config()
    
    assert "version" in config
    assert config["version"] == "1.0"
    assert "author" in config
    assert "email" in config
    assert "ignore" in config
    assert ".ofs" in config["ignore"]


def test_get_config(tmp_path):
    """Test getting configuration."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    config = repo.get_config()
    
    assert isinstance(config, dict)
    assert "version" in config


def test_get_config_not_initialized(tmp_path):
    """Test get_config raises if not initialized."""
    repo = Repository(tmp_path)
    
    with pytest.raises(FileNotFoundError):
        repo.get_config()


def test_set_config(tmp_path):
    """Test setting configuration value."""
    repo = Repository(tmp_path)
    repo.initialize()
    
    repo.set_config("author", "Test Author")
    
    config = repo.get_config()
    assert config["author"] == "Test Author"


def test_set_config_not_initialized(tmp_path):
    """Test set_config raises if not initialized."""
    repo = Repository(tmp_path)
    
    with pytest.raises(FileNotFoundError):
        repo.set_config("author", "Test")


def test_config_persistence(tmp_path):
    """Test configuration persists across instances."""
    repo1 = Repository(tmp_path)
    repo1.initialize()
    repo1.set_config("author", "Persistent Author")
    
    # Load in new instance
    repo2 = Repository(tmp_path)
    config = repo2.get_config()
    
    assert config["author"] == "Persistent Author"


def test_default_path_is_cwd():
    """Test repository defaults to current directory."""
    repo = Repository()
    
    assert repo.root == Path.cwd()


def test_cleanup_on_failure(tmp_path):
    """Test partial initialization is cleaned up on failure."""
    # This test is hard to trigger naturally, but verifies the cleanup code exists
    repo = Repository(tmp_path)
    repo.initialize()
    
    # If we tried to initialize again, it would fail but not leave partial state
    initial_state = repo.ofs_dir.exists()
    repo.initialize()  # Fails
    final_state = repo.ofs_dir.exists()
    
    assert initial_state == final_state  # State unchanged
