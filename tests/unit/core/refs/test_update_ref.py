"""Tests for reference management (update_ref)."""

import pytest
from pathlib import Path
from ofs.core.refs.update_ref import update_ref, update_head, init_head
from ofs.core.refs.read_head import read_head, resolve_head


def test_update_ref_creates_file(tmp_path):
    """Test that update_ref creates the ref file."""
    ref_file = tmp_path / "refs" / "heads" / "main"
    
    update_ref(ref_file, "003")
    
    assert ref_file.exists()
    assert ref_file.read_text().strip() == "003"


def test_update_ref_atomic(tmp_path):
    """Test that update_ref overwrites existing ref."""
    ref_dir = tmp_path / "refs"
    ref_dir.mkdir()
    ref_file = ref_dir / "test_ref"
    
    update_ref(ref_file, "001")
    assert ref_file.read_text().strip() == "001"
    
    update_ref(ref_file, "002")
    assert ref_file.read_text().strip() == "002"


def test_init_head(tmp_path):
    """Test initializing HEAD."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    init_head(ofs_dir)
    
    head_file = ofs_dir / "HEAD"
    assert head_file.exists()
    assert "ref: refs/heads/main" in head_file.read_text()


def test_update_head_normal_mode(tmp_path):
    """Test updating HEAD in normal (non-detached) mode."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Initialize HEAD
    init_head(ofs_dir)
    
    # Update HEAD to commit 003
    update_head(ofs_dir, "003", detached=False)
    
    # Should update refs/heads/main
    main_ref = ofs_dir / "refs" / "heads" / "main"
    assert main_ref.exists()
    assert main_ref.read_text().strip() == "003"
    
    # HEAD should still be symbolic
    assert "ref: refs/heads/main" in read_head(ofs_dir)


def test_update_head_detached_mode(tmp_path):
    """Test updating HEAD in detached mode."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    # Update HEAD to detached state
    update_head(ofs_dir, "002", detached=True)
    
    # HEAD should point directly to commit
    assert read_head(ofs_dir) == "002"


def test_update_head_creates_branch(tmp_path):
    """Test that update_head creates branch ref if it doesn't exist."""
    ofs_dir = tmp_path / ".ofs"
    ofs_dir.mkdir()
    
    init_head(ofs_dir)
    
    # Branch ref doesn't exist yet
    main_ref = ofs_dir / "refs" / "heads" / "main"
    assert not main_ref.exists()
    
    # Update HEAD
    update_head(ofs_dir, "001", detached=False)
    
    # Now branch ref should exist
    assert main_ref.exists()
    assert main_ref.read_text().strip() == "001"
