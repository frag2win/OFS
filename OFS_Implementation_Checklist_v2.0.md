# OFS Implementation Checklist
## Version 2.0 - Production Development Plan

---

## Overview

This checklist provides a detailed, actionable plan for implementing OFS from design through production deployment. Each item includes acceptance criteria, testing requirements, and dependencies.

**Estimated Timeline:** 11 weeks (1 developer full-time)

---

## Phase 0: Project Foundation (Week 1)

### P0.1 - Repository Structure
**Priority:** P0 | **Owner:** Dev Lead | **Estimate:** 2 hours

- [ ] Create GitHub repository with appropriate license
- [ ] Set up directory structure:
  ```
  ofs/
  ├── ofs/                    # Main package
  │   ├── __init__.py
  │   ├── __main__.py
  │   ├── core/               # Core functionality
  │   ├── commands/           # CLI commands
  │   └── utils/              # Helper modules
  ├── tests/                  # Test suite
  ├── docs/                   # Documentation
  ├── scripts/                # Build/deployment scripts
  ├── README.md
  ├── ARCHITECTURE.md
  ├── CONTRIBUTING.md
  ├── LICENSE
  └── setup.py
  ```
- [ ] Add .gitignore (Python, IDE files)
- [ ] Create initial README with project description

**Acceptance Criteria:**
- Repository structure matches specification
- All directories created with placeholder files
- README describes project purpose

**Testing:**
- Manual verification of directory tree

---

### P0.2 - Development Environment
**Priority:** P0 | **Owner:** Dev Lead | **Estimate:** 3 hours

- [ ] Python version requirement: ≥3.8
- [ ] Virtual environment setup instructions documented
- [ ] Code formatting: Black (line length 100)
- [ ] Linting: Pylint, Flake8, MyPy
- [ ] Pre-commit hooks configured
- [ ] CI/CD pipeline skeleton (GitHub Actions)

**Configuration Files:**
- [ ] `.pylintrc` - Pylint configuration
- [ ] `setup.cfg` - Flake8, MyPy settings
- [ ] `.pre-commit-config.yaml` - Git hooks
- [ ] `.github/workflows/ci.yml` - CI pipeline

**Acceptance Criteria:**
- `make lint` runs without errors
- `make format` applies Black formatting
- Pre-commit hooks execute on commit
- CI pipeline runs on push

**Testing:**
- Run lint on empty package (should pass)
- Trigger CI pipeline with dummy commit

---

### P0.3 - Documentation Framework
**Priority:** P0 | **Owner:** Tech Writer | **Estimate:** 4 hours

- [ ] Documentation structure defined
- [ ] ARCHITECTURE.md created with:
  - System overview
  - Component descriptions
  - Data flow diagrams
  - File format specifications
- [ ] CONTRIBUTING.md with:
  - Setup instructions
  - Coding standards
  - Pull request process
- [ ] Sphinx setup for API docs (optional)

**Acceptance Criteria:**
- ARCHITECTURE.md complete with diagrams
- CONTRIBUTING.md reviewed by team
- Documentation builds without warnings

---

### P0.4 - Testing Framework
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 4 hours

- [ ] Unit test structure using `unittest`
- [ ] Test fixtures for repository creation
- [ ] Test helpers for file operations
- [ ] Mock filesystem for isolation
- [ ] Coverage reporting configured (pytest-cov)

**Test Directory Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_repository.py
├── test_objects.py
├── test_index.py
├── test_commits.py
├── fixtures/
│   ├── sample_files/
│   └── expected_outputs/
└── integration/
    └── test_workflows.py
```

**Acceptance Criteria:**
- `make test` runs all tests
- Coverage report generated
- Fixtures accessible from all tests

**Testing:**
- Create dummy test that passes
- Verify coverage reporting works

---

## Phase 1: Core Storage (Weeks 2-3)

### P1.1 - SHA-256 Hashing Module
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 6 hours

**File:** `ofs/utils/hash.py`

- [ ] Implement `compute_hash(data: bytes) -> str`
  - Uses `hashlib.sha256()`
  - Returns hex digest (64 characters)
  - Handles streaming for large files (chunk by chunk)
- [ ] Implement `compute_file_hash(path: Path) -> str`
  - Reads file in 8KB chunks
  - Returns SHA-256 hash
  - Handles binary and text files identically
- [ ] Implement `verify_hash(path: Path, expected_hash: str) -> bool`
  - Recomputes hash
  - Compares with expected
  - Returns True/False

**Acceptance Criteria:**
- Same content always produces same hash
- Large files (100MB) hashed without loading into memory
- Hash matches output from `sha256sum` command

**Testing:**
```python
def test_hash_consistency():
    data = b"Hello, OFS!"
    hash1 = compute_hash(data)
    hash2 = compute_hash(data)
    assert hash1 == hash2

