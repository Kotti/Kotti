---
phase: "01"
plan: "01"
subsystem: packaging
tags: [pyproject-toml, hatchling, src-layout, packaging, uv]
dependency_graph:
  requires: []
  provides: [pyproject-toml, src-layout, uv-lock, entry-points]
  affects: [all-subsequent-phases]
tech_stack:
  added: [hatchling, uv.lock]
  patterns: [src-layout, single-source-of-truth pyproject.toml, PEP 735 dependency-groups]
key_files:
  created:
    - pyproject.toml
    - uv.lock
    - src/kotti/ (moved from kotti/)
  modified:
    - src/kotti/__init__.py
    - src/kotti/tests/__init__.py
    - src/kotti/tests/test_*.py (14 files)
decisions:
  - "hatchling chosen over uv_build for non-Python asset inclusion support"
  - "setuptools<79 pinned as dependency to preserve pkg_resources until Phase 2 (DEP-04/DEP-05)"
  - "license field must use dict form: {text = '...'} not bare string"
  - "mock -> unittest.mock replacement done in Phase 1 (removed from test deps)"
  - "yield_fixture -> fixture replacement done (removed in pytest 4.0)"
metrics:
  duration: "16m 12s"
  completed: "2026-02-27"
  tasks_completed: 3
  files_changed: 24
---

# Phase 1 Plan 1: Packaging Foundation Migration Summary

**One-liner:** Single pyproject.toml with hatchling build backend, src/kotti/ layout, all 6 entry points, uv.lock — full packaging modernization from setup.py/setup.cfg/MANIFEST.in multi-file setup.

## What Was Built

Migrated Kotti from a multi-file packaging setup (setup.py + setup.cfg + MANIFEST.in + pytest.ini + tox.ini) to a single `pyproject.toml` with hatchling as build backend and src layout. The package is now installable as `pip install kotti[dev]` or `uv sync --group dev` with full reproducibility via a committed `uv.lock`.

### Key Outcomes

- `pyproject.toml` is now the sole metadata source (no setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini)
- Package lives at `src/kotti/` with file history preserved via `git mv`
- All 6 entry points declared and functional: `paste.app_factory`, `fanstatic.libraries`, 3 console scripts, `pytest11`
- `kotti.__version__` now returns `"2.1.0.dev0"` via `importlib.metadata` (backwards compatible)
- Deprecated extras aliases (`testing`, `development`) preserved for backwards compatibility
- `uv.lock` committed covering 128 packages across all extras and dependency groups
- 379 tests collect and run without import errors

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 3a0fe23b | feat | Add pyproject.toml with hatchling, src layout config, all entry points |
| dae8e800 | refactor | Move kotti/ to src/kotti/ for src layout (history preserved) |
| 56e53b18 | chore | Delete setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini, .coveragerc |
| 636e0d30 | feat | Add kotti.__version__ via importlib.metadata; pin setuptools<79 |
| 1ac9ffd6 | chore | Commit uv.lock covering all extras and dependency groups |
| 3d82c255 | fix | Replace 'mock' package with unittest.mock; replace yield_fixture with fixture |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] hatchling rejects bare string license field**
- **Found during:** Task 1 verification (uv pip install -e ".[dev]")
- **Issue:** `license = "BSD-derived (http://www.repoze.org/LICENSE.txt)"` fails hatchling validation — requires SPDX identifier or dict form
- **Fix:** Changed to `license = {text = "BSD-derived (http://www.repoze.org/LICENSE.txt)"}`
- **Files modified:** pyproject.toml
- **Commit:** 636e0d30

**2. [Rule 1 - Bug] setuptools 79+ removed pkg_resources as standalone module**
- **Found during:** Task 2 reinstall (uv pip install -e ".[dev]")`
- **Issue:** Fresh venv with setuptools>=79 has no `pkg_resources` module — Kotti's `__init__.py` does `import pkg_resources` at module load
- **Fix:** Added `setuptools<79` as an explicit dependency to preserve `pkg_resources` until Phase 2 (DEP-04/DEP-05) replaces it with `importlib.resources`
- **Files modified:** pyproject.toml
- **Commit:** 636e0d30
- **Note:** This pin will be lifted when Phase 2 completes the pkg_resources → importlib migration

**3. [Rule 1 - Bug] 'mock' package missing from venv (removed from test deps)**
- **Found during:** Task 3 pytest collection
- **Issue:** 14 test files imported `from mock import ...` — the standalone `mock` package was correctly removed from test deps (use stdlib `unittest.mock`), but imports weren't updated
- **Fix:** Replaced all `from mock import X` with `from unittest.mock import X` across 14 test files; replaced `import mock` with `import unittest.mock as mock`
- **Files modified:** src/kotti/tests/__init__.py and 13 other test files
- **Commit:** 3d82c255

**4. [Rule 1 - Bug] pytest.yield_fixture removed (pytest 4.0)**
- **Found during:** Task 3 pytest collection (surfaced with pytest>=8)
- **Issue:** `from pytest import yield_fixture` and `@yield_fixture` used in `tests/__init__.py` — removed in pytest 4.0; use `@fixture` with `yield` instead
- **Fix:** Removed `from pytest import yield_fixture`; replaced all `@yield_fixture` with `@fixture` (functions already used `yield` body pattern)
- **Files modified:** src/kotti/tests/__init__.py
- **Commit:** 3d82c255

**5. [Rule 3 - Blocking] No virtual environment existed**
- **Found during:** Task 2 reinstall attempt
- **Issue:** No `.venv` in project root; `uv pip install` requires a venv or `--system` flag
- **Fix:** Created `.venv` with `uv venv` (Python 3.12.11), then installed with `uv pip install -e ".[dev]"`
- **Files modified:** .venv/ (not tracked in git)

## Verification Results

All success criteria met:

| Criterion | Status |
|-----------|--------|
| pyproject.toml sole metadata source | PASS |
| hatchling build backend | PASS |
| src/kotti/ layout with all assets | PASS |
| All 6 entry points declared and functional | PASS |
| Deprecated extra aliases preserved | PASS |
| setuptools_git and check-manifest absent | PASS |
| kotti.__version__ == "2.1.0.dev0" | PASS |
| Editable install works (import resolves to src/) | PASS |
| 379 tests collect without errors | PASS |
| uv.lock committed | PASS |

## Requirements Fulfilled

- PKG-01: pyproject.toml is single source of truth
- PKG-02: hatchling is build backend
- PKG-03: src layout in place
- PKG-04: All 6 entry points work
- PKG-05: Non-Python assets included by hatchling default
- PKG-06: setuptools_git and check-manifest removed
- PKG-07: setup.py and setup.cfg deleted
- PKG-08: uv.lock committed (128 packages)

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| pyproject.toml exists | FOUND |
| src/kotti/ directory exists | FOUND |
| uv.lock exists | FOUND |
| src/kotti/__init__.py exists | FOUND |
| 01-01-SUMMARY.md exists | FOUND |
| All 6 task commits exist | FOUND (3a0fe23b, dae8e800, 56e53b18, 636e0d30, 1ac9ffd6, 3d82c255) |
