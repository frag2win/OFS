"""Tests for ignore pattern matching."""

import pytest
from pathlib import Path
from ofs.utils.ignore.patterns import should_ignore, load_ignore_patterns


def test_should_ignore_exact_match():
    """Test ignoring exact filename match."""
    patterns = ["*.tmp", "*.log"]
    
    assert should_ignore(Path("file.tmp"), patterns) is True
    assert should_ignore(Path("file.log"), patterns) is True
    assert should_ignore(Path("file.txt"), patterns) is False


def test_should_ignore_directory():
    """Test ignoring directory."""
    patterns = ["__pycache__", ".ofs"]
    
    assert should_ignore(Path("__pycache__"), patterns) is True
    assert should_ignore(Path(".ofs"), patterns) is True
    assert should_ignore(Path("src"), patterns) is False


def test_should_ignore_with_repo_root(tmp_path):
    """Test ignoring with repository root."""
    patterns = ["*.tmp"]
    repo_root = tmp_path
    
    file_path = tmp_path / "src" / "file.tmp"
    file_path.parent.mkdir()
    file_path.write_text("Temp")
    
    assert should_ignore(file_path, patterns, repo_root) is True


def test_load_ignore_patterns_without_file(tmp_path):
    """Test loading ignore patterns when no .ofsignore exists."""
    patterns = load_ignore_patterns(tmp_path)
    
    # Should have default patterns
    assert ".ofs" in patterns
    assert "*.tmp" in patterns
    assert "__pycache__" in patterns


def test_load_ignore_patterns_with_file(tmp_path):
    """Test loading ignore patterns from .ofsignore."""
    # Create .ofsignore
    ofsignore = tmp_path / ".ofsignore"
    ofsignore.write_text("*.pyc\n# Comment\nbuild/\n")
    
    patterns = load_ignore_patterns(tmp_path)
    
    # Should have both default and custom patterns
    assert ".ofs" in patterns  # Default
    assert "*.pyc" in patterns  # Custom
    assert "build/" in patterns  # Custom
    # Comments should be filtered out
    assert "# Comment" not in patterns
