"""Unit tests for terminal progress indicators."""

import sys
from io import StringIO
from unittest.mock import patch

from ofs.utils.ui.progress import ProgressBar, track


def test_progressbar_initialization():
    """Test progress bar initialization and attribute setting."""
    bar = ProgressBar(total=100, description="Testing", width=20)
    assert bar.total == 100
    assert bar.description == "Testing"
    assert bar.width == 20
    assert bar.current == 0


@patch("sys.stdout", new_callable=StringIO)
def test_progressbar_update(mock_stdout):
    """Test progress bar output formatting."""
    # Force attached to TTY for testing
    mock_stdout.isatty = lambda: True
    
    bar = ProgressBar(total=10, description="Task", width=10, fill_char="X", empty_char="-")
    
    # Needs force=True to bypass rate limiting in tests
    bar.update(5, force=True)
    
    output = mock_stdout.getvalue()
    assert "\rTask |" in output
    assert "XXXXX-----" in output  # 50% fill
    assert " 50%" in output
    assert "(5/10)" in output


@patch("sys.stdout", new_callable=StringIO)
def test_progressbar_finish(mock_stdout):
    """Test progress bar finish outputs a newline."""
    mock_stdout.isatty = lambda: True
    
    bar = ProgressBar(total=10)
    bar.finish()
    
    output = mock_stdout.getvalue()
    assert "\n" in output
    assert "100%" in output


@patch("sys.stdout.isatty")
def test_progressbar_disabled_when_piped(mock_isatty):
    """Test progress bar disables itself when output is piped."""
    mock_isatty.return_value = False
    
    bar = ProgressBar(total=10)
    assert bar._disabled is True


@patch("sys.stdout", new_callable=StringIO)
def test_track_generator(mock_stdout):
    """Test the track generator wrapper."""
    mock_stdout.isatty = lambda: True
    
    items = [1, 2, 3]
    result = list(track(items, description="Loop"))
    
    assert result == [1, 2, 3]
    
    output = mock_stdout.getvalue()
    assert "Loop" in output
    assert "100%" in output
    assert "\n" in output


@patch("sys.stdout", new_callable=StringIO)
def test_progressbar_zero_total(mock_stdout):
    """Test progress bar handles zero total gracefully."""
    mock_stdout.isatty = lambda: True
    
    # Should automatically convert 0 to 1 to prevent division by zero
    bar = ProgressBar(total=0)
    assert bar.total == 1
    
    bar.update(0, force=True)
    assert "0/1" in mock_stdout.getvalue()
