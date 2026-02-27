# Phase 1: Packaging Foundation - Research

**Researched:** 2026-02-27
**Domain:** Python packaging — pyproject.toml, build backends, src layout, uv lockfiles
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Build backend:**
- RESEARCH NEEDED resolved below: `uv_build` is viable but has trade-offs; see Standard Stack. Hatchling remains the recommended choice for Kotti's asset inclusion needs.

**Dependency groups:**
- Split extras: [dev], [test], [docs] as separate groups in pyproject.toml
- [dev] is a superset that includes [test] + [docs] — developers install `.[dev]`, CI installs granularly
- Use modern short names ([dev], [test], [docs]) but keep old names ([development], [testing]) as deprecated aliases
- Check current extras_require in setup.cfg for any user-facing extras that must be preserved for compatibility

**Version management:**
- Static version string in pyproject.toml: `version = "2.1.0.dev0"`
- Bump from 2.0.10dev0 to 2.1.0.dev0 to signal the modernization milestone
- `kotti.__version__` exposed at runtime via `importlib.metadata.version("kotti")` for backwards compatibility
- The .dev0 suffix keeps it as a pre-release

**Transition cleanup:**
- Clean break: delete setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini in one commit
- Drop tox entirely — test commands use `uv run pytest` directly, CI workflow replaces tox matrices
- Migrate pytest configuration to [tool.pytest.ini_options] in pyproject.toml
- Dedicated commit for src layout move (`git mv kotti/ src/kotti/`) to preserve file history

**Lock file:**
- uv.lock covers base package + all extras (dev, test, docs) — full reproducibility
- CI uses `uv sync --locked` — fails if lock is stale, forcing explicit updates
- Lock targets `requires-python = ">=3.10"` for multi-version resolution

### Claude's Discretion
- Exact pyproject.toml section ordering and formatting
- hatchling configuration details for package data inclusion (.pt, .po, .mo, .zcml, alembic)
- How to handle the MANIFEST.in rules during migration to hatchling's inclusion config
- Commit ordering beyond the dedicated src layout move commit

### Deferred Ideas (OUT OF SCOPE)
- Adding explicit [postgres] and [mysql] extras for database-specific dependencies — would be new capability, evaluate in a future phase
- tox replacement patterns (if anyone externally uses tox with Kotti) — document in migration guide if needed
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PKG-01 | Project uses pyproject.toml as single source of truth (replaces setup.py, setup.cfg, pytest.ini, tox.ini) | Standard Stack: complete pyproject.toml template; Code Examples: full migration |
| PKG-02 | Project uses hatchling as build backend | Standard Stack: hatchling vs uv_build analysis; Architecture: build backend config |
| PKG-03 | Project uses src layout (src/kotti/) | Architecture Patterns: src layout with hatchling; Pitfalls: stale editable install trap |
| PKG-04 | All six entry points (paste.app_factory, fanstatic.libraries, 3 console_scripts, pytest11) work correctly from pyproject.toml | Code Examples: entry point TOML; Pitfalls: src layout reinstall required |
| PKG-05 | Non-Python package data (.pt, .po, .mo, .zcml, alembic scripts, static assets) included in sdist/wheel | Architecture: hatchling include patterns; Pitfalls: package data inclusion trap |
| PKG-06 | setuptools_git and check-manifest removed | State of the Art: these tools are obsolete; removed via clean break commit |
| PKG-07 | setup.py and setup.cfg deleted (not coexisting with pyproject.toml) | Architecture: clean break strategy; Pitfalls: coexistence issues |
| PKG-08 | uv used as package manager with committed uv.lock | Standard Stack: uv lock workflow; Code Examples: dependency group commands |
</phase_requirements>

---

## Summary

Phase 1 migrates Kotti's packaging from a multi-file setup (setup.py + setup.cfg + MANIFEST.in + pytest.ini + tox.ini) to a single pyproject.toml with hatchling as build backend and src layout. The migration is well-understood: hatchling natively handles entry points, non-Python asset inclusion, and src layout with minimal configuration. The primary implementation risk is the src layout move — a stale editable install after `git mv kotti/ src/kotti/` creates silent import ambiguity that is easy to miss during development but caught immediately by the `kotti.__file__` check.

