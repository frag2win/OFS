# OFS Architectural Audit — Phase 0–6 Hardening Report

**Date:** February 22, 2026  
**Scope:** Correctness, Determinism, Algorithmic Complexity, Performance, Locality  
**Baseline:** 348 tests passing, 87.06% coverage

---

# 1️⃣ Correctness & Determinism Audit

## 1.1 Hidden Global Mutable State

> [!CAUTION]
> **FOUND — `_commit_cache` in `ofs/core/commits/load.py` (line 13)**

```python
# Module-level global mutable dict
_commit_cache: Dict[Tuple[str, str], Optional[dict]] = {}
```

**Impact:** This dict persists across the entire Python process lifetime. In production this is benign (single CLI invocation per process), but in **test suites** this causes **cross-test cache contamination** — a test that loads commit `001` from repo A poisons the cache for a subsequent test that creates a different commit `001` in repo B at the same resolved path.

**Why tests still pass:** Tests use `tmp_path` which generates unique directories, so `str(commits_dir.resolve())` differs per test. However, this is fragile and breaks if two tests ever share the same temp directory or if the cache isn't cleared between test phases.

**Refactoring:**

```diff
# Option A: Scope cache to Repository instance (RECOMMENDED)
# Move cache into a class or pass it as parameter
# Option B: Clear cache in conftest.py fixture (MINIMAL)
+@pytest.fixture(autouse=True)
+def clear_commit_cache():
+    from ofs.core.commits.load import clear_commit_cache
+    clear_commit_cache()
+    yield
+    clear_commit_cache()
```

---

## 1.2 Global Mutable State — Color Override

> [!WARNING]
> **FOUND — `_USE_COLOR_OVERRIDE` in `ofs/utils/ui/color.py` (line 25)**

```python
_USE_COLOR_OVERRIDE = None
```

**Impact:** `set_color_enabled(False)` persists across the entire process. If the CLI dispatcher sets `--no-color`, it leaks into subsequent commands in the same process (relevant for test suites). Color tests already call `reset_color_override()` in setup/teardown, which is correct but fragile.

**Recommendation:** No code change needed, but add an `autouse` fixture in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def reset_ui_state():
    from ofs.utils.ui.color import reset_color_override
    reset_color_override()
    yield
    reset_color_override()
```

---

## 1.3 Unsafe File Writes (Atomicity Violations)

> [!CAUTION]
> **FOUND — 2 locations bypass the project's own `atomic_write()` utility**

### Location 1: `ofs/core/commits/save.py` (lines 30–32)

```python
temp_file = commit_file.with_suffix(".tmp")
temp_file.write_text(json.dumps(commit_obj, indent=2))
temp_file.rename(commit_file)   # ❌ Fails on Windows if target exists
```

**Problem:** On Windows, `Path.rename()` will raise `FileExistsError` if the target already exists. The project's own `atomic_write()` in `ofs/utils/filesystem/atomic_write.py` handles this correctly with `os.name == "nt"` check + `unlink()` before rename.

**Fix:**

```diff
-temp_file = commit_file.with_suffix(".tmp")
-temp_file.write_text(json.dumps(commit_obj, indent=2))
-temp_file.rename(commit_file)
+from ofs.utils.filesystem.atomic_write import atomic_write
+atomic_write(commit_file, json.dumps(commit_obj, indent=2).encode("utf-8"))
```

### Location 2: `ofs/core/refs/update_ref.py` (lines 26–31)

```python
temp_path = ref_path.parent / f"{ref_path.name}.tmp"
temp_path.write_text(value.strip() + "\n")
if temp_path.exists():
    temp_path.replace(ref_path)