def test_hash_known_value():
    # Empty string SHA-256
    assert compute_hash(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_large_file_hash():
    # Create 100MB file
    with open("large.bin", "wb") as f:
        f.write(b"x" * 100_000_000)
    hash_result = compute_file_hash(Path("large.bin"))
    assert len(hash_result) == 64  # Hex digest length
```

---

### P1.2 - Object Storage
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 8 hours

**File:** `ofs/core/objects.py`

- [ ] Class `ObjectStore`:
  - `__init__(self, ofs_dir: Path)`
  - `store(self, content: bytes) -> str`
  - `retrieve(self, hash_value: str) -> bytes`
  - `exists(self, hash_value: str) -> bool`
  - `verify(self, hash_value: str) -> bool`

**Implementation Details:**
```python
class ObjectStore:
    def __init__(self, ofs_dir: Path):
        self.objects_dir = ofs_dir / "objects"
        self.objects_dir.mkdir(parents=True, exist_ok=True)
    
    def store(self, content: bytes) -> str:
        """
        Store content in object database.
        Returns: SHA-256 hash of content
        """
        hash_value = compute_hash(content)
        
        # Avoid storing duplicates
        if self.exists(hash_value):
            return hash_value
        
        # Store as objects/ab/cdef123...
        prefix = hash_value[:2]
        suffix = hash_value[2:]
        
        obj_dir = self.objects_dir / prefix
        obj_dir.mkdir(exist_ok=True)
        
        obj_path = obj_dir / suffix
        
        # Atomic write
        temp_path = obj_path.with_suffix(".tmp")
        temp_path.write_bytes(content)
        temp_path.rename(obj_path)  # Atomic on POSIX/Windows
        
        return hash_value
    
    def retrieve(self, hash_value: str) -> bytes:
        """Retrieve content by hash."""
        obj_path = self._get_path(hash_value)
        if not obj_path.exists():
            raise FileNotFoundError(f"Object not found: {hash_value}")
        
        content = obj_path.read_bytes()
        
        # Verify integrity
        actual_hash = compute_hash(content)
        if actual_hash != hash_value:
            raise ValueError(f"Corruption detected: {hash_value}")
        
        return content
```

**Acceptance Criteria:**
- Same content stored once (deduplication)
- Objects stored in 2-level directory structure (ab/cdef...)
- Retrieval verifies hash every time
- Atomic writes (temp file + rename)

**Testing:**
```python
def test_store_and_retrieve():
    store = ObjectStore(Path(".ofs"))
    content = b"Test content"
    hash_val = store.store(content)
    retrieved = store.retrieve(hash_val)
    assert retrieved == content

def test_deduplication():
    store = ObjectStore(Path(".ofs"))
    hash1 = store.store(b"Same content")
    hash2 = store.store(b"Same content")
    assert hash1 == hash2
    # Verify only one file created
    obj_path = store._get_path(hash1)
    assert obj_path.exists()

def test_corruption_detection():
    store = ObjectStore(Path(".ofs"))
    hash_val = store.store(b"Original")
    
    # Corrupt the object
    obj_path = store._get_path(hash_val)
    obj_path.write_bytes(b"Corrupted")
    
    # Should raise on retrieval
    with pytest.raises(ValueError, match="Corruption"):
        store.retrieve(hash_val)
```

---

### P1.3 - Repository Initialization
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 6 hours

**File:** `ofs/core/repository.py`

- [ ] Class `Repository`:
  - `__init__(self, path: Path)`
  - `initialize() -> bool`
  - `is_initialized() -> bool`
  - `get_config() -> dict`
  - `set_config(key: str, value: Any)`

**Implementation:**
```python
class Repository:
    def __init__(self, path: Path = Path.cwd()):
        self.root = path
        self.ofs_dir = path / ".ofs"
        self.objects_dir = self.ofs_dir / "objects"
        self.refs_dir = self.ofs_dir / "refs" / "heads"
        self.commits_dir = self.ofs_dir / "commits"
        self.index_file = self.ofs_dir / "index.json"
        self.head_file = self.ofs_dir / "HEAD"
        self.config_file = self.ofs_dir / "config.json"
    
    def initialize(self) -> bool:
        """Initialize OFS repository."""
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
                "author": os.environ.get("USER", "unknown"),
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
        """Check if repository is initialized."""
        return (self.ofs_dir.exists() and 
                self.head_file.exists() and
                self.config_file.exists())
```

**Acceptance Criteria:**
- Creates all required directories and files
- Fails gracefully if already initialized
- Cleans up on failure (partial initialization)
- Sets default author from environment

**Testing:**
```python
def test_initialize_new_repo(tmp_path):
    repo = Repository(tmp_path)
    assert repo.initialize() is True
    assert (tmp_path / ".ofs").exists()
    assert (tmp_path / ".ofs" / "HEAD").exists()
    assert repo.is_initialized()

def test_initialize_twice_fails(tmp_path):
    repo = Repository(tmp_path)
    repo.initialize()
    assert repo.initialize() is False  # Second attempt fails

def test_config_defaults(tmp_path):
    repo = Repository(tmp_path)
    repo.initialize()
    config = repo.get_config()
    assert "version" in config
    assert "author" in config
    assert ".ofs" in config["ignore"]
```

---

### P1.4 - Index Management
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 8 hours

**File:** `ofs/core/index.py`

- [ ] Class `Index`:
  - `__init__(self, index_file: Path)`
  - `add(self, file_path: Path, hash_value: str, metadata: dict)`
  - `remove(self, file_path: Path)`
  - `get_entries() -> List[dict]`
  - `clear()`
  - `has_changes() -> bool`

**Index Entry Format:**
```json
{
  "path": "src/main.py",
  "hash": "abc123...",
  "size": 4096,
  "mode": "100644",
  "mtime": "2026-01-28T14:30:00Z"
}
```

**Implementation:**
```python
class Index:
    def __init__(self, index_file: Path):
        self.index_file = index_file
        self._entries = self._load()
    
    def _load(self) -> List[dict]:
        """Load index from disk."""
        if not self.index_file.exists():
            return []
        try:
            return json.loads(self.index_file.read_text())
        except json.JSONDecodeError:
            print("Warning: Corrupt index file, using empty index")
            return []
    
    def _save(self):
        """Save index to disk (atomic)."""
        temp_file = self.index_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(self._entries, indent=2))
        temp_file.rename(self.index_file)
    
    def add(self, file_path: Path, hash_value: str, metadata: dict):
        """Add or update file in index."""
        # Remove existing entry for this path
        self._entries = [e for e in self._entries if e["path"] != str(file_path)]
        
        # Add new entry
        entry = {
            "path": str(file_path),
            "hash": hash_value,
            "size": metadata.get("size", 0),
            "mode": metadata.get("mode", "100644"),
            "mtime": metadata.get("mtime", datetime.now().isoformat())
        }
        self._entries.append(entry)
        self._save()
    
    def has_changes(self) -> bool:
        """Check if index has staged changes."""
        return len(self._entries) > 0
