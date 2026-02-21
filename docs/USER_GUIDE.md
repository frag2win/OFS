# OFS User Guide - Commit System

**Version:** 1.0  
**Phase:** 3 Complete

---

## Quick Start

### Creating Your First Commit

```bash
# Initialize a repository
ofs init

# Create a file
echo "Hello, OFS!" > hello.txt

# Stage the file
ofs add hello.txt

# Create a commit
ofs commit -m "Add hello.txt"
```

**Output:**
```
[main 001] Add hello.txt
 1 file(s) changed
 1 file(s) added
```

---

## Commands

### ofs commit

Create a snapshot of your staged changes.

**Usage:**
```bash
ofs commit -m "Your message here"
```

**Requirements:**
- Message must be at least 3 characters
- At least one file must be staged
- Repository must be initialized

**Examples:**
```bash
# Good commit messages
ofs commit -m "Add user authentication"
ofs commit -m "Fix login bug"
ofs commit -m "Update README with examples"

# Bad - too short
ofs commit -m "ok"  # ERROR: Message too short
```

**What Happens:**
1. Validates staged changes exist
2. Creates commit with sequential ID (001, 002, 003...)
3. Updates repository history
4. Clears staging area

---

### ofs log

View commit history.

**Usage:**
```bash
# Full format (default)
ofs log

# Limit number of commits
ofs log -n 5

# Compact one-line format
ofs log --oneline
```

**Full Format Output:**
```
Commit 003
Author: jsmith
Date:   2026-01-30 20:30:45

    Add authentication module

    Changes:
      + src/auth.py (4096 bytes)
      M src/main.py (8192 bytes)

Commit 002
Author: jsmith
Date:   2026-01-30 15:20:30

    Initial project structure
    
    Changes:
      + src/main.py (6144 bytes)
```

**Oneline Format Output:**
```
003 2026-01-30 20:30 jsmith  Add authentication module
002 2026-01-30 15:20 jsmith  Initial project structure
001 2026-01-30 10:00 jsmith  First commit
```

---

### ofs checkout

Restore your repository to a previous commit.

**Usage:**
```bash
# Interactive mode (default - warns on uncommitted changes)
ofs checkout <commit-id>

# Force mode (discards uncommitted changes without warning)
ofs checkout --force <commit-id>
```

**Examples:**
```bash
# Go back to commit 002
ofs checkout 002

# Force checkout (skip warnings)
ofs checkout --force 002
```

**⚠️ IMPORTANT: Checkout Safety**

Checkout will **overwrite your working directory** to match the commit state. Any uncommitted changes will be **LOST**.

**Safe Workflow:**
1. Check status: `ofs status`
2. Commit changes: `ofs commit -m "Save work"`
3. Then checkout: `ofs checkout <commit-id>`

**Warning Example:**
```
$ ofs checkout 002
⚠️  WARNING: You have uncommitted changes in the staging area
These changes will be LOST if you proceed.

Your uncommitted changes:
  • src/main.py
  • README.md

Options:
  1. Commit your changes:  ofs commit -m 'save work'
  2. Force checkout:        ofs checkout --force 002

Continue anyway? (y/N): 
```

---

## Understanding Commit IDs

OFS uses **sequential numeric IDs**: 001, 002, 003, etc.

**Why not SHA hashes like Git?**
- **Easier to remember**: "checkout 5" vs "checkout a7f8e3b92c1d4f6e..."
- **Simpler for offline use**: No clock synchronization needed
- **Perfect for single-user**: No distributed merge conflicts
- **Human-friendly**: Clear chronological order

**How it works:**
```
First commit  → 001
Second commit → 002
Third commit  → 003
...and so on
```

---

## Common Workflows

### Making Changes

```bash
# 1. Make your changes
echo "New feature" >> src/feature.py

# 2. Add to staging
ofs add src/feature.py

# 3. Commit
ofs commit -m "Add new feature"
```

### Reviewing History

```bash
# See all commits
ofs log

# See recent commits only
ofs log -n 3

# Quick overview
ofs log --oneline
```

### Time Travel (Checkout)

```bash
# View commit history
ofs log --oneline
# 003 2026-01-30 20:30 jsmith  Latest work
# 002 2026-01-30 15:20 jsmith  Previous version
# 001 2026-01-30 10:00 jsmith  First commit

# Go back to commit 002
ofs checkout 002
# Your files now match commit 002 exactly

# Return to latest
ofs checkout 003
```

