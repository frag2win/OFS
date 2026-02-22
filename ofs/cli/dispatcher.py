"""CLI dispatcher - routes commands to their handlers.

Uses a table-driven command mapping for maintainability.
"""

import sys
import argparse

from ofs import __version__


# ── Command handler functions ──────────────────────────────────────

def _handle_init(args) -> int:
    from ofs.core.repository.init import Repository
    repo = Repository()
    success = repo.initialize()
    return 0 if success else 1


def _handle_add(args) -> int:
    from ofs.commands.add import execute
    return execute(args.paths)


def _handle_status(args) -> int:
    from ofs.commands.status import execute
    return execute()


def _handle_commit(args) -> int:
    from ofs.commands.commit import execute
    return execute(args.message)


def _handle_log(args) -> int:
    from ofs.commands.log import execute
    return execute(
        limit=getattr(args, 'number', None),
        oneline=getattr(args, 'oneline', False),
    )


def _handle_checkout(args) -> int:
    from ofs.commands.checkout import execute
    return execute(
        args.commit_id,
        force=getattr(args, 'force', False),
    )


def _handle_verify(args) -> int:
    from ofs.commands.verify import execute
    return execute(
        verbose=getattr(args, 'verbose', False),
    )


def _handle_diff(args) -> int:
    from ofs.commands.diff import execute
    return execute(
        commit1=getattr(args, 'commit1', None) or None,
        commit2=getattr(args, 'commit2', None) or None,
        cached=getattr(args, 'cached', False),
    )


# ── Command dispatch table ────────────────────────────────────────

COMMANDS = {
    "init":     _handle_init,
    "add":      _handle_add,
    "status":   _handle_status,
    "commit":   _handle_commit,
    "log":      _handle_log,
    "checkout": _handle_checkout,
    "verify":   _handle_verify,
    "diff":     _handle_diff,
}


# ── Main entry point ──────────────────────────────────────────────

def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="ofs",
        description="OFS - Offline File System: Local-first version control for air-gapped environments",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"OFS {__version__}",
        help="Show program's version number and exit"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize a new OFS repository")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add files to staging area")
    add_parser.add_argument("paths", nargs="+", help="Files or directories to add")
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Create a new commit")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    
    # Status command
    subparsers.add_parser("status", help="Show repository status")
    
    # Log command
    log_parser = subparsers.add_parser("log", help="Show commit history")
    log_parser.add_argument("-n", "--number", type=int, help="Limit number of commits shown")
    log_parser.add_argument("--oneline", action="store_true", help="Show compact format")
    
    # Checkout command
    checkout_parser = subparsers.add_parser("checkout", help="Checkout a commit")
    checkout_parser.add_argument("commit_id", help="Commit ID to checkout")
    checkout_parser.add_argument("--force", action="store_true", help="Discard local changes")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify repository integrity")
    verify_parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Show changes")
    diff_parser.add_argument("commit1", nargs="?", help="First commit (optional)")
    diff_parser.add_argument("commit2", nargs="?", help="Second commit (optional)")
    diff_parser.add_argument("--cached", action="store_true", help="Show staged changes vs HEAD")
    
    args = parser.parse_args()
    
    # Handle global flags
    if hasattr(args, 'no_color') and args.no_color:
        from ofs.utils.ui.color import set_color_enabled
        set_color_enabled(False)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Table-driven dispatch
    handler = COMMANDS.get(args.command)
    
    if handler is None:
        print(f"OFS: Command '{args.command}' not yet implemented")
        print(f"Available: {', '.join(COMMANDS.keys())}")
        return 1
    
    try:
        return handler(args)
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return 1
    except ValueError as e:
        print(f"Error: {str(e)}")
        return 1
    except OSError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
