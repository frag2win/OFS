# guidelines.md

## Your project info

- Name: OFS (Offline File System)
- Version: 0.1.0 (In Development)
- Status: Active Development - Week 1-11 Implementation Roadmap
- Repository: https://github.com/frag2win/OFS
- Purpose: Enterprise-grade, local-first version control system for air-gapped environments
- Target Users: Defense/aerospace developers, embedded systems teams, regulated industries

## What it's about

OFS is a production-ready version control system engineered specifically for high-security, air-gapped environments where traditional VCS tools (Git, SVN) cannot operate due to network dependencies and complex installation requirements.

Core Problem Solved:
- Air-gapped facilities cannot use Git (network dependencies, complex setup)
- Manual file versioning is error-prone and lacks audit trails
- No viable offline-first version control exists for restricted environments
- Lost work from accidental overwrites with no recovery mechanism
- Compliance gaps due to missing change documentation

Solution Approach:
- Pure Python standard library only (zero external dependencies)
- Content-addressable storage with SHA-256 cryptographic verification
- Deterministic operations (same inputs always produce same outputs)
- Linear commit history (no branches/merges in v1)
- Atomic operations using temp file + rename pattern
- Transparent human-readable JSON formats
- Complete offline operation with no network code

Key Features:
- Repository initialization and configuration
- File staging with automatic deduplication
- Cryptographically verified commits
- Checkout to any previous commit
- Integrity verification and corruption detection
- Cross-platform (Windows, Linux, macOS)

## Tech stack

Language: Pure Python 3.8+
Dependencies: ZERO (standard library only)

Core Libraries:
- hashlib - SHA-256 hashing (FIPS 140-2 approved)
- pathlib - Cross-platform filesystem operations
- json - Human-readable metadata serialization
- argparse - CLI interface
- dataclasses - Data models
- unittest/pytest - Testing framework

Storage Architecture:
- Content-addressable blob storage (objects/)
- Sequential commit history (commits/001.json, 002.json, etc.)
- JSON-based staging index (index.json)
- Reference pointers (refs/heads/main)
- Configuration management (config.json)

Repository Structure:
```
.ofs/
├── objects/          # Content-addressable blob storage (SHA-256)
│   └── ab/
│       └── cdef123...  # File content by hash
├── commits/          # Commit history (sequential, numbered)
│   ├── 001.json
│   ├── 002.json
│   └── ...
├── refs/heads/       # Branch references
│   └── main         # Pointer to latest commit
├── index.json        # Staging area
├── HEAD              # Current commit pointer
└── config.json       # Repository configuration
```

Development Tools:
- pylint - Linting
- mypy - Type checking
- pytest - Unit testing
- pytest-cov - Coverage reporting
- Black - Code formatting (line length 100)

## Important commands

Development Setup:
```bash
# Set up virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/macOS

# Install development dependencies (optional, for testing only)
pip install pytest pytest-cov pylint mypy black

# Run tests
python -m pytest tests/
python -m pytest tests/ -v  # Verbose output
python -m pytest tests/ --cov=ofs  # With coverage report
python -m pytest tests/ --cov=ofs --cov-report=html  # HTML coverage

# Code quality
python -m pylint ofs/
python -m mypy ofs/
python -m black ofs/ --check  # Check formatting
python -m black ofs/  # Apply formatting
```

OFS Basic Usage:
```bash
# Initialize a new repository
python -m ofs init

# Add files to staging
python -m ofs add myfile.txt
python -m ofs add src/  # Add directory recursively
python -m ofs add .  # Add all changes

# Create a commit
python -m ofs commit -m "Your commit message"

# View repository status
python -m ofs status

# View commit history
python -m ofs log
python -m ofs log -n 5  # Last 5 commits
python -m ofs log --oneline  # Compact format

# Checkout previous commit
python -m ofs checkout 001

# Verify repository integrity
python -m ofs verify

# Show differences (if implemented)
python -m ofs diff
python -m ofs diff 001 002
```