A key research finding: uv now ships its own build backend (`uv_build`, available since uv 0.5.x, requires `uv_build>=0.10.2`). This is what the user saw as a "uv-only workflow." However, `uv_build` currently has limited support for fine-grained non-Python data inclusion patterns — it is designed for pure Python packages following strict src layout conventions. Kotti requires explicit inclusion of `.pt`, `.po`, `.mo`, `.zcml`, alembic scripts, and static assets; hatchling's `[tool.hatch.build.targets.wheel]` configuration handles this cleanly. The recommendation is hatchling, not `uv_build`, and the CONTEXT.md requirement PKG-02 is validated.

The extras structure needs one complication addressed: the current setup.py uses old names (`testing`, `development`, `docs`). The plan is to add the new short names as the canonical groups and keep the old names as deprecated aliases pointing to the same dependency sets. uv's `[dependency-groups]` table (PEP 735) is the forward-looking approach, but for a PyPI-published library that consumers `pip install Kotti[testing]`, `[project.optional-dependencies]` remains the correct mechanism — `[dependency-groups]` is for internal dev tooling only.

**Primary recommendation:** Use hatchling as build backend. Configure `[tool.hatch.build.targets.wheel]` with explicit include patterns for all non-Python assets. Use `[project.optional-dependencies]` for user-facing extras and `[dependency-groups]` for internal dev groups. Generate and commit `uv.lock` covering all groups.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hatchling | `>=1.27` | Build backend (PEP 517) | PyPA-maintained; native src layout support; explicit non-Python data inclusion; entry points in TOML; no setup.py |
| uv | `>=0.5` | Package manager, venv, lockfile | Replaces pip/pip-tools/virtualenv/tox; 10-100x faster; `uv.lock` for reproducibility |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv_build | `>=0.10.2,<0.11.0` | uv's own build backend | Pure-Python packages without complex data inclusion needs — NOT recommended for Kotti |
| build | `>=1.0` | Build frontend (PEP 517) | `python -m build` or `uv build` to produce wheel/sdist for inspection |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hatchling | uv_build | uv_build is simpler for pure-Python but lacks mature non-Python data include patterns needed by Kotti |
| hatchling | flit-core | flit-core does not support entry points well; wrong tool for a CMS framework |
| hatchling | setuptools | Viable but requires more config; `setup.py` imperative style is the thing being abandoned |
| [project.optional-dependencies] | [dependency-groups] (PEP 735) | dependency-groups is for project-internal tooling; user-facing extras on PyPI must stay in optional-dependencies |

**Installation:**
```bash
# No installation — hatchling is the build-backend; uv is the runtime tool
# uv install: https://docs.astral.sh/uv/getting-started/installation/
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Architecture Patterns

### Recommended Project Structure

```
kotti/                          # repo root
├── pyproject.toml              # single source of truth (new)
├── uv.lock                     # committed lockfile (new)
├── src/
│   └── kotti/                  # moved from kotti/ at root
│       ├── __init__.py
│       ├── alembic/            # migration scripts (included as data)
│       ├── locale/             # .po/.mo files (included as data)
│       ├── static/             # CSS, JS, images (included as data)
│       ├── templates/          # .pt Chameleon templates (included as data)
│       ├── workflow.zcml       # ZCML config (included as data)
│       └── tests/
│           └── __init__.py     # pytest11 plugin entry point
├── AUTHORS.txt
├── CHANGES.txt
└── README.rst
```

### Pattern 1: pyproject.toml Build System Block

**What:** Declares hatchling as the PEP 517 build backend.
**When to use:** Always — this is the foundation.

```toml
# Source: https://github.com/pypa/hatch (Context7 /pypa/hatch)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Pattern 2: src Layout with Hatchling

**What:** Tells hatchling where to find the package and how to strip the `src/` prefix in the wheel.
**When to use:** With any src layout project.

```toml
# Source: https://github.com/pypa/hatch/blob/master/docs/config/build.md (Context7 /pypa/hatch)
[tool.hatch.build.targets.wheel]
packages = ["src/kotti"]

# Equivalent (more explicit):
[tool.hatch.build.targets.wheel]
only-include = ["src/kotti"]
sources = ["src"]
```

### Pattern 3: Non-Python Asset Inclusion

**What:** Explicitly includes Kotti's runtime assets in both wheel and sdist.
**When to use:** Any package with templates, locales, static files, or migration scripts.

```toml
# Source: https://github.com/pypa/hatch/blob/master/docs/config/build.md (Context7 /pypa/hatch)
[tool.hatch.build.targets.wheel]
packages = ["src/kotti"]
# All files under src/kotti/ are included by default when packages is set.
# No additional include patterns needed for hatchling — it includes all files
# in the package directory, not just .py files.

[tool.hatch.build.targets.sdist]
include = [
  "/src",
  "/AUTHORS.txt",
  "/CHANGES.txt",
  "/README.rst",
]
```

