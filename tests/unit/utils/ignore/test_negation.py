"""Unit tests for ignore negation patterns."""

import pytest
from pathlib import Path

from ofs.utils.ignore.patterns import should_ignore, load_ignore_patterns


def test_negation_basic():
    """Test basic negation pattern."""
    patterns = ["*.log", "!important.log"]
    
    # Regular .log files should be ignored
    assert should_ignore(Path("test.log"), patterns) is True
    assert should_ignore(Path("debug.log"), patterns) is True
    
    # important.log should NOT be ignored (negated)
    assert should_ignore(Path("important.log"), patterns) is False


def test_negation_order_matters():
    """Test that pattern order matters for negation."""
    # Negate first, then ignore
    patterns1 = ["!important.log", "*.log"]
    assert should_ignore(Path("important.log"), patterns1) is True  # Ignored by *.log
    
    # Ignore first, then negate
    patterns2 = ["*.log", "!important.log"]
    assert should_ignore(Path("important.log"), patterns2) is False  # Un-ignored


def test_negation_directory():
    """Test negation for directories."""
    patterns = ["build/", "!build/config.json"]
    
    assert should_ignore(Path("build/output.txt"), patterns) is True
    assert should_ignore(Path("build/config.json"), patterns) is False


def test_negation_wildcard_then_specific():
    """Test wildcard pattern with specific file negation."""
    patterns = ["*.tmp", "!cache.tmp"]
    
    assert should_ignore(Path("test.tmp"), patterns) is True
    assert should_ignore(Path("data.tmp"), patterns) is True
    assert should_ignore(Path("cache.tmp"), patterns) is False


def test_multiple_negations():
    """Test multiple negation patterns."""
    patterns = ["*.log", "!important.log", "!critical.log"]
    
    assert should_ignore(Path("test.log"), patterns) is True
    assert should_ignore(Path("important.log"), patterns) is False
    assert should_ignore(Path("critical.log"), patterns) is False


def test_negation_with_path():
    """Test negation with path patterns."""
    patterns = ["logs/**", "!logs/keep.txt"]
    
    assert should_ignore(Path("logs/debug.log"), patterns) is True
    assert should_ignore(Path("logs/keep.txt"), patterns) is False


def test_negation_no_match():
    """Test negation pattern that doesn't match anything."""
    patterns = ["*.log", "!nonexistent.log"]
    
    # File that doesn't match negation is still ignored
    assert should_ignore(Path("test.log"), patterns) is True


def test_negation_empty_patterns():
    """Test with empty pattern list."""
    patterns = []
    
    assert should_ignore(Path("anyfile.txt"), patterns) is False


def test_negation_only():
    """Test with only negation patterns."""
    patterns = ["!keep.txt"]
    
    # Negation with no prior ignore has no effect
    assert should_ignore(Path("keep.txt"), patterns) is False
    assert should_ignore(Path("other.txt"), patterns) is False


def test_load_ignore_patterns_with_negation(tmp_path):
    """Test loading .ofsignore with negation patterns."""
    # Create .ofsignore with negation
    ofsignore = tmp_path / ".ofsignore"
    ofsignore.write_text(
        "# Ignore all logs\n"
        "*.log\n"
        "\n"
        "# But keep important ones\n"
        "!important.log\n"
        "!critical.log\n"
    )
    
    patterns = load_ignore_patterns(tmp_path)
    
    # Check default patterns are included
    assert ".ofs" in patterns
    assert "*.tmp" in patterns
    
    # Check custom patterns from .ofsignore
    assert "*.log" in patterns
    assert "!important.log" in patterns
    assert "!critical.log" in patterns
    
    # Test the patterns work
    assert should_ignore(Path("test.log"), patterns) is True
    assert should_ignore(Path("important.log"), patterns) is False


def test_complex_negation_scenario():
    """Test complex real-world scenario."""
    patterns = [
        "*.pyc",
        "*.log",
        "!important.pyc",
        "!critical.log"
    ]
    
    # .pyc files ignored
    assert should_ignore(Path("module.pyc"), patterns) is True
    assert should_ignore(Path("test.pyc"), patterns) is True
    
    # But important.pyc is not
    assert should_ignore(Path("important.pyc"), patterns) is False
    
    # .log files ignored
    assert should_ignore(Path("debug.log"), patterns) is True
    
    # But critical.log is not
    assert should_ignore(Path("critical.log"), patterns) is False
