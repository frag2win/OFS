# Phase 7: Testing & Quality — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-02-22  
**Status:** ✅ Complete  

---

## 1. Objective

Establish a comprehensive testing foundation for OFS before documentation and packaging phases. Measure performance baselines, validate failure handling, increase coverage to ≥92%, and confirm cross-platform correctness — without introducing any new features.

---

## 2. Scope

| Area | In Scope | Out of Scope |
|------|----------|-------------|
| Performance | Benchmark harness (measure & report) | Hard timing assertions |
| Reliability | Deterministic corruption/failure tests | SIGKILL / power-loss simulation |
| Coverage | Edge-case tests to push 87% → 92% | Artificial 95%+ coverage |
| Cross-platform | Path, EOL, case sensitivity tests | Multi-OS CI execution |

---

## 3. Deliverables

### P7.3 — Performance Benchmark Harness

**File:** `tests/performance/test_benchmarks.py`  
**Run with:** `pytest tests/performance/ -s --no-header`

| Scenario | Setup | What Is Measured |
|----------|-------|-----------------|
| Add 100 files | 1KB each | Wall-clock time for `ofs add .` |
| Add 1000 files | 1KB each | Wall-clock time for `ofs add .` |
| Commit 1000 files | Pre-staged | Wall-clock time for `ofs commit` |
| Checkout 1000 files | From latest commit | Wall-clock time for `ofs checkout` |
| Verify ~1000 objects | Full repo | Wall-clock time for `ofs verify` |
| Diff 500 changed files | Modified working tree | Wall-clock time for `ofs diff` |

**Design decisions:**
- No hard timing thresholds — performance varies across machines
- Reports files/sec where applicable
- Uses `time.perf_counter()` for precision
- Each test creates an isolated repo via `tmp_path`

---

### P7.4 — Chaos / Reliability Tests

**File:** `tests/chaos/test_chaos.py`  
**Tests:** 15

| Category | Tests | What Is Validated |
|----------|-------|------------------|
| Corrupted Objects | 3 | Flipped bytes, empty files, deleted objects → `verify` detects |
| Corrupted Commits | 3 | Deleted JSON, malformed JSON, bad file hash → `verify` detects |
| Broken Refs | 2 | HEAD → nonexistent commit, empty HEAD → graceful handling |
| Missing Parents | 2 | Deleted middle/root commit → `build_tree_state` doesn't crash |
| Corrupted Index | 3 | Bad JSON, missing file, stale hash → handled gracefully |
| Disk-Full Simulation | 2 | Monkeypatched `store()`/`write_text()` → commands return error, don't crash |

---

### P7.1 — Coverage Boost (87% → 92%)

**Files:**
- `tests/unit/test_coverage_boost.py` (27 tests)
- `tests/unit/test_coverage_boost_2.py` (9 tests)

**Coverage gaps closed:**

| Module | Before | After | Tests Added |
|--------|--------|-------|-------------|
| `commands/verify/execute.py` | 67% | 97% | Healthy repo, verbose mode, not-a-repo, corruption |
| `commands/diff/execute.py` | 57% | 77% | Cached, commit-to-commit, working-vs-commit, nonexistent |
| `commands/log/execute.py` | 86% | 97% | Empty repo, not-a-repo, oneline, limit |
| `core/index/manager.py` | 87% | 95% | `batch_add()`, replace existing, persistence |
| `commands/commit/execute.py` | 78% | 85% | Not-a-repo, unchanged files |
| `commands/checkout/execute.py` | 83% | 88% | Not-a-repo, nonexistent commit, force, cancelled, corrupted hash, write failure |

---

### P7.5 — Cross-Platform Guards

**File:** `tests/unit/utils/test_cross_platform.py`  
**Tests:** 15 (14 passed, 1 skipped on Windows)

| Category | Tests | What Is Validated |
|----------|-------|------------------|
| Path Normalization | 4 | Forward/back slashes, dot paths, stored paths use `/` |
| Line Endings | 3 | LF ≠ CRLF hashes, binary roundtrip, `write_bytes` preserves |
| Case Sensitivity | 2 | OS-aware file case handling, hash independence from filename |
| Ignore Patterns | 6 | Forward slash, compiled, negation, recursive `**`, `.ofsignore` loading |

---

## 4. Bugs Discovered & Fixed

### Bug 1: `_diff_working_vs_commit` — wrong argument type
- **Location:** `ofs/commands/diff/execute.py:234`
- **Root cause:** Passed `repo` (Repository object) instead of `None` to `scan_working_tree(repo_root, ignore_patterns)`
- **Impact:** `ofs diff <commit_id>` always crashed with `TypeError: 'Repository' object is not iterable`
- **Fix:** Changed to `scan_working_tree(repo_root)` — uses default pattern loading

### Bug 2: `_diff_working_vs_commit` — double path relativization
- **Location:** `ofs/commands/diff/execute.py:235`
- **Root cause:** Called `.relative_to(repo_root)` on paths already returned as relative by `scan_working_tree`
- **Impact:** `ValueError` on Windows when comparing working tree to a commit
- **Fix:** Changed to `.as_posix()` directly

---

## 5. Final Metrics

```
Tests:    413 passed, 1 skipped
Coverage: 92% (1537 statements, 122 uncovered)
Time:     9.67s (excluding benchmarks)
```

### Test Distribution

| Category | Count |
|----------|-------|
| Unit tests | 359 |
| Integration tests | 24 |
| Reliability tests | 12 |
| Chaos tests | 15 |
| Cross-platform tests | 15 |
| **Total** | **413 + 1 skipped** |

---

## 6. Constraints Honored

- ✅ No new features added
- ✅ No architecture changes
- ✅ No JSON format changes
- ✅ No new dependencies
- ✅ No concurrency introduced
- ✅ No packaging changes
- ✅ No CLI argument changes
- ✅ Benchmarks measure only, no hard assertions
- ✅ Chaos tests are deterministic (no real process kills)
- ✅ Cross-platform tests run on single OS

---

## 7. How to Run

```bash
# All tests (fast)
pytest -q

# With coverage
pytest --cov=ofs --cov-report=term-missing

# Benchmarks only (slow, ~60s)
pytest tests/performance/ -s --no-header

# Chaos tests only
pytest tests/chaos/ -q

# Cross-platform tests only
pytest tests/unit/utils/test_cross_platform.py -q
```
