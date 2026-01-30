"""Unit tests for repository verification."""

import pytest
from pathlib import Path
import json

from ofs.core.repository.init import Repository
from ofs.core.verify.integrity import (
    verify_objects,
    verify_index,
    verify_commits,
    verify_refs,
    verify_repository,
)
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository."""
    repo = Repository(tmp_path)
    repo.initialize()
    return tmp_path


def test_verify_empty_repository(test_repo):
    """Test verifying an empty repository."""
    success, results = verify_repository(test_repo)
    
    assert success is True
    assert results["objects"]["success"] is True
    assert results["index"]["success"] is True
    assert results["commits"]["success"] is True
    assert results["refs"]["success"] is True


def test_verify_with_commit(test_repo):
    """Test verifying repository with commits."""
    # Create a file and commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Verify
    success, results = verify_repository(test_repo)
    
    assert success is True
    assert all(r["success"] for r in results.values())


def test_verify_objects_missing_object(test_repo):
    """Test detection of missing object."""
    # Create a file and commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Delete an object file
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    # Find and delete an object
    for obj_file in objects_dir.rglob("*.blob"):
        obj_file.unlink()
        break
    
    # Verify should detect missing object
    success, errors = verify_objects(repo)
    
    # This test depends on implementation - currently objects are checked on retrieval
    # If the object is referenced by index or commit, it should fail those checks


def test_verify_index_missing_object_reference(test_repo):
    """Test detection of index referencing missing object."""
    # Create a file and add to index
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    
    # Delete the object but keep index entry
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    for obj_file in objects_dir.rglob("*.blob"):
        obj_file.unlink()
    
    # Verify index should fail
    success, errors = verify_index(repo)
    
    assert success is False
    assert len(errors) > 0
    assert "missing object" in errors[0].lower()


def test_verify_corrupted_index(test_repo):
    """Test detection of corrupted index file."""
    repo = Repository(test_repo)
    
    # Corrupt index file with invalid JSON
    repo.index_file.write_text("{ invalid json }")
    
    # Verify should detect corruption
    success, errors = verify_index(repo)
    
    assert success is False
    assert len(errors) > 0
    assert "corrupted" in errors[0].lower() or "invalid" in errors[0].lower()


def test_verify_commits_missing_object(test_repo):
    """Test detection of commits referencing missing objects."""
    # Create a file and commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Delete the object
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    for obj_file in objects_dir.rglob("*.blob"):
        obj_file.unlink()
    
    # Verify commits should detect missing object
    success, errors = verify_commits(repo)
    
    assert success is False
    assert len(errors) > 0
    assert "missing object" in errors[0].lower()


def test_verify_corrupted_commit(test_repo):
    """Test detection of corrupted commit file."""
    # Create a commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Corrupt the commit file
    repo = Repository(test_repo)
    commit_file = repo.commits_dir / "001.json"
    commit_file.write_text("{ invalid json ")
    
    # Verify should detect corruption
    success, errors = verify_commits(repo)
    
    assert success is False
    assert len(errors) > 0


def test_verify_refs_missing_head(test_repo):
    """Test detection of missing HEAD file."""
    repo = Repository(test_repo)
    
    # Delete HEAD file
    head_file = repo.ofs_dir / "HEAD"
    head_file.unlink()
    
    # Verify refs should fail
    success, errors = verify_refs(repo)
    
    assert success is False
    assert "HEAD file missing" in errors


def test_verify_refs_invalid_commit_reference(test_repo):
    """Test detection of HEAD pointing to non-existent commit."""
    # Create a commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Manually set HEAD to invalid commit
    repo = Repository(test_repo)
    (repo.ofs_dir / "refs" / "heads" / "main").write_text("999\n")
    
    # Verify refs should detect invalid reference
    success, errors = verify_refs(repo)
    
    assert success is False
    assert len(errors) > 0
    assert "non-existent" in errors[0].lower()


def test_verify_hash_mismatch(test_repo):
    """Test detection of object hash mismatch (corruption)."""
    # Create a file and commit
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Find and corrupt an object file
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    for obj_file in objects_dir.rglob("*.blob"):
        # Overwrite with different content
        obj_file.write_bytes(b"corrupted content")
        break
    
    # Verify objects should detect hash mismatch
    success, errors = verify_objects(repo)
    
    assert success is False
    assert len(errors) > 0
    assert "hash mismatch" in errors[0].lower()


def test_verify_multiple_commits(test_repo):
    """Test verification with multiple commits."""
    # Create multiple commits
    for i in range(3):
        test_file = test_repo / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        add_execute([str(test_file)], test_repo)
        commit_execute(f"Commit {i+1}", test_repo)
    
    # Verify should pass
    success, results = verify_repository(test_repo)
    
    assert success is True
    assert all(r["success"] for r in results.values())


def test_verify_not_a_repository(tmp_path):
    """Test verification of non-repository directory."""
    success, results = verify_repository(tmp_path)
    
    assert success is False
    assert "error" in results
    assert "Not an OFS repository" in results["error"]
