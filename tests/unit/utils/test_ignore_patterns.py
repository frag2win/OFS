"""Tests for ignore pattern matching."""

import pytest
from pathlib import Path
from ofs.utils.ignore.patterns import should_ignore, load_ignore_patterns


class TestShouldIgnore:
    """Tests for should_ignore function."""
    
    def test_empty_patterns(self):
        """Empty patterns should match nothing."""
        assert not should_ignore(Path("file.txt"), [])
        assert not should_ignore(Path("any/path/here.py"), [])
    

    
    def test_simple_file_pattern(self):
        """Simple filename patterns."""
        patterns = ["*.pyc"]
        assert should_ignore(Path("file.pyc"), patterns)
        assert not should_ignore(Path("file.py"), patterns)
    
    def test_directory_pattern(self):
        """Directory patterns."""
        patterns = ["__pycache__"]
        assert should_ignore(Path("__pycache__"), patterns)
    
    def test_wildcard_patterns(self):
        """Wildcard * patterns."""
        patterns = ["*.log", "temp*"]
        assert should_ignore(Path("debug.log"), patterns)
        assert should_ignore(Path("temp_file.txt"), patterns)
        assert should_ignore(Path("temporary.dat"), patterns)
    
    def test_double_star_pattern(self):
        """Double star ** patterns for any directory."""
        patterns = ["**/build"]
        assert should_ignore(Path("build"), patterns)
    
    def test_multiple_extensions(self):
        """Multiple extension patterns."""
        patterns = ["*.pyc", "*.pyo", "*.pyd"]
        assert should_ignore(Path("module.pyc"), patterns)
        assert should_ignore(Path("module.pyo"), patterns)
        assert should_ignore(Path("module.pyd"), patterns)
        assert not should_ignore(Path("module.py"), patterns)
    
    def test_ofs_directory(self):
        """OFS directory should be ignored."""
        patterns = [".ofs", ".ofs/**"]
        assert should_ignore(Path(".ofs"), patterns)
    
    def test_with_repo_root(self, tmp_path):
        """Test with repo_root for relative path calculation."""
        patterns = ["*.log"]
        file_path = tmp_path / "logs" / "debug.log"
        assert should_ignore(file_path, patterns, tmp_path)
    
    def test_path_str_match(self):
        """Match against full path string."""
        patterns = ["logs/*.log"]
        assert should_ignore(Path("logs/error.log"), patterns)
    
    def test_name_vs_path_matching(self):
        """Pattern should match both name and path."""
        patterns = ["*.txt"]
        assert should_ignore(Path("subdir/file.txt"), patterns)
        assert should_ignore(Path("file.txt"), patterns)


class TestLoadIgnorePatterns:
    """Tests for load_ignore_patterns function."""
    
    def test_default_patterns_always_included(self, tmp_path):
        """Default patterns are always loaded."""
        patterns = load_ignore_patterns(tmp_path)
        assert ".ofs" in patterns
        assert "__pycache__" in patterns
        assert "*.tmp" in patterns
        assert "*.swp" in patterns
    
    def test_load_from_ofsignore(self, tmp_path):
        """Patterns loaded from .ofsignore file."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("*.log\n*.bak\n")
        
        patterns = load_ignore_patterns(tmp_path)
        assert "*.log" in patterns
        assert "*.bak" in patterns
    
    def test_comments_ignored(self, tmp_path):
        """Comment lines are not included."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("# This is a comment\n*.log\n")
        
        patterns = load_ignore_patterns(tmp_path)
        assert "# This is a comment" not in patterns
        assert "*.log" in patterns
    
    def test_empty_lines_ignored(self, tmp_path):
        """Empty lines are not included."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("*.log\n\n\n*.bak\n")
        
        patterns = load_ignore_patterns(tmp_path)
        assert "" not in patterns
    
    def test_missing_ofsignore(self, tmp_path):
        """Missing .ofsignore returns only defaults."""
        patterns = load_ignore_patterns(tmp_path)
        # Should have defaults but nothing from file
        assert ".ofs" in patterns
        assert len(patterns) == 6  # Default count
    
    def test_whitespace_stripped(self, tmp_path):
        """Whitespace around patterns is stripped."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("  *.log  \n\t*.bak\t\n")
        
        patterns = load_ignore_patterns(tmp_path)
        assert "*.log" in patterns
        assert "*.bak" in patterns


    def test_load_patterns_exception(self, tmp_path, monkeypatch):
        """Test exception handling during pattern loading (line 97)."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("*.log")
        
        # Mock read_text to raise exception
        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")
            
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        
        # Should return defaults only
        patterns = load_ignore_patterns(tmp_path)
        assert ".ofs" in patterns
        assert "*.log" not in patterns


class TestIgnoreEdgeCases:
    """Edge case tests."""
    
    def test_pattern_with_repo_root_value_error(self, tmp_path):
        """Handle ValueError when path not relative to repo_root."""
        patterns = ["*.log"]
        # Path not under repo_root
        other_path = Path("C:/completely/different/path/file.log")
        # Should not raise, should still match on name
        result = should_ignore(other_path, patterns, tmp_path)
        assert result  # Should match on filename
    
    def test_none_patterns(self):
        """Empty list patterns returns False."""
        assert not should_ignore(Path("file.txt"), [])
    
    def test_complex_path(self, tmp_path):
        """Complex nested paths."""
        patterns = ["**/node_modules"]
        # Match the directory name at least
        assert should_ignore(Path("node_modules"), patterns)

    def test_pattern_match_full_path(self, tmp_path):
        """Test matching against full path string (line 53)."""
        # Create a case where filename doesn't match, but full path does
        patterns = ["src/test/*.py"]
        # With repo_root, this becomes src/test/file.py
        file_path = tmp_path / "src" / "test" / "file.py"
        assert should_ignore(file_path, patterns, repo_root=tmp_path)

    def test_pattern_double_star_prefix(self, tmp_path):
        """Test matching with **/ prefix (line 57)."""
        patterns = ["**/temp.log"]
        assert should_ignore(Path("a/b/c/temp.log"), patterns)
        assert should_ignore(Path("temp.log"), patterns)

    def test_load_patterns_exception(self, tmp_path, monkeypatch):
        """Test exception handling during pattern loading (line 97)."""
        ignore_file = tmp_path / ".ofsignore"
        ignore_file.write_text("*.log")
        
        # Mock read_text to raise exception
        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")
            
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        
        # Should return defaults only, incorrectly swallowing exception is the behavior we test
        patterns = load_ignore_patterns(tmp_path)
        assert ".ofs" in patterns
        assert "*.log" not in patterns