```

**Note:** This uses `Path.replace()` which IS atomic on both POSIX and Windows (unlike `Path.rename()`). This is technically correct but inconsistent with the pattern used everywhere else. The redundant `if temp_path.exists()` check (it was just written successfully) suggests a logic confusion.

**Fix (consistency):**

```diff
-temp_path = ref_path.parent / f"{ref_path.name}.tmp"
-temp_path.write_text(value.strip() + "\n")
-if temp_path.exists():
-    temp_path.replace(ref_path)
+from ofs.utils.filesystem.atomic_write import atomic_write
+atomic_write(ref_path, (value.strip() + "\n").encode("utf-8"))
```

---

## 1.4 Inconsistent Path Normalization

> [!WARNING]
> **FOUND — Mixed forward/backslash handling in ignore patterns**

In `ofs/utils/ignore/patterns.py` line 80:

```python
if path_str.startswith(dir_pattern + '/') or path_str.startswith(dir_pattern + '\\'):
```

This handles the Windows backslash case, which is good. However, `path_str` comes from `str(path)` or `str(rel_path)`, which produces backslashes on Windows. This means `fnmatch.fnmatch(path_str, pattern)` (line 90) may fail if the user writes `build/` as a pattern but `path_str` is `build\file.py`.

**Recommendation:** Normalize `path_str` to always use forward slashes before matching:

```python
path_str = str(rel_path).replace("\\", "/")
```

---

## 1.5 Duplicated Commit-Tree Reconstruction Logic

> [!WARNING]
> **FOUND — `build_tree_state()` has ONE canonical location but is imported circularly**

`build_tree_state()` lives in `ofs/commands/checkout/execute.py`, but is imported by:
- `ofs/commands/diff/execute.py` (line 15)
- `ofs/core/commits/create.py` (line 85, inside `get_file_actions`)

The function is fundamentally a **core operation** (tree reconstruction), not a command-layer concern. It should live in `ofs/core/commits/` or `ofs/core/`.

**Impact:** The circular import in `create.py` is guarded by a function-level import (`from ofs.commands.checkout.execute import build_tree_state` inside `get_file_actions()`), which works but is architecturally wrong — core logic should never import from the commands layer.

**Refactoring:** Move `build_tree_state()` to `ofs/core/commits/tree.py` (new file) and update all imports.

---

## 1.6 Circular Imports

> [!CAUTION]
> **FOUND — `ofs/core/commits/create.py` → `ofs/commands/checkout/execute.py`**

```python
# ofs/core/commits/create.py line 85
from ofs.commands.checkout.execute import build_tree_state
```

**This violates the architectural layering.** The architecture diagram shows:

```
CLI → Commands → Core → Utils
```

Core should NEVER import from Commands. This creates a fragile circular dependency chain.

---

## 1.7 Inconsistent Error Message Formats

> [!NOTE]
> **FOUND — 3 patterns used inconsistently across commands**

| Pattern | Example | Used In |
|---------|---------|---------|
| `Error: <msg>` | `"Error: Not an OFS repository"` | add, checkout, diff, status |
| `[FAIL] <msg>` | `"[FAIL] Repository verification failed"` | verify |
| `Warning: <msg>` | `"Warning: Path does not exist"` | add |

**Recommendation:** Standardize on `Error:` for errors and `Warning:` for warnings. The `[OK]`/`[FAIL]` pattern in verify is acceptable as it's a diagnostic tool.

---

## 1.8 CLI-State Side Effects

> [!WARNING]
> **FOUND — `--no-color` leaks into `os.environ`**

In `ofs/cli/dispatcher.py`:

```python
if hasattr(args, 'no_color') and args.no_color:
    os.environ["NO_COLOR"] = "1"
```

Setting `os.environ["NO_COLOR"]` mutates the process environment permanently, which leaks into child processes and test suites. This is a side effect that persists beyond the CLI invocation.

**Recommendation:** Only use `set_color_enabled(False)` and remove the `os.environ` mutation.

---

## 1.9 `atomic_write()` — Windows Race Condition

> [!CAUTION]
> **FOUND — Non-atomic window in `atomic_write.py` lines 40–43**

```python
if os.name == "nt" and file_path.exists():
    file_path.unlink()       # ← Target is gone
    # CRASH HERE = DATA LOSS