```

**Acceptance Criteria:**
- Index persisted as JSON
- Atomic saves (temp + rename)
- Duplicate paths overwritten (latest wins)
- Corrupted index handled gracefully

**Testing:**
```python
def test_add_entry(tmp_path):
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add(Path("test.txt"), "abc123", {"size": 100})
    entries = index.get_entries()
    
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"
    assert entries[0]["hash"] == "abc123"

def test_update_existing(tmp_path):
    index_file = tmp_path / "index.json"
    index = Index(index_file)
    
    index.add(Path("test.txt"), "abc123", {"size": 100})
    index.add(Path("test.txt"), "def456", {"size": 200})
    entries = index.get_entries()
    
    # Should have only one entry (updated)
    assert len(entries) == 1
    assert entries[0]["hash"] == "def456"

def test_persistence(tmp_path):
    index_file = tmp_path / "index.json"
    index1 = Index(index_file)
    index1.add(Path("test.txt"), "abc123", {"size": 100})
    
    # Load in new instance
    index2 = Index(index_file)
    entries = index2.get_entries()
    assert len(entries) == 1
```

---

## Phase 2: File Operations (Week 4)

### P2.1 - Add Command
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 12 hours

**File:** `ofs/commands/add.py`

- [ ] Implement `add_files(repo: Repository, paths: List[Path])`
- [ ] Support wildcards (`ofs add *.py`)
- [ ] Support directories (`ofs add src/`)
- [ ] Recursive directory traversal
- [ ] Ignore pattern matching
- [ ] File size validation (max 100MB)
- [ ] Progress indicator for large operations

**Implementation:**
```python
def add_files(repo: Repository, paths: List[Path], verbose: bool = False):
    """Add files to staging index."""
    if not repo.is_initialized():
        print("Error: Not an OFS repository")
        return False
    
    # Expand paths (glob, directories)
    files_to_add = []
    for path in paths:
        if path.is_dir():
            files_to_add.extend(_walk_directory(path, repo))
        else:
            files_to_add.append(path)
    
    # Filter ignored files
    ignore_patterns = repo.get_config().get("ignore", [])
    files_to_add = [f for f in files_to_add if not _is_ignored(f, ignore_patterns)]
    
    if not files_to_add:
        print("No files to add")
        return True
    
    # Add each file
    object_store = ObjectStore(repo.ofs_dir)
    index = Index(repo.index_file)
    
    for file_path in files_to_add:
        try:
            # Size check
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                print(f"Warning: Skipping {file_path} (too large: {file_size} bytes)")
                continue
            
            # Read and store
            content = file_path.read_bytes()
            hash_value = object_store.store(content)
            
            # Add to index
            metadata = {
                "size": file_size,
                "mode": "100644",
                "mtime": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            index.add(file_path.relative_to(repo.root), hash_value, metadata)
            
            if verbose:
                print(f"Added {file_path} ({hash_value[:8]})")
                
        except Exception as e:
            print(f"Error adding {file_path}: {e}")
            continue
    
    print(f"Staged {len(files_to_add)} file(s)")
    return True
```

**Acceptance Criteria:**
- Handles individual files
- Handles directories (recursive)
- Respects ignore patterns
- Skips files >100MB
- Updates index atomically
- Shows progress for many files

**Testing:**
```python
def test_add_single_file(tmp_repo):
    file = tmp_repo / "test.txt"
    file.write_text("Hello")
    
    add_files(Repository(tmp_repo), [file])
    
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    assert len(entries) == 1
    assert entries[0]["path"] == "test.txt"

def test_add_directory(tmp_repo):
    (tmp_repo / "src").mkdir()
    (tmp_repo / "src" / "a.py").write_text("A")
    (tmp_repo / "src" / "b.py").write_text("B")
    
    add_files(Repository(tmp_repo), [tmp_repo / "src"])
    
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    assert len(entries) == 2

def test_ignore_patterns(tmp_repo):
    (tmp_repo / "keep.txt").write_text("Keep")
    (tmp_repo / "ignore.tmp").write_text("Ignore")
    
    add_files(Repository(tmp_repo), [tmp_repo])
    
    index = Index(tmp_repo / ".ofs" / "index.json")
    entries = index.get_entries()
    paths = [e["path"] for e in entries]
    assert "keep.txt" in paths
    assert "ignore.tmp" not in paths
```

---

### P2.2 - Status Command
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 8 hours

**File:** `ofs/commands/status.py`

- [ ] Show current commit info
- [ ] List staged files
- [ ] List modified files (not staged)
- [ ] List untracked files
- [ ] Color-coded output (optional)

**Implementation:**
```python
def show_status(repo: Repository, verbose: bool = False):
    """Display repository status."""
    if not repo.is_initialized():
        print("Error: Not an OFS repository")
        return False
    
    # Get current commit
    head_commit = _get_head_commit(repo)
    if head_commit:
        print(f"On commit {head_commit['id']} ({head_commit['timestamp']})")
        print(f'  "{head_commit["message"]}"')
    else:
        print("On branch main (no commits yet)")
    print()
    
    # Get staged files
    index = Index(repo.index_file)
    staged = index.get_entries()
    
    if staged:
        print("Changes to be committed:")
        for entry in staged:
            status = _get_file_status(repo, entry, head_commit)
            print(f"  {status}: {entry['path']}")
        print()
    else:
        print("No changes staged for commit")
        print()
    
    # Get modified files (working dir != staged)
    modified = _get_modified_files(repo, staged)
    if modified:
        print("Changes not staged:")
        for path in modified:
            print(f"  modified: {path}")
        print()
    
    # Get untracked files
    untracked = _get_untracked_files(repo, staged)
    if untracked:
        print("Untracked files:")
        for path in untracked:
            print(f"  {path}")
        print()
    
    return True
```

**Acceptance Criteria:**
- Shows current commit or "no commits"
- Lists all staged files
- Detects modified files (working != staged)
- Lists untracked files
- Clear visual separation

**Testing:**
```python
def test_status_no_commits(tmp_repo, capsys):
    show_status(Repository(tmp_repo))
    captured = capsys.readouterr()
    assert "no commits yet" in captured.out

def test_status_with_staged(tmp_repo, capsys):
    # Add file
    file = tmp_repo / "test.txt"
    file.write_text("Hello")
    add_files(Repository(tmp_repo), [file])
    
    show_status(Repository(tmp_repo))
    captured = capsys.readouterr()
    assert "test.txt" in captured.out
    assert "Changes to be committed" in captured.out
```

---

## Phase 3: Commit System (Week 5)

### P3.1 - Commit Creation
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 12 hours

**File:** `ofs/commands/commit.py`

- [ ] Validate non-empty index
- [ ] Generate sequential commit ID
- [ ] Build commit object
- [ ] Save commit to `.ofs/commits/<id>.json`
- [ ] Update refs/heads/main
- [ ] Update HEAD
- [ ] Clear index

**Commit Format:**
```json
{
  "id": "003",
  "parent": "002",
  "message": "Add authentication module",
  "author": "jsmith",
  "email": "jsmith@example.com",
  "timestamp": "2026-01-28T14:32:10.123456Z",
  "files": [
    {
      "path": "src/auth.py",
      "hash": "abc123...",
      "size": 4096,
      "action": "added"
    }
  ]
}
```

**Implementation:**
```python
def create_commit(repo: Repository, message: str, author: str = None) -> bool:
    """Create a new commit from staged changes."""
    if not repo.is_initialized():
        print("Error: Not an OFS repository")
        return False
    
    # Validate index not empty
    index = Index(repo.index_file)
    if not index.has_changes():
        print("Error: Nothing to commit (staging index empty)")
        print("Use 'ofs add <file>' to stage changes")
        return False
    
    # Validate message
    if not message or len(message) < 3:
        print("Error: Commit message too short (min 3 characters)")
        return False
    
    # Get config
    config = repo.get_config()
    author = author or config.get("author", "unknown")
    email = config.get("email", "")
    
    # Get parent commit
    parent_id = _get_head_commit_id(repo)
    
    # Generate new commit ID
    commit_id = _get_next_commit_id(repo)
    
    # Build commit object
    commit = {
        "id": commit_id,
        "parent": parent_id,
        "message": message.strip(),
        "author": author,
        "email": email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": []
    }
    
    # Add file entries
    entries = index.get_entries()
    for entry in entries:
        action = _determine_action(repo, entry, parent_id)
        commit["files"].append({
            "path": entry["path"],
            "hash": entry["hash"],
            "size": entry["size"],
            "action": action
        })
    
    # Save commit (atomic)
    commit_file = repo.commits_dir / f"{commit_id}.json"
    temp_file = commit_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(commit, indent=2))
    temp_file.rename(commit_file)
    
    # Update refs (atomic)
    main_ref = repo.refs_dir / "main"
    temp_ref = main_ref.with_suffix(".tmp")
    temp_ref.write_text(commit_id)
    temp_ref.rename(main_ref)
    
    # Clear index
    index.clear()
    
    print(f"[{commit_id}] {message}")
    print(f"{len(commit['files'])} file(s) changed")
    return True
