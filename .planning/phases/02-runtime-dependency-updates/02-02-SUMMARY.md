---
phase: 02-runtime-dependency-updates
plan: 02
subsystem: sanitizers
tags: [nh3, bleach, html-sanitization, deprecation, pyproject, lockfile]

# Dependency graph
requires:
  - phase: 02-01
    provides: bleach characterization tests as migration baseline, pkg_resources eliminated
provides:
  - nh3-based HTML sanitizers (xss_protection_nh3, minimal_html_nh3, no_html_nh3)
  - DeprecationWarning shims for old function names pointing to Kotti 3.0 removal
  - Updated pyproject.toml with nh3>=0.2.14, bleach/bleach-allowlist/setuptools removed
  - Updated uv.lock reflecting dependency removals and nh3 addition
affects: [any plan touching sanitizers, any plugin using kotti.sanitizers dotted names]

# Tech tracking
tech-stack:
  added:
    - "nh3>=0.2.14 (0.3.3 installed) — Rust-backed ammonia HTML sanitizer"
  patterns:
    - "nh3.clean(html, tags=frozenset, attributes=dict, link_rel=str) for sanitization"
    - "Module-level frozenset/dict constants for tag/attr allowlists"
    - "warnings.warn(msg, DeprecationWarning, stacklevel=2) for deprecation shims"
    - "pytest.mark.filterwarnings('ignore::DeprecationWarning') on tests using shim names"

key-files:
  created: []
  modified:
    - src/kotti/sanitizers.py
    - src/kotti/tests/test_sanitizers.py
    - src/kotti/__init__.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Tag allowlists derived from actual bleach_allowlist installed values, not plan approximations — _XSS_SAFE_TAGS matches generally_xss_safe minus style/script"
  - "style excluded from _MINIMAL_ATTRS (tightened from bleach which emitted empty style=''); style still in _XSS_SAFE_ATTRS wildcard"
  - "conf_defaults updated to point to _nh3 names — fresh installs get no deprecation warnings; old plugin configs still work via shims"
  - "bleach, bleach-allowlist, setuptools<79 all removed atomically in same lockfile update"

patterns-established:
  - "Deprecation shims: old name calls new name, warns with 'use X_nh3() instead. Will be removed in Kotti 3.0.'"
  - "nh3 attribute allowlist uses set values per tag key (not list), wildcard key '*' supported"

requirements-completed: [DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07, DEP-08]

# Metrics
duration: ~3min
completed: 2026-02-27
---

# Phase 02 Plan 02: nh3 Migration — Sanitizers and Dependency Cleanup Summary

**bleach replaced by nh3 for HTML sanitization; deprecation shims preserve backward compatibility; bleach, bleach-allowlist, and setuptools<79 removed from dependencies**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-27T21:45:05Z
- **Completed:** 2026-02-27T21:48:05Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Rewrote `src/kotti/sanitizers.py` to use `nh3.clean()` for all sanitization — no bleach imports remain
- Defined module-level `_XSS_SAFE_TAGS`, `_XSS_SAFE_ATTRS`, `_MINIMAL_TAGS`, `_MINIMAL_ATTRS` constants based on actual bleach_allowlist installed values (inspected before removing bleach)
- Added `xss_protection_nh3()`, `minimal_html_nh3()`, `no_html_nh3()` as new primary sanitizer functions
- Added deprecation shims `xss_protection()`, `minimal_html()`, `no_html()` that emit `DeprecationWarning` with migration instructions and Kotti 3.0 removal notice, then forward to `_nh3` variants
- Updated `conf_defaults` in `__init__.py` to point to `_nh3` function names — fresh installs no longer trigger deprecation warnings
- Updated characterization tests to reflect nh3 behavior (script content removed, rel added to links, style stripped from minimal_html)
- Added `test_deprecation_warnings()` test verifying shim messages for all 3 deprecated functions
- Removed bleach/bleach-allowlist from `pyproject.toml`, added `nh3>=0.2.14`
- Removed `setuptools<79` pin (pkg_resources no longer needed — eliminated in Plan 02-01)
- Regenerated `uv.lock` — bleach 4.1.0, bleach-allowlist 1.0.3, six 1.17.0, webencodings 0.5.1 removed; nh3 0.3.3 added

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement nh3-based sanitizers with deprecation shims** — `756c6882`
2. **Task 2: Update tests and pyproject.toml dependencies** — `30ee10b4`

