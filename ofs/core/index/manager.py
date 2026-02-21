"""Index management for OFS staging area."""

from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from ofs.utils.filesystem.atomic_write import atomic_write


class Index:
    """Staging index for OFS.
    
    Manages the staging area where files are prepared for commit.
    Persists to .ofs/index.json as JSON array.
    
    Maintains both a list (for ordering/serialization) and a dict
    (for O(1) lookups by path).
    
    Attributes:
        index_file: Path to index.json
        _entries: List of index entries (cached in memory)
        _entries_by_path: Dict mapping path -> entry for O(1) lookup
    """
    
    def __init__(self, index_file: Path):
        """Initialize Index.
        
        Args:
            index_file: Path to index.json file
        """
        self.index_file = index_file
        self._entries = self._load()
        self._entries_by_path: Dict[str, Dict[str, Any]] = {
            e["path"]: e for e in self._entries
        }
    
    def _load(self) -> List[Dict[str, Any]]:
        """Load index from disk.
        
        Returns:
            List of index entries
        """
        if not self.index_file.exists():
            return []
        
        try:
            content = self.index_file.read_text()
            return json.loads(content)
        except json.JSONDecodeError:
            print("Warning: Corrupt index file, using empty index")
            return []
    
    def _save(self) -> None:
        """Save index to disk (atomic)."""
        content = json.dumps(self._entries, indent=2)
        atomic_write(self.index_file, content.encode("utf-8"))
    
    def add(self, file_path: str, hash_value: str, metadata: Dict[str, Any]) -> None:
        """Add or update file in index.
        
        If file already exists, replaces with new entry.
        
        Args:
            file_path: Relative path to file
            hash_value: SHA-256 hash of content
            metadata: Additional metadata (size, mode, mtime)
            
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> index.add("src/main.py", "abc123...", {"size": 1024})
        """
        # Build new entry
        entry = {
            "path": file_path,
            "hash": hash_value,
            **metadata
        }
        
        # Remove existing entry for this path (if any)
        if file_path in self._entries_by_path:
            self._entries = [e for e in self._entries if e["path"] != file_path]
        
        # Add new entry
        self._entries.append(entry)
        self._entries_by_path[file_path] = entry
        self._save()
    
    def batch_add(self, entries: List[tuple]) -> None:
        """Add multiple files with a single atomic write.
        
        Args:
            entries: List of (file_path, hash_value, metadata) tuples
            
        Example:
            >>> index.batch_add([
            ...     ("a.py", "abc...", {"size": 100}),
            ...     ("b.py", "def...", {"size": 200}),
            ... ])
        """
        for file_path, hash_value, metadata in entries:
            entry = {
                "path": file_path,
                "hash": hash_value,
                **metadata
            }
            # Remove existing entry for this path
            if file_path in self._entries_by_path:
                self._entries = [e for e in self._entries if e["path"] != file_path]
            self._entries.append(entry)
            self._entries_by_path[file_path] = entry
        
        # Single atomic save for all entries
        self._save()
    
    def remove(self, file_path: str) -> bool:
        """Remove file from index.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            True if file was removed, False if not found
            
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> index.remove("src/main.py")
            True
        """
        if file_path not in self._entries_by_path:
            return False
        
        self._entries = [e for e in self._entries if e["path"] != file_path]
        del self._entries_by_path[file_path]
        self._save()
        return True
    
    def get_entries(self) -> List[Dict[str, Any]]:
        """Get all index entries.
        
        Returns:
            List of all entries
            
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> entries = index.get_entries()
            >>> len(entries)
            2
        """
        return self._entries.copy()
    
    def clear(self) -> None:
        """Clear all entries from index.
        
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> index.clear()
            >>> index.get_entries()
            []
        """
        self._entries = []
        self._entries_by_path = {}
        self._save()
    
    def has_changes(self) -> bool:
        """Check if index has staged changes.
        
        Returns:
            True if index has entries, False if empty
            
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> index.has_changes()
            False
        """
        return len(self._entries) > 0
    
    def find_entry(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Find entry by path. O(1) lookup.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Entry dict if found, None otherwise
            
        Example:
            >>> index = Index(Path(".ofs/index.json"))
            >>> entry = index.find_entry("src/main.py")
            >>> entry["hash"] if entry else None
            'abc123...'
        """
        entry = self._entries_by_path.get(file_path)
        return entry.copy() if entry else None