```

**Acceptance Criteria:**
- Rejects empty index
- Generates sequential IDs (001, 002, 003...)
- Atomic commits (all-or-nothing)
- Updates HEAD correctly
- Clears index after success

**Testing:**
```python
def test_commit_success(tmp_repo):
    # Stage file
    file = tmp_repo / "test.txt"
    file.write_text("Hello")
    repo = Repository(tmp_repo)
    add_files(repo, [file])
    
    # Commit
    assert create_commit(repo, "First commit") is True
    
    # Verify commit exists
    commit_file = tmp_repo / ".ofs" / "commits" / "001.json"
    assert commit_file.exists()
    
    commit = json.loads(commit_file.read_text())
    assert commit["id"] == "001"
    assert commit["message"] == "First commit"

def test_commit_empty_index_fails(tmp_repo):
    repo = Repository(tmp_repo)
    assert create_commit(repo, "Empty commit") is False

def test_commit_sequential_ids(tmp_repo):
    repo = Repository(tmp_repo)
    
    for i in range(3):
        file = tmp_repo / f"file{i}.txt"
        file.write_text(f"Content {i}")
        add_files(repo, [file])
        create_commit(repo, f"Commit {i}")
    
    # Verify IDs
    assert (tmp_repo / ".ofs" / "commits" / "001.json").exists()
    assert (tmp_repo / ".ofs" / "commits" / "002.json").exists()
    assert (tmp_repo / ".ofs" / "commits" / "003.json").exists()
