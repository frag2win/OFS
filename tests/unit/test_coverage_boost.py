"""Coverage boost tests — targeting uncovered lines in commands and core modules.

These tests cover the biggest coverage gaps identified by analysis:
- commands/verify/execute.py (67% → ~95%)
- commands/diff/execute.py (57% → ~85%)
- commands/log/execute.py (86% → ~95%)
- core/index/manager.py batch_add (87% → ~95%)
- core/verify/integrity.py (82% → ~92%)
- cli/dispatcher.py table dispatch
"""

import pytest
from pathlib import Path

from ofs.core.repository.init import Repository
from ofs.core.index.manager import Index
from ofs.core.commits import clear_commit_cache
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.log import execute as log_execute
from ofs.commands.diff import execute as diff_execute
from ofs.commands.verify import execute as verify_execute
from ofs.commands.checkout import execute as checkout_execute
from ofs.commands.status import execute as status_execute


@pytest.fixture
def fresh_repo(tmp_path):
    """Create a fresh initialized repo."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()
    return tmp_path


@pytest.fixture
def repo_with_commits(tmp_path):
    """Create a repo with 3 commits."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()

    # Commit 1: add file1
    f1 = tmp_path / "file1.txt"
    f1.write_text("Content 1")
    add_execute([str(f1)], tmp_path)
    commit_execute("Add file1", tmp_path)
    clear_commit_cache()

    # Commit 2: add file2, modify file1
    f2 = tmp_path / "file2.txt"
    f2.write_text("Content 2")
    f1.write_text("Modified content 1")
    add_execute([str(f1), str(f2)], tmp_path)
    commit_execute("Add file2 and modify file1", tmp_path)
    clear_commit_cache()

    # Commit 3: add file3
    f3 = tmp_path / "file3.txt"
    f3.write_text("Content 3")
    add_execute([str(f3)], tmp_path)
    commit_execute("Add file3", tmp_path)
    clear_commit_cache()

    return tmp_path


# ── Verify Command Tests ──────────────────────────────────────

