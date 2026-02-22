"""Performance benchmarks for OFS operations.

Run with: pytest tests/performance/ -s --no-header
The -s flag is required to see timing output.

These tests measure and report wall-clock time. They do NOT assert
hard timing thresholds — performance varies across machines.
"""

import pytest
import time
from pathlib import Path

from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute
from ofs.commands.checkout import execute as checkout_execute
from ofs.commands.verify import execute as verify_execute
from ofs.commands.diff import execute as diff_execute
from ofs.core.commits import clear_commit_cache


def _create_files(directory: Path, count: int, size: int = 1024) -> list:
    """Create N files of given size in directory."""
    files = []
    for i in range(count):
        subdir = directory / f"dir_{i // 100}"
        subdir.mkdir(parents=True, exist_ok=True)
        f = subdir / f"file_{i:04d}.txt"
        f.write_bytes(bytes(f"File {i} content padding " * (size // 25 + 1), "utf-8")[:size])
        files.append(f)
    return files


def _setup_repo(tmp_path: Path) -> Path:
    """Initialize a fresh OFS repo."""
    repo = Repository(tmp_path)
    repo.initialize()
    clear_commit_cache()
    return tmp_path


def _measure(label: str, func):
    """Measure and print wall-clock time for a function."""
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    print(f"  {label}: {elapsed:.3f}s")
    return result, elapsed


class TestBenchmarks:
    """Performance benchmarks — measure and report, no hard assertions."""

    def test_add_100_files(self, tmp_path, capsys):
        """Benchmark: staging 100 files."""
        repo_root = _setup_repo(tmp_path)
        _create_files(repo_root, 100)

        print("\n--- Benchmark: Add 100 files (1KB each) ---")
        result, elapsed = _measure("ofs add .", lambda: add_execute(
            [str(repo_root)], repo_root
        ))
        assert result == 0, "add failed"
        print(f"  Files/sec: {100 / elapsed:.0f}")

    def test_add_1000_files(self, tmp_path, capsys):
        """Benchmark: staging 1000 files."""
        repo_root = _setup_repo(tmp_path)
        _create_files(repo_root, 1000)

        print("\n--- Benchmark: Add 1000 files (1KB each) ---")
        result, elapsed = _measure("ofs add .", lambda: add_execute(
            [str(repo_root)], repo_root
        ))
        assert result == 0, "add failed"
        print(f"  Files/sec: {1000 / elapsed:.0f}")

    def test_commit_1000_files(self, tmp_path, capsys):
        """Benchmark: committing 1000 pre-staged files."""
        repo_root = _setup_repo(tmp_path)
        _create_files(repo_root, 1000)

        # Pre-stage
        add_execute([str(repo_root)], repo_root)
        clear_commit_cache()

        print("\n--- Benchmark: Commit 1000 files ---")
        result, elapsed = _measure("ofs commit", lambda: commit_execute(
            "Benchmark commit with 1000 files", repo_root
        ))
        assert result == 0, "commit failed"

    def test_checkout_1000_files(self, tmp_path, capsys):
        """Benchmark: checkout restoring 1000 files."""
        repo_root = _setup_repo(tmp_path)
        _create_files(repo_root, 1000)

        # Stage + commit
        add_execute([str(repo_root)], repo_root)
        commit_execute("Base commit", repo_root)
        clear_commit_cache()

        # Create a second commit with more files
        for i in range(5):
            f = repo_root / f"extra_{i}.txt"
            f.write_text(f"Extra {i}")
        add_execute([str(repo_root)], repo_root)
        commit_execute("Second commit", repo_root)
        clear_commit_cache()

        print("\n--- Benchmark: Checkout 1000 files (back to 001) ---")
        result, elapsed = _measure("ofs checkout 001", lambda: checkout_execute(
            "001", force=True, repo_root=repo_root
        ))
        assert result == 0, "checkout failed"

    def test_verify_1000_objects(self, tmp_path, capsys):
        """Benchmark: verifying repo with ~1000 objects."""
        repo_root = _setup_repo(tmp_path)
        _create_files(repo_root, 1000)

        add_execute([str(repo_root)], repo_root)
        commit_execute("Benchmark commit", repo_root)
        clear_commit_cache()

        print("\n--- Benchmark: Verify ~1000 objects ---")
        result, elapsed = _measure("ofs verify", lambda: verify_execute(
            verbose=False, repo_root=repo_root
        ))
        assert result == 0, "verify failed"

    def test_diff_500_changed_files(self, tmp_path, capsys):
        """Benchmark: diff with 500 modified files."""
        repo_root = _setup_repo(tmp_path)
        files = _create_files(repo_root, 500)

        # Stage + commit
        add_execute([str(repo_root)], repo_root)
        commit_execute("Base commit", repo_root)
        clear_commit_cache()

        # Modify all 500 files
        for f in files:
            f.write_text(f"MODIFIED {f.name}")

        print("\n--- Benchmark: Diff 500 changed files ---")
        result, elapsed = _measure("ofs diff", lambda: diff_execute(
            repo_root=repo_root
        ))
        # diff returns 0 regardless of whether changes exist
        print(f"  Files/sec: {500 / elapsed:.0f}")
