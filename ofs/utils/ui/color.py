"""Terminal color and formatting utilities.

This module provides zero-dependency ANSI escape sequence-based
terminal formatting, respecting the NO_COLOR standard.
"""

import os
import sys

# Standard ANSI escape sequences
_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_DIM = "\033[2m"

# Colors
_ANSI_RED = "\033[31m"
_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_BLUE = "\033[34m"
_ANSI_MAGENTA = "\033[35m"
_ANSI_CYAN = "\033[36m"
_ANSI_WHITE = "\033[37m"

# Global state to override color detection (for testing or --no-color flag)
_USE_COLOR_OVERRIDE = None


def _should_use_color() -> bool:
    """Determine if color output should be used.
    
    Checks:
    1. Explicit override (testing/flags)
    2. NO_COLOR environment variable
    3. If stdout/stderr is attached to a terminal (tty)
    """
    if _USE_COLOR_OVERRIDE is not None:
        return _USE_COLOR_OVERRIDE
        
    # Standard NO_COLOR check (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False
        
    # Check if we are in a terminal (not piped or redirected)
    # Using sys.stdout dynamically to support mocking in tests
    try:
        if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
            return False
    except AttributeError:
        # safe fallback if sys.stdout is replaced with something weird
        pass
        
    return True


def set_color_enabled(enabled: bool):
    """Explicitly enable or disable color output.
    
    Args:
        enabled: True to force color, False to disable color
    """
    global _USE_COLOR_OVERRIDE
    _USE_COLOR_OVERRIDE = enabled


def reset_color_override():
    """Reset color tracking to automatic environment detection."""
    global _USE_COLOR_OVERRIDE
    _USE_COLOR_OVERRIDE = None


def _format(text: str, code: str) -> str:
    """Apply an ANSI escape code to text if colors are enabled."""
    if not _should_use_color():
        return text
    return f"{code}{text}{_ANSI_RESET}"


# Color methods
def red(text: str) -> str:
    """Format text as red."""
    return _format(text, _ANSI_RED)


def green(text: str) -> str:
    """Format text as green."""
    return _format(text, _ANSI_GREEN)


def yellow(text: str) -> str:
    """Format text as yellow."""
    return _format(text, _ANSI_YELLOW)


def blue(text: str) -> str:
    """Format text as blue."""
    return _format(text, _ANSI_BLUE)


def magenta(text: str) -> str:
    """Format text as magenta."""
    return _format(text, _ANSI_MAGENTA)


def cyan(text: str) -> str:
    """Format text as cyan."""
    return _format(text, _ANSI_CYAN)


def white(text: str) -> str:
    """Format text as white."""
    return _format(text, _ANSI_WHITE)


# Style methods
def bold(text: str) -> str:
    """Format text as bold."""
    return _format(text, _ANSI_BOLD)


def dim(text: str) -> str:
    """Format text as dim/faint."""
    return _format(text, _ANSI_DIM)
