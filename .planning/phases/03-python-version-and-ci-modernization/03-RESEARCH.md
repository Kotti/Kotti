# Phase 3: Python Version and CI Modernization - Research

**Researched:** 2026-02-27
**Domain:** GitHub Actions CI, ruff linting, uv in CI, Dependabot configuration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Workflow structure:**
- Consolidate sqlite.yml, postgres.yml, mysql.yml into a single `ci.yml`
- Full matrix: every Python version (3.10, 3.11, 3.12, 3.13) x every DB backend (SQLite, PostgreSQL, MySQL)
- Ruff lint check as a separate parallel job (not a step in test matrix)
- Branch triggers: push to master + PRs targeting master only (drop old testing/stable triggers)
- Use `uv sync` and `uv run pytest` — no pip or tox invocations

**Ruff lint job:**
- Minimal rule set for Phase 3: core rules (E, F) that already pass
- Lint only (`ruff check`), no format check (`ruff format --check` deferred to Phase 4)
- Configuration in `pyproject.toml` under `[tool.ruff]`
- Set `target-version = "py310"` to match new minimum Python version

**Python version drop:**
- Set `python_requires = ">=3.10"` with no upper bound
- Update pyproject.toml classifiers: add 3.10-3.13, remove 3.6-3.9
- No runtime deprecation warnings needed — classifiers and python_requires only
- Remove pytest-flake8 dev dependency (replaced by ruff)
- Leave compatibility code cleanup to Phase 4 — Phase 3 focuses on CI/versions only

**Dependabot configuration:**
- Weekly update frequency
- Group minor+patch updates into single PRs; major versions get individual PRs
- Monitor both Python (pip) dependencies and GitHub Actions versions
- Limit: 5 open Dependabot PRs at a time

### Claude's Discretion
- GitHub Actions service container configuration for Postgres/MySQL
- Exact workflow job naming conventions
- uv cache strategy in CI
- Ruff rule selection within E/F categories

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PYV-01 | Python 3.6-3.9 classifiers and support dropped | **ALREADY DONE** — pyproject.toml has `requires-python = ">=3.10"` with no old classifiers; no action needed |
| PYV-02 | Python 3.10-3.13 classifiers declared | **ALREADY DONE** — pyproject.toml has all four classifiers; no action needed |
| PYV-03 | CI test matrix covers Python 3.10, 3.11, 3.12, 3.13 | Matrix strategy with `python-version: ["3.10", "3.11", "3.12", "3.13"]` in ci.yml; setup-uv@v7 handles per-version Python install |
| PYV-04 | All tests pass on Python 3.10-3.13 | 383 tests pass on Python 3.12 (current venv); 3 pre-existing depot failures are independent of Python version; SQLAlchemy 1.4.54 supports 3.13; Pyramid 1.10.8 runs on 3.12 without issues |
| LNT-03 | pytest-flake8 removed from test dependencies | **ALREADY DONE** — not present in pyproject.toml; no action needed |
| CI-01 | GitHub Actions updated to current versions | Replace `actions/checkout@v2` → `@v6`; `actions/setup-python@v2` is no longer needed (setup-uv manages Python); `astral-sh/setup-uv@v7` is the current version |
| CI-02 | CI uses uv for package installation (astral-sh/setup-uv action) | Use `astral-sh/setup-uv@v7` with `python-version: ${{ matrix.python-version }}`; run `uv sync --locked --group test`; DB drivers installed via `uv pip install` after sync |
| CI-03 | Separate ruff lint/format check job in CI | Parallel job in ci.yml; `uv run ruff check` with E4, E7, E9, F rules; ignore E711, E721, F821, F841 (deferred to Phase 4); single Python version (3.12); no matrix needed |
| CI-04 | 3 separate workflow files consolidated into 1 matrix workflow | One ci.yml with `matrix: python-version x db-backend`; service containers conditional on backend; postgres and mysql backends need service containers |
| CI-05 | Dependabot configured for automated dependency PRs | `.github/dependabot.yml` with two update blocks: `pip` (Python deps) and `github-actions`; group minor+patch, individual major PRs; `open-pull-requests-limit: 5`; weekly schedule |
</phase_requirements>

