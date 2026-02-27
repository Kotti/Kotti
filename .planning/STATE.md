# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-27)

**Core value:** Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users
**Current focus:** Phase 1 — Packaging Foundation

## Current Position

Phase: 1 of 5 (Packaging Foundation)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-02-27 — Roadmap created, all 39 requirements mapped across 5 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
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

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 2]: nh3 attribute allowlist implementation needs design at implementation time — write characterization tests first
- [Phase 3]: Pyramid 1.x compatibility with Python 3.12/3.13 is uncertain — CI matrix may surface pin issues

## Session Continuity

Last session: 2026-02-27
Stopped at: Roadmap created, STATE.md initialized, REQUIREMENTS.md traceability updated
Resume file: None