temp_path.rename(file_path)  # ← Target is restored
```

Between `unlink()` and `rename()`, if the process crashes, the target file is **deleted and the temp file isn't renamed**. On Windows, use `os.replace()` which is atomic:

```diff
-if os.name == "nt" and file_path.exists():
-    file_path.unlink()
-temp_path.rename(file_path)
+temp_path.replace(file_path)  # atomic on both POSIX and Windows
```

`Path.replace()` is available since Python 3.3 and handles the cross-platform case correctly.

---

# 2️⃣ Algorithmic Complexity Review

## Complexity Table

| Operation | Time Complexity | Disk I/O | Memory | Key Bottleneck |
|-----------|----------------|----------|--------|----------------|
| `build_tree_state(cid)` | O(C × F) | C JSON reads + list_commits glob | O(F) tree dict | Replays ALL commits from 001→cid |
| `checkout(cid)` | O(C×F + F_r + F_d) | C JSON + F_r object reads + F_r file writes | O(F) tree + O(max_file) content | Calls `build_tree_state` TWICE (target + current HEAD) |
| `verify_repository()` | O(Obj + Idx + C×F) | Reads ALL objects + index + ALL commits | O(Obj) list + O(Idx) entries | Reads every object byte; recomputes every hash |
| `ofs diff (commit vs commit)` | O(C×F + F_d × S) | 2× `build_tree_state` + object retrieves | O(F) trees + O(S) diff lines | Two full history replays |
| `ofs diff (working vs staged)` | O(Idx × S) | Idx object reads + Idx file reads | O(S) diff per file | Object `retrieve()` re-hashes on every read |
| Working tree scan | O(W × P) | Walks entire directory tree | O(W) file set | W files × P patterns for ignore matching |
| Index loading | O(1) disk + O(Idx) parse | 1 JSON read | O(Idx) entries | Parsed once per `Index()` constructor |
| Commit loading (cached) | O(1) amortized | 1 JSON read (first access) | O(1) per commit | Global cache — see §1.1 |
| `list_commits()` | O(C × log C) | C JSON reads (bypasses cache!) | O(C) commit objects | Re-parses ALL commits from disk every time |

**Legend:** C = total commits, F = total files across commits, F_r = files to restore, F_d = files in diff, S = file size (lines), W = working tree files, P = ignore patterns, Obj = total objects, Idx = index entries.

---

## 2.1 `build_tree_state()` — O(C × F) Full History Replay

**Current behavior:** Calls `list_commits()` which globs ALL `.json` files, parses ALL of them into memory, reverses the list, then iterates from commit 001 to `commit_id`, applying file entries to build the tree.

**Redundancy:** `list_commits()` bypasses the commit cache entirely — it reads and parses every commit file from disk directly. This means commit JSON is parsed twice: once by `list_commits()`, and once if `load_commit()` is later called.

**Safe optimization:**

```python
def build_tree_state(commit_id: str, commits_dir: Path) -> Dict[str, dict]:
    """Build tree by walking parent chain (newest→oldest), then applying in order."""
    # Walk parent chain to collect commits from target back to root
    chain = []
    current_id = commit_id
    while current_id:
        commit = load_commit(current_id, commits_dir)  # Uses cache!
        if not commit:
            break
        chain.append(commit)
        current_id = commit.get('parent')
    
    # Apply from oldest to newest
    tree_state = {}
    for commit in reversed(chain):
        for file_entry in commit.get('files', []):
            path = file_entry.get('path')
            if file_entry.get('action') == 'deleted':
                tree_state.pop(path, None)
            else:
                tree_state[path] = file_entry
    return tree_state
```

**Improvement:** Changes from O(C × F) to O(D × F_avg) where D = depth of target commit. Also leverages commit cache instead of re-parsing.

---

## 2.2 Checkout — Double `build_tree_state`

**Current:** `execute()` calls `build_tree_state(commit_id)` once for the target, then later calls `build_tree_state(current_head)` to find files to remove.

**Optimization:** Build both trees in a single pass since the current HEAD is always an ancestor of or sibling to the target.

---

## 2.3 `ObjectStore.retrieve()` — Hash Recomputation on Every Read

**Current:** Every `retrieve()` call re-reads the file AND recomputes SHA-256 hash for integrity verification:

```python
content = obj_path.read_bytes()
actual_hash = compute_hash(content)  # ← SHA-256 of entire content
```

**Impact:** For diff operations comparing N files, this means N SHA-256 computations even though we already know the hash (it's the lookup key). The hash is embedded in the filesystem path.

**Safe optimization (optional):** Add a `retrieve_unchecked()` method for trusted internal paths where the hash is already validated by the filesystem structure:

```python
def retrieve_unchecked(self, hash_value: str) -> bytes:
    """Retrieve without hash verification (for performance-critical paths)."""
    obj_path = self._get_path(hash_value)
    if not obj_path.exists():
        raise FileNotFoundError(f"Object not found: {hash_value}")
    return obj_path.read_bytes()