**Critical finding:** Unlike setuptools (which requires `include_package_data = true` or explicit `package-data`), hatchling includes ALL files within the package directory by default when `packages` is set. The `.pt`, `.po`, `.mo`, `.zcml`, and alembic scripts are automatically included without extra configuration.

### Pattern 4: Entry Points in pyproject.toml

**What:** Declares all six of Kotti's entry points in standard TOML format.

```toml
# Source: https://github.com/pypa/hatch/blob/master/docs/config/metadata.md (Context7 /pypa/hatch)
[project.scripts]
kotti-migrate = "kotti.migrate:kotti_migrate_command"
kotti-reset-workflow = "kotti.workflow:reset_workflow_command"
kotti-migrate-storage = "kotti.filedepot:migrate_storages_command"

[project.entry-points."paste.app_factory"]
main = "kotti:main"

[project.entry-points."fanstatic.libraries"]
kotti = "kotti.fanstatic:lib_kotti"

[project.entry-points."pytest11"]
kotti = "kotti.tests"
```

### Pattern 5: Optional Dependencies (Extras) with Backward-Compatible Aliases

**What:** Declares new short-name extras as canonical, keeps old names as aliases.
**When to use:** Public library with existing users who do `pip install Kotti[testing]`.

```toml
# Source: https://github.com/pypa/hatch/blob/master/docs/config/metadata.md (Context7 /pypa/hatch)
[project.optional-dependencies]
# New canonical names
test = [
    "WebTest",
    "Pillow",
    "pyquery",
    "pytest>=8",
    "pytest-cov",
    "zope.testbrowser>=5.0.0",
]
docs = [
    "Sphinx",
    "docutils",
    "repoze.sphinx.autointerface",
    "sphinx_rtd_theme",
]
dev = [
    "kotti[test]",
    "kotti[docs]",
    "pipdeptree",
    "pyramid_debugtoolbar",
]
# Deprecated aliases — preserved for backward compatibility
testing = ["kotti[test]"]
development = ["kotti[dev]"]
```

**Removed from test extras (vs current setup.py):**
- `mock` — use `unittest.mock` from stdlib (Phase 2 task, but remove from extras now)
- `pytest-flake8` — linting is no longer baked into pytest (Phase 4 task, remove now)
- `pytest-virtualenv` — not needed with uv-managed envs
- `tox` — runner, not a test library; dropping entirely
- `check-manifest` — obsolete with hatchling
- `setuptools-git` (in docs) — obsolete

### Pattern 6: Dependency Groups for Internal Dev Tooling

**What:** PEP 735 dependency groups for uv-managed dev workflows (distinct from PyPI extras).
**When to use:** Tools that are only ever used locally or in CI, not by library consumers.

```toml
# Source: https://docs.astral.sh/uv (Context7 /llmstxt/astral_sh_uv_llms_txt)
[dependency-groups]
dev = [
    {include-group = "test"},
    {include-group = "docs"},
    "pipdeptree",
    "pyramid_debugtoolbar",
]
test = [
    "WebTest",
    "Pillow",
    "pyquery",
    "pytest>=8",
    "pytest-cov",
    "zope.testbrowser>=5.0.0",
]
docs = [
    "Sphinx",
    "docutils",
    "repoze.sphinx.autointerface",
    "sphinx_rtd_theme",
]
```

**IMPORTANT:** Both `[project.optional-dependencies]` AND `[dependency-groups]` should exist:
- `[project.optional-dependencies]` = user-facing, published to PyPI, `pip install kotti[test]`
- `[dependency-groups]` = local dev and CI, `uv sync --group dev`

The two systems can coexist. In practice, CI uses `uv sync --group test` (no extras overhead), while external users use `pip install kotti[testing]`.

### Pattern 7: pytest Configuration Migration

**What:** Moves pytest.ini options into pyproject.toml; removes pytest-flake8 from addopts.

```toml
[tool.pytest.ini_options]
addopts = [
    "--ignore=src/kotti/templates/",
    "--capture=no",
    "--strict-markers",      # was --strict (renamed in pytest 6+)
    "--tb=native",
    "--cov=kotti",
    "--cov-report=term-missing",
]
testpaths = ["src/kotti"]    # was kotti/ in pytest.ini
python_files = ["test_*.py"]
markers = [
    "user: mark test to be run as the given user",
    "slow: mark test to be run only with --runslow option",
]
# Note: --flake8 and flake8-* options removed entirely
```

