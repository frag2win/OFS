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
        version="OFS 0.1.0",
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
    
    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Show changes")
    diff_parser.add_argument("commit1", nargs="?", help="First commit (optional)")
    diff_parser.add_argument("commit2", nargs="?", help="Second commit (optional)")
    
    args = parser.parse_args()
    
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
            
        elif args.command == "init":
            from ofs.core.repository.init import Repository
            repo = Repository()
            success = repo.initialize()
            return 0 if success else 1
            
        else:
            print(f"OFS: Command '{args.command}' not yet implemented")
            print("Available: init, add, status")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
