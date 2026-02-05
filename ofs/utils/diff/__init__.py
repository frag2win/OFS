"""Diff utilities package."""

from ofs.utils.diff.compute import (
    is_binary,
    compute_file_diff,
    format_diff_header,
    compute_diff_stats,
)

__all__ = [
    'is_binary',
    'compute_file_diff',
    'format_diff_header',
    'compute_diff_stats',
]