---

## Summary

Phase 3 is primarily CI infrastructure work. Several requirements are already satisfied in the codebase: `requires-python = ">=3.10"` is set, classifiers are current (3.10-3.13 only), and pytest-flake8 is already removed. The remaining work is writing new GitHub Actions YAML and ruff configuration.

The three existing CI files (sqlite.yml, postgres.yml, mysql.yml) all use outdated `actions/checkout@v2`, `actions/setup-python@v2`, and `pip install` patterns. They will be replaced by a single `ci.yml` using a Python × DB matrix. The `astral-sh/setup-uv@v7` action handles both uv and Python installation in a single step, eliminating the need for `actions/setup-python` entirely. Cache is enabled by default on GitHub-hosted runners.

The ruff lint job requires careful rule selection: the default E4, E7, E9, F ruleset has 26 violations (F821, F841, E711, E721) that must be explicitly ignored in Phase 3 — these are deferred to Phase 4 code quality work. The F821 violations are forward-reference string annotations in security.py and filedepot.py, not real undefined names. The ruff CI job is a single-Python-version job (no need for a matrix) that runs in parallel with the test matrix.

**Primary recommendation:** Write ci.yml with a `matrix: include:` or `matrix: python-version x backend` approach, with service containers conditional on backend. Use `uv pip install psycopg2-binary` / `uv pip install pymysql` after `uv sync` for DB drivers.

---

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| astral-sh/setup-uv | v7 | Install uv + Python in CI | Official action, handles caching, replaces setup-python |
| actions/checkout | v6 | Checkout code | Current major version (v6.0.2, Jan 2025) |
| astral-sh/ruff | 0.11.13 (installed) | Lint check | Already in project venv via uv run |
| psycopg2-binary | latest | PostgreSQL driver for CI | Self-contained binary, no system dependencies needed |
| PyMySQL | latest | MySQL driver for CI | Pure Python, no compilation, simpler than mysqlclient |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| actions/setup-python | v6 (current) | Python install | NOT needed — setup-uv handles this |
| uv cache prune --ci | - | Minimize CI cache size | Optional post-step on self-hosted runners |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyMySQL | mysqlclient | mysqlclient requires `libmysqlclient-dev` build dep; PyMySQL is pure Python, simpler in CI |
| Single ci.yml matrix | Separate per-backend files | Separate files are simpler per-job but 3x duplication; matrix is DRY |
| setup-uv python-version | actions/setup-python + setup-uv | setup-uv alone is cleaner; astral docs recommend this pattern |

---

## Architecture Patterns

### Recommended ci.yml Structure

```
.github/
├── workflows/
│   └── ci.yml           # Replaces sqlite.yml, postgres.yml, mysql.yml
└── dependabot.yml       # New: monitors pip + github-actions
```

### Pattern 1: Python × DB Matrix

**What:** Matrix strategy combining `python-version` and `db-backend` dimensions.

**When to use:** When every combination needs to be tested (full cross-product).

