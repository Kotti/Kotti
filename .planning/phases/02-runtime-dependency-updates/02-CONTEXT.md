# Phase 2: Runtime Dependency Updates - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace deprecated runtime dependencies (bleach, pkg_resources, mock) with modern equivalents while preserving behavior and maintaining plugin compatibility. Pins on pyramid<2 and sqlalchemy<2 are maintained. No new capabilities added.

</domain>

<decisions>
## Implementation Decisions

### Sanitization equivalence (bleach → nh3)
- Semantic equivalence, not exact string match — HTML must render the same in a browser, minor whitespace/quoting differences are acceptable
- Characterization tests compare parsed DOM behavior, not raw string output
- Tighten allowlists where bleach was overly broad, with deprecation warnings for anything dropped
- Characterization tests kept permanently as a regression suite (sanitization is security-critical)

### Plugin compatibility
- New API function names for sanitizers; old names get deprecation shims that forward to the new functions
- Deprecation shims live until next major Kotti version
- Deprecation warnings include migration instructions: "sanitize() is deprecated, use nh3_clean() instead. Will be removed in Kotti X.0"
- pkg_resources removal is internal to Kotti — no compatibility wrapper needed for plugins using pkg_resources directly

### Already-done overlap / cleanup scope
- Phase 1 already replaced mock→unittest.mock and pkg_resources→importlib.metadata for __version__, but Phase 2 does a thorough sweep (full grep) to confirm zero remaining occurrences before marking DEP-03/DEP-04 complete
- DEP-05 (Alembic directory discovery): use stdlib importlib.resources (Python 3.10+ target, no backport needed)
- DEP-07/DEP-08 pins verified as explicit success criterion after all changes
- Remove `mock` from pyproject.toml test dependencies if still listed

### Claude's Discretion
- How to handle nh3 gaps (tags/attributes bleach allowed but nh3 can't support) — pragmatic approach based on what nh3 actually supports
- Exact new function names for the sanitizer API
- Implementation details of importlib.resources for Alembic path discovery

</decisions>

<specifics>
## Specific Ideas

- "New API with shim" approach for sanitizers — not a silent swap, but an intentional API evolution with a clean migration path
- Deprecation warnings should be actionable: include the exact replacement function name and removal version
- Belt-and-suspenders verification of pyramid/sqlalchemy pins even though Phase 2 shouldn't touch them

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-runtime-dependency-updates*
*Context gathered: 2026-02-27*