## Workflow

Implementation Roadmap (11 weeks):
```
Phase 0 (Week 1): Project Foundation
- Repository structure setup
- Development environment configuration
- Documentation framework
- Testing framework

Phase 1 (Weeks 2-3): Core Storage
- SHA-256 hashing module
- Content-addressable object storage
- Repository initialization
- Index management (staging area)

Phase 2 (Week 4): File Operations
- ofs add command
- ofs status command
- Ignore pattern matching
- Directory traversal

Phase 3 (Week 5): Commit System
- Commit creation and metadata
- Sequential commit ID generation
- Atomic commit operations
- ofs log command

Phase 4 (Week 6): State Management
- ofs checkout command
- Working directory restoration
- ofs verify command
- Corruption detection

Phase 5 (Week 7): Additional Features
- ofs diff command
- Enhanced status output
- Configuration management

Phase 6 (Weeks 8-9): Testing & Quality
- Unit test coverage (95%+ target)
- Integration tests
- Cross-platform testing
- Chaos engineering (power-loss, corruption)

Phase 7 (Week 10): Documentation
- User manual
- Command reference
- Troubleshooting guide
- Architecture documentation

Phase 8 (Week 11): Release Preparation
- Final testing
- Security audit
- Deployment procedures
- Version 1.0 release
```

Development Workflow:
1. Review relevant PRD sections before implementing features
2. Write code following design principles (see below)
3. Add comprehensive unit tests (target 95% coverage)
4. Run linters and type checkers
5. Update documentation
6. Test on multiple platforms if possible

Code Quality Standards:
- Type hints required on all functions
- Docstrings (Google style) on all public APIs
- Maximum function length: 50 lines
- Maximum cyclomatic complexity: 10
- Test coverage: 90%+ minimum

## Anything helpful for project

Design Principles (CRITICAL):
```
1. Offline-First: No network code whatsoever, no network assumptions
2. Zero Dependencies: Pure Python standard library only
3. Deterministic: Same inputs always produce same outputs
4. Transparent: Human-readable formats, visible state
5. Fail-Safe: Detect and reject corruption, never silently fail
6. Auditable: Complete history, tamper-evident
7. Immutable: History never changes, only extends
8. Explicit: No implicit behavior, no magic
9. Portable: Pure Python ≥3.8, no OS-specific code
10. Maintainable: Clear code structure, comprehensive docs
```

Code Organization:
```
ofs/
├── __init__.py
├── __main__.py        # CLI entry point
├── core/              # Core business logic
│   ├── repository.py  # Repository initialization and management
│   ├── objects.py     # Content-addressable blob storage
│   ├── index.py       # Staging area management
│   └── commits.py     # Commit creation and history
├── commands/          # CLI command implementations
│   ├── init.py        # ofs init
│   ├── add.py         # ofs add
│   ├── commit.py      # ofs commit
│   ├── checkout.py    # ofs checkout
│   ├── log.py         # ofs log
│   ├── status.py      # ofs status
│   └── verify.py      # ofs verify
├── utils/             # Helper modules
│   ├── hash.py        # SHA-256 hashing utilities
│   ├── filesystem.py  # File operations
│   └── validation.py  # Input validation
└── exceptions/        # Custom exceptions

tests/
├── test_repository.py
├── test_objects.py
├── test_index.py
├── test_commits.py
└── integration/
    └── test_workflows.py
```

Documentation Structure:
- README.md - Quick start and overview
- docs/ARCHITECTURE.md - System architecture and design principles
- docs/CONTRIBUTING.md - Contribution guidelines for developers
- docs/requirements/OFS_Enhanced_PRD_v2.0.md - Complete product specification
- docs/requirements/OFS_Implementation_Checklist_v2.0.md - Development roadmap
- docs/requirements/OFS_File_Structure_Detailed.md - Detailed file structure
- docs/requirements/OFS_Enhancement_Summary.md - Project enhancement overview

