# OFS Architecture

## System Overview

OFS is a content-addressable, local-first version control system built with simplicity, reliability, and offline operation as core principles.

## Design Principles

1. **Offline-First**: No network code whatsoever
2. **Zero Dependencies**: Pure Python standard library only
3. **Deterministic**: Same inputs always produce same outputs
4. **Transparent**: Human-readable formats, visible state
5. **Fail-Safe**: Detect and reject corruption, never silently fail
6. **Auditable**: Complete history, tamper-evident
7. **Immutable**: History never changes, only extends

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│  (argparse, command dispatch, output formatting)        │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  Command Layer                           │
│  Init │ Add │ Commit │ Checkout │ Log │ Verify │ Diff  │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  Core Repository                         │
│  ┌─────────────┬──────────────┬────────────────┐       │
│  │   Objects   │    Index     │    Commits     │       │
│  │   Storage   │  Management  │   Management   │       │
│  └─────────────┴──────────────┴────────────────┘       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  Utility Layer                           │
│  Hash │ Filesystem │ Validation │ Serialization         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                Operating System                          │
│         (Filesystem, I/O, Platform APIs)                │
└─────────────────────────────────────────────────────────┘
```

## Repository Structure

```
project/
├── .ofs/                    # OFS metadata directory
│   ├── objects/             # Content-addressable blob storage
│   │   └── ab/
│   │       └── cdef123...   # File content (SHA-256 hash)
│   ├── refs/
│   │   └── heads/
│   │       └── main         # Pointer to latest commit
│   ├── commits/             # Commit history (chronological)
│   │   ├── 001.json
│   │   ├── 002.json
│   │   └── ...
│   ├── index.json           # Staging area state
│   ├── HEAD                 # Current branch/commit pointer
│   └── config.json          # Repository configuration
└── [working files]
```

## Core Components

### 1. Object Store (`core/objects/`)

Content-addressable storage using SHA-256 hashing:

- Files stored by hash (collision-resistant)
- Automatic deduplication (identical content = one copy)
- Two-level directory structure (ab/cdef123...)
- Verification on every read operation
- Immutable once written

### 2. Index Management (`core/index/`)

Staging area for preparing commits:

- JSON-based storage
- Tracks file path, hash, size, mode, mtime
- Atomic updates (temp file + rename)
- Handles additions, modifications, removals

### 3. Commit System (`core/commits/`)

Linear, sequential commit history:

- Commits numbered sequentially (001, 002, 003...)
- Each commit references parent
- No branches, no merges (v1 scope)
- Append-only (history never rewritten)

### 4. Reference Management (`core/refs/`)

Pointers to commits:

- HEAD points to current commit
- Branch refs point to latest commit
- Human-readable text files

## Data Formats

### Commit Object

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

### Index Entry

```json
{
  "path": "src/main.py",
  "hash": "abc123...",
  "size": 4096,
  "mode": "100644",
  "mtime": "2026-01-28T14:30:00Z"
}
```

## Key Operations

### Adding a File

```
1. User runs: ofs add src/auth.py
2. CLI validates file exists
3. Read file content into memory
4. Compute SHA-256 hash
5. Check if hash exists in .ofs/objects/
6. If not, write content to .ofs/objects/ab/cdef123...
7. Update .ofs/index.json with file metadata
8. Print confirmation
```

### Creating a Commit

```
1. User runs: ofs commit -m "Added auth"
2. CLI validates index not empty
3. Generate commit ID (next sequential number)
4. Read current HEAD to get parent commit
5. Build commit object with metadata
6. Write to temp file: .ofs/commits/003.json.tmp
7. Atomic rename to .ofs/commits/003.json
8. Update refs/heads/main (temp + rename)
9. Update HEAD
10. Clear index
11. Print confirmation
```

### Checking Out

```
1. User runs: ofs checkout 001
2. Validate commit exists
3. Check for uncommitted changes (warn if present)
4. Verify all object hashes exist
5. For each file in commit:
   - Retrieve content from objects/
   - Verify hash
   - Write to working directory
6. Remove files not in commit
7. Update index.json
8. Update HEAD
```

## Atomicity Guarantees

All operations use atomic writes:

```python
# Write to temp file
temp_file.write_text(content)

# Atomic rename (POSIX/Windows guarantee)
temp_file.rename(final_file)
```

This ensures no partial state is ever visible, even if power fails during operation.

## Security Model

### Threat Protection

✅ **Protected Against:**
- Accidental overwrites
- File corruption
- Pilot error
- Silent data loss

❌ **NOT Protected Against:**
- Malicious actors with filesystem access
- Physical device compromise
- Intentional sabotage

### Security Controls

- SHA-256 (FIPS 140-2 approved)
- No network communication
- No external executables
- Path traversal prevention
- Input validation on all user data

## Performance Considerations

### Scalability Limits (v1)

- Maximum files per repository: 10,000
- Maximum file size: 100MB
- Maximum repository size: 10GB
- Maximum commit history: 10,000 commits

### Optimization Strategies

- Streaming hash computation for large files
- Deduplication reduces storage
- Simple linear history (no complex DAG)
- JSON parsing only when needed

## Future Enhancements (v2+)

- Network operations (push, pull, sync)
- Branching and merging
- Diff visualization
- Large file support (\u003e100MB)
- Compression

## Code Organization

See [OFS_File_Structure_Detailed.md](../OFS_File_Structure_Detailed.md) for complete file structure.

Key modules:
- `ofs/core/` - Core business logic
- `ofs/commands/` - CLI command implementations
- `ofs/utils/` - Utility functions
- `ofs/models/` - Data models
- `ofs/cli/` - CLI infrastructure
- `ofs/exceptions/` - Custom exceptions

## References

- [Product Requirements Document](../OFS_Enhanced_PRD_v2.0.md)
- [Implementation Checklist](../OFS_Implementation_Checklist_v2.0.md)
- [File Structure](../OFS_File_Structure_Detailed.md)
