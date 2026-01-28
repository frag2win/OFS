# Contributing to OFS

Thank you for your interest in contributing to OFS! This document provides guidelines for development.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/frag2win/OFS.git
   cd OFS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install development dependencies**
   ```bash
   # OFS has zero runtime dependencies
   # Install only development tools:
   pip install pytest pytest-cov black pylint mypy flake8
   ```

4. **Verify setup**
   ```bash
   python -m pytest tests/
   ```

## Code Style

### Python Style Guide

- **Line length**: 100 characters
- **Formatter**: Black
- **Type hints**: Required on all functions
- **Docstrings**: Google style, required on all public functions

### Example

```python
def compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data.
    
    Args:
        data: Bytes to hash
        
    Returns:
        Hex digest of SHA-256 hash
        
    Example:
        >>> compute_hash(b"hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    import hashlib
    return hashlib.sha256(data).hexdigest()
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=ofs --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_objects.py

# Run with verbose output
python -m pytest tests/ -v
```

### Writing Tests

- Test files: `tests/unit/test_*.py`
- Test functions: `def test_*():`
- Use fixtures from `tests/conftest.py`
- Aim for \u003e90% code coverage

Example test:

```python
def test_store_and_retrieve(tmp_repo):
    """Test storing and retrieving content."""
    from ofs.core.objects import ObjectStore
    
    store = ObjectStore(tmp_repo / ".ofs")
    content = b"Test content"
    
    # Store
    hash_val = store.store(content)
    
    # Retrieve
    retrieved = store.retrieve(hash_val)
    
    assert retrieved == content
```

## Code Quality

### Linting

```bash
# Run all linters
python -m pylint ofs/
python -m flake8 ofs/
python -m mypy ofs/

# Format code
python -m black ofs/ tests/
```

### Pre-commit Checklist

Before committing:

- [ ] All tests pass
- [ ] Code formatted with Black
- [ ] No linting errors
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Tests added for new features

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches

### Commit Messages

Use conventional commits:

```
feat: add checkout command
fix: correct hash verification in object store
docs: update architecture documentation
test: add tests for index management
refactor: simplify commit creation logic
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

3. **Push to GitHub**
   ```bash
   git push origin feature/my-feature
   ```

4. **Create Pull Request**
   - Describe changes clearly
   - Reference related issues
   - Ensure CI passes
   - Request review

## Project Structure

```
ofs/
├── ofs/                    # Main package
│   ├── core/              # Core business logic
│   ├── commands/          # CLI commands
│   ├── utils/             # Utilities
│   ├── models/            # Data models
│   └── cli/               # CLI infrastructure
└── tests/                 # Test suite
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── fixtures/         # Test data
```

## Design Principles

When contributing, adhere to:

1. **Offline-First**: No network code
2. **Zero Dependencies**: Standard library only
3. **Deterministic**: Same inputs → same outputs
4. **Transparent**: Human-readable formats
5. **Fail-Safe**: Detect corruption, never silently fail
6. **Testable**: Write testable, isolated code

## Common Tasks

### Adding a New Command

1. Create `ofs/commands/mycommand/execute.py`
2. Implement command logic
3. Add to CLI dispatcher
4. Write tests in `tests/unit/commands/mycommand/`
5. Update documentation

### Adding a New Utility

1. Create `ofs/utils/category/function.py`
2. Write single-purpose function
3. Add type hints and docstring
4. Write unit tests
5. Import in `__init__.py`

## Getting Help

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Read [OFS_Enhanced_PRD_v2.0.md](../OFS_Enhanced_PRD_v2.0.md) for requirements
- Open an issue for questions
- Join discussions on GitHub

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing to OFS! 🚀
