"""Repository class for OFS."""

from pathlib import Path
import json
import os
import shutil
from typing import Dict, Any, Optional


class Repository:
    """OFS Repository management.
    
    Handles repository initialization, configuration, and state queries.
    
    Attributes:
        root: Repository root directory (contains .ofs/)
        ofs_dir: .ofs metadata directory
        objects_dir: .ofs/objects directory
        refs_dir: .ofs/refs/heads directory
        commits_dir: .ofs/commits directory
        index_file: .ofs/index.json file
        head_file: .ofs/HEAD file
        config_file: .ofs/config.json file
    """
    
    def __init__(self, path: Optional[Path] = None):
        """Initialize Repository instance.
        
        Args:
            path: Path to repository root (default: current directory)
        """
        self.root = path if path else Path.cwd()
        self.ofs_dir = self.root / ".ofs"
        self.objects_dir = self.ofs_dir / "objects"
        self.refs_dir = self.ofs_dir / "refs" / "heads"
        self.commits_dir = self.ofs_dir / "commits"
        self.index_file = self.ofs_dir / "index.json"
        self.head_file = self.ofs_dir / "HEAD"
        self.config_file = self.ofs_dir / "config.json"
    
    def initialize(self) -> bool:
        """Initialize OFS repository.
        
        Creates .ofs/ directory structure and default configuration.
        
        Returns:
            True if successful, False if already initialized or error
            
        Example:
            >>> repo = Repository(Path("/tmp/myproject"))
            >>> repo.initialize()
            Initialized empty OFS repository in /tmp/myproject/.ofs
            True
        """
        if self.is_initialized():
            print(f"Error: Repository already initialized in {self.ofs_dir}")
            return False
        
        try:
            # Create directory structure
            self.commits_dir.mkdir(parents=True)
            self.refs_dir.mkdir(parents=True)
            self.objects_dir.mkdir(parents=True)
            
            # Initialize HEAD
            self.head_file.write_text("ref: refs/heads/main\n")
            
            # Initialize empty index
            self.index_file.write_text("[]")
            
            # Initialize config
            config = {
                "version": "1.0",
                "author": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
                "email": "",
                "ignore": [".ofs", "*.tmp", "*.swp", "__pycache__", ".DS_Store"]
            }
            self.config_file.write_text(json.dumps(config, indent=2))
            
            print(f"Initialized empty OFS repository in {self.ofs_dir}")
            return True
            
        except Exception as e:
            print(f"Error initializing repository: {e}")
            # Cleanup partial initialization
            if self.ofs_dir.exists():
                shutil.rmtree(self.ofs_dir)
            return False
    
    def is_initialized(self) -> bool:
        """Check if repository is initialized.
        
        Returns:
            True if .ofs directory exists with required files
            
        Example:
            >>> repo = Repository()
            >>> repo.is_initialized()
            False
        """
        return (
            self.ofs_dir.exists() and
            self.head_file.exists() and
            self.config_file.exists()
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Get repository configuration.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If repository not initialized
            
        Example:
            >>> repo = Repository()
            >>> repo.initialize()
            >>> config = repo.get_config()
            >>> 'author' in config
            True
        """
        if not self.is_initialized():
            raise FileNotFoundError("Repository not initialized")
        
        return json.loads(self.config_file.read_text())
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Raises:
            FileNotFoundError: If repository not initialized
            
        Example:
            >>> repo = Repository()
            >>> repo.initialize()
            >>> repo.set_config("author", "John Doe")
            >>> repo.get_config()["author"]
            'John Doe'
        """
        if not self.is_initialized():
            raise FileNotFoundError("Repository not initialized")
        
        config = self.get_config()
        config[key] = value
        self.config_file.write_text(json.dumps(config, indent=2))
