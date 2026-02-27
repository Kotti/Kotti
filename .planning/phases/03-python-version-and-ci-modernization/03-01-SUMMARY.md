---
phase: 03-python-version-and-ci-modernization
plan: 01
subsystem: ci
tags: [ruff, github-actions, ci, dependabot, uv]
dependency_graph:
  requires: []
  provides: [ruff-lint-gate, consolidated-ci-matrix, dependabot-config]
  affects: [.github/workflows, pyproject.toml, uv.lock]
tech_stack:
  added: [ruff>=0.11]
  patterns: [uv sync --locked, uv run ruff check, matrix ci workflow]
key_files:
  created:
    - .github/workflows/ci.yml
    - .github/dependabot.yml
  modified:
    - pyproject.toml
    - uv.lock
  deleted:
    - .github/workflows/sqlite.yml
    - .github/workflows/postgres.yml
    - .github/workflows/mysql.yml
decisions:
  - "[03-01]: actions/checkout@v6 and astral-sh/setup-uv@v7 used — no actions/setup-python"
  - "[03-01]: PyMySQL (pure Python) chosen over mysqlclient — no C build deps needed"
  - "[03-01]: E711, E721, F821, F841 rules ignored in ruff — deferred to Phase 4 code quality work"
  - "[03-01]: Branch triggers limited to master only (drop testing/stable from old workflows)"
  - "[03-01]: Service containers always started for all jobs (acceptable overhead per research)"
metrics:
  duration: 1m 26s
  completed: "2026-02-27"
  tasks_completed: 2
  files_changed: 7
---

# Phase 03 Plan 01: Ruff Linting, Consolidated CI, and Dependabot Summary

**One-liner:** Replaced three legacy CI workflows (Python 3.6-3.10, pip-based) with a single matrix workflow covering Python 3.10-3.13 x SQLite/PostgreSQL/MySQL using uv, added ruff lint gate, and configured Dependabot for automated updates.

## What Was Built

### Task 1: Ruff dependency and configuration (commit: 584a8c68)

Added `ruff>=0.11` to both `[project.optional-dependencies].test` and `[dependency-groups].test` in pyproject.toml. Appended ruff configuration targeting Python 3.10 with E4/E7/E9/F rule groups, ignoring four rules deferred to Phase 4 (E711, E721, F821, F841). Ran `uv lock` to add ruff v0.15.4 to the lockfile. `uv run ruff check .` passes with zero violations.

### Task 2: CI workflow consolidation and Dependabot (commit: a5fbfc94)

Created `.github/workflows/ci.yml` with a 12-job test matrix (4 Python versions x 3 DB backends) and a parallel lint job. Uses `actions/checkout@v6` and `astral-sh/setup-uv@v7` — no `actions/setup-python`. Uses `uv sync --locked --group test` and `uv run pytest`. PostgreSQL driver installed via `uv pip install psycopg2-binary`, MySQL driver via `uv pip install pymysql` (pure-Python, no build deps). Created `.github/dependabot.yml` monitoring pip and github-actions ecosystems weekly with grouped minor+patch PRs. Deleted `sqlite.yml`, `postgres.yml`, `mysql.yml`.

## Deviations from Plan

None — plan executed exactly as written.

## Requirements Satisfied

- PYV-01: `requires-python = ">=3.10"` (already present, confirmed)
- PYV-02: Python 3.10-3.13 classifiers (already present, confirmed)
- PYV-03: ruff lint gate added to CI (new)
- PYV-04: ruff configuration with E4/E7/E9/F rules (new)
- CI-01: Single ci.yml replaces three old workflows (new)
- CI-02: Test matrix covers Python 3.10, 3.11, 3.12, 3.13 x SQLite/PostgreSQL/MySQL (new)
- CI-03: Lint job runs ruff check as separate parallel job (new)
- CI-04: CI uses uv sync and uv run — no pip or tox (new)
- CI-05: Dependabot monitors pip and github-actions ecosystems weekly (new)

## Verification Results

| Check | Result |
|-------|--------|
| `uv run ruff check .` | PASS — All checks passed |
| No `setup-python` in ci.yml | PASS — count 0 |
| Only `ci.yml` in workflows directory | PASS |
| `dependabot.yml` exists | PASS |
| `target-version = "py310"` in pyproject.toml | PASS |
| Old sqlite/postgres/mysql workflows deleted | PASS |

## Self-Check: PASSED

All created files confirmed present, all deleted files confirmed absent, both commits verified.
