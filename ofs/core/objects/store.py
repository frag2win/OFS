"""Object storage implementation for OFS."""

from pathlib import Path
from typing import Optional
from ofs.utils.hash import compute_hash
from ofs.utils.filesystem.atomic_write import atomic_write


class ObjectStore:
    """Content-addressable object storage.
    
    Stores file contents by their SHA-256 hash in a two-level directory structure.
    Provides automatic deduplication and integrity verification.
    
    Directory structure:
        objects/ab/cdef123...  # First 2 chars / remaining 62 chars
    
    Attributes:
        objects_dir: Path to objects directory
    """
    
    def __init__(self, ofs_dir: Path):
        """Initialize object store.
        
        Args:
            ofs_dir: Path to .ofs directory
        """
        self.objects_dir = ofs_dir / "objects"
        self.objects_dir.mkdir(parents=True, exist_ok=True)
    
    def store(self, content: bytes) -> str:
        """Store content and return its hash.
        
        If content already exists (same hash), does not write duplicate.
        Uses atomic writes to prevent corruption.
        
        Args:
            content: Bytes to store
            
        Returns:
            SHA-256 hash of content (64 hex chars)
            
        Example:
            >>> store = ObjectStore(Path(".ofs"))
            >>> hash_val = store.store(b"hello world")
            >>> len(hash_val)
            64
        """
        hash_value = compute_hash(content)
        
        # Check if already exists (deduplication)
        if self.exists(hash_value):
            return hash_value
        
        # Get path for this hash
        obj_path = self._get_path(hash_value)
        
        # Ensure subdirectory exists
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write
        atomic_write(obj_path, content)
        
        return hash_value
    
    def retrieve(self, hash_value: str) -> bytes:
        """Retrieve content by hash.
        
        Verifies integrity by recomputing hash.
        
        Args:
            hash_value: SHA-256 hash (64 hex chars)
            
        Returns:
            Original content bytes
            
        Raises:
            FileNotFoundError: If object doesn't exist
            ValueError: If hash verification fails (corruption detected)
            
        Example:
            >>> store = ObjectStore(Path(".ofs"))
            >>> hash_val = store.store(b"hello")
            >>> content = store.retrieve(hash_val)
            >>> content
            b'hello'
        """
        obj_path = self._get_path(hash_value)
        
        if not obj_path.exists():
            raise FileNotFoundError(f"Object not found: {hash_value}")
        
        # Read content
        content = obj_path.read_bytes()
        
        # Verify integrity
        actual_hash = compute_hash(content)
        if actual_hash != hash_value:
            raise ValueError(
                f"Corruption detected: {hash_value} "
                f"(actual: {actual_hash})"
            )
        
        return content
    
    def exists(self, hash_value: str) -> bool:
        """Check if object exists.
        
        Args:
            hash_value: SHA-256 hash (64 hex chars)
            
        Returns:
            True if object exists, False otherwise
            
        Example:
            >>> store = ObjectStore(Path(".ofs"))
            >>> store.exists("abc123...")
            False
        """
        return self._get_path(hash_value).exists()
    
    def verify(self, hash_value: str) -> bool:
        """Verify object integrity.
        
        Recomputes hash and checks it matches.
        
        Args:
            hash_value: SHA-256 hash (64 hex chars)
            
        Returns:
            True if object exists and hash matches, False if corruption detected
            
        Raises:
            FileNotFoundError: If object doesn't exist
            
        Example:
            >>> store = ObjectStore(Path(".ofs"))
            >>> hash_val = store.store(b"data")
            >>> store.verify(hash_val)
            True
        """
        try:
            self.retrieve(hash_value)
            return True
        except ValueError:
            # Corruption detected
            return False
    
    def _get_path(self, hash_value: str) -> Path:
        """Get filesystem path for hash.
        
        Uses two-level structure: first 2 chars / remaining 62 chars
        
        Args:
            hash_value: SHA-256 hash (64 hex chars)
            
        Returns:
            Path to object file
            
        Example:
            >>> store = ObjectStore(Path(".ofs"))
            >>> path = store._get_path("abcdef123...")
            >>> str(path)
            '.ofs/objects/ab/cdef123...'
        """
        prefix = hash_value[:2]
        suffix = hash_value[2:]
        return self.objects_dir / prefix / suffix
