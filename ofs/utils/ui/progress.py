"""Terminal progress indicators.

This module provides zero-dependency progress bars and spinners
for long-running operations in OFS.
"""

import sys
import time
from typing import Optional


class ProgressBar:
    """A simple terminal progress bar.
    
    Attributes:
        total (int): Total number of items to process.
        description (str): Text to show before the progress bar.
        width (int): Width of the progress bar in characters.
        fill_char (str): Character to use for filled portion.
        empty_char (str): Character to use for empty portion.
    """
    
    def __init__(
        self, 
        total: int, 
        description: str = "", 
        width: int = 40,
        fill_char: str = "█",
        empty_char: str = "░"
    ):
        """Initialize progress bar."""
        self.total = max(1, total)  # Avoid division by zero
        self.description = description
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.current = 0
        self._last_update = 0.0
        self._disabled = False
        
        # Disable if not attached to a terminal
        try:
            if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
                self._disabled = True
        except AttributeError:
            pass
            
    def start(self):
        """Start the progress bar and print initial state."""
        if self._disabled:
            return
        self.update(0)
        
    def update(self, current: int, force: bool = False):
        """Update progress bar to current value.
        
        Args:
            current: Current progress value
            force: Force UI update ignoring time thresholds
        """
        self.current = min(current, self.total)
        
        if self._disabled:
            return
            
        # Rate limit updates to prevent terminal flickering (max ~20fps)
        now = time.time()
        if not force and now - self._last_update < 0.05 and self.current < self.total:
            return
            
        self._last_update = now
        
        # Calculate percentage and bar fill
        percent = self.current / self.total
        filled_len = int(self.width * percent)
        
        bar = self.fill_char * filled_len + self.empty_char * (self.width - filled_len)
        percent_str = f"{int(percent * 100):3d}%"
        count_str = f"{self.current}/{self.total}"
        
        desc = f"{self.description} " if self.description else ""
        
        # Use carriage return to overwrite current line
        line = f"\r{desc}|{bar}| {percent_str} ({count_str})"
        
        # Print and flush directly to stdout
        sys.stdout.write(line)
        sys.stdout.flush()
        
    def finish(self):
        """Complete the progress bar and move to next line."""
        if self._disabled:
            return
        self.update(self.total, force=True)
        sys.stdout.write("\n")
        sys.stdout.flush()


def track(sequence, description: str = "", total: Optional[int] = None):
    """Generator that yields items from sequence while updating a progress bar.
    
    Args:
        sequence: Iterable of items
        description: Text to show before progress bar
        total: Total items (if None, len(sequence) is used)
        
    Yields:
        Items from the sequence
    """
    if total is None:
        try:
            total = len(sequence)
        except TypeError:
            total = 100  # Fallback if length unknown
            
    bar = ProgressBar(total=total, description=description)
    bar.start()
    
    for i, item in enumerate(sequence, 1):
        yield item
        bar.update(i)
        
    bar.finish()
