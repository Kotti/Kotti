---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in-progress
last_updated: "2026-02-27T17:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 10
  completed_plans: 3
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-27)

**Core value:** Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users
**Current focus:** Phase 2 — Runtime Dependency Updates

## Current Position

Phase: 2 of 5 (Runtime Dependency Updates)
Plan: 1 of 3 in current phase
Status: Phase 2, Plan 1 complete
Last activity: 2026-02-27 — Completed 02-01: bleach characterization tests + pkg_resources migration to importlib

Progress: [███░░░░░░░] 30%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: ~10m
- Total execution time: ~37m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 1 | 2 | 22m 12s | 11m 6s |
| Phase 2 | 1 (of 3) | ~15m | ~15m |

**Recent Trend:**
- Last 5 plans: 01-01 (16m 12s), 01-02 (6m), 02-01 (~15m)
- Trend: Stable

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
- [02-01]: Bleach normalizes CSS trailing semicolons — 'color: red' becomes 'color: red;' in output
- [02-01]: <marquee> IS in generally_xss_safe (bleach_allowlist) — xss_protection preserves it (plan comment was wrong)
- [02-01]: importlib.resources.files() returns real path for hatchling builds — no as_file() context manager needed
- [02-01]: get_version() simplified to return __version__ directly — already set via importlib.metadata at top of __init__.py

### Pending Todos

None.

### Blockers/Concerns

- [Phase 2]: nh3 attribute allowlist implementation needs design at implementation time — characterization tests now ready
- [Phase 3]: Pyramid 1.x compatibility with Python 3.12/3.13 is uncertain — CI matrix may surface pin issues
- [Phase 2]: setuptools<79 pin must be lifted in Plan 02-02 when bleach is swapped for nh3 (atomic lockfile update)
- [Phase 2]: 3 pre-existing test_file.py failures (depot/cgi FieldStorage filename=None issue) need fixing

## Session Continuity

Last session: 2026-02-27T17:00:00Z
Stopped at: Completed 02-01-PLAN.md — bleach characterization tests + pkg_resources migration to importlib
Resume file: None