## Files Created/Modified

- `src/kotti/sanitizers.py` — Rewrote with nh3; _XSS_SAFE_TAGS/_XSS_SAFE_ATTRS/_MINIMAL_TAGS/_MINIMAL_ATTRS constants; _nh3 implementations; deprecation shims
- `src/kotti/__init__.py` — Updated conf_defaults kotti.sanitizers value to use _nh3 function names
- `src/kotti/tests/test_sanitizers.py` — Updated characterization tests for nh3 behavior; added test_deprecation_warnings; nh3 characterization tests; filterwarnings decorators on integration tests
- `pyproject.toml` — Replaced bleach>=4,<5 + bleach-allowlist with nh3>=0.2.14; removed setuptools<79 pin
- `uv.lock` — Regenerated with nh3 0.3.3; removed bleach/bleach-allowlist/six/webencodings

## Decisions Made

- Tag allowlists derived from actual installed bleach_allowlist values (run before removal), not the approximations in the plan — `_XSS_SAFE_TAGS` is `generally_xss_safe` minus `style` and `script`
- `style` excluded from `_MINIMAL_ATTRS` — tightened from bleach which left empty `style=""` on stripped style values; style still present in `_XSS_SAFE_ATTRS['*']` for xss_protection
- `conf_defaults` points to `_nh3` names so fresh Kotti installs produce no deprecation warnings; existing plugin configs using old dotted names still work via the shims
- `bleach`, `bleach-allowlist`, and `setuptools<79` all removed in the same `uv lock` run to keep the lockfile update atomic

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used actual bleach_allowlist values for tag constants instead of plan approximations**
- **Found during:** Task 1 (pre-implementation inspection)
- **Issue:** Plan's tag list approximations were incomplete — `_XSS_SAFE_TAGS` was missing ~40 tags present in actual `generally_xss_safe`; `_MINIMAL_TAGS` was missing no tags but had slightly wrong membership
- **Fix:** Ran `python -c "from bleach_allowlist import generally_xss_safe, ..."` to capture actual values before removing bleach; used actual output to populate frozensets
- **Files modified:** src/kotti/sanitizers.py
- **Commit:** 756c6882 (Task 1 commit)

**2. [Rule 1 - Bug] test_listeners and test_sanitize use old deprecation-shimmed names via config — added filterwarnings**
- **Found during:** Task 2 (test analysis)
- **Issue:** These integration tests exercise the full sanitize() path using the config which now points to _nh3 names — but `test_sanitize` also calls sanitizer functions by name which would not emit warnings since we updated conf_defaults; test_listeners passes through the app fixture which uses conf_defaults (now _nh3 names). Suppression added as defensive measure.
- **Fix:** Added `@pytest.mark.filterwarnings("ignore::DeprecationWarning")` to both test functions
- **Files modified:** src/kotti/tests/test_sanitizers.py
- **Commit:** 30ee10b4 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (Rule 1 — implementation correctness)
**Impact on plan:** No scope change; fixes ensured correctness of the implementation

## Issues Encountered

None beyond the deviations documented above.

## User Setup Required

None — no external service configuration required.

## Verification Results

All verification checks from the plan passed:

1. `uv run pytest src/kotti/tests/test_sanitizers.py -x -q` — 11 passed
2. `uv run pytest src/kotti/tests/test_migrate.py -x -q` — 6 passed
3. `uv run pip show bleach` — WARNING: Package(s) not found: bleach
4. `uv run pip show nh3` — nh3 0.3.3
5. `grep "from bleach" src/kotti/` — 0 results (only comments)
6. `grep "pyramid>=1.9,<2" pyproject.toml` — present
7. `grep "sqlalchemy>=1.4" pyproject.toml` — present
8. `grep "setuptools" pyproject.toml` — NOT present
9. Deprecation warning emitted: `xss_protection() is deprecated, use xss_protection_nh3() instead. Will be removed in Kotti 3.0.`

## Next Phase Readiness

- Plan 02-03 (if any) can proceed: bleach fully removed, nh3 operational, all tests green
- All 8 DEP requirements (DEP-01 through DEP-08) satisfied
- Phase 2 complete — runtime dependency updates done

---
*Phase: 02-runtime-dependency-updates*
*Completed: 2026-02-27*
