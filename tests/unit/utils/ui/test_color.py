"""Unit tests for terminal UI color utilities."""

import os
import sys
from unittest.mock import patch

from ofs.utils.ui.color import (
    red, green, yellow, bold, dim,
    set_color_enabled, reset_color_override, _should_use_color
)


def setup_function():
    """Reset state before each test."""
    reset_color_override()
    # Ensure NO_COLOR is not set for base tests
    if "NO_COLOR" in os.environ:
        del os.environ["NO_COLOR"]


def teardown_function():
    """Reset state after each test."""
    reset_color_override()
    if "NO_COLOR" in os.environ:
        del os.environ["NO_COLOR"]


@patch("sys.stdout.isatty")
def test_should_use_color_tty(mock_isatty):
    """Test color enabled when in TTY."""
    mock_isatty.return_value = True
    assert _should_use_color() is True


@patch("sys.stdout.isatty")
def test_should_not_use_color_piped(mock_isatty):
    """Test color disabled when output is piped/redirected."""
    mock_isatty.return_value = False
    assert _should_use_color() is False


@patch("sys.stdout.isatty")
def test_no_color_env_var(mock_isatty):
    """Test NO_COLOR environment variable overrides TTY."""
    mock_isatty.return_value = True
    os.environ["NO_COLOR"] = "1"
    
    assert _should_use_color() is False


@patch("sys.stdout.isatty")
def test_explicit_override(mock_isatty):
    """Test explicit override."""
    # Even if piped, if we force color, it should be True
    mock_isatty.return_value = False
    set_color_enabled(True)
    assert _should_use_color() is True
    
    # Even if in TTY, if we force no color, it should be False
    mock_isatty.return_value = True
    set_color_enabled(False)
    assert _should_use_color() is False


def test_color_formatting_enabled():
    """Test string formatting when colors are enabled."""
    set_color_enabled(True)
    
    assert red("text") == "\033[31mtext\033[0m"
    assert green("text") == "\033[32mtext\033[0m"
    assert yellow("text") == "\033[33mtext\033[0m"
    assert bold("text") == "\033[1mtext\033[0m"
    assert dim("text") == "\033[2mtext\033[0m"


def test_color_formatting_disabled():
    """Test string formatting when colors are disabled."""
    set_color_enabled(False)
    
    assert red("text") == "text"
    assert green("text") == "text"
    assert yellow("text") == "text"
    assert bold("text") == "text"
    assert dim("text") == "text"


def test_color_nesting():
    """Test color formatting doesn't break horribly (though we don't fully support reset stacks)."""
    set_color_enabled(True)
    # This is a known limitation of simple ANSI wrappers: the inner reset clears the outer color.
    # We mainly test that it doesn't crash.
    result = bold(red("text"))
    assert "text" in result
    assert "\033[1m" in result
    assert "\033[31m" in result
    assert "\033[0m" in result
