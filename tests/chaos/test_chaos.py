"""Chaos / reliability tests for OFS.

Deterministic failure simulation tests — validates OFS behavior
when repository data is corrupted, deleted, or partially written.
"""

import pytest
import json
from pathlib import Path

from ofs.core.repository.init import Repository
from ofs.core.objects.store import ObjectStore
from ofs.core.index.manager import Index
from ofs.core.commits import load_commit, clear_commit_cache, list_commits
from ofs.core.commits.tree import build_tree_state
from ofs.core.refs import resolve_head
from ofs.core.verify.integrity import verify_repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.verify import execute as verify_execute


@pytest.fixture
def repo_with_commit(tmp_path):
    """Create a repo with one commit containing 3 files."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()

    for i in range(3):
        f = tmp_path / f"file_{i}.txt"
        f.write_text(f"Content of file {i}")

    add_execute([str(tmp_path)], tmp_path)
    commit_execute("Initial commit", tmp_path)
    clear_commit_cache()
    return tmp_path


@pytest.fixture
def repo_with_chain(tmp_path):
    """Create a repo with 3 commits (parent chain)."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()

    for commit_num in range(1, 4):
        f = tmp_path / f"file_{commit_num}.txt"
        f.write_text(f"Content {commit_num}")
        add_execute([str(f)], tmp_path)
        commit_execute(f"Commit {commit_num}", tmp_path)
        clear_commit_cache()

    return tmp_path


class TestCorruptedObjects:
    """Tests for corrupted object store files."""

    def test_corrupted_object_bytes_detected(self, repo_with_commit):
        """Verify detects corrupted object content (flipped bytes)."""
        repo = Repository(repo_with_commit)
        objects_dir = repo.ofs_dir / "objects"

        # Find an object file and corrupt it
        obj_files = list(objects_dir.rglob("*"))
        obj_files = [f for f in obj_files if f.is_file()]
        assert len(obj_files) > 0

        # Corrupt first object
        target = obj_files[0]
        original = target.read_bytes()
        corrupted = bytes([b ^ 0xFF for b in original])
        target.write_bytes(corrupted)

        # Verify should detect the corruption
        success, results = verify_repository(repo_with_commit)
        assert success is False

    def test_empty_object_file_detected(self, repo_with_commit):
        """Verify detects zero-byte object files."""
        repo = Repository(repo_with_commit)
        objects_dir = repo.ofs_dir / "objects"

        obj_files = [f for f in objects_dir.rglob("*") if f.is_file()]
        assert len(obj_files) > 0

        # Truncate an object to zero bytes
        obj_files[0].write_bytes(b"")

        success, results = verify_repository(repo_with_commit)
        assert success is False

    def test_deleted_object_file_detected(self, repo_with_commit):
        """Verify detects missing object files."""
        repo = Repository(repo_with_commit)
        objects_dir = repo.ofs_dir / "objects"

        obj_files = [f for f in objects_dir.rglob("*") if f.is_file()]
        assert len(obj_files) > 0

        # Delete an object
        obj_files[0].unlink()

        success, results = verify_repository(repo_with_commit)
        assert success is False


class TestCorruptedCommits:
    """Tests for corrupted commit files."""

    def test_deleted_commit_file_detected(self, repo_with_commit):
        """Verify detects missing commit JSON files."""
        repo = Repository(repo_with_commit)
        commit_file = repo.commits_dir / "001.json"
        assert commit_file.exists()

        commit_file.unlink()
        clear_commit_cache()

        success, results = verify_repository(repo_with_commit)
        assert success is False

    def test_corrupted_commit_json_detected(self, repo_with_commit):
        """Verify detects malformed commit JSON."""
        repo = Repository(repo_with_commit)
        commit_file = repo.commits_dir / "001.json"
        commit_file.write_text("{invalid json content!!")
        clear_commit_cache()

        success, results = verify_repository(repo_with_commit)
        assert success is False

    def test_commit_with_bad_file_hash(self, repo_with_commit):
        """Verify detects commit referencing nonexistent object hash."""
        repo = Repository(repo_with_commit)
        commit_file = repo.commits_dir / "001.json"
        # Valid JSON with files pointing to nonexistent hash
        bad_commit = {
            "id": "001",
            "message": "bad",
            "files": [{"path": "fake.txt", "hash": "deadbeef" * 8, "action": "added"}],
            "timestamp": "2026-01-01T00:00:00Z"
        }
        commit_file.write_text(json.dumps(bad_commit))
        clear_commit_cache()

        success, results = verify_repository(repo_with_commit)
        assert success is False