Core Concepts:
- Content-Addressable Storage: Files stored by SHA-256 hash in .ofs/objects/ with 2-level directory structure (ab/cdef123...) for automatic deduplication
- Sequential Commits: Linear history numbered 001.json, 002.json, 003.json, etc. in .ofs/commits/
- Atomic Operations: All writes use temp file + atomic rename pattern to prevent partial state
- Immutable History: Objects and commits never change once written, only extend
- Staging Index: .ofs/index.json tracks files to be committed (similar to git staging area)
- References: .ofs/refs/heads/main points to latest commit, .ofs/HEAD to current commit

Key Algorithms:
- Hash computation: SHA-256 streaming for large files (8KB chunks)
- Object storage: Two-level directory (first 2 chars of hash as directory)
- Deduplication: Store content by hash, identical content = one copy
- Commit numbering: Sequential integers with zero-padding (001, 002, etc.)
- Atomic writes: temp_file.write() → os.rename() for all metadata updates

Performance Limits (v1):
- Maximum files per repository: 10,000
- Maximum file size: 100MB per file
- Maximum repository size: 10GB total
- Maximum commit history: 10,000 commits
- Memory usage: Less than 100MB peak RSS
- Disk space overhead: Less than 10% metadata vs content ratio

Performance Targets:
- Repository initialization: Less than 1 second
- File staging (1MB file): Less than 100ms
- Commit creation: Less than 500ms
- Checkout (100 files): Less than 5 seconds
- Verification (1000 objects): Less than 10 seconds

Security Model:
- SHA-256 cryptographic verification (FIPS 140-2 approved)
- No network communication whatsoever (zero network code)
- No external executables (no subprocess calls)
- Path traversal prevention (validate all paths within repo)
- Input validation on all user data
- No arbitrary code execution (no eval, exec, pickle)

Threat Protection:
- Protected against: accidental overwrites, file corruption, pilot error, silent data loss
- NOT protected against: malicious actors with filesystem access, physical device compromise, intentional sabotage

Testing Strategy:
- Unit tests: 95%+ coverage target
- Integration tests: End-to-end workflow testing
- Cross-platform tests: Windows, Linux, macOS
- Chaos engineering: Power-loss simulation, corruption detection, disk full scenarios
- Performance benchmarks: Verify targets met

Common Gotchas:
- This is NOT Git - it's a simplified, offline-first alternative with different goals
- No branching or merging in v1 (linear history only, single branch)
- No compression in v1 (raw content stored)
- No partial checkouts (entire repository state restored)
- No sub-modules or nested repositories
- All operations are local - no push/pull/remote/clone operations
- Author info from environment variables (USER env var)
- Ignore patterns in .ofs/config.json (not .gitignore format)
- Design philosophy: Simplicity and transparency over features
- File paths must be relative to repository root
- Windows/Unix path handling differences managed by pathlib

Functional Requirements Summary:
- FR-1: Repository initialization (ofs init)
- FR-2: Repository status (ofs status)
- FR-3: Add files to staging (ofs add)
- FR-4: Commit staged changes (ofs commit -m "message")
- FR-5: View commit history (ofs log)
- FR-6: Checkout previous commits (ofs checkout \u003cid\u003e)
- FR-7: Integrity verification (ofs verify)
- FR-8: Ignore patterns (.ofsignore support)
- FR-9: Show changes (ofs diff)

Error Handling Philosophy:
- Fail early and loudly (no silent failures)
- Provide actionable error messages with suggested fixes
- Clean up partial state on failures
- Never silently corrupt data
- Verify integrity on every read operation
- Example: "Error: Cannot commit with empty staging index. Suggestion: Use 'ofs add \u003cfile\u003e' to stage files first."

Success Metrics:
- Installation success rate: 100% (no external dependencies)
- Data integrity verification: 100% (zero undetected corruption)
- Rollback accuracy: 100% (exact state restoration)
- Cross-platform compatibility: 100% (Windows, Linux, macOS)
- User satisfaction target: 4.5/5 or higher
