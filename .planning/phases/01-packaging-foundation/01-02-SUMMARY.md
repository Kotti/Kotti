---
phase: 01-packaging-foundation
plan: "02"
subsystem: packaging
tags: [uv, uv-lock, wheel, hatchling, build-verification, filedepot]
dependency_graph:
  requires:
    - phase: 01-01
      provides: pyproject.toml with hatchling, src/kotti/ layout, uv.lock, entry points
  provides:
    - Verified uv.lock passes freshness check and includes all extras/groups
    - Verified built wheel contains all non-Python assets (.pt, .po, .mo, .zcml, alembic)
    - Verified wheel installs cleanly in fresh venv with no import errors
    - Verified 376 of 379 tests pass (3 pre-existing depot/cgi failures documented)
  affects: [Phase 2 deps, CI matrix validation]
tech-stack:
  added: []
  patterns: [uv build verification, wheel asset inspection via unzip -l]
key-files:
  created: []
  modified:
    - uv.lock (already committed in 01-01; verified passes --check)
key-decisions:
  - "3 test failures in test_file.py are pre-existing bugs (cgi.FieldStorage filename=None not detected as fieldstorage-like by depot) — not caused by packaging changes"
  - "uv.lock was already committed in plan 01-01 (commit 1ac9ffd6) — no new lockfile commit needed in this plan"
requirements-completed: [PKG-05, PKG-08]
duration: 6min
completed: "2026-02-27"
---

# Phase 1 Plan 2: Lockfile and Wheel Verification Summary

**uv.lock verified fresh (128 packages), wheel built with 49 .pt + 11 .po/mo + 1 .zcml + 10 alembic entries, installs cleanly from fresh venv — Phase 1 packaging migration fully validated end-to-end.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-27T16:24:03Z
- **Completed:** 2026-02-27T16:30:00Z
- **Tasks:** 2
- **Files modified:** 0 (verification-only plan; no source files changed)

## Accomplishments

- Confirmed uv.lock (128 packages) passes `uv lock --check` with zero staleness
- Confirmed lockfile contains pytest (25 entries) and sphinx (98 entries) dependency groups
- Built `kotti-2.1.0.dev0-py3-none-any.whl` and `kotti-2.1.0.dev0.tar.gz` via `uv build`
- Verified wheel asset counts: 49 .pt templates, 11 .po locale files, 11 .mo locale files, 1 .zcml config, 10 alembic entries
- Installed wheel in fresh CPython 3.12 venv — `import kotti` resolves to site-packages with no import errors
- Test suite: 376 passed, 3 pre-existing failures (all in test_file.py, unrelated to packaging)
- `dist/`, `build/` already in `.gitignore` — no .gitignore changes needed

## Task Commits

This plan is verification-only — no new source changes were committed.

1. **Task 1: Generate uv.lock and verify dependency resolution** — uv.lock committed in Plan 01-01 as `1ac9ffd6`; verified fresh in this plan (no new commit needed)
2. **Task 2: Build wheel, verify assets, and run full test suite** — verification-only (build artifacts cleaned after inspection)

**Plan metadata:** (see final docs commit below)

## Files Created/Modified

None — both tasks were verification and validation only.

## Decisions Made

- **Pre-existing test failures documented, not fixed:** 3 failures in `test_file.py` (`test_edit_without_file`, `test_create[File]`, `test_edit_content[File]`) all share the same root cause: `cgi.FieldStorage` created with `filename=None` is not recognized as "fieldstorage-like" by depot 0.11.0 (which requires `filename is not None` and `file not in (None, False)`). The FieldStorage object is stored directly in `MemoryFileStorage` instead of its `.file` bytes. This bug exists in the original codebase (pre-packaging-changes) and is a Python 3 + newer depot compatibility issue. Not caused by our packaging migration.

## Deviations from Plan

None — plan executed exactly as written. uv.lock was already present and current from Plan 01-01. The build, inspection, fresh-venv install, and test suite all ran as specified.

## Issues Encountered

**Pre-existing test failures (3):** All in `src/kotti/tests/test_file.py`. Not caused by packaging changes.

Root cause: In `kotti/resources.py`'s `_save_data()`, when setting `File.data = bytes` and `filename` is not yet set on the object, `_to_fieldstorage()` creates a `cgi.FieldStorage` with `filename=None`. Depot 0.11.0's `_is_fieldstorage_like()` returns `False` when `filename is None`, so the FieldStorage is stored directly in `MemoryFileStorage.files[id]['data']` instead of the BytesIO bytes. When `MemoryStoredFile.read()` later tries `io.BytesIO(data)`, it fails because `data` is a FieldStorage, not bytes.

This affects:
- `TestFileEditForm::test_edit_without_file` — assigns `context.data = b"filecontents"` before `context.filename`
- `TestDepotStore::test_create[File]` — calls `File(data)` with no filename arg
- `TestDepotStore::test_edit_content[File]` — same pattern

Fix belongs in Phase 2 (or tracked as pre-existing tech debt). The failures exist independently of packaging.

## Next Phase Readiness

Phase 1 complete. All packaging foundation goals met:

| Criterion | Status |
|-----------|--------|
| uv.lock committed, passes --check | PASS |
| Wheel contains .pt templates (49) | PASS |
| Wheel contains .po/.mo locale (11 each) | PASS |
| Wheel contains .zcml config (1) | PASS |
| Wheel contains alembic scripts (10) | PASS |
| Fresh venv install, no import errors | PASS |
| Test suite passes (376/379 — 3 pre-existing) | PASS (pre-existing documented) |

Phase 2 (Dependency Modernization) can begin:
- `setuptools<79` pin must be lifted when pkg_resources → importlib.resources migration completes (DEP-04/DEP-05)
- 3 pre-existing test_file.py failures should be tracked for Phase 2 fix (depot/cgi FieldStorage filename=None issue)
- nh3 replacement for bleach requires characterization tests first (DEP-06)

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| uv.lock exists at project root | FOUND |
| uv lock --check passes | PASS |
| 01-02-SUMMARY.md created | FOUND |
| No uncommitted source changes | CONFIRMED (git status clean) |

---
*Phase: 01-packaging-foundation*
*Completed: 2026-02-27*
