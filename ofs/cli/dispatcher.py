"""CLI dispatcher - routes commands to their handlers."""

import sys
import argparse


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
        version="OFS 1.0.0",
        help="Show program's version number and exit"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new OFS repository")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add files to staging area")
    add_parser.add_argument("paths", nargs="+", help="Files or directories to add")
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Create a new commit")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show repository status")
    
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
    
    # Dispatch to command handlers
    try:
        if args.command == "add":
            from ofs.commands.add import execute as add_execute
            return add_execute(args.paths)
            
        elif args.command == "status":
            from ofs.commands.status import execute as status_execute
            return status_execute()
            
        elif args.command == "commit":
            from ofs.commands.commit import execute as commit_execute
            return commit_execute(args.message)
            
        elif args.command == "log":
            from ofs.commands.log import execute as log_execute
            return log_execute(
                limit=args.number if hasattr(args, 'number') else None,
                oneline=args.oneline if hasattr(args, 'oneline') else False
            )
            
        elif args.command == "checkout":
            from ofs.commands.checkout import execute as checkout_execute
            return checkout_execute(
                args.commit_id,
                force=args.force if hasattr(args, 'force') else False
            )
            
        elif args.command == "verify":
            from ofs.commands.verify import execute as verify_execute
            return verify_execute(
                verbose=args.verbose if hasattr(args, 'verbose') else False
            )
            
        elif args.command == "diff":
            from ofs.commands.diff import execute as diff_execute
            return diff_execute(
                commit1=args.commit1 if hasattr(args, 'commit1') and args.commit1 else None,
                commit2=args.commit2 if hasattr(args, 'commit2') and args.commit2 else None,
                cached=args.cached if hasattr(args, 'cached') else False
            )
            
        elif args.command == "init":
            from ofs.core.repository.init import Repository
            repo = Repository()
            success = repo.initialize()
            return 0 if success else 1
            
        else:
            print(f"OFS: Command '{args.command}' not yet implemented")
            print("Available: init, add, status, commit, log, checkout, verify")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
