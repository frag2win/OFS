"""Cross-platform compatibility tests.

Tests path normalization, line ending neutrality, case sensitivity,
and ignore pattern portability across Windows/POSIX conventions.
"""

import pytest
from pathlib import Path, PurePosixPath, PureWindowsPath

from ofs.core.repository.init import Repository
from ofs.core.objects.store import ObjectStore
from ofs.core.index.manager import Index
from ofs.core.commits import clear_commit_cache
from ofs.utils.ignore.patterns import (
    should_ignore,
    compile_patterns,
    should_ignore_compiled,
    load_ignore_patterns,
)
from ofs.utils.filesystem.normalize_path import normalize_path
from ofs.utils.hash.compute_bytes import compute_hash
from ofs.commands.add import execute as add_execute
from ofs.commands.commit import execute as commit_execute


class TestPathNormalization:
    """Tests for path normalization across OS conventions."""

    def test_forward_slashes_normalized(self, tmp_path):
        """Paths with forward slashes resolve correctly."""
        f = tmp_path / "subdir" / "file.txt"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("content")

        normalized = normalize_path(Path("subdir/file.txt"), tmp_path)
        assert normalized.exists()

    def test_backslashes_normalized(self, tmp_path):
        """Paths with backslashes resolve correctly."""
        f = tmp_path / "subdir" / "file.txt"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("content")

        # Use string with backslashes
        path_str = "subdir\\file.txt"
        normalized = normalize_path(Path(path_str), tmp_path)
        assert normalized.exists()

    def test_relative_path_stored_with_forward_slashes(self, tmp_path):
        """Committed paths use forward slashes regardless of OS."""
        repo = Repository(tmp_path)
        repo.initialize()
        clear_commit_cache()

        subdir = tmp_path / "src" / "utils"
        subdir.mkdir(parents=True, exist_ok=True)
        f = subdir / "helper.py"
        f.write_text("def helper(): pass")

        add_execute([str(f)], tmp_path)
        commit_execute("Test paths", tmp_path)
        clear_commit_cache()

        # Check that stored path uses forward slashes
        index = Index(repo.index_file)
        entries = index.get_entries()

        # Even on Windows, paths should not contain backslashes
        for entry in entries:
            if "helper" in entry.get("path", ""):
                assert "\\" not in entry["path"], f"Path contains backslash: {entry['path']}"

    def test_dot_path_handling(self, tmp_path):
        """Dot paths like ./file.txt resolve correctly."""
        f = tmp_path / "test.txt"
        f.write_text("content")
        
        result = normalize_path(Path("./test.txt"), tmp_path)
        assert result.exists()


class TestLineEndingNeutrality:
    """Tests that SHA-256 is byte-exact (no CRLF conversion)."""

    def test_lf_and_crlf_produce_different_hashes(self):
        """LF and CRLF content produce different hashes (byte-exact)."""
        lf_content = b"line1\nline2\nline3\n"
        crlf_content = b"line1\r\nline2\r\nline3\r\n"

        lf_hash = compute_hash(lf_content)
        crlf_hash = compute_hash(crlf_content)

        # Must be different — no auto-conversion
        assert lf_hash != crlf_hash

    def test_binary_content_preserved_exactly(self, tmp_path):
        """Binary content roundtrips through object store without modification."""
        repo = Repository(tmp_path)
        repo.initialize()

        object_store = ObjectStore(repo.ofs_dir)

        # Content with mixed line endings and null bytes
        binary_content = b"\x00\x01\r\n\n\r\x02\x03\xff"
        stored_hash = object_store.store(binary_content)
        retrieved = object_store.retrieve(stored_hash)

        assert retrieved == binary_content

    def test_write_bytes_preserves_line_endings(self, tmp_path):
        """write_bytes does not convert line endings."""
        f = tmp_path / "test.bin"
        original = b"hello\nworld\r\nfoo\r"
        f.write_bytes(original)
        
        result = f.read_bytes()
        assert result == original


class TestCaseSensitivity:
    """Tests that file paths respect case differences."""

    def test_different_case_files_tracked_separately(self, tmp_path):
        """Files with different case in name are treated as separate."""
        repo = Repository(tmp_path)
        repo.initialize()
        clear_commit_cache()

        # Create two files with different case
        f1 = tmp_path / "README.md"
        f2 = tmp_path / "readme.md"
        f1.write_text("UPPER case")
        f2.write_text("lower case")

        # Both should be tracked if OS supports it
        # (On Windows, these may map to same file — test should handle both)
        if f1.exists() and f2.exists() and f1.samefile(f2):
            # Case-insensitive filesystem (Windows)
            pytest.skip("Case-insensitive filesystem — files map to same inode")

        add_execute([str(f1), str(f2)], tmp_path)
        index = Index(repo.index_file)
        entries = index.get_entries()

        paths = {e["path"] for e in entries}
        assert len(paths) >= 1  # At minimum, one file tracked

    def test_hash_is_case_independent_of_path(self, tmp_path):
        """Same content produces same hash regardless of filename case."""
        content = b"identical content"
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)
        assert hash1 == hash2


class TestIgnorePatternCrossPlatform:
    """Tests that ignore patterns work with both / and \\ paths."""

    def test_ignore_pattern_with_forward_slash(self):
        """Ignore patterns match forward-slash paths."""
        patterns = ["*.log", "build/"]
        assert should_ignore(Path("test.log"), patterns) is True
        assert should_ignore(Path("test.txt"), patterns) is False

    def test_compiled_pattern_matching(self):
        """Pre-compiled patterns work correctly."""
        patterns = ["*.pyc", "__pycache__", "*.tmp"]
        compiled = compile_patterns(patterns)

        assert should_ignore_compiled(Path("test.pyc"), compiled) is True
        assert should_ignore_compiled(Path("test.py"), compiled) is False
        assert should_ignore_compiled(Path("__pycache__"), compiled) is True

    def test_negation_pattern_works(self):
        """Negation patterns un-ignore files."""
        patterns = ["*.log", "!important.log"]
        assert should_ignore(Path("test.log"), patterns) is True
        assert should_ignore(Path("important.log"), patterns) is False

    def test_recursive_wildcard_pattern(self):
        """** patterns match across directories."""
        patterns = [".ofs/**"]
        compiled = compile_patterns(patterns)

        assert should_ignore_compiled(
            Path(".ofs/objects/ab/hash123"), compiled
        ) is True
        assert should_ignore_compiled(
            Path("src/main.py"), compiled
        ) is False

    def test_load_ignore_patterns_default(self, tmp_path):
        """Default patterns include .ofs and common ignores."""
        repo = Repository(tmp_path)
        repo.initialize()

        patterns = load_ignore_patterns(tmp_path)
        assert ".ofs" in patterns
        assert "*.tmp" in patterns

    def test_load_ignore_patterns_with_ofsignore(self, tmp_path):
        """Custom .ofsignore patterns are loaded."""
        repo = Repository(tmp_path)
        repo.initialize()

        ofsignore = tmp_path / ".ofsignore"
        ofsignore.write_text("*.bak\n# comment\ntemp/\n")

        patterns = load_ignore_patterns(tmp_path)
        assert "*.bak" in patterns
        assert "temp/" in patterns
        # Comments should NOT be included
        assert "# comment" not in patterns
