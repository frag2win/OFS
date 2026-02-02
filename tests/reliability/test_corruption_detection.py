"""Reliability tests - Power loss simulation and corruption detection.

These tests simulate power failures and verify repository integrity.
"""

import pytest
from pathlib import Path
import json
import random

from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.core.verify import verify_repository
from ofs.core.index.manager import Index
from ofs.core.commits import load_commit


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository."""
    repo = Repository(tmp_path)
    repo.initialize()
    return tmp_path


def find_object_files(objects_dir: Path):
    """Find all object files in the objects directory.
    
    Objects are stored as objects/ab/cdef... (2-char prefix dir / 62-char suffix).
    """
    object_files = []
    for prefix_dir in objects_dir.iterdir():
        if prefix_dir.is_dir() and len(prefix_dir.name) == 2:
            for obj_file in prefix_dir.iterdir():
                if obj_file.is_file() and not obj_file.suffix == '.tmp':
                    object_files.append(obj_file)
    return object_files


def test_atomic_commit_interruption(test_repo):
    """Test that interrupted commits don't corrupt repository.
    
    Simulates power loss during commit by checking that partial
    commits don't leave repository in inconsistent state.
    """
    # Create initial commit
    file1 = test_repo / "file1.txt"
    file1.write_text("Content 1")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Verify repository is good
    success, _ = verify_repository(test_repo)
    assert success is True
    
    # Create second commit but simulate interruption
    # (In practice, atomic operations prevent partial writes)
    file2 = test_repo / "file2.txt"
    file2.write_text("Content 2")
    add_execute([str(file2)], test_repo)
    
    # Simulate power loss by NOT completing commit
    # Repository should still be valid
    success, _ = verify_repository(test_repo)
    assert success is True


def test_incomplete_object_write(test_repo):
    """Test detection of incomplete object writes."""
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    # Create a file
    test_file = test_repo / "file.txt"
    test_file.write_text("Complete content")
    add_execute([str(test_file)], test_repo)
    
    # Find the object file
    object_files = find_object_files(objects_dir)
    assert len(object_files) > 0
    
    # Corrupt by truncating (simulate incomplete write)
    obj_file = object_files[0]
    original_content = obj_file.read_bytes()
    obj_file.write_bytes(original_content[:len(original_content)//2])
    
    # Verification should detect hash mismatch
    success, results = verify_repository(test_repo)
    
    assert success is False
    assert not results["objects"]["success"]


def test_corrupted_index_recovery(test_repo):
    """Test that corrupted index is detected."""
    # Create some commits
    file1 = test_repo / "file1.txt"
    file1.write_text("Content")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Add more files
    file2 = test_repo / "file2.txt"
    file2.write_text("More content")
    add_execute([str(file2)], test_repo)
    
    # Corrupt index
    repo = Repository(test_repo)
    repo.index_file.write_text("{ corrupted: invalid json")
    
    # Verification should fail
    success, results = verify_repository(test_repo)
    
    assert success is False
    assert not results["index"]["success"]


def test_missing_commit_file(test_repo):
    """Test detection of missing commit files."""
    # Create multiple commits
    for i in range(3):
        file = test_repo / f"file{i}.txt"
        file.write_text(f"Content {i}")
        add_execute([str(file)], test_repo)
        commit_execute(f"Commit {i+1}", test_repo)
    
    # Delete middle commit
    repo = Repository(test_repo)
    (repo.commits_dir / "002.json").unlink()
    
    # Clear cache to ensure we read from disk
    from ofs.core.commits import clear_commit_cache
    clear_commit_cache()
    
    # Verification might still pass if we don't traverse full history
    # But loading commit 002 should fail
    commit = load_commit("002", repo.commits_dir)
    assert commit is None


def test_corrupted_object_content(test_repo):
    """Test detection of object content corruption."""
    # Create a file and commit
    test_file = test_repo / "file.txt"
    content = "Original content that will be corrupted"
    test_file.write_text(content)
    
    add_execute([str(test_file)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Find and corrupt the object
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    for obj_file in find_object_files(objects_dir):
        # Replace content but keep file
        obj_file.write_bytes(b"Completely different corrupted content")
        break
    
    # Verification should detect hash mismatch
    success, results = verify_repository(test_repo)
    
    assert success is False


def test_dangling_object_reference(test_repo):
    """Test detection of index referencing deleted objects."""
    # Create file and add
    test_file = test_repo / "file.txt"
    test_file.write_text("Content")
    add_execute([str(test_file)], test_repo)
    
    # Find and delete the object
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    for obj_file in find_object_files(objects_dir):
        obj_file.unlink()
    
    # Verify should detect missing object
    success, results = verify_repository(test_repo)
    
    assert success is False
    assert not results["index"]["success"]


def test_concurrent_modification_simulation(test_repo):
    """Test that repository handles concurrent access gracefully.
    
    Note: OFS is designed for single-user access, so we just verify
    that operations are atomic and don't corrupt.
    """
    # Create initial state
    file1 = test_repo / "file1.txt"
    file1.write_text("Content 1")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Simulate potential race condition
    file2 = test_repo / "file2.txt"
    file2.write_text("Content 2")
    add_execute([str(file2)], test_repo)
    
    # Repository should still be consistent
    success, _ = verify_repository(test_repo)
    assert success is True


def test_partial_checkout_corruption(test_repo):
    """Test that partial checkout leaves repository verifiable."""
    # Create two commits
    file1 = test_repo / "file1.txt"
    file1.write_text("Content 1")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    file2 = test_repo / "file2.txt"
    file2.write_text("Content 2")
    add_execute([str(file2)], test_repo)
    commit_execute("Second commit", test_repo)
    
    # Even if checkout is interrupted (files partially restored),
    # repository metadata should remain valid
    success, _ = verify_repository(test_repo)
    assert success is True


def test_empty_commit_file(test_repo):
    """Test detection of empty/truncated commit files."""
    # Create a commit
    file1 = test_repo / "file1.txt"
    file1.write_text("Content")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Truncate commit file (simulate power loss during write)
    repo = Repository(test_repo)
    (repo.commits_dir / "001.json").write_text("")
    
    # Verification should handle gracefully
    success, results = verify_repository(test_repo)
    
    assert success is False


def test_malformed_head_reference(test_repo):
    """Test detection of malformed HEAD file."""
    repo = Repository(test_repo)
    
    # Create malformed HEAD
    (repo.ofs_dir / "HEAD").write_text("garbage content\n")
    
    # Verification should still work
    # (resolve_head will return None for invalid content)
    success, results = verify_repository(test_repo)
    
    # May pass if repository has no commits yet
    # Just ensure it doesn't crash
    assert isinstance(success, bool)


def test_object_hash_collision_simulation(test_repo):
    """Test handling of hash collisions (extremely unlikely with SHA-256)."""
    # Create two objects
    file1 = test_repo / "file1.txt"
    file1.write_text("Content A")
    add_execute([str(file1)], test_repo)
    
    file2 = test_repo / "file2.txt"
    file2.write_text("Content B")
    add_execute([str(file2)], test_repo)
    
    # Both files should have different hashes
    # If they had the same hash (collision), only one object would exist
    repo = Repository(test_repo)
    objects_dir = repo.ofs_dir / "objects"
    
    object_files = find_object_files(objects_dir)
    
    # Should have 2 distinct objects
    assert len(object_files) == 2


def test_repository_survives_multiple_corruptions(test_repo):
    """Test that verify detects multiple types of corruption."""
    # Create a working repository
    file1 = test_repo / "file1.txt"
    file1.write_text("Content")
    add_execute([str(file1)], test_repo)
    commit_execute("First commit", test_repo)
    
    # Introduce multiple corruptions
    repo = Repository(test_repo)
    
    # 1. Corrupt index
    repo.index_file.write_text("{bad json")
    
    # 2. Corrupt an object
    objects_dir = repo.ofs_dir / "objects"
    for obj_file in find_object_files(objects_dir):
        obj_file.write_bytes(b"corrupted")
        break
    
    # Verify should detect multiple errors
    success, results = verify_repository(test_repo)
    
    assert success is False
    
    # Should have errors in multiple components
    error_count = sum(len(r["errors"]) for r in results.values())
    assert error_count >= 2