```

---

## Phase 4: History & Recovery (Week 6)

### P4.1 - Log Command
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 6 hours

**File:** `ofs/commands/log.py`

- [ ] Display commits in reverse chronological order
- [ ] Support `--oneline` flag
- [ ] Support `-n <count>` limit
- [ ] Show file changes (optional `--stat`)

**Testing:**
- Verify chronological order
- Test limit flag
- Test oneline format
- Test with no commits

---

### P4.2 - Checkout Command
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 12 hours

**File:** `ofs/commands/checkout.py`

- [ ] Validate commit exists
- [ ] Detect uncommitted changes
- [ ] Prompt for confirmation (unless `--force`)
- [ ] Restore all files from commit
- [ ] Verify hashes before writing
- [ ] Remove files not in target commit
- [ ] Update index and HEAD

**Safety Implementation:**
```python
def checkout_commit(repo: Repository, commit_id: str, force: bool = False) -> bool:
    """Restore repository to specific commit."""
    
    # Validate commit exists
    commit_file = repo.commits_dir / f"{commit_id}.json"
    if not commit_file.exists():
        print(f"Error: Commit {commit_id} not found")
        return False
    
    # Check for uncommitted changes (unless --force)
    if not force and _has_uncommitted_changes(repo):
        print("Error: You have uncommitted changes")
        print("Commit your changes or use 'ofs checkout --force'")
        return False
    
    # Load commit
    commit = json.loads(commit_file.read_text())
    
    # Load object store
    object_store = ObjectStore(repo.ofs_dir)
    
    # Verify all objects exist and are valid
    print("Verifying commit integrity...")
    for file_entry in commit["files"]:
        hash_val = file_entry["hash"]
        if not object_store.exists(hash_val):
            print(f"Error: Missing object {hash_val} for {file_entry['path']}")
            return False
        try:
            # Verify hash
            object_store.retrieve(hash_val)
        except ValueError as e:
            print(f"Error: Corrupted object {hash_val}: {e}")
            return False
    
    # Restore files
    print(f"Checking out commit {commit_id}...")
    for file_entry in commit["files"]:
        file_path = repo.root / file_entry["path"]
        content = object_store.retrieve(file_entry["hash"])
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write
        temp_path = file_path.with_suffix(".ofs-tmp")
        temp_path.write_bytes(content)
        temp_path.rename(file_path)
    
    # Remove files not in commit
    _cleanup_untracked_files(repo, commit)
    
    # Update index
    index = Index(repo.index_file)
    index.clear()
    for file_entry in commit["files"]:
        index.add(
            Path(file_entry["path"]),
            file_entry["hash"],
            {"size": file_entry["size"]}
        )
    
    # Update HEAD
    (repo.refs_dir / "main").write_text(commit_id)
    
    print(f"HEAD is now at {commit_id}")
    return True
