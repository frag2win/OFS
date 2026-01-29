"""Integration test for add and status workflow."""

import pytest
from pathlib import Path
from ofs.core.repository.init import Repository
from ofs.commands.add import execute as add_execute
from ofs.commands.status import execute as status_execute


def test_full_add_status_workflow(tmp_repo, capsys):
    """Test complete workflow: init → add files → status → modify → status."""
    # Initialize repository
    repo = Repository(tmp_repo)
    assert repo.initialize() is True
    
    # Create multiple files
    (tmp_repo / "file1.txt").write_text("File 1 content")
    (tmp_repo / "file2.txt").write_text("File 2 content")
    
    src_dir = tmp_repo / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")
    
    # Add files
    exit_code = add_execute(["file1.txt", "file2.txt", "src/"], tmp_repo)
    assert exit_code == 0
    
    # Check status shows staged files
    status_execute(tmp_repo)
    captured = capsys.readouterr()
    assert "Changes to be committed" in captured.out
    assert "file1.txt" in captured.out
    assert "file2.txt" in captured.out
    
    # Modify a file
    (tmp_repo / "file1.txt").write_text("Modified content")
    
    # Check status shows modification
    status_execute(tmp_repo)
    captured = capsys.readouterr()
    assert "Changes not staged" in captured.out or "modified" in captured.out
    
    # Add an untracked file
    (tmp_repo / "new_file.txt").write_text("New file")
    
    # Check status shows untracked
    status_execute(tmp_repo)
    captured = capsys.readouterr()
    assert "Untracked files" in captured.out
    assert "new_file.txt" in captured.out


def test_add_empty_directory_ignored(tmp_repo):
    """Test that empty directories are not added."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create empty directory
    empty_dir = tmp_repo / "empty"
    empty_dir.mkdir()
    
    # Try to add it
    exit_code = add_execute(["empty/"], tmp_repo)
    
    # Should return error (no files found)
    assert exit_code == 1


def test_add_with_ofsignore_file(tmp_repo):
    """Test that .ofsignore patterns are respected."""
    # Initialize repository
    repo = Repository(tmp_repo)
    repo.initialize()
    
    # Create .ofsignore
    ofsignore = tmp_repo / ".ofsignore"
    ofsignore.write_text("*.log\ntemp/\n")
    
    # Create files
    (tmp_repo / "important.txt").write_text("Keep this")
    (tmp_repo / "debug.log").write_text("Ignore this")
    
    temp_dir = tmp_repo / "temp"
    temp_dir.mkdir()
    (temp_dir / "cache.dat").write_text("Ignore this too")
    
    # Add all
    add_execute(["."], tmp_repo)
    
    # Verify only non-ignored files are staged
    from ofs.core.index.manager import Index
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    paths = {entry["path"] for entry in entries}
    
    assert "important.txt" in paths
    assert "debug.log" not in paths
    assert "temp/cache.dat" not in paths or "temp\\cache.dat" not in paths