```

**Invalidation:** This is safe because objects are immutable once written and the hash IS the filename.

---

## 2.4 `list_commits()` — Bypasses Cache, Re-parses Everything

**Current:** `list_commits()` in `ofs/core/commits/list.py` globs `*.json`, reads and parses every file, then sorts. It never touches the `_commit_cache` from `load.py`.

**Impact:** Called by `build_tree_state()`, which means every tree reconstruction re-parses all commit files from disk.

**Optimization:** Addressed by the parent-chain approach in §2.1.

---

## 2.5 `verify_commits()` — Also Bypasses Cache

Same issue as §2.4. `verify_commits()` in `integrity.py` directly reads and parses all commit files, ignoring the cache. For verification this is arguably correct (you want to verify what's on disk, not what's cached), but it should be documented as intentional.

---

# 3️⃣ Performance Bottleneck Identification

## Bottleneck 1: O(C²×F) — Repeated Full History Replay

**Where:** `checkout` calls `build_tree_state` twice. `diff` between commits calls it twice. `get_file_actions` during `commit` calls it once.

**Impact quantification:** For a repository with 1000 commits × 100 files per commit:
- `list_commits` = glob + parse 1000 JSON files = ~1000 disk reads
- Tree construction = 1000 × 100 = 100,000 dict operations
- Per checkout = 2× = 200,000 dict operations + 2000 JSON parses
- This scales linearly with commit count, making old repositories progressively slower.

**Fix:** Parent-chain traversal (§2.1) reduces from O(C) to O(D) where D ≤ C.

---

## Bottleneck 2: O(Idx × hash_cost) — `_diff_working_vs_staged`

**Where:** `ofs/commands/diff/execute.py` line 100:

```python
staged_content = object_store.retrieve(entry['hash'])
```

**Impact:** `retrieve()` reads the file AND recomputes SHA-256. For a staging area with 100 files of 1MB each, this is 100MB of hashing. The hash is already known from the object store path.

**Fix:** Use `retrieve_unchecked()` as proposed in §2.3.

---

## Bottleneck 3: O(W × P) — Ignore Pattern Matching

**Where:** `scan_working_tree` calls `should_ignore` for every file, which iterates all patterns.

**Impact:** For W=10,000 files and P=50 patterns, that's 500,000 `fnmatch` calls. Each `fnmatch` call is O(pattern_length × path_length).

**Optimization:** Pre-compile patterns with `fnmatch.translate()` + `re.compile()`:

```python
import re

def compile_patterns(patterns: List[str]) -> List[Tuple[str, re.Pattern, bool]]:
    compiled = []
    for p in patterns:
        is_negation = p.startswith('!')
        raw = p[1:] if is_negation else p
        regex = re.compile(fnmatch.translate(raw))
        compiled.append((raw, regex, is_negation))
    return compiled
```

**Improvement:** Reduces from repeated `fnmatch` interpretation to a single regex match per pattern.

---

## Bottleneck 4: O(N) Index Lookup by Path — Linear Scan

**Where:** `Index.find_entry()` and `Index.add()` both do linear scans:

```python
# find_entry: O(n)
for entry in self._entries:
    if entry["path"] == file_path:

# add: O(n) list comprehension to remove existing
self._entries = [e for e in self._entries if e["path"] != file_path]
```

**Impact:** For an index with 10,000 entries, adding a single file triggers a full list scan.

**Optimization:** Maintain a secondary `dict` index:

```python
self._entries_by_path: Dict[str, dict] = {e["path"]: e for e in self._entries}
```

**Trade-off:** O(1) lookup vs O(n) memory for the dict. Worthwhile for repositories with >1000 staged files.

---

## Bottleneck 5: Index Saved on Every `add()` Call

**Where:** `Index.add()` calls `self._save()` after every single file addition. During `ofs add .` on a directory with 1000 files, the index JSON is serialized and atomically written 1000 times.

**Impact:** 1000 × (JSON serialize + temp write + atomic rename) = significant I/O.

**Optimization:** Add a `batch_add()` method or a context manager:

```python
def batch_add(self, entries: List[Tuple[str, str, dict]]):
    for path, hash_val, meta in entries:
        self._entries = [e for e in self._entries if e["path"] != path]
        self._entries.append({"path": path, "hash": hash_val, **meta})
    self._save()  # Single write