### Pattern 8: uv Lock File Generation

**What:** Generate and commit a lock covering all extras and dependency groups.

```bash
# Source: https://docs.astral.sh/uv (Context7 /llmstxt/astral_sh_uv_llms_txt)

# Generate lock (resolves all extras and groups)
uv lock

# Sync dev environment (all dependency groups)
uv sync --group dev

# CI: sync only what's needed, fail if lock is stale
uv sync --locked --group test

# Verify lockfile is up to date
uv lock --check
```

### Anti-Patterns to Avoid

- **Coexisting setup.py + pyproject.toml:** setuptools will read both and produce undefined behavior. Delete setup.py in the same commit that creates pyproject.toml.
- **Using `[dependency-groups]` for user-facing extras:** dependency-groups are local-only; they do not appear on PyPI. Keep user-facing extras in `[project.optional-dependencies]`.
- **Using `uv_build` for Kotti:** uv_build is for pure-Python packages with convention-driven layouts. Kotti's asset inclusion needs make hatchling a better fit.
- **Forgetting to reinstall after src layout move:** `git mv kotti/ src/kotti/` without a fresh `uv pip install -e .` leaves a stale `.pth` file pointing to the old location.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Non-Python data inclusion in wheel | Manual file copying or custom build hooks | hatchling's default include-all-in-package behavior | hatchling includes ALL files under the package directory when `packages` is set — no extra config needed |
| Cross-version dep resolution | requirements.txt per Python version | `uv lock` with `requires-python = ">=3.10"` | uv resolves across all supported Python versions in a single lockfile |
| Deprecated extra names | Conditional logic in setup.py | Alias extras: `"testing" = ["kotti[test]"]` | TOML optional-dependencies support cross-reference extras natively |
| MANIFEST.in equivalents | Keep MANIFEST.in alongside pyproject.toml | `[tool.hatch.build.targets.sdist]` include patterns | hatchling replaces MANIFEST.in entirely; coexistence adds confusion |

**Key insight:** The main custom-code trap in this phase is package data — developers assume non-Python assets need custom build steps or MANIFEST.in. With hatchling, they don't. The default behavior of `packages = ["src/kotti"]` includes everything in that directory, including templates, locale files, and static assets.

---

## Common Pitfalls

### Pitfall 1: Stale Editable Install After src Layout Move

**What goes wrong:** After `git mv kotti/ src/kotti/`, Python still imports from the old flat-layout path if the package was installed in editable mode before the move. Two `kotti` packages become visible.

**Why it happens:** `pip install -e .` (or `uv pip install -e .`) writes a `.pth` file pointing to the directory where `kotti/` was found. The move changes the directory structure but not the installed path entry.

**How to avoid:** Immediately after the `git mv` commit, run `uv pip install -e .` (or the equivalent). Verify with `python -c "import kotti; print(kotti.__file__)"` — must show `src/kotti/__init__.py`.

**Warning signs:** `kotti.__file__` path does not contain `/src/`; pytest discovers no tests after layout change.

### Pitfall 2: pytest addopts References Old Path

**What goes wrong:** The existing pytest.ini has `--ignore=kotti/templates/` and runs tests in `kotti/`. After the src layout move, these paths are wrong — pytest either finds nothing or recurses into wrong directories.

**Why it happens:** pytest.ini paths are relative to the config file location (project root). `kotti/` no longer exists at the project root after the move.

**How to avoid:** Update simultaneously with the layout move: `--ignore=src/kotti/templates/` and `testpaths = ["src/kotti"]`. Also change `--strict` to `--strict-markers` (the old flag was renamed and will error on pytest>=7).

**Warning signs:** `uv run pytest` finds 0 tests, or errors with "unrecognized arguments: --strict".

### Pitfall 3: pkg_resources Must Be Replaced Before Tests Pass

**What goes wrong:** `kotti/__init__.py` calls `pkg_resources.require("Kotti")[0].version` and `kotti/migrate.py` calls `pkg_resources.resource_filename("kotti", "alembic")`. These work fine in editable installs today but `pkg_resources` is deprecated and its `resource_filename` returns a filesystem path string — the replacement `importlib.resources.files()` returns a `Traversable`, breaking code that treats it as a string.

**Why it happens:** This is a Phase 2 item (`DEP-04`, `DEP-05`) but the src layout move in Phase 1 can surface it earlier if tests exercise these paths directly.