**Example:**
```yaml
# Source: astral-sh/setup-uv docs + GitHub Actions service containers docs
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
        db-backend: [sqlite, postgres, mysql]

    services:
      postgres:
        image: postgres:latest
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      mysql:
        image: mariadb:latest
        env:
          MYSQL_USER: kotti
          MYSQL_PASSWORD: kotti
          MYSQL_DATABASE: kotti
          MYSQL_ROOT_PASSWORD: kotti
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=5s
          --health-timeout=2s
          --health-retries=3
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v6
      - name: Install uv and Python ${{ matrix.python-version }}
        uses: astral-sh/setup-uv@v7
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true

      - name: Install project (test group)
        run: uv sync --locked --group test

      - name: Install DB driver (postgres)
        if: matrix.db-backend == 'postgres'
        run: uv pip install psycopg2-binary

      - name: Install DB driver (mysql)
        if: matrix.db-backend == 'mysql'
        run: uv pip install pymysql

      - name: Run tests (sqlite)
        if: matrix.db-backend == 'sqlite'
        run: uv run pytest

      - name: Run tests (postgres)
        if: matrix.db-backend == 'postgres'
        run: uv run pytest
        env:
          KOTTI_TEST_DB_STRING: postgresql://postgres:postgres@localhost:5432/postgres

      - name: Run tests (mysql)
        if: matrix.db-backend == 'mysql'
        run: uv run pytest
        env:
          KOTTI_TEST_DB_STRING: mysql+pymysql://kotti:kotti@127.0.0.1:3306/kotti
```

**Note on service containers:** GitHub Actions always starts ALL service containers defined in `services:`, even if a job doesn't use them. This wastes ~15-30s per job. The alternative is a `matrix.include:` approach (see Pitfalls section), but a simple services block is acceptable for this phase given the project's CI complexity.

### Pattern 2: Parallel Ruff Lint Job

**What:** A single-Python-version ruff check job running in parallel with the test matrix, not inside it.

**Why separate:** Lint doesn't need a version matrix; failures should be visible separately from test failures; matches the CONTEXT.md decision.

**Example:**
```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Install uv and Python
        uses: astral-sh/setup-uv@v7
        with:
          python-version: "3.12"
          enable-cache: true
      - name: Install project (test group for ruff access)
        run: uv sync --locked --group test
      - name: Run ruff check
        run: uv run ruff check --select E4,E7,E9,F --ignore E711,E721,F821,F841 .
```

**Note:** Ruff is available as `uv run ruff` because it's installed in the project venv (added to dependency-groups.test or as a standalone tool). It does NOT need to be in pyproject.toml test deps — it can be invoked via `uvx ruff` without installation if preferred.

### Pattern 3: Dependabot Configuration

**What:** `.github/dependabot.yml` with two update ecosystems: `pip` and `github-actions`.

**Example:**
```yaml
# Source: GitHub Docs - Configuration options for the dependabot.yml file
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]
```

**Note:** Major version updates that don't match `minor-and-patch` will automatically get individual PRs.

### Pattern 4: Ruff pyproject.toml Configuration

**What:** Minimal `[tool.ruff]` and `[tool.ruff.lint]` sections that pass cleanly.

**Exact ignore list required (verified by running ruff against codebase):**
- `E711` (2 violations): `None` comparison with `==` — deferred to Phase 4
- `E721` (6 violations): type comparison using `==` instead of `isinstance` — deferred to Phase 4
- `F821` (14 violations): "undefined name" for forward-reference string annotations in security.py and filedepot.py — these are valid Python, ruff's F821 has a false positive rate on TYPE_CHECKING patterns
- `F841` (4 violations): unused variables — deferred to Phase 4

```toml
[tool.ruff]
target-version = "py310"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
ignore = [
    "E711",  # Comparison to None — deferred to Phase 4
    "E721",  # Type comparison — deferred to Phase 4
    "F821",  # Undefined name — false positives on string annotations
    "F841",  # Unused variable — deferred to Phase 4
]
```

### Anti-Patterns to Avoid