```

---

# 4️⃣ Memory & CPU Locality Review

## 4.1 JSON Parsing Repetition

| Data | Parsed Repeatedly? | Impact |
|------|---------------------|--------|
| Commit files | Yes — `list_commits()` re-parses all, ignoring cache | High for repos with many commits |
| Index JSON | No — parsed once in `Index.__init__()` | ✅ Good |
| Config JSON | Parsed per operation (low frequency) | ✅ Acceptable |
| `.ofsignore` | Parsed per `load_ignore_patterns()` call | Low — called once per command |

**Fix:** Parent-chain traversal eliminates `list_commits()` calls in `build_tree_state()`.

## 4.2 Sequential vs Random File Access

| Operation | Access Pattern | Locality |
|-----------|---------------|----------|
| Object store iterate (verify) | Iterates `objects/` prefix dirs sequentially | ✅ Good — sequential directory walk |
| Object retrieve (diff) | Random access by hash | ⚠️ Poor — hash prefix creates random seeks |
| Commit file read | Sequential glob then parse | ✅ Good |
| Working tree scan | Recursive directory walk | ✅ Good — follows FS structure |

**Optimization for diff:** When comparing two commits, sort the file paths before retrieving objects. This doesn't improve random hash seeks, but reduces the number of directory-level seeks if multiple files share the same hash prefix.

## 4.3 Commit Replay Optimization

**Current:** Tree reconstruction replays ALL commits from 001. For commit 500, this means loading 500 JSON files and iterating through 500 file lists.

**Proposed: Snapshot Checkpoints** (Future Phase 7+ idea — marked as future, not implemented):

> [!NOTE]
> Every N commits (e.g., N=100), persist a full tree-state snapshot as `.ofs/snapshots/100.json`. Tree reconstruction then starts from the nearest snapshot instead of commit 001. This is a Phase 7+ consideration.

**Immediate optimization (safe for Phase 6):** The parent-chain traversal from §2.1 already eliminates the need for `list_commits()` and uses the commit cache.

## 4.4 Data Locality Suggestions

1. **Index:** Already good — single JSON file, parsed once, held in memory.
2. **Commits:** Switch to parent-chain traversal to avoid scanning the entire `commits/` directory.
3. **Objects:** Consider sorting diffed paths before retrieval to improve prefix-bucket locality.
4. **Ignore patterns:** Pre-compile regex patterns once per command invocation, store as compiled list.

---

# Summary of All Findings

## Critical Issues (Must Fix)

| # | Issue | File | Severity |
|---|-------|------|----------|
| 1 | `atomic_write()` Windows race condition — use `Path.replace()` | `ofs/utils/filesystem/atomic_write.py:40-43` | **CRITICAL** |
| 2 | `save_commit()` bypasses `atomic_write()`, fails on Windows | `ofs/core/commits/save.py:30-32` | **HIGH** |
| 3 | Circular import: core → commands layer | `ofs/core/commits/create.py:85` | **HIGH** |
| 4 | Global `_commit_cache` — cross-test contamination risk | `ofs/core/commits/load.py:13` | **MEDIUM** |

## Optimization Opportunities

| # | Optimization | Impact | Risk |
|---|-------------|--------|------|
| 1 | Parent-chain tree traversal | O(D×F) vs O(C×F) | Low |
| 2 | Pre-compiled ignore patterns | ~10× faster matching | Low |
| 3 | Batch index writes | 1 write vs N writes for `add .` | Low |
| 4 | `retrieve_unchecked()` for trusted reads | Skip SHA-256 on every read | Low |
| 5 | Remove `os.environ["NO_COLOR"]` mutation | Eliminates side effect | None |

## Architecture Violations

| # | Violation | Fix |
|---|----------|-----|
| 1 | `build_tree_state()` in commands layer, used by core | Move to `ofs/core/commits/tree.py` |
| 2 | `get_file_actions()` imports from commands layer | Will be fixed by moving `build_tree_state` |