**How to avoid:** Phase 1 should NOT replace pkg_resources — that is Phase 2. However, verify that the existing `pkg_resources` code still works after the layout move and uv install. The alembic path `KOTTI_SCRIPT_DIR = pkg_resources.resource_filename("kotti", "alembic")` will point to `src/kotti/alembic` after reinstall — confirm this is what `test_migrate.py` expects.

**Warning signs:** `test_migrate.py::TestScriptDirectoryWithDefaultEnvPy::test_env_py_location` fails with path mismatch after layout move.

### Pitfall 4: check-manifest Must Be Removed Before Build

**What goes wrong:** `check-manifest` is in `development_requires` and `setup_requires`. After deleting setup.cfg (which contains the `[check-manifest]` stanza), any `check-manifest` invocation will error with no config found. More importantly, `setuptools_git` (in `setup_requires`) is the old VCS-integration mechanism — it must be removed.

**Why it happens:** The `[check-manifest]` section in setup.cfg configured what to ignore. Deleting setup.cfg without removing check-manifest usage from CI/Makefile leaves broken CI steps.

**How to avoid:** Search for `check-manifest` and `setuptools_git` usage in Makefile, CI workflows, pre-commit hooks, and remove all invocations. Neither tool is replaced — hatchling handles data inclusion and uv handles reproducibility.

**Warning signs:** CI step fails with `check-manifest: error: could not find setup.cfg or pyproject.toml [check-manifest] section`.

### Pitfall 5: extras_require Old Names Break User pip installs

**What goes wrong:** Existing Kotti users and Kotti add-on developers may have documented `pip install Kotti[development]` or `pip install Kotti[testing]` in their own setup files or docs. Removing these extra names breaks their installations silently (pip just ignores unknown extras with a warning).

**Why it happens:** The decision to use modern short names (`[dev]`, `[test]`, `[docs]`) is correct for new work but existing users reference the old names.

**How to avoid:** Keep the old names as aliases in `[project.optional-dependencies]`:
```toml
testing = ["kotti[test]"]
development = ["kotti[dev]"]
```
This requires zero extra maintenance and provides a clean transition path. Mark in CHANGES.txt that the new canonical names are `[test]`, `[docs]`, `[dev]`.

### Pitfall 6: uv.lock Missing Groups or Extras

**What goes wrong:** `uv lock` without flags only locks the base package. If the lock file was generated without `--all-extras` or explicit group flags, CI `uv sync --locked --group test` fails with "dependency not in lock".

**How to avoid:** Generate the initial lock with all extras and groups:
```bash
uv lock  # uv automatically includes all extras and dependency-groups in the lockfile
```
uv 0.5+ generates a universal lockfile that includes all groups and extras by default. Verify by checking that the lock file contains entries for test deps like `pytest` and `WebTest`.

---

## Code Examples

Verified patterns from Context7 and official docs:

### Complete pyproject.toml Skeleton for Kotti

