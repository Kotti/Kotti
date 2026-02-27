# Phase 3: Python Version and CI Modernization - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Consolidate three CI workflow files into one matrix workflow, update Python version support to 3.10-3.13, switch CI tooling to uv, add ruff as a lint gate, and configure Dependabot. Code quality fixes and formatting are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Workflow structure
- Consolidate sqlite.yml, postgres.yml, mysql.yml into a single `ci.yml`
- Full matrix: every Python version (3.10, 3.11, 3.12, 3.13) x every DB backend (SQLite, PostgreSQL, MySQL)
- Ruff lint check as a separate parallel job (not a step in test matrix)
- Branch triggers: push to master + PRs targeting master only (drop old testing/stable triggers)
- Use `uv sync` and `uv run pytest` — no pip or tox invocations

### Ruff lint job
- Minimal rule set for Phase 3: core rules (E, F) that already pass
- Lint only (`ruff check`), no format check (`ruff format --check` deferred to Phase 4)
- Configuration in `pyproject.toml` under `[tool.ruff]`
- Set `target-version = "py310"` to match new minimum Python version

### Python version drop
- Set `python_requires = ">=3.10"` with no upper bound
- Update pyproject.toml classifiers: add 3.10-3.13, remove 3.6-3.9
- No runtime deprecation warnings needed — classifiers and python_requires only
- Remove pytest-flake8 dev dependency (replaced by ruff)
- Leave compatibility code cleanup to Phase 4 — Phase 3 focuses on CI/versions only

### Dependabot configuration
- Weekly update frequency
- Group minor+patch updates into single PRs; major versions get individual PRs
- Monitor both Python (pip) dependencies and GitHub Actions versions
- Limit: 5 open Dependabot PRs at a time

### Claude's Discretion
- GitHub Actions service container configuration for Postgres/MySQL
- Exact workflow job naming conventions
- uv cache strategy in CI
- Ruff rule selection within E/F categories

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-python-version-and-ci-modernization*
*Context gathered: 2026-02-27*