```

**Acceptance Criteria:**
- Restores exact state from commit
- Detects uncommitted changes
- Verifies all hashes before writing
- Atomic file writes
- Handles missing files gracefully

**Testing:**
```python
def test_checkout_restores_files(tmp_repo):
    repo = Repository(tmp_repo)
    
    # Create commit 1
    file = tmp_repo / "test.txt"
    file.write_text("Version 1")
    add_files(repo, [file])
    create_commit(repo, "Commit 1")
    
    # Create commit 2
    file.write_text("Version 2")
    add_files(repo, [file])
    create_commit(repo, "Commit 2")
    
    # Checkout commit 1
    checkout_commit(repo, "001")
    
    # Verify content
    assert file.read_text() == "Version 1"

def test_checkout_detects_uncommitted(tmp_repo):
    repo = Repository(tmp_repo)
    
    file = tmp_repo / "test.txt"
    file.write_text("Version 1")
    add_files(repo, [file])
    create_commit(repo, "Commit 1")
    
    # Make uncommitted change
    file.write_text("Modified")
    
    # Checkout should fail
    assert checkout_commit(repo, "001", force=False) is False

def test_checkout_force_overwrites(tmp_repo):
    repo = Repository(tmp_repo)
    
    file = tmp_repo / "test.txt"
    file.write_text("Version 1")
    add_files(repo, [file])
    create_commit(repo, "Commit 1")
    
    # Make uncommitted change
    file.write_text("Modified")
    
    # Force checkout should succeed
    assert checkout_commit(repo, "001", force=True) is True
    assert file.read_text() == "Version 1"
