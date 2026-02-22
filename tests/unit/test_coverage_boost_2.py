"""Second batch of coverage boost tests targeting remaining gaps.

Focuses heavily on edge cases, error handlers, and specific untracked lines
in diff/execute.py, commit/execute.py, and checkout/execute.py.
"""

import pytest
from pathlib import Path

from ofs.core.repository.init import Repository
from ofs.core.commits import clear_commit_cache
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.diff import execute as diff_execute
from ofs.commands.checkout import execute as checkout_execute


@pytest.fixture
def repo_with_commits(tmp_path):
    """Create a repo with commits."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()

    f1 = tmp_path / "file1.txt"
    f1.write_text("content 1")
    add_execute([str(f1)], tmp_path)
    commit_execute("Initial commit", tmp_path)
    clear_commit_cache()
    
    return tmp_path


# ── Diff coverage: _diff_working_vs_commit (lines 226-279) ─────────

class TestDiffWorkingVsCommit:
    """Tests for diff between working directory and a specific commit."""
    
    def test_diff_working_vs_commit_no_changes(self, repo_with_commits, capsys):
        """Diff against HEAD with no working tree changes."""
        result = diff_execute(commit1="001", repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "No differences" in captured.out
        
    def test_diff_working_vs_commit_modified(self, repo_with_commits, capsys):
        """Diff against commit with modified file."""
        f1 = repo_with_commits / "file1.txt"
        f1.write_text("modified content")
        
        result = diff_execute(commit1="001", repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "modified file" in captured.out
        assert "file1.txt" in captured.out
        
    def test_diff_working_vs_commit_deleted(self, repo_with_commits, capsys):
        """Diff against commit with deleted file."""
        f1 = repo_with_commits / "file1.txt"
        f1.unlink()
        
        result = diff_execute(commit1="001", repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "deleted file: file1.txt" in captured.out
        
    def test_diff_working_vs_commit_new(self, repo_with_commits, capsys):
        """Diff against commit with new file in working tree."""
        f2 = repo_with_commits / "file2.txt"
        f2.write_text("new content")
        
        result = diff_execute(commit1="001", repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "new file" in captured.out
        assert "file2.txt" in captured.out


# ── Commit coverage gaps ──────────────────────────────────────────

class TestCommitCoverageGaps:
    
    def test_commit_no_changes_vs_parent(self, repo_with_commits, capsys):
        """Commit fails if staging area matches HEAD exactly."""
        # file1.txt is already in HEAD with "content 1".
        # Let's re-add it unchanged.
        f1 = repo_with_commits / "file1.txt"
        add_execute([str(f1)], repo_with_commits)
        
        result = commit_execute("redundant commit", repo_root=repo_with_commits)
        assert result == 1
        captured = capsys.readouterr()
        assert "No changes to commit" in captured.out

    def test_commit_not_a_repo(self, tmp_path, capsys):
        """Commit fails when not in a repo."""
        result = commit_execute("message", repo_root=tmp_path)
        assert result == 1
        captured = capsys.readouterr()
        assert "Not an OFS repository" in captured.out


# ── Checkout coverage gaps ────────────────────────────────────────

class TestCheckoutCoverageGaps:
    
    def test_checkout_uncommitted_changes_cancelled(self, repo_with_commits, capsys, monkeypatch):
        """Checkout cancelled when user inputs 'N' to warning."""
        f2 = repo_with_commits / "file2.txt"
        f2.write_text("staged but not committed")
        add_execute([str(f2)], repo_with_commits)
        
        # Mock input to return "n"
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        
        result = checkout_execute("001", force=False, repo_root=repo_with_commits)
        assert result == 1
        captured = capsys.readouterr()
        assert "Checkout cancelled" in captured.out

    def test_checkout_corrupted_commit_missing_hash(self, repo_with_commits, capsys):
        """Checkout fails if commit JSON is missing 'hash' for a file."""
        import json
        repo = Repository(repo_with_commits)
        commit_file = repo.commits_dir / "001.json"
        
        # Break the commit structure
        data = json.loads(commit_file.read_text())
        data["files"][0].pop("hash", None)
        commit_file.write_text(json.dumps(data))
        clear_commit_cache()
        
        result = checkout_execute("001", force=True, repo_root=repo_with_commits)
        assert result == 1
        captured = capsys.readouterr()
        assert "Commit corrupted" in captured.out
        
    def test_checkout_write_failure(self, repo_with_commits, monkeypatch, capsys):
        """Checkout handles file write errors gracefully."""
        # Create a second commit
        f2 = repo_with_commits / "file2.txt"
        f2.write_text("content 2")
        add_execute([str(f2)], repo_with_commits)
        commit_execute("Commit 2", repo_root=repo_with_commits)
        clear_commit_cache()
        
        # Now checkout 001, but make it fail to unlink file2.txt
        original_unlink = Path.unlink
        def mock_unlink(self, *args, **kwargs):
            if "file2.txt" in str(self):
                raise OSError("Mock unlink error")
            return original_unlink(self, *args, **kwargs)
            
        monkeypatch.setattr(Path, "unlink", mock_unlink)
        
        # It's a warning, not a hard crash, checkout still finishes
        result = checkout_execute("001", force=True, repo_root=repo_with_commits)
        assert result == 0
        captured = capsys.readouterr()
        assert "Warning: Could not remove file2.txt" in captured.out