```toml
# Source: Context7 /pypa/hatch, /llmstxt/astral_sh_uv_llms_txt

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "Kotti"
version = "2.1.0.dev0"
description = "A high-level, Pythonic web application framework based on Pyramid and SQLAlchemy."
readme = {file = "README.rst", content-type = "text/x-rst"}
requires-python = ">=3.10"
license = "BSD-derived (http://www.repoze.org/LICENSE.txt)"
authors = [
    {name = "Kotti Developers", email = "kotti@googlegroups.com"},
]
keywords = ["kotti", "web", "cms", "wcms", "pylons", "pyramid", "sqlalchemy", "bootstrap"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Framework :: Pylons",
    "Framework :: Pyramid",
    "License :: Repoze Public License",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
]
dependencies = [
    "Babel",
    "Chameleon>=2.7.4",
    "alembic>=0.8.0",
    "bcrypt",
    "bleach>=4,<5",        # replaced in Phase 2
    "bleach-allowlist",    # replaced in Phase 2
    "colander>=1.3.2",
    "deform==2.0.14",
    "docopt",
    "fanstatic>=1.0.0",
    "filedepot",
    "formencode>=2.0.0a",
    "html2text",
    "iso8601>=0.1.13",
    "js.angular",
    "js.bootstrap>=3.0.0",
    "js.deform==2.0.14",
    "js.fineuploader",
    "js.html5shiv",
    "js.jquery<2.0.0.dev",
    "js.jquery_form",
    "js.jquery_tablednd",
    "js.jquery_timepicker_addon",
    "js.jqueryui>=1.8.24",
    "js.jqueryui_tagit",
    "lingua>=1.3",
    "pyramid>=1.9,<2",     # Pyramid 2.0 removed pyramid.compat; upgrade is a separate milestone
    "pyramid_beaker",
    "pyramid_chameleon",
    "pyramid_deform>=0.2a3",
    "pyramid_mailer",
    "pyramid_tm",
    "pyramid_zcml>=1.1.0",
    "repoze.lru",
    "repoze.workflow>=1.0b1",
    "repoze.zcml>=1.0b1",
    "sqlalchemy>=1.4.16,<2",  # SA 2.0 removed declarative_base/baked queries; separate milestone
    "sqlalchemy-utils>=0.37.6",
    "transaction>=1.1.0",
    "unidecode",
    "waitress",
    "zope.deprecation",
    "zope.interface",
    "zope.sqlalchemy",
]

[project.urls]
Homepage = "http://kotti.pylonsproject.org/"
Repository = "https://github.com/Kotti/Kotti"
Changelog = "https://github.com/Kotti/Kotti/blob/master/CHANGES.txt"

[project.scripts]
kotti-migrate = "kotti.migrate:kotti_migrate_command"
kotti-reset-workflow = "kotti.workflow:reset_workflow_command"
kotti-migrate-storage = "kotti.filedepot:migrate_storages_command"

[project.entry-points."paste.app_factory"]
main = "kotti:main"

[project.entry-points."fanstatic.libraries"]
kotti = "kotti.fanstatic:lib_kotti"

[project.entry-points."pytest11"]
kotti = "kotti.tests"

[project.optional-dependencies]
# New canonical names
test = [
    "WebTest",
    "Pillow",
    "pyquery",
    "pytest>=8",
    "pytest-cov",
    "zope.testbrowser>=5.0.0",
]
docs = [
    "Sphinx",
    "docutils",
    "repoze.sphinx.autointerface",
    "sphinx_rtd_theme",
]
dev = [
    "kotti[test]",
    "kotti[docs]",
    "pipdeptree",
    "pyramid_debugtoolbar",
]
# Deprecated aliases — preserved for backward compatibility
testing = ["kotti[test]"]
development = ["kotti[dev]"]

# --- Build ---

[tool.hatch.build.targets.wheel]
packages = ["src/kotti"]
# Hatchling includes ALL files under src/kotti/ by default (templates, locale, static, alembic, zcml)
# No additional include patterns needed.

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/AUTHORS.txt",
    "/CHANGES.txt",
    "/CONTRIBUTORS.txt",
    "/README.rst",
    "/LICENSE.txt",
    "/COPYRIGHT.txt",
    "/app.ini",
    "/development.ini",
]

# --- pytest ---

[tool.pytest.ini_options]
addopts = [
    "--ignore=src/kotti/templates/",
    "--capture=no",
    "--strict-markers",
    "--tb=native",
    "--cov=kotti",
    "--cov-report=term-missing",
]
testpaths = ["src/kotti"]
python_files = ["test_*.py"]
markers = [
    "user: mark test to be run as the given user",
    "slow: mark test to be run only with --runslow option",
]

# --- uv ---

[tool.uv]
# Package includes all extras/groups in the lockfile by default
```

### Verify Package Data in Built Wheel

```bash
# Build the wheel
uv build

# Inspect contents — confirm templates, locale, alembic, zcml are present
unzip -l dist/Kotti-2.1.0.dev0-py3-none-any.whl | grep -E "\.(pt|po|mo|zcml)$|alembic/"

# Install from wheel in fresh venv and verify no import errors
uv venv /tmp/test-kotti-wheel
uv pip install --python /tmp/test-kotti-wheel/bin/python dist/Kotti-2.1.0.dev0-py3-none-any.whl
/tmp/test-kotti-wheel/bin/python -c "import kotti; print(kotti.__file__)"
```

### Verify src Layout Install

```bash
# After git mv kotti/ src/kotti/ and reinstall:
uv pip install -e .
python -c "import kotti; print(kotti.__file__)"
# Expected: .../src/kotti/__init__.py

# Verify all six entry points are registered
python -c "
from importlib.metadata import entry_points
for group in ['paste.app_factory', 'fanstatic.libraries', 'console_scripts', 'pytest11']:
    eps = entry_points(group=group)
    kotti_eps = [ep for ep in eps if 'kotti' in ep.name or 'kotti' in str(ep.value)]
    print(f'{group}: {kotti_eps}')
"
```