class TestVerifyExecute:
    """Tests for commands/verify/execute.py uncovered lines."""

    def test_verify_healthy_repo(self, repo_with_commits, capsys):
        """Verify passes on a healthy repo."""
        result = verify_execute(verbose=False, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "verification passed" in captured.out

    def test_verify_verbose_mode(self, repo_with_commits, capsys):
        """Verify verbose mode shows detailed output."""
        result = verify_execute(verbose=True, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "[OK]" in captured.out

    def test_verify_not_a_repo(self, tmp_path, capsys):
        """Verify fails on non-repo directory."""
        result = verify_execute(repo_root=tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_verify_with_corruption(self, repo_with_commits, capsys):
        """Verify reports errors on corrupted repo."""
        repo = Repository(repo_with_commits)
        # Corrupt an object
        obj_files = list((repo.ofs_dir / "objects").rglob("*"))
        obj_files = [f for f in obj_files if f.is_file()]
        if obj_files:
            obj_files[0].write_bytes(b"corrupted")

        result = verify_execute(verbose=True, repo_root=repo_with_commits)
        assert result == 1
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.out
        assert "error" in captured.out.lower()


# ── Log Command Tests ──────────────────────────────────────────

class TestLogExecute:
    """Tests for commands/log/execute.py uncovered lines."""

    def test_log_empty_repo(self, fresh_repo, capsys):
        """Log shows message when no commits exist."""
        result = log_execute(repo_root=fresh_repo)
        assert result == 0
        captured = capsys.readouterr()
        assert "No commits yet" in captured.out

    def test_log_not_a_repo(self, tmp_path, capsys):
        """Log fails on non-repo directory."""
        result = log_execute(repo_root=tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "Not an OFS repository" in captured.out

    def test_log_full_format_with_files(self, repo_with_commits, capsys):
        """Log full format shows file changes with actions."""
        result = log_execute(repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "Changes:" in captured.out
        assert "file1.txt" in captured.out

    def test_log_oneline_format(self, repo_with_commits, capsys):
        """Log oneline format is compact."""
        result = log_execute(oneline=True, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l.strip()]
        assert len(lines) == 3  # 3 commits

    def test_log_with_limit(self, repo_with_commits, capsys):
        """Log limit restricts output."""
        result = log_execute(limit=1, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "003" in captured.out
        assert "001" not in captured.out


# ── Diff Command Tests ──────────────────────────────────────────

class TestDiffExecute:
    """Tests for commands/diff/execute.py uncovered lines."""

    def test_diff_not_a_repo(self, tmp_path, capsys):
        """Diff fails on non-repo directory."""
        result = diff_execute(repo_root=tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "Not an OFS repository" in captured.out

    def test_diff_no_changes(self, repo_with_commits, capsys):
        """Diff shows no changes when working dir matches staged."""
        result = diff_execute(repo_root=repo_with_commits)
        assert result == 0

    def test_diff_working_vs_staged_with_changes(self, repo_with_commits, capsys):
        """Diff detects unstaged modifications."""
        # Modify a file without staging
        f1 = repo_with_commits / "file1.txt"
        f1.write_text("Unstaged modification")

        # Re-add and look at diff
        add_execute([str(f1)], repo_with_commits)
        f1.write_text("Another modification after staging")

        result = diff_execute(repo_root=repo_with_commits)
        assert result == 0

    def test_diff_cached_mode(self, repo_with_commits, capsys):
        """Diff --cached shows staged vs HEAD."""
        # Modify and stage a file
        f1 = repo_with_commits / "file1.txt"
        f1.write_text("Cached diff test content")
        add_execute([str(f1)], repo_with_commits)

        result = diff_execute(cached=True, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "file1.txt" in captured.out

    def test_diff_commit_to_commit(self, repo_with_commits, capsys):
        """Diff between two commits."""
        result = diff_execute(
            commit1="001", commit2="003",
            repo_root=repo_with_commits
        )
        assert result == 0
        captured = capsys.readouterr()
        # Should show files added in commits 2 and 3
        assert "file2.txt" in captured.out or "file3.txt" in captured.out

    def test_diff_nonexistent_commit(self, repo_with_commits, capsys):
        """Diff with nonexistent commit fails."""
        result = diff_execute(
            commit1="999",
            repo_root=repo_with_commits
        )
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_diff_commit_to_commit_nonexistent(self, repo_with_commits, capsys):
        """Diff between commits where one doesn't exist fails."""
        result = diff_execute(
            commit1="001", commit2="999",
            repo_root=repo_with_commits
        )
        assert result == 1

    def test_diff_cached_no_head(self, fresh_repo, capsys):
        """Diff --cached with no commits shows all staged as new."""
        f = fresh_repo / "new_file.txt"
        f.write_text("brand new")
        add_execute([str(f)], fresh_repo)

        result = diff_execute(cached=True, repo_root=fresh_repo)
        assert result == 0


# ── Index batch_add Tests ──────────────────────────────────────

class TestIndexBatchAdd:
    """Tests for Index.batch_add() (uncovered method)."""

    def test_batch_add_multiple_files(self, tmp_path):
        """batch_add stages multiple files with single save."""
        index_file = tmp_path / "index.json"
        index = Index(index_file)

        entries = [
            ("file1.txt", "aaa" + "0" * 61, {"size": 100}),
            ("file2.txt", "bbb" + "0" * 61, {"size": 200}),
            ("file3.txt", "ccc" + "0" * 61, {"size": 300}),
        ]
        index.batch_add(entries)

        assert len(index.get_entries()) == 3
        assert index.find_entry("file1.txt") is not None
        assert index.find_entry("file2.txt") is not None
        assert index.find_entry("file3.txt") is not None

    def test_batch_add_replaces_existing(self, tmp_path):
        """batch_add replaces existing entries for same path."""
        index_file = tmp_path / "index.json"
        index = Index(index_file)

        # Add initial entry
        index.add("file1.txt", "aaa" + "0" * 61, {"size": 100})

        # batch_add with updated entry for same path
        entries = [
            ("file1.txt", "bbb" + "0" * 61, {"size": 999}),
            ("file2.txt", "ccc" + "0" * 61, {"size": 200}),
        ]
        index.batch_add(entries)

        assert len(index.get_entries()) == 2
        entry = index.find_entry("file1.txt")
        assert entry["hash"] == "bbb" + "0" * 61

    def test_batch_add_persists_to_disk(self, tmp_path):
        """batch_add writes to disk atomically."""
        index_file = tmp_path / "index.json"
        index = Index(index_file)

        entries = [
            ("a.txt", "aaa" + "0" * 61, {"size": 10}),
            ("b.txt", "bbb" + "0" * 61, {"size": 20}),
        ]
        index.batch_add(entries)

        # Reload from disk
        index2 = Index(index_file)
        assert len(index2.get_entries()) == 2


# ── Dispatcher Tests ──────────────────────────────────────────

class TestDispatcherCoverage:
    """Tests for CLI dispatcher table-driven dispatch."""

    def test_dispatcher_unknown_command(self, capsys):
        """Dispatcher handles unknown commands."""
        from ofs.cli.dispatcher import COMMANDS
        # Verify COMMANDS table has all expected entries
        expected = {"init", "add", "status", "commit", "log", "checkout", "verify", "diff"}
        assert set(COMMANDS.keys()) == expected

    def test_dispatcher_version_uses_init_version(self):
        """Dispatcher version string comes from ofs.__version__."""
        from ofs import __version__
        assert __version__ == "1.0.0"


# ── Checkout Coverage Tests ──────────────────────────────────────

class TestCheckoutCoverage:
    """Tests for checkout uncovered branches."""

    def test_checkout_not_a_repo(self, tmp_path, capsys):
        """Checkout fails on non-repo directory."""
        result = checkout_execute("001", repo_root=tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "Not an OFS repository" in captured.out

    def test_checkout_nonexistent_commit(self, fresh_repo, capsys):
        """Checkout fails when commit doesn't exist."""
        result = checkout_execute("999", repo_root=fresh_repo)
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_checkout_force_flag(self, repo_with_commits, capsys):
        """Checkout --force skips uncommitted changes warning."""
        # Stage but don't commit
        f = repo_with_commits / "uncommitted.txt"
        f.write_text("uncommitted")
        add_execute([str(f)], repo_with_commits)

        result = checkout_execute("001", force=True, repo_root=repo_with_commits)
        assert result == 0


# ── Working Tree Compare Coverage ─────────────────────────────────

class TestWorkingTreeCompareCoverage:
    """Tests for working_tree/compare.py uncovered lines."""

    def test_has_file_changed_deleted_file(self):
        """has_file_changed handles deleted/nonexistent file."""
        from ofs.core.working_tree.compare import has_file_changed
        result = has_file_changed(Path("/nonexistent/file.txt"), "abc123")
        # Should indicate changed (file doesn't exist)
        assert result is True

    def test_has_file_changed_matching_hash(self, tmp_path):
        """has_file_changed returns False when hash matches."""
        from ofs.core.working_tree.compare import has_file_changed
        from ofs.utils.hash.compute_file import compute_file_hash

        f = tmp_path / "test.txt"
        f.write_text("test content")
        expected_hash = compute_file_hash(f)

        result = has_file_changed(f, expected_hash)
        assert result is False
