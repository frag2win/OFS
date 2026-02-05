"""Unit tests for diff computation utilities."""

import pytest
from pathlib import Path

from ofs.utils.diff.compute import (
    is_binary,
    compute_file_diff,
    format_diff_header,
    compute_diff_stats,
)


def test_is_binary_text_file():
    """Test binary detection for text files."""
    text_content = b"This is plain text\nWith multiple lines\n"
    assert is_binary(text_content) is False


def test_is_binary_file_with_null():
    """Test binary detection for files with null bytes."""
    binary_content = b"Some text\x00more text"
    assert is_binary(binary_content) is True


def test_is_binary_empty_file():
    """Test binary detection for empty files."""
    assert is_binary(b"") is False


def test_compute_file_diff_text_modification():
    """Test diff for modified text file."""
    old_content = b"line 1\nline 2\nline 3\n"
    new_content = b"line 1\nmodified line 2\nline 3\n"
    
    diff = compute_file_diff(
        old_content,
        new_content,
        "file.txt",
        "file.txt"
    )
    
    assert len(diff) > 0
    assert any("-line 2" in line for line in diff)
    assert any("+modified line 2" in line for line in diff)


def test_compute_file_diff_binary_files():
    """Test diff for binary files."""
    old_content = b"binary\x00content"
    new_content = b"different\x00binary"
    
    diff = compute_file_diff(
        old_content,
        new_content,
        "file.bin",
        "file.bin"
    )
    
    assert len(diff) == 1
    assert "Binary files" in diff[0]


def test_compute_file_diff_identical_files():
    """Test diff for identical files."""
    content = b"same content\n"
    
    diff = compute_file_diff(
        content,
        content,
        "file.txt",
        "file.txt"
    )
    
    assert len(diff) == 0


def test_compute_file_diff_new_file():
    """Test diff for new file (empty old content)."""
    new_content = b"new file\ncontent\n"
    
    diff = compute_file_diff(
        b"",
        new_content,
        "file.txt",
        "file.txt"
    )
    
    assert len(diff) > 0
    assert any("+new file" in line for line in diff)


def test_compute_file_diff_deleted_file():
    """Test diff for deleted file (empty new content)."""
    old_content = b"deleted file\ncontent\n"
    
    diff = compute_file_diff(
        old_content,
        b"",
        "file.txt",
        "file.txt"
    )
    
    assert len(diff) > 0
    assert any("-deleted file" in line for line in diff)


def test_format_diff_header_modified():
    """Test diff header for modified file."""
    header = format_diff_header("file.txt", "file.txt", "modified")
    
    assert len(header) == 1
    assert "diff --ofs a/file.txt b/file.txt" in header[0]


def test_format_diff_header_new():
    """Test diff header for new file."""
    header = format_diff_header("file.txt", "file.txt", "new")
    
    assert len(header) == 2
    assert "diff --ofs" in header[0]
    assert "new file" in header[1]


def test_format_diff_header_deleted():
    """Test diff header for deleted file."""
    header = format_diff_header("file.txt", "file.txt", "deleted")
    
    assert len(header) == 2
    assert "diff --ofs" in header[0]
    assert "deleted file" in header[1]


def test_compute_diff_stats():
    """Test diff statistics computation."""
    diff_lines = [
        "--- a/file.txt",
        "+++ b/file.txt",
        "@@ -1,3 +1,3 @@",
        " line 1",
        "-old line 2",
        "+new line 2",
        " line 3",
        "+added line 4"
    ]
    
    additions, deletions = compute_diff_stats(diff_lines)
    
    assert additions == 2  # "new line 2" and "added line 4"
    assert deletions == 1  # "old line 2"


def test_compute_diff_stats_no_changes():
    """Test diff stats for no changes."""
    diff_lines = []
    
    additions, deletions = compute_diff_stats(diff_lines)
    
    assert additions == 0
    assert deletions == 0