### kotti.__version__ via importlib.metadata (Phase 1 addition)

```python
# Add to kotti/__init__.py to expose __version__ for backwards compat
# Keep existing get_version() for now — pkg_resources replacement is Phase 2
from importlib.metadata import version as _version, PackageNotFoundError as _PNF
try:
    __version__ = _version("Kotti")
except _PNF:
    __version__ = "unknown"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| setup.py + setup.cfg | pyproject.toml | PEP 517 (2017), mainstream ~2022 | Single declarative config file |
| MANIFEST.in | Build backend-specific include patterns | ~2022 with hatchling/flit adoption | Eliminated for hatchling projects |
| find_packages() | Explicit `packages = ["src/kotti"]` | With src layout adoption | More explicit, no accidental inclusions |
| tox | `uv run pytest` | uv 0.4+ (2024) | Faster, no tox.ini needed |
| pytest.ini | `[tool.pytest.ini_options]` in pyproject.toml | pytest 6+ (2020) | One fewer file |
| pip install | uv sync / uv pip install | uv 0.1+ (2023) | 10-100x faster, lockfile support |
| setuptools_git | Removed (not replaced) | ~2020 | VCS-based file discovery no longer needed |

**Deprecated/outdated:**
- `setup_requires`: Eliminated entirely — setuptools used this for build-time deps, PEP 517 backends handle this via `[build-system].requires`
- `setuptools_git`: Unmaintained; hatchling doesn't need VCS integration for file discovery
- `check-manifest`: Unnecessary when MANIFEST.in is gone; hatchling provides explicit include patterns
- `pytest-flake8`: Anti-pattern; linting should not be baked into the test runner
- `pytest.yield_fixture`: Removed in pytest 4.0; use `@pytest.fixture` with `yield` syntax
- `--strict` (pytest): Renamed to `--strict-markers` in pytest 6+

**New capabilities available:**
- `uv_build` backend (uv 0.5+, package `uv_build>=0.10.2`): uv's own native build backend for pure-Python projects with src layout. Investigated for Kotti but not recommended due to non-Python asset inclusion needs.
- `[dependency-groups]` (PEP 735, uv 0.5+): Separate from `[project.optional-dependencies]`; for project-internal dev tooling only.

---

## Open Questions

1. **Current extras_require: are `[testing]` or `[development]` used by any downstream Kotti add-ons?**
   - What we know: The current setup.py defines `extras_require={'testing': ..., 'development': ..., 'docs': ...}`. Multiple add-ons in the Kotti ecosystem install `Kotti[testing]` in their own test dependencies.
   - What's unclear: Whether any published Kotti add-on uses `Kotti[development]` in its install chain.
   - Recommendation: Keep both old names as aliases indefinitely. Zero cost, zero risk of breaking downstream.

2. **Should `kotti.tests` as pytest11 plugin require import of the full test suite at collection time?**
   - What we know: The `pytest11` entry point `kotti = kotti.tests` loads `kotti/tests/__init__.py` which registers fixtures. This currently works with the flat layout.
   - What's unclear: Whether the tests `__init__.py` has any absolute path assumptions that break under src layout.
   - Recommendation: Run `uv run pytest --co -q 2>&1 | head -20` after the layout move to verify fixture discovery.

3. **Does `uv lock` with current dependencies resolve cleanly for Python 3.10-3.13?**
   - What we know: `pyramid>=1.9,<2` and `sqlalchemy>=1.4,<2` both have known Python 3.12/3.13 compatibility concerns (raised in STATE.md).
   - What's unclear: Whether uv lock will error during resolution or produce a valid-but-broken lockfile.
   - Recommendation: Run `uv lock` early as a smoke test. If it fails, `uv lock --python 3.10` to identify the problematic constraint.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, version from `pytest>=6` in setup.py — upgrade to `>=8` in pyproject.toml) |
| Config file | `[tool.pytest.ini_options]` in pyproject.toml (Wave 0 creates this) |
| Quick run command | `uv run pytest src/kotti/tests/ -x -q` |
| Full suite command | `uv run pytest --cov=kotti --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | pyproject.toml is the only metadata source (no setup.py/setup.cfg) | smoke | `test -f pyproject.toml && test ! -f setup.py && test ! -f setup.cfg` | ❌ Wave 0 |
| PKG-02 | hatchling is the build backend | smoke | `python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert d['build-system']['build-backend']=='hatchling.build'"` | ❌ Wave 0 |
| PKG-03 | src layout: kotti.__file__ contains /src/ | smoke | `uv run python -c "import kotti; assert '/src/' in kotti.__file__, kotti.__file__"` | ❌ Wave 0 |
| PKG-04 | All six entry points registered | smoke | `uv run python -c "from importlib.metadata import entry_points; eps=entry_points(); assert any('kotti' in str(e) for e in eps.get('paste.app_factory',[]))"` | ❌ Wave 0 |
| PKG-05 | .pt/.po/.mo/.zcml/alembic in built wheel | integration | `uv build && unzip -l dist/Kotti-*.whl \| grep -cE '\.(pt\|po\|mo\|zcml)$$'` | ❌ Wave 0 |
| PKG-06 | setuptools_git and check-manifest absent from deps | smoke | `python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); deps=str(d); assert 'setuptools_git' not in deps and 'check-manifest' not in deps"` | ❌ Wave 0 |
| PKG-07 | setup.py and setup.cfg deleted | smoke | `test ! -f setup.py && test ! -f setup.cfg` | ❌ Wave 0 |
| PKG-08 | uv.lock committed and passes --check | smoke | `uv lock --check` | ❌ Wave 0 |