### Safe Experimentation

```bash
# Save current work
ofs commit -m "Before experiment"

# Try something
echo "Experimental code" >> test.py
ofs add test.py
ofs commit -m "Experiment"

# If experiment failed, go back
ofs log --oneline
# 002 ... Experiment
# 001 ... Before experiment

ofs checkout 001  # Revert to before experiment
```

---

## Best Practices

### 1. Commit Often

✅ **Good:**
```bash
ofs commit -m "Add login form"
ofs commit -m "Add password validation"
ofs commit -m "Add error handling"
```

❌ **Avoid:**
```bash
# One massive commit after days of work
ofs commit -m "Did everything"
```

### 2. Write Clear Messages

✅ **Good:**
- "Fix login bug when password is empty"
- "Add user profile page"
- "Update API to v2.0"

❌ **Avoid:**
- "stuff"
- "changes"
- "asdf"

### 3. Check Status Before Checkout

✅ **Safe:**
```bash
ofs status  # Check for uncommitted changes
ofs commit -m "Save work"  # Commit first
ofs checkout 002  # Safe to checkout
```

❌ **Risky:**
```bash
# Made changes but didn't commit
ofs checkout 002  # ⚠️ Will lose changes!
```

---

## Troubleshooting

### "Error: Nothing to commit"

**Problem:** No files staged

**Solution:**
```bash
# Stage files first
ofs add .
ofs commit -m "Your message"
```

---

### "Error: Commit message too short"

**Problem:** Message less than 3 characters

**Solution:**
```bash
# Use a descriptive message (≥3 chars)
ofs commit -m "Fix bug"  # ✓ Good
```

---

### "Warning: You have uncommitted changes"

**Problem:** Trying to checkout with uncommitted work

**Solution 1 - Commit first:**
```bash
ofs commit -m "Save work"
ofs checkout 002
```

**Solution 2 - Force (lose changes):**
```bash
ofs checkout --force 002  # Discards uncommitted changes
```

---

### "Error: Commit not found"

**Problem:** Invalid commit ID

**Solution:**
```bash
# Check available commits
ofs log --oneline

# Use valid ID
ofs checkout 003  # Must exist
```

---

## Limitations (v1)

### No Branching Yet

**Current:**
```
001 ← 002 ← 003 ← 004 (linear history only)
```

**Not supported:**
```
         ← feature branch
        /
001 ← 002 ← 003 (main)
```

**Workaround:**
Use filesystem copies for experimental work:
```bash
cp -r project/ project-experiment/
cd project-experiment/
# Experiment here
```

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `ofs commit -m "msg"` | Save snapshot | `ofs commit -m "Add feature"` |
| `ofs log` | View history | `ofs log` |
| `ofs log -n 5` | Limit output | `ofs log -n 5` |
| `ofs log --oneline` | Compact format | `ofs log --oneline` |
| `ofs checkout <id>` | Restore commit | `ofs checkout 002` |
| `ofs checkout --force <id>` | Force restore | `ofs checkout --force 002` |

---

## Next Steps

- Learn about `ofs status` - See current repository state
- Learn about `ofs add` - Stage files for commit
- Learn about repository verification (Phase 4)

---

**Need help?** Run any command with `--help`:
```bash
ofs commit --help
ofs log --help
ofs checkout --help
```

---

## Global CLI Options

Starting in Phase 6, OFS supports several global flags to control output formatting and command-line experience:

### `--version`
Print the current version of the OFS client.
```bash
ofs --version
# Output: OFS 1.0.0
```

### `--no-color`
By default, OFS output (like `ofs status` and `ofs diff`) is colored using standard ANSI escape codes for readability (green for additions, red for deletions).
If you want to disable colors (e.g. for scripting, or terminal incompatibility):
```bash
ofs --no-color status
```
*Note: OFS also respects the standard `NO_COLOR=1` environment variable.*

### Progress Indicators
For operations that process a large amount of files (`ofs add`, `ofs verify`, `ofs checkout`), OFS will automatically display a progress bar when run interactively in a terminal.
If you pipe the output (e.g. `ofs verify > results.txt`), the progress bar disables itself automatically to prevent log corruption.
