# OFS - Offline File System

**A production-ready, local-first version control system engineered for air-gapped environments.**

## Overview

OFS (Offline File System) is an version control system designed specifically for high-security, air-gapped environments where traditional distributed version control systems cannot operate. It provides cryptographically-verified file versioning, deterministic state management, and complete operational transparency without requiring network connectivity, external dependencies, or complex infrastructure.

## Key Features

- **Offline-First**: Zero network dependencies, works completely offline
- **Zero Dependencies**: Pure Python 3.8+ standard library only
- **Content-Addressable Storage**: SHA-256 based object store with automatic deduplication
- **Deterministic**: Same inputs always produce same outputs
- **Transparent**: Human-readable formats, visible state
- **Cryptographic Integrity**: All content verified with SHA-256
- **Atomic Operations**: All-or-nothing commits prevent corruption
- **Cross-Platform**: Works on Windows, Linux, macOS

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/frag2win/OFS.git
cd OFS

# Run OFS (no installation required)
python -m ofs --help
```

### Basic Usage

```bash
# Initialize a new repository
python -m ofs init

# Add files to staging
python -m ofs add myfile.txt
python -m ofs add src/

# View what's staged
python -m ofs status

# Create a commit snapshot
python -m ofs commit -m "Initial commit"

# View commit history
python -m ofs log

# View compact history
python -m ofs log --oneline

# Restore to a previous commit
python -m ofs checkout 001

# Verify repository integrity
python -m ofs verify
python -m ofs verify --verbose  # Detailed output
```

### Example Workflow

```bash
# 1. Initialize repository
python -m ofs init

# 2. Create some files
echo "Hello, OFS!" > hello.txt
mkdir src
echo "print('Hello')" > src/main.py

# 3. Stage files
python -m ofs add .

# 4. Create first commit
python -m ofs commit -m "Add initial files"
# Output: [main 001] Add initial files

# 5. Make changes
echo "World!" >> hello.txt

# 6. Stage and commit changes
python -m ofs add hello.txt
python -m ofs commit -m "Update hello.txt"
# Output: [main 002] Update hello.txt

# 7. View history
python -m ofs log --oneline
# 002 2026-01-30 20:45 user  Update hello.txt
# 001 2026-01-30 20:40 user  Add initial files

# 8. Go back to first commit
python -m ofs checkout 001
# Output: ✓ Checked out to commit 001 "Add initial files"

# 9. Return to latest
python -m ofs checkout 002
```

## Use Cases

OFS is ideal for:

- **Defense & Aerospace**: Air-gapped development facilities
- **Critical Infrastructure**: Isolated control systems
- **Research Labs**: Secure R&D environments
- **Regulated Industries**: Compliance-driven workflows
- **Embedded Systems**: Resource-constrained devices

## Project Status

**Current Version**: 0.3.1 (Phase 3 Refined) ✅

**Completed Phases:**
- Phase 0: Project Foundation
- Phase 1: Core Storage (Object Store, Index)
- Phase 2: File Operations (add, status)
- Phase 3: Commit System (commit, log, checkout)

**Test Coverage:** 88.67% (299 tests, all passing) ✅

**v0.3.1 Refinements:**
- Fixed critical checkout bug (ghost files not being removed)
- Fixed commit tracking bug (false deletion markers)  
- Resolved test cache pollution issues (stable test suite)
- Improved test coverage from 78% to 88.67%
- Enhanced Windows compatibility (ASCII console output)
- added `verify` command for repository integrity checking
- Performance optimizations and code quality improvements

See [Implementation Checklist](docs/requirements/OFS_Implementation_Checklist_v2.0.md) for the complete roadmap.

## Documentation

**User Documentation:**
- [User Guide](docs/USER_GUIDE.md) - Complete command reference and examples
- [Phase 3 Summary](docs/phase3/Phase3_Summary.md) - Latest implementation details

**Technical Documentation:**
- [Product Requirements Document](docs/requirements/OFS_Enhanced_PRD_v2.0.md) - Complete specification
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Implementation Checklist](docs/requirements/OFS_Implementation_Checklist_v2.0.md) - Development roadmap

## Requirements

- Python 3.8 or higher
- No external dependencies

## Architecture

OFS uses a content-addressable storage model similar to Git but simplified for offline-first operation:

```
.ofs/
├── objects/          # Content-addressable blob storage (SHA-256)
├── commits/          # Commit history (sequential, numbered)
├── refs/heads/       # Branch references
├── index.json        # Staging area
├── HEAD              # Current commit pointer
└── config.json       # Repository configuration
```

## Development

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install pytest pytest-cov

# Run all tests (299 tests)
python -m pytest tests/unit/ tests/integration/ tests/reliability/

# Run tests with coverage
python -m pytest tests/ --cov=ofs --cov-report=term

# Run linters
python -m pylint ofs/
python -m mypy ofs/
```

### Testing

OFS has comprehensive test coverage:

- **Unit Tests**: Core module functionality (commits, refs, objects, index)
- **Integration Tests**: End-to-end workflows (checkout, commit cycles)
- **Reliability Tests**: Edge cases, error handling, corruption detection

**Coverage by Module:**
- Core commits: 95%+
- Repository: 92%+  
- Commands: 85-90%
- Utils: 90-100%
- CLI: 85%+

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

[To be determined - Please add license information]

## Authors (Notes)
Name - Shubham pawar 
portfolio: https://shubham-pawar.vercel.app/

OFS Development Team
## Support

For issues and questions, please open an issue on GitHub.

---

**Built for environments where security and reliability matter most.**