Additionally, success criterion 1 ("pip install kotti from the built wheel works in a fresh virtualenv") maps to an integration test:

| Criterion | Test Type | Command |
|-----------|-----------|---------|
| Fresh venv install, no import errors | integration/manual | `uv venv /tmp/kotti-test && uv pip install --python /tmp/kotti-test/bin/python dist/Kotti-*.whl && /tmp/kotti-test/bin/python -c "import kotti"` |
| pytest discovery works | smoke | `uv run pytest --co -q 2>&1 \| grep -c "test session starts"` |

### Sampling Rate

- **Per task commit:** `uv run pytest src/kotti/tests/ -x -q --no-cov` (fast, skips coverage overhead)
- **Per wave merge:** `uv run pytest --cov=kotti --cov-report=term-missing`
- **Phase gate:** Full suite green + `uv build` + wheel inspection before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `src/kotti/tests/test_packaging.py` — smoke tests for PKG-01 through PKG-08 (filesystem checks + entry point checks)
- [ ] `[tool.pytest.ini_options]` in `pyproject.toml` — pytest config must exist before tests run
- [ ] `uv sync --group test` — installs test dependencies before pytest can run

*(No existing test file covers the packaging requirements. The existing `test_migrate.py` validates `KOTTI_SCRIPT_DIR` path behavior, which is tangentially relevant to PKG-05 but does not directly validate wheel contents.)*

---

## Sources

### Primary (HIGH confidence)

- `/pypa/hatch` (Context7) — build backend config, entry points, include patterns, src layout, optional-dependencies
- `/llmstxt/astral_sh_uv_llms_txt` (Context7) — uv lock, dependency-groups, uv_build backend, sync commands
- Existing codebase inspection: `setup.py`, `setup.cfg`, `MANIFEST.in`, `pytest.ini`, `tox.ini`, `kotti/__init__.py`, `kotti/migrate.py`
- `.planning/research/STACK.md` — prior research on hatchling vs alternatives (HIGH confidence, 2026-02-27)
- `.planning/research/PITFALLS.md` — prior research on packaging migration pitfalls (HIGH confidence, 2026-02-27)

### Secondary (MEDIUM confidence)

- uv 0.7.13 (installed locally) confirms `uv build` command is available
- Context7 docs confirm `uv_build` requires `uv_build>=0.10.2` as separate package — verified as real but limited for non-Python assets

### Tertiary (LOW confidence)

- `uv_build` non-Python data include capabilities: Context7 shows `[tool.uv.build-backend]` with `module-root` and `data` keys but the `data` option is limited to headers/scripts types, not arbitrary directory trees. Confidence LOW that `uv_build` supports Kotti's full asset inclusion needs without custom config.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — hatchling is PyPA-standard, verified via Context7 official docs
- Architecture: HIGH — patterns verified from official hatchling and uv docs; codebase inspection confirms what assets exist
- Pitfalls: HIGH — based on codebase inspection (actual pkg_resources calls, actual pytest.ini options found) plus prior research
- uv_build assessment: MEDIUM — feature set confirmed via Context7, but "not recommended for Kotti" conclusion is based on docs reading + absence of clear data inclusion examples, not a live test

**Research date:** 2026-02-27
**Valid until:** 2026-05-27 (hatchling and uv are stable; lockfile format stable since uv 0.4)
