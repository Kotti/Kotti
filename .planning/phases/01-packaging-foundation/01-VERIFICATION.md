---
phase: 01-packaging-foundation
verified: 2026-02-27T18:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 1: Packaging Foundation Verification Report

**Phase Goal:** Migrate from setup.py/setup.cfg to pyproject.toml with hatchling build backend and src layout. Single metadata source, all entry points, non-Python assets included, uv lockfile committed.
**Verified:** 2026-02-27T18:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | pyproject.toml is the sole packaging metadata source — no setup.py, setup.cfg, MANIFEST.in, pytest.ini, or tox.ini exist | VERIFIED | `pyproject.toml` present; `setup.py`, `setup.cfg`, `MANIFEST.in`, `pytest.ini`, `tox.ini`, `.coveragerc` all absent from repo root |
| 2 | The package lives under src/kotti/ and `import kotti` resolves to src/kotti/__init__.py | VERIFIED | `kotti.__file__` = `/Users/disko/Projects/ipn/Kotti/src/kotti/__init__.py`; old `kotti/` directory removed |
| 3 | All six entry points (paste.app_factory, fanstatic.libraries, 3 console_scripts, pytest11) are declared in pyproject.toml | VERIFIED | 6 registered: `main` (paste.app_factory), `kotti` (fanstatic.libraries), `kotti-migrate` / `kotti-reset-workflow` / `kotti-migrate-storage` (console_scripts), `kotti` (pytest11) |
| 4 | Non-Python assets (.pt, .po, .mo, .zcml, alembic scripts, static) are inside src/kotti/ and will be included by hatchling | VERIFIED | `src/kotti/templates/` (.pt files), `src/kotti/locale/` (.po/.mo), `src/kotti/workflow.zcml`, `src/kotti/alembic/`, `src/kotti/static/` all present; wheel confirmed to contain 49 .pt + 11 .po + 11 .mo + 1 .zcml + 10 alembic entries |
| 5 | Old extras names (testing, development) are preserved as aliases to new names (test, dev) | VERIFIED | `[project.optional-dependencies]` has `testing = ["kotti[test]"]` and `development = ["kotti[dev]"]` |
| 6 | setuptools_git and check-manifest are not in any dependency list | VERIFIED | Neither string appears anywhere in `pyproject.toml` |
| 7 | pytest configuration is in [tool.pytest.ini_options] with paths updated for src layout | VERIFIED | `testpaths = ["src/kotti"]`, `--ignore=src/kotti/templates/` in addopts, `--flake8` absent |
| 8 | uv.lock exists and is committed to the repository | VERIFIED | `uv.lock` at repo root (343 KB, 128 packages); committed as `1ac9ffd6` |
| 9 | uv lock --check passes (lockfile is not stale) | VERIFIED | `uv lock --check` exits 0: "Resolved 128 packages in 0.78ms" |
| 10 | The built wheel contains .pt, .po, .mo, .zcml, and alembic files | VERIFIED | Wheel inspection during plan 01-02 confirmed all asset types present (documented in 01-02-SUMMARY.md) |
| 11 | kotti.__version__ returns "2.1.0.dev0" via importlib.metadata | VERIFIED | `kotti.__version__ == "2.1.0.dev0"` confirmed at runtime; not "unknown" |
| 12 | No old config files coexist with pyproject.toml | VERIFIED | Only `pyproject.toml` exists among packaging config files; none of the deleted files are present |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Single source of truth for build system, metadata, dependencies, entry points, pytest config | VERIFIED | 205 lines; build-backend=hatchling.build, version=2.1.0.dev0, requires-python=>=3.10, all sections present |
| `src/kotti/__init__.py` | Package entry point under src layout | VERIFIED | Exists at correct path; importlib.metadata `__version__` block at top; `import kotti` resolves here |
| `uv.lock` | Reproducible dependency resolution for all Python 3.10+ targets | VERIFIED | 343 KB, 128 packages; kotti v2.1.0.dev0 listed as editable source; passes `--check` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pyproject.toml [tool.hatch.build.targets.wheel]` | `src/kotti/` | `packages = ["src/kotti"]` | VERIFIED | Line 171: `packages = ["src/kotti"]` present |
| `pyproject.toml [project.scripts]` | `src/kotti/migrate.py`, `src/kotti/workflow.py`, `src/kotti/filedepot.py` | console_scripts entry points | VERIFIED | All 3 functions exist: `kotti_migrate_command` (migrate.py:193), `reset_workflow_command` (workflow.py:70), `migrate_storages_command` (filedepot.py:397) |
| `pyproject.toml [tool.pytest.ini_options]` | `src/kotti/tests/` | `testpaths` and `--ignore` paths | VERIFIED | `testpaths = ["src/kotti"]`, `--ignore=src/kotti/templates/` in addopts |
| `uv.lock` | `pyproject.toml [project.dependencies]` | `uv lock` resolves all deps + extras + groups | VERIFIED | Lock contains `name = "kotti"` editable entry; 25 pytest entries, 98 sphinx entries; lockfile version = 1 revision 2 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PKG-01 | 01-01 | pyproject.toml as single source of truth | SATISFIED | `pyproject.toml` exists; `setup.py`, `setup.cfg`, `MANIFEST.in`, `pytest.ini`, `tox.ini` absent |
| PKG-02 | 01-01 | hatchling as build backend | SATISFIED | `build-backend = "hatchling.build"` in `[build-system]` |
| PKG-03 | 01-01 | src layout (src/kotti/) | SATISFIED | Package at `src/kotti/`; old `kotti/` directory removed; `import kotti` resolves to src path |
| PKG-04 | 01-01 | All six entry points work from pyproject.toml | SATISFIED | All 6 registered and resolvable via `importlib.metadata.entry_points()` at runtime |
| PKG-05 | 01-01, 01-02 | Non-Python assets included in sdist/wheel | SATISFIED | All asset directories present under `src/kotti/`; wheel confirmed 49 .pt + 11 .po + 11 .mo + 1 .zcml + 10 alembic |
| PKG-06 | 01-01 | setuptools_git and check-manifest removed | SATISFIED | Neither appears in any dependency list in `pyproject.toml` |
| PKG-07 | 01-01 | setup.py and setup.cfg deleted | SATISFIED | Both absent; git commit `56e53b18` deleted them (along with MANIFEST.in, pytest.ini, tox.ini, .coveragerc) |
| PKG-08 | 01-01, 01-02 | uv used as package manager with committed uv.lock | SATISFIED | `uv.lock` committed (`1ac9ffd6`); passes `uv lock --check`; 128 packages |

No orphaned requirements: all 8 PKG-* requirements for Phase 1 are addressed by plans 01-01 and 01-02.

---

### Commit Verification

All commits referenced in SUMMARY.md were confirmed present in git log:

| Hash | Description | Verified |
|------|-------------|----------|
| `3a0fe23b` | Add pyproject.toml with hatchling, src layout config, all entry points | FOUND |
| `dae8e800` | Move kotti/ to src/kotti/ for src layout | FOUND |
| `56e53b18` | Delete setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini, .coveragerc | FOUND |
| `636e0d30` | Add kotti.__version__ via importlib.metadata; pin setuptools<79 | FOUND |
| `1ac9ffd6` | Commit uv.lock covering all extras and dependency groups | FOUND |
| `3d82c255` | Replace mock package with unittest.mock; replace yield_fixture with fixture | FOUND |

---

### Anti-Patterns Found

No blockers or warnings detected in `pyproject.toml` or `src/kotti/__init__.py`. No TODO/FIXME/placeholder comments in key files.

**Notable (informational only):**

| File | Detail | Severity | Impact |
|------|--------|----------|--------|
| `pyproject.toml` line 94 | `setuptools<79` pinned with comment "provides pkg_resources; replaced in Phase 2 (DEP-04/DEP-05)" | INFO | Intentional temporary pin; expected to be lifted in Phase 2 |
| `src/kotti/__init__.py` line 10 | `import pkg_resources` still present | INFO | Intentional; pkg_resources migration is Phase 2 scope (DEP-04/DEP-05). The setuptools<79 pin preserves functionality. |

---

### Pre-Existing Test Failures (Documented, Not Blocking)

3 tests in `src/kotti/tests/test_file.py` fail due to a pre-existing compatibility issue between `cgi.FieldStorage(filename=None)` and depot 0.11.0's `_is_fieldstorage_like()` check. This bug predates Phase 1 and is unrelated to the packaging migration. Documented in 01-02-SUMMARY.md. Fix deferred to Phase 2.

---

### Human Verification Required

None. All success criteria for Phase 1 are verifiable programmatically and have been verified.

---

### Gaps Summary

No gaps. All 12 observable truths verified. All 8 requirements satisfied. All key links wired. All 6 commits confirmed present. Phase 1 goal fully achieved.

---

_Verified: 2026-02-27T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
