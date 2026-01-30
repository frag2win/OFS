"""Tests for reference management (read_head)."""

import pytest
from pathlib import Path
from ofs.core.refs.read_head import read_head, resolve_head, is_detached_head
from ofs.core.refs.update_ref import update_ref, init_head


def test_read_head_symbolic_ref(tmp_path):
    """Test reading symbolic HEAD ref."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Initialize HEAD
    init_head(ofs_dir)
    
    head_content = read_head(ofs_dir)
    
    assert head_content == "ref: refs/heads/main"


def test_read_head_detached(tmp_path):
    """Test reading detached HEAD."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Set detached HEAD
    update_ref(ofs_dir / "HEAD", "003")
    
    head_content = read_head(ofs_dir)
    
    assert head_content == "003"


def test_read_head_missing(tmp_path):
    """Test reading HEAD when file doesn't exist."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    head_content = read_head(ofs_dir)
    
    assert head_content is None


def test_resolve_head_symbolic_ref(tmp_path):
    """Test resolving symbolic HEAD to commit ID."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Initialize HEAD and create branch ref
    init_head(ofs_dir)
    update_ref(ofs_dir / "refs" / "heads" / "main", "003")
    
    commit_id = resolve_head(ofs_dir)
    
    assert commit_id == "003"


def test_resolve_head_detached(tmp_path):
    """Test resolving detached HEAD."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Set detached HEAD
    update_ref(ofs_dir / "HEAD", "002")
    
    commit_id = resolve_head(ofs_dir)
    
    assert commit_id == "002"


def test_resolve_head_no_commits(tmp_path):
    """Test resolving HEAD when no commits exist."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Initialize HEAD but no branch ref yet
    init_head(ofs_dir)
    
    commit_id = resolve_head(ofs_dir)
    
    assert commit_id is None


def test_is_detached_head_symbolic(tmp_path):
    """Test is_detached_head with symbolic ref."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    init_head(ofs_dir)
    
    assert is_detached_head(ofs_dir) is False


def test_is_detached_head_detached(tmp_path):
    """Test is_detached_head with detached HEAD."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    update_ref(ofs_dir / "HEAD", "003")
    
    assert is_detached_head(ofs_dir) is True