```

---

### P4.3 - Verify Command
**Priority:** P0 | **Owner:** Backend Dev | **Estimate:** 8 hours

**File:** `ofs/commands/verify.py`

- [ ] Verify all object hashes
- [ ] Verify commit chain integrity
- [ ] Verify index consistency
- [ ] Detect orphaned objects
- [ ] Report detailed errors
- [ ] Suggest recovery actions

**Testing:**
- Test with healthy repository → pass
- Test with corrupted object → detect
- Test with broken commit chain → detect
- Test with invalid index → detect

---

## Phase 5: Advanced Features (Week 7)

### P5.1 - Diff Command
**Priority:** P1 | **Owner:** Backend Dev | **Estimate:** 12 hours

**File:** `ofs/commands/diff.py`

- [ ] Show uncommitted changes
- [ ] Compare two commits
- [ ] Line-by-line diff for text files
- [ ] Binary file detection
- [ ] Color-coded output

---

### P5.2 - Ignore System
**Priority:** P1 | **Owner:** Backend Dev | **Estimate:** 6 hours

**File:** `ofs/utils/ignore.py`

- [ ] Parse `.ofsignore` file
- [ ] Glob pattern matching
- [ ] Negation patterns (`!`)
- [ ] Default patterns in config

---

## Phase 6: CLI & UX (Week 8)

### P6.1 - Command-Line Interface
**Priority:** P0 | **Owner:** Frontend Dev | **Estimate:** 10 hours

**File:** `ofs/__main__.py`

- [ ] Argument parsing (argparse)
- [ ] Command dispatch
- [ ] `--help` for all commands
- [ ] `--version` flag
- [ ] Exit codes (0 = success, 1 = error)

**CLI Structure:**
```python
def main():
    parser = argparse.ArgumentParser(
        prog="ofs",
        description="Offline File System - Local-first version control"
    )
    parser.add_argument("--version", action="version", version="OFS 1.0.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # ofs init
    init_parser = subparsers.add_parser("init", help="Initialize repository")
    
    # ofs add
    add_parser = subparsers.add_parser("add", help="Add files to staging")
    add_parser.add_argument("paths", nargs="+", help="Files or directories")
    
    # ofs commit
    commit_parser = subparsers.add_parser("commit", help="Create commit")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    
    # ... other commands
    
    args = parser.parse_args()
    
    # Dispatch
    if args.command == "init":
        return init_command(args)
    elif args.command == "add":
        return add_command(args)
    # ...
    
if __name__ == "__main__":
    sys.exit(main())
```

**Testing:**
- Test each command via CLI
- Test help text
- Test invalid arguments

---

### P6.2 - Progress Indicators
**Priority:** P1 | **Owner:** Frontend Dev | **Estimate:** 4 hours

- [ ] Progress bar for large operations
- [ ] Spinner for waiting
- [ ] File count indicators
- [ ] Percentage complete

---

### P6.3 - Color Output
**Priority:** P2 | **Owner:** Frontend Dev | **Estimate:** 3 hours

- [ ] Color-coded status messages
- [ ] Respect `NO_COLOR` environment variable
- [ ] `--no-color` flag
- [ ] Detect terminal capabilities

---

## Phase 7: Testing & Quality (Weeks 9-10)

### P7.1 - Unit Test Coverage
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 20 hours

- [ ] Test coverage ≥ 95%
- [ ] All edge cases covered
- [ ] Error paths tested
- [ ] Mock filesystem for isolation

---

### P7.2 - Integration Tests
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 16 hours

**Test Scenarios:**
- [ ] Complete workflow: init → add → commit → checkout → verify
- [ ] Multiple commits with rollback
- [ ] Large files (100MB boundary)
- [ ] Binary files (images, executables)
- [ ] Deep directory structures
- [ ] Special characters in filenames
- [ ] Cross-platform paths

---

### P7.3 - Performance Benchmarks
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 12 hours

**Benchmarks:**
- [ ] Add 1000 files (1KB each) → < 30 seconds
- [ ] Commit 1000 files → < 5 seconds
- [ ] Checkout 1000 files → < 10 seconds
- [ ] Verify 1000 objects → < 15 seconds
- [ ] Memory usage < 100MB during operations

---

### P7.4 - Chaos Testing
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 16 hours

**Simulations:**
- [ ] SIGKILL during commit → repository intact
- [ ] Disk full during add → graceful failure
- [ ] Corrupted object → detected by verify
- [ ] Deleted commit file → detected
- [ ] Power loss simulation (sync delays)

---

### P7.5 - Cross-Platform Testing
**Priority:** P0 | **Owner:** QA Lead | **Estimate:** 12 hours

**Platforms:**
- [ ] Linux (Ubuntu 22.04, RHEL 8)
- [ ] Windows (Windows 10, Windows 11)
- [ ] macOS (macOS 12, macOS 13)

**Test Cases:**
- [ ] Path separators (/ vs \)
- [ ] Case sensitivity
- [ ] Line endings (LF vs CRLF)
- [ ] Special characters in paths
- [ ] Filesystem limitations

---

## Phase 8: Documentation (Week 11)

### P8.1 - User Documentation
**Priority:** P0 | **Owner:** Tech Writer | **Estimate:** 16 hours

- [ ] README.md with quick start
- [ ] Tutorial: First commit in 5 minutes
- [ ] Command reference (all commands)
- [ ] FAQ
- [ ] Troubleshooting guide
- [ ] Migration guide (from manual versioning)

---

### P8.2 - Developer Documentation
**Priority:** P0 | **Owner:** Tech Writer | **Estimate:** 12 hours

- [ ] ARCHITECTURE.md (system design)
- [ ] CONTRIBUTING.md (development setup)
- [ ] API documentation (if library use supported)
- [ ] Design decisions document
- [ ] Testing guide

---

### P8.3 - Video Tutorials
**Priority:** P1 | **Owner:** Tech Writer | **Estimate:** 8 hours

- [ ] Installation video (5 min)
- [ ] Basic workflow video (10 min)
- [ ] Advanced features video (15 min)

---

## Phase 9: Deployment (Week 11)

### P9.1 - Packaging
**Priority:** P0 | **Owner:** DevOps | **Estimate:** 12 hours

**Distribution Methods:**
- [ ] PyPI package (`pip install ofs`)
- [ ] Standalone script (single file)
- [ ] Debian package (.deb)
- [ ] RPM package (.rpm)
- [ ] Homebrew formula (macOS)
- [ ] Windows installer (.exe)

---

### P9.2 - CI/CD Pipeline
**Priority:** P0 | **Owner:** DevOps | **Estimate:** 8 hours

- [ ] GitHub Actions workflow
- [ ] Automated testing on PR
- [ ] Automated builds
- [ ] Automated releases
- [ ] Changelog generation

---

### P9.3 - Release Checklist
**Priority:** P0 | **Owner:** Product Manager | **Estimate:** 4 hours

- [ ] Version 1.0.0 tagged
- [ ] Release notes written
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Security audit complete
- [ ] Performance benchmarks met
- [ ] Cross-platform verification complete
- [ ] Announcement prepared

---

## Acceptance Criteria Summary

### Must-Have (P0)
- [x] Repository initialization works
- [x] Files can be staged and committed
- [x] Commit history viewable
- [x] Checkout restores exact state
- [x] Integrity verification detects all corruption
- [x] Cross-platform compatibility (Linux, Windows, macOS)
- [x] Zero external dependencies
- [x] Test coverage ≥ 95%

### Should-Have (P1)
- [ ] Diff shows changes clearly
- [ ] Ignore patterns work correctly
- [ ] Progress indicators for long operations
- [ ] Color-coded output

### Nice-to-Have (P2)
- [ ] Performance optimizations
- [ ] Video tutorials
- [ ] Homebrew/APT packages

---

## Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Cross-platform bugs | Medium | High | Extensive testing on all platforms |
| Performance issues | Low | Medium | Early benchmarking, optimization |
| Data corruption | Low | Critical | Comprehensive verification, atomic ops |
| Hash collisions | Very Low | High | SHA-256 is collision-resistant |
| Incomplete testing | Medium | High | Dedicated QA phase, coverage metrics |

---

## Definition of Done

A feature is complete when:
1. Code implemented and reviewed
2. Unit tests written (coverage ≥ 90%)
3. Integration tests passing
4. Documentation updated
5. Cross-platform tested
6. Performance benchmarks met
7. Security review passed

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Foundation | Project structure, dev environment |
| 2-3 | Core Storage | Hashing, objects, repository, index |
| 4 | File Operations | Add, status commands |
| 5 | Commit System | Commit creation, atomicity |
| 6 | History & Recovery | Log, checkout, verify |
| 7 | Advanced Features | Diff, ignore system |
| 8 | CLI & UX | Command interface, progress, colors |
| 9-10 | Testing & Quality | Unit, integration, chaos, performance |
| 11 | Documentation & Deploy | Docs, packaging, release |

**Total: 11 weeks (1 developer)**

---

**END OF CHECKLIST**
