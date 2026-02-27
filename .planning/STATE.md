# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-27)

**Core value:** Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users
**Current focus:** Phase 1 — Packaging Foundation

## Current Position

Phase: 1 of 5 (Packaging Foundation)
Plan: 2 of 2 in current phase
Status: Phase 1 complete
Last activity: 2026-02-27 — Completed 01-02: uv.lock verification + wheel build + test suite validation

Progress: [██░░░░░░░░] 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 11m 6s
- Total execution time: 22m 12s

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 1 | 2 | 22m 12s | 11m 6s |

**Recent Trend:**
- Last 5 plans: 01-01 (16m 12s), 01-02 (6m)
- Trend: Faster (verification-only plan)

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
- [01-02]: 3 test_file.py failures are pre-existing (cgi.FieldStorage filename=None not fieldstorage-like in depot 0.11.0) — not caused by packaging changes

### Pending Todos

None.

### Blockers/Concerns

- [Phase 2]: nh3 attribute allowlist implementation needs design at implementation time — write characterization tests first
- [Phase 3]: Pyramid 1.x compatibility with Python 3.12/3.13 is uncertain — CI matrix may surface pin issues
- [Phase 2]: setuptools<79 pin must be lifted when pkg_resources usage replaced with importlib.resources
- [Phase 2]: 3 pre-existing test_file.py failures (depot/cgi FieldStorage filename=None issue) need fixing

## Session Continuity

Last session: 2026-02-27T16:30:00Z
Stopped at: Completed 01-02-PLAN.md — uv.lock verification, wheel build, asset inspection, test suite
Resume file: None
