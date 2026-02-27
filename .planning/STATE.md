# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-27)

**Core value:** Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users
**Current focus:** Phase 1 — Packaging Foundation

## Current Position

Phase: 1 of 5 (Packaging Foundation)
Plan: 1 of ? in current phase
Status: In progress
Last activity: 2026-02-27 — Completed 01-01: pyproject.toml + src layout + uv.lock

Progress: [█░░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 16m 12s
- Total execution time: 16m 12s

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 1 | 1 | 16m 12s | 16m 12s |

**Recent Trend:**
- Last 5 plans: 01-01 (16m 12s)
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Phase ordering is strict — packaging first, then deps, then CI, then code quality, then docs
- [Roadmap]: bleach→nh3 requires characterization tests before switching (not drop-in)
- [Roadmap]: pkg_resources→importlib must be verified via kotti-migrate CLI (not just pytest)
- [Roadmap]: Formatting must land as isolated first commit in Phase 4 (preserves git blame)
- [Roadmap]: Documentation migrating to MkDocs + Material for MkDocs (not updating Sphinx)
- [Roadmap]: pyramid>=1.9,<2 and sqlalchemy>=1.4,<2 pins maintained throughout this milestone
- [01-01]: hatchling license field requires dict form `{text = "..."}` not bare string
- [01-01]: setuptools<79 pinned as dependency to preserve pkg_resources until Phase 2 (DEP-04/DEP-05)
- [01-01]: mock -> unittest.mock completed in Phase 1 (removed from test deps, imports updated)
- [01-01]: yield_fixture -> fixture replacement completed (pytest 4.0 compatibility)

### Pending Todos

None.

### Blockers/Concerns

- [Phase 2]: nh3 attribute allowlist implementation needs design at implementation time — write characterization tests first
- [Phase 3]: Pyramid 1.x compatibility with Python 3.12/3.13 is uncertain — CI matrix may surface pin issues
- [Phase 2]: setuptools<79 pin must be lifted when pkg_resources usage replaced with importlib.resources

## Session Continuity

Last session: 2026-02-27T16:21:02Z
Stopped at: Completed 01-01-PLAN.md — pyproject.toml migration, src layout, uv.lock
Resume file: None