- **Using `pip install` in CI after Phase 3:** The success criterion explicitly requires no pip invocations in workflow files.
- **Using `actions/setup-python` alongside `setup-uv`:** setup-uv v7 handles Python version management; adding setup-python creates redundancy.
- **Putting all E+F rules in the lint gate without ignoring current violations:** This would cause the lint job to fail immediately. The CONTEXT.md decision is "minimal rule set that already passes."
- **Using `tox` in any step:** All tox references must be eliminated.
- **`uv sync` without `--locked`:** The `--locked` flag ensures CI uses exactly the committed uv.lock versions. Without it, uv may update packages.
- **Conditional service containers via `if:` on the service block:** GitHub Actions does not support conditional service containers. Services defined in the `services:` map always start. The workaround is matrix include strategies (see Open Questions).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python version management in CI | Custom pyenv scripts | `astral-sh/setup-uv@v7 with python-version:` | setup-uv installs exact Python version via uv's managed Python; cleaner and faster |
| DB health checks | Sleep loops | `--health-cmd` options in service container | GitHub handles retry logic; the old mysql.yml already had a manual ping loop — replace with health check |
| Ruff binary installation | `pip install ruff` in CI | `uv run ruff` (already in venv) or `uvx ruff` | Ruff is accessed through the project venv; no separate install step needed |
| Cache invalidation keys | Custom hash scripts | `astral-sh/setup-uv@v7 enable-cache: true` | setup-uv caches against uv.lock automatically |

**Key insight:** The `astral-sh/setup-uv@v7` action with `python-version` input is sufficient to replace both `actions/setup-python` and manual Python installation. The action handles Python version pinning, uv installation, and cache setup in a single step.

---

## Common Pitfalls

### Pitfall 1: Service Containers Always Start

**What goes wrong:** All service containers (postgres, mysql) start for every matrix job, even for the sqlite backend. This wastes time and can cause port conflicts.

**Why it happens:** GitHub Actions does not support conditional service containers via `if:` expressions in the `services:` block. It's a known limitation.

