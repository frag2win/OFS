"""ofs verify command implementation.

This module implements the 'ofs verify' command to check repository integrity.
"""

from pathlib import Path
from ofs.core.verify import verify_repository


def execute(verbose: bool = False, repo_root: Path = None) -> int:
    """Execute the 'ofs verify' command.
    
    Args:
        verbose: Show detailed output
        repo_root: Repository root (defaults to current directory)
        
    Returns:
        int: Exit code (0 for success, 1 for errors)
    """
    # Find repository root
    if repo_root is None:
        repo_root = Path.cwd()
    
    print("Verifying repository integrity...")
    print()
    
    # Run verification
    success, results = verify_repository(repo_root, verbose)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return 1
    
    # Print results
    components = ["objects", "index", "commits", "refs"]
    component_names = {
        "objects": "Object Store",
        "index": "Index",
        "commits": "Commit History",
        "refs": "References"
    }
    
    for component in components:
        result = results[component]
        name = component_names[component]
        
        if result["success"]:
            print(f"✓ {name}: OK")
        else:
            print(f"✗ {name}: FAILED")
            if verbose or True:  # Always show errors
                for error in result["errors"]:
                    print(f"  - {error}")
    
    print()
    
    if success:
        print("✓ Repository verification passed")
        print("  All checks successful")
        return 0
    else:
        # Count total errors
        total_errors = sum(len(r["errors"]) for r in results.values())
        print(f"✗ Repository verification failed")
        print(f"  {total_errors} error(s) found")
        print()
        print("Hint: Run 'ofs verify --verbose' for detailed error information")
        return 1