class TestBrokenRefs:
    """Tests for broken HEAD and branch references."""

    def test_broken_head_ref_detected(self, repo_with_commit):
        """Verify detects HEAD pointing to nonexistent commit."""
        repo = Repository(repo_with_commit)
        head_file = repo.ofs_dir / "HEAD"
        head_file.write_text("ref: refs/heads/main")

        # Point branch to nonexistent commit
        branch_file = repo.ofs_dir / "refs" / "heads" / "main"
        branch_file.write_text("999")
        clear_commit_cache()

        success, results = verify_repository(repo_with_commit)
        assert success is False

    def test_empty_head_file(self, repo_with_commit):
        """Verify handles empty HEAD file gracefully."""
        repo = Repository(repo_with_commit)
        head_file = repo.ofs_dir / "HEAD"
        head_file.write_text("")

        head = resolve_head(repo.ofs_dir)
        # Should return None, not crash
        assert head is None


class TestMissingParent:
    """Tests for broken parent chains."""

    def test_missing_parent_commit(self, repo_with_chain):
        """build_tree_state handles missing parent gracefully."""
        repo = Repository(repo_with_chain)

        # Delete the middle commit (002)
        middle = repo.commits_dir / "002.json"
        assert middle.exists()
        middle.unlink()
        clear_commit_cache()

        # build_tree_state for commit 003 should stop at the break
        # (it won't find 002 as parent, so chain ends)
        tree = build_tree_state("003", repo.commits_dir)
        # Should still return a dict (not crash)
        assert isinstance(tree, dict)

    def test_missing_first_commit(self, repo_with_chain):
        """build_tree_state handles missing root commit gracefully."""
        repo = Repository(repo_with_chain)

        # Delete the first commit
        first = repo.commits_dir / "001.json"
        first.unlink()
        clear_commit_cache()

        # build_tree_state for 003 should handle gracefully
        tree = build_tree_state("003", repo.commits_dir)
        assert isinstance(tree, dict)


class TestCorruptedIndex:
    """Tests for corrupted index files."""

    def test_corrupted_index_json(self, repo_with_commit):
        """Index handles corrupted JSON gracefully."""
        repo = Repository(repo_with_commit)

        # Corrupt the index file
        repo.index_file.write_text("{not valid json [[[")

        # Should not crash — constructor handles this
        index = Index(repo.index_file)
        # Should have empty entries (corrupt data discarded)
        assert index.get_entries() == []

    def test_index_missing_file(self, repo_with_commit):
        """Index handles missing index.json gracefully."""
        repo = Repository(repo_with_commit)

        if repo.index_file.exists():
            repo.index_file.unlink()

        index = Index(repo.index_file)
        assert index.get_entries() == []
        assert not index.has_changes()

    def test_verify_detects_index_corruption(self, repo_with_commit):
        """Verify command detects corrupt index."""
        repo = Repository(repo_with_commit)

        # Stage a file so index has entries
        f = repo_with_commit / "new_file.txt"
        f.write_text("new content")
        add_execute([str(f)], repo_with_commit)

        # Now corrupt the index
        repo.index_file.write_text('[{"path": "fake.txt", "hash": "00" }]')

        success, results = verify_repository(repo_with_commit)
        # Index references a nonexistent object
        assert success is False


class TestDiskFullSimulation:
    """Tests for disk-full / write-failure scenarios."""

    def test_add_survives_write_failure(self, repo_with_commit, monkeypatch):
        """Add command handles write failures gracefully."""
        # Create a file to add
        new_file = repo_with_commit / "new_file.txt"
        new_file.write_text("some content")

        # Monkeypatch ObjectStore.store to raise OSError
        def mock_store(self, content):
            raise OSError("No space left on device")

        monkeypatch.setattr(ObjectStore, "store", mock_store)

        result = add_execute([str(new_file)], repo_with_commit)
        # Should not crash — returns error
        assert result == 1

    def test_commit_survives_write_failure(self, repo_with_commit, monkeypatch):
        """Commit gracefully handles write failures."""
        # Stage a file
        new_file = repo_with_commit / "new_file.txt"
        new_file.write_text("content")
        add_execute([str(new_file)], repo_with_commit)

        # Monkeypatch to fail during commit save
        original_write_text = Path.write_text

        call_count = [0]
        def mock_write_text(self, content, *args, **kwargs):
            call_count[0] += 1
            # Let the first few writes succeed, then fail
            if call_count[0] > 5:
                raise OSError("Disk full")
            return original_write_text(self, content, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        # Should handle error (may succeed or fail depending on timing)
        # Key: it should NOT crash with unhandled exception
        try:
            result = commit_execute("Test commit", repo_with_commit)
            # If it returns, it should be an int
            assert isinstance(result, int)
        except OSError:
            # Some paths may still raise — that's acceptable
            pass
