---
phase: 02-runtime-dependency-updates
plan: 01
subsystem: testing
tags: [bleach, nh3, pkg_resources, importlib, characterization-tests, sanitizers, migration]

# Dependency graph
requires:
  - phase: 01-packaging-foundation
    provides: hatchling-based packaging, importlib.metadata __version__, dev environment with uv
provides:
  - Bleach characterization tests capturing exact output for all 3 sanitizers (baseline for nh3 migration)
  - pkg_resources fully replaced with importlib equivalents across src/kotti/ and docs/
  - get_version() using __version__ (importlib.metadata), no pkg_resources
  - KOTTI_SCRIPT_DIR resolved via importlib.resources.files(), no pkg_resources
affects: [02-02-nh3-migration, any plan touching sanitizers or migrate.py]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "importlib.resources.files('kotti') / 'alembic' for package-relative path resolution"
    - "importlib.metadata.version() for version lookup, aliased to avoid namespace collision"
    - "Characterization tests document exact library behavior as migration baseline"

key-files:
  created: []
  modified:
    - src/kotti/tests/test_sanitizers.py
    - src/kotti/__init__.py
    - src/kotti/migrate.py
    - docs/conf.py

key-decisions:
  - "Bleach normalizes CSS: 'color: red' becomes 'color: red;' (trailing semicolon) — captured in characterization test"
  - "<marquee> IS in generally_xss_safe (bleach_allowlist), so xss_protection preserves it — corrected from plan assumption"
  - "importlib.resources.files() returns real filesystem path for hatchling builds, no as_file() context manager needed"
  - "get_version() simplified to return __version__ directly — already set via importlib.metadata at module top"

patterns-established:
  - "Characterization tests: capture EXACT library behavior before migration, update for new library in next plan"
  - "importlib.resources.files(pkg) / subdir for package data paths (replaces pkg_resources.resource_filename)"

requirements-completed: [DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07, DEP-08]

# Metrics
duration: 15min
completed: 2026-02-27
---

# Phase 02 Plan 01: Bleach Characterization Tests and pkg_resources Migration Summary

**Bleach sanitizer characterization tests added as nh3 migration baseline, and pkg_resources fully eliminated from src/kotti/ and docs/ via importlib equivalents**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-27
- **Completed:** 2026-02-27
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added 3 bleach characterization tests capturing exact output for xss_protection, minimal_html, and no_html sanitizers — these become the "before" snapshot for the nh3 migration in Plan 02-02
- Replaced all pkg_resources usage in `__init__.py`, `migrate.py`, and `docs/conf.py` with importlib equivalents — zero pkg_resources imports remain in src/kotti/ or docs/
- Verified: no PyPI mock imports (`from mock import` / `import mock`) in source; pyramid>=1.9,<2 and sqlalchemy>=1.4.16,<2 pins confirmed in pyproject.toml

## Task Commits

Each task was committed atomically:

1. **Task 1: Bleach characterization tests and mock/pin verification** - `f0951583` (feat)
2. **Task 2: Replace pkg_resources with importlib in __init__.py, migrate.py, docs/conf.py** - `bbe7e85c` (feat)

## Files Created/Modified

- `src/kotti/tests/test_sanitizers.py` - Added 3 characterization tests capturing exact bleach behavior (xss_protection, minimal_html, no_html)
- `src/kotti/__init__.py` - Removed pkg_resources import; get_version() now returns __version__ directly
- `src/kotti/migrate.py` - Replaced pkg_resources with importlib.resources; KOTTI_SCRIPT_DIR uses importlib_resources.files("kotti") / "alembic"
- `docs/conf.py` - Replaced pkg_resources with importlib.metadata.version() aliased as _pkg_version

## Decisions Made

- Bleach normalizes CSS trailing semicolons: the input `style="color: red"` produces `style="color: red;"` in output — test captures actual behavior, not the input
- `<marquee>` IS in `generally_xss_safe` (bleach_allowlist), so xss_protection preserves it — the plan comment assumed it would be stripped, but actual behavior is to preserve it; test was corrected to match actual bleach output
- `importlib.resources.files("kotti") / "alembic"` returns a real filesystem path for hatchling wheel builds, so `str()` cast suffices — no `as_file()` context manager needed
- `get_version()` simplified to `return __version__` since `__version__` is already set via `importlib.metadata.version("Kotti")` at module top

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected characterization test assertions to match actual bleach output**
- **Found during:** Task 1 (characterization test execution)
- **Issue:** Plan specified `style="color: red"` and `<marquee> not in sanitized` — but actual bleach output adds trailing semicolon to CSS (`color: red;`) and preserves `<marquee>` (it is in generally_xss_safe)
- **Fix:** Updated test assertions to reflect actual bleach behavior: `'style="color: red;"'` and `assert "<marquee>" in sanitized`
- **Files modified:** src/kotti/tests/test_sanitizers.py
- **Verification:** All 10 sanitizer tests pass after correction
- **Committed in:** f0951583 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — behavior mismatch in plan's expected output)
**Impact on plan:** Necessary correction — characterization tests must capture what bleach ACTUALLY does, not what the plan assumed it would do.

## Issues Encountered

None beyond the test assertion corrections documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-02 (nh3 migration) can now proceed: characterization tests provide the "before" baseline
- pkg_resources fully eliminated — setuptools<79 pin can be lifted in Plan 02-02 when bleach is replaced with nh3 (keeping the lockfile update atomic)
- All 16 tests pass (10 sanitizer + 6 migrate) with importlib replacements

---
*Phase: 02-runtime-dependency-updates*
*Completed: 2026-02-27*