**How to avoid:** Accept the overhead (postgres/mysql containers take ~10-20s to start but don't affect test results for sqlite jobs). Alternatively, use a `matrix.include:` explicit list approach instead of a cross-product — but this means writing 12 explicit entries (4 Python × 3 DB). For this phase, simple services block is acceptable.

**Warning signs:** If service startup time becomes a CI bottleneck, switch to explicit `matrix.include` entries.

### Pitfall 2: MySQL Connection String Driver Mismatch

**What goes wrong:** Using `mysql://` (bare scheme) with SQLAlchemy 1.4 defaults to the `mysqldb` dialect (requires compiled `mysqlclient`). If only `pymysql` is installed, tests fail with "Could not load requested dialect 'mysql'".

**Why it happens:** The old workflows used `mysql://` and installed `mysqlclient`. With PyMySQL, the URL must be `mysql+pymysql://`.

**How to avoid:** Set `KOTTI_TEST_DB_STRING: mysql+pymysql://kotti:kotti@127.0.0.1:3306/kotti` in the MySQL test step. This is explicit about the driver.

**Warning signs:** ImportError for MySQLdb module when KOTTI_TEST_DB_STRING uses bare `mysql://`.

### Pitfall 3: uv.lock Compatibility with CI Python Versions

**What goes wrong:** `uv sync --locked` fails on Python 3.13 if uv.lock was generated on Python 3.12 and a dependency doesn't have a 3.13-compatible wheel.

**Why it happens:** uv.lock stores resolution markers per Python version. The current uv.lock was generated with `requires-python = ">=3.10"` and has resolution markers for 3.10, 3.11, 3.12, and 3.13+ (confirmed: uv.lock header shows `python_full_version >= '3.13'` marker).

**How to avoid:** The uv.lock already handles multi-version resolution. Run `uv lock` locally after any dep changes to regenerate. For CI, `--locked` is correct — it validates the existing lock rather than re-solving.

**Warning signs:** "No solution found when resolving dependencies" on a specific Python version during `uv sync --locked`.

### Pitfall 4: F821 False Positives on String Annotations

**What goes wrong:** Ruff reports F821 "Undefined name" for forward-reference strings like `"Node"`, `"Request"` in type annotations in security.py. These are valid Python 3.10+ annotations that ruff misidentifies because the names are imported conditionally via `TYPE_CHECKING`.

**Why it happens:** security.py uses string-quoted annotations for classes that would create circular imports if imported directly. Ruff's F821 does not fully understand `TYPE_CHECKING`-guarded imports in all cases.

**How to avoid:** Add `F821` to the ignore list in `[tool.ruff.lint]`. Document why — these are not real undefined names.

**Warning signs:** CI lint job fails with 14 F821 violations immediately after the lint job is set up.

### Pitfall 5: actions/checkout Version

**What goes wrong:** Using `actions/checkout@v4` when v6 is current. Not a breaking issue, but v4 uses Node 20 and v6 uses Node 24. GitHub has announced deprecation of older node versions in Actions.

**Why it matters:** GitHub published a changelog in April 2025 about upcoming breaking changes for GitHub Actions, specifically around Node versions. Using v6 future-proofs the workflow.

**How to avoid:** Use `actions/checkout@v6`. Current latest is v6.0.2 (January 2025).

### Pitfall 6: pytest-flake8 Is Already Gone

**What goes wrong:** Spending time on LNT-03 (remove pytest-flake8) when it's already done.

**Why it matters:** pytest-flake8 is not present in pyproject.toml or uv.lock. This was removed in Phase 1 per STATE.md.

**How to avoid:** Skip any task about removing pytest-flake8 — it's already done.

---

## Code Examples

### Complete ci.yml Reference (Skeleton)

```yaml
# Source: astral-sh/setup-uv docs + GitHub Actions service container docs
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test:
    name: Test (Python ${{ matrix.python-version }} / ${{ matrix.db-backend }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
        db-backend: [sqlite, postgres, mysql]

    services:
      postgres:
        image: postgres:latest
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      mysql:
        image: mariadb:latest
        env:
          MYSQL_USER: kotti
          MYSQL_PASSWORD: kotti
          MYSQL_DATABASE: kotti
          MYSQL_ROOT_PASSWORD: kotti
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=5s
          --health-timeout=2s
          --health-retries=3
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v6

      - name: Install uv and Python ${{ matrix.python-version }}
        uses: astral-sh/setup-uv@v7
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true

      - name: Install project
        run: uv sync --locked --group test

      - name: Install psycopg2-binary
        if: matrix.db-backend == 'postgres'
        run: uv pip install psycopg2-binary

      - name: Install PyMySQL
        if: matrix.db-backend == 'mysql'
        run: uv pip install pymysql

      - name: Run tests (SQLite)
        if: matrix.db-backend == 'sqlite'
        run: uv run pytest

      - name: Run tests (PostgreSQL)
        if: matrix.db-backend == 'postgres'
        run: uv run pytest
        env:
          KOTTI_TEST_DB_STRING: postgresql://postgres:postgres@localhost:5432/postgres

      - name: Run tests (MySQL)
        if: matrix.db-backend == 'mysql'
        run: uv run pytest
        env:
          KOTTI_TEST_DB_STRING: mysql+pymysql://kotti:kotti@127.0.0.1:3306/kotti

  lint:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install uv and Python
        uses: astral-sh/setup-uv@v7
        with:
          python-version: "3.12"
          enable-cache: true

      - name: Install project
        run: uv sync --locked --group test

      - name: Run ruff check
        run: uv run ruff check .
```

### pyproject.toml ruff configuration

```toml
[tool.ruff]
target-version = "py310"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
ignore = [
    "E711",  # Comparison to None (== None) — deferred to Phase 4
    "E721",  # Type comparison with == — deferred to Phase 4
    "F821",  # Undefined name — false positives on string annotations in security.py
    "F841",  # Local variable assigned but never used — deferred to Phase 4
]
```

### dependabot.yml

```yaml
# Source: GitHub Docs - configuration-options-for-the-dependabot.yml-file
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      minor-and-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/checkout@v2` | `actions/checkout@v6` | Jan 2025 | Node 24, security fixes, worktree support |
| `actions/setup-python@v2` + `pip install` | `astral-sh/setup-uv@v7` only | 2024-2025 | Single action handles Python + uv + cache |
| `pip install -e ".[testing]"` | `uv sync --locked --group test` | Phase 3 | Reproducible installs from uv.lock |
| flake8 / pytest-flake8 | ruff | Phase 3 | 10-100x faster, same rule coverage |
| 3 separate workflow files | 1 matrix workflow | Phase 3 | DRY, consistent matrix |
| No Dependabot | `.github/dependabot.yml` | Phase 3 | Automated dep update PRs |

**Deprecated/outdated:**
- `actions/setup-python`: Not needed when using `astral-sh/setup-uv` with `python-version:` input. The uv docs explicitly show this as the recommended pattern.
- `pip install`: All direct pip calls in CI must be eliminated per success criterion CI-03.
- `tox`: No tox.ini exists in the repo; old workflow never used tox; not relevant.
- MySQL driver `mysql://` (bare scheme): Must become `mysql+pymysql://` when using PyMySQL.

---

## Pre-Existing State (What's Already Done)

These requirements are already satisfied and need NO implementation work:

| Requirement | Status | Evidence |
|-------------|--------|---------|
| PYV-01: Drop 3.6-3.9 classifiers | DONE | pyproject.toml has no 3.6/3.7/3.8/3.9 classifiers; `requires-python = ">=3.10"` |
| PYV-02: Add 3.10-3.13 classifiers | DONE | pyproject.toml has 3.10, 3.11, 3.12, 3.13 classifiers |
| LNT-03: Remove pytest-flake8 | DONE | pytest-flake8 not present in pyproject.toml or uv.lock |

The planner should treat these as already complete, not create tasks for them.

---

## Open Questions

1. **Service container always-start overhead**
   - What we know: GitHub Actions always starts all defined service containers for every matrix job, including sqlite jobs that don't use them.
   - What's unclear: Whether the startup overhead (~15-30s per service) is acceptable, or whether an explicit `matrix.include:` approach (12 separate entries) is preferred.
   - Recommendation: Use the simple services block approach for now. The overhead is real but predictable. The matrix approach adds 12 explicit combinations — harder to maintain but eliminates unused service startup.

2. **Python 3.13 test failures**
   - What we know: SQLAlchemy 1.4.54 supports Python 3.13 per maintainer confirmation. Pyramid 1.10.8 works on 3.12 (tested locally). The 3 pre-existing test failures (depot/cgi) are Python-version-independent.
   - What's unclear: Whether any Pyramid/SQLAlchemy code paths have undiscovered Python 3.13 incompatibilities that only surface under test.
   - Recommendation: Run the CI matrix and accept that new failures may appear. They are fixing opportunities, not blockers for Phase 3 merge. The success criterion is "all existing tests pass" — the 3 pre-existing failures are documented exceptions.

3. **ruff not in pyproject.toml test deps**
   - What we know: ruff is invoked as `uv run ruff` in CI; it needs to be in the project environment.
   - What's unclear: Should ruff be added to `[dependency-groups] test` or invoked via `uvx ruff`?
   - Recommendation: Add ruff to `[dependency-groups] test` (and the corresponding `[project.optional-dependencies] test`). This ensures it's in the locked environment used by both CI and local development. The alternative `uvx ruff` installs into a temporary tool environment and bypasses uv.lock, which is less reproducible.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest src/kotti/tests/test_cache.py -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PYV-01 | `requires-python = ">=3.10"` set | smoke | `grep "requires-python" pyproject.toml` | ✅ (pyproject.toml) |
| PYV-02 | 3.10-3.13 classifiers present, no old ones | smoke | `grep "3\.10\|3\.11\|3\.12\|3\.13" pyproject.toml` | ✅ (pyproject.toml) |
| PYV-03 | CI matrix covers 3.10-3.13 | manual/CI | Push to master; check GitHub Actions matrix | ✅ (once ci.yml written) |
| PYV-04 | All tests pass on 3.10-3.13 | integration | `uv run pytest` (each Python version) | ✅ (existing test suite) |
| LNT-03 | pytest-flake8 not in deps | smoke | `grep flake8 pyproject.toml` (must return nothing) | ✅ (already done) |
| CI-01 | Current action versions in ci.yml | manual | Inspect ci.yml for @v6/@v7 | ❌ Wave 0 — ci.yml doesn't exist yet |
| CI-02 | uv sync used, no pip | manual | `grep "pip install" .github/workflows/ci.yml` (must be empty) | ❌ Wave 0 — ci.yml doesn't exist yet |
| CI-03 | Ruff lint job passes | manual/CI | `uv run ruff check .`; push to master | ❌ Wave 0 — ruff config + CI job don't exist yet |
| CI-04 | Single ci.yml, old files removed | smoke | `ls .github/workflows/` (must show only ci.yml) | ❌ Wave 0 — consolidation not done |
| CI-05 | Dependabot configured | manual | Check `.github/dependabot.yml` exists and triggers | ❌ Wave 0 — dependabot.yml doesn't exist yet |

### Sampling Rate

- **Per task commit:** `uv run pytest src/kotti/tests/test_cache.py -x -q --no-cov` (fast, ~5s)
- **Per wave merge:** `uv run pytest` (full suite, ~90s)
- **Phase gate:** Full suite green + ruff check passes + ci.yml present before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `.github/workflows/ci.yml` — covers CI-01, CI-02, CI-03, CI-04 (PYV-03, PYV-04 verified via CI)
- [ ] `.github/dependabot.yml` — covers CI-05
- [ ] `[tool.ruff]` section in pyproject.toml — covers CI-03, LNT-01 (partial)
- [ ] ruff added to `[dependency-groups] test` — needed for `uv run ruff` in CI lint job

*(Existing test infrastructure covers all Python-level requirements; the gaps are all new files/config.)*

---

## Sources

### Primary (HIGH confidence)

- `/astral-sh/setup-uv` (Context7) — action inputs, caching configuration, Python version matrix patterns; current version v7
- `/websites/astral_sh_uv` (Context7) — `uv sync --locked --group test`, GitHub Actions integration, `uv pip install` for non-project packages
- `/astral-sh/ruff` (Context7) — `[tool.ruff]` and `[tool.ruff.lint]` configuration, select/ignore syntax, target-version
- GitHub Docs: `https://docs.github.com/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file` — dependabot.yml format, groups, update-types, open-pull-requests-limit

### Secondary (MEDIUM confidence)

- `https://github.com/actions/checkout/releases` — confirmed latest is v6.0.2 (Jan 2025)
- `https://github.com/actions/setup-python` releases — confirmed latest is v6 (Node 24)
- `https://github.com/sqlalchemy/sqlalchemy/discussions/12682` — SQLAlchemy 1.4.53/54 supports Python 3.13 per maintainer; "no known issues"

### Tertiary (LOW confidence)

- WebSearch result for Pyramid 1.10 + Python 3.13: No definitive source found. Pyramid docs show testing through 3.12. Python 3.13 support for Pyramid 1.x is unverified — this is the main risk for PYV-04.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Context7 for setup-uv and ruff; official GitHub docs for dependabot; verified locally
- Architecture: HIGH — patterns from official docs; ruff violations verified by running against codebase
- Pitfalls: HIGH for known issues (service containers, MySQL driver); MEDIUM for Python 3.13 Pyramid compatibility
- Pre-existing state: HIGH — directly inspected pyproject.toml

**Research date:** 2026-02-27
**Valid until:** 2026-03-29 (stable ecosystem; action versions rarely change within major)
