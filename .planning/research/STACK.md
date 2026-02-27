# Technology Stack: Kotti Modernization

**Project:** Kotti — Pyramid-based CMS framework
**Researched:** 2026-02-27
**Scope:** Packaging, tooling, and dev-experience modernization

---

## Current State (Baseline)

| Area | Current | Problem |
|------|---------|---------|
| Build system | `setup.py` + `setuptools_git` | Deprecated imperative format; `setuptools_git` unmaintained |
| Config scatter | `setup.py`, `setup.cfg`, `tox.ini`, `pytest.ini` | 4 separate files, no single source of truth |
| Linting | `pytest-flake8` (baked into test run) | Slow, deprecated plugin; flake8 itself largely superseded |
| Formatting | None | No enforced formatting |
| Import sorting | None | No enforced import order |
| Package manager | `pip` | No lockfile, no fast resolver, no workspace support |
| Test runner | `pytest 6+` via tox | tox config targets py36/py37/py38 (all EOL) |
| Python targets | 3.6–3.10 (classifiers), 3.6–3.8 (tox) | EOL versions, excludes 3.11/3.12/3.13 |
| Source layout | Flat (`kotti/` at repo root) | `find_packages()` can accidentally pick up test dirs; src layout is the current standard |
| Manifest | `MANIFEST.in` | Superseded by `pyproject.toml` + VCS integration |

---

## Recommended Stack

### Build Backend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **hatchling** | `>=1.25` | Build backend (replaces setup.py) | Ships with `hatch`, no config required for simple cases, first-class `pyproject.toml` citizen, supports src layout with zero friction. Backed by PyPA. Handles MANIFEST.in replacement via `[tool.hatch.build]`. |

**Why hatchling over alternatives:**
- **setuptools**: Still supported but requires more config for src layout; `setup.py`-style imperative logic is the thing we're moving away from. Use setuptools only if entry points or custom build steps require it — Kotti has neither that hatchling cannot handle.
- **flit**: Minimal, but opinionated against packages with entry points and non-pure-Python builds. Kotti has 6 entry points; flit is not a good fit.
- **hatchling**: Handles entry points natively in `pyproject.toml`, supports include/exclude patterns, src layout, and dynamic version reading. Best fit for Kotti.

Confidence: HIGH — hatchling is the PyPA-recommended default for new projects as of PEP 517 ecosystem maturation; setuptools remains viable but hatchling is clearly the forward momentum.

### Package Manager

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **uv** | `>=0.5` | Package management, venv, lockfiles | 10-100x faster than pip; replaces pip, pip-tools, virtualenv, and tox as task runner. Astral (ruff's creators). Active development, stable CLI. |

**uv replaces:**
- `pip install` → `uv pip install` or `uv sync`
- `pip-tools` / `requirements.txt` pinning → `uv lock` + `uv.lock`
- `virtualenv` / `python -m venv` → `uv venv`
- `tox` (for test matrix) → `uv run --python 3.11 pytest` or keep tox with uv executor

**Migration approach for Kotti:**
```bash
# Install uv (system-wide, one time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Replace: pip install -e ".[testing]"
uv sync --extra testing

# Replace: tox
# Option A: uv-native (no tox dependency)
uv run --python 3.11 pytest
uv run --python 3.12 pytest

# Option B: tox with uv executor (keeps tox.ini, faster)
# In tox.ini: set runner = uv
```

**Lockfile strategy:**
- Add `uv.lock` to version control for reproducible dev installs
- `uv.lock` is cross-platform and replaces the manual `requirements.txt`
- Keep `requirements.txt` as an optional export only (`uv pip compile`)

Confidence: HIGH — uv 0.4+ has stable lockfile format; the tool is production-ready.

### Linting and Formatting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **ruff** | `>=0.6` | Lint + format + import sort | Replaces flake8, isort, and black in one tool. Written in Rust; runs in milliseconds on the full Kotti codebase. Configures in `pyproject.toml`. |

**ruff replaces all of:**
- `pytest-flake8` (remove entirely — it bakes linting into the test run, which is an anti-pattern)
- `flake8` + any plugins
- `isort`
- `black` (via `ruff format`)

**Configuration in `pyproject.toml`:**
```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade (auto-modernize syntax)
    "C4",  # flake8-comprehensions
]
ignore = [
    "E501",  # line length handled by formatter
]

[tool.ruff.lint.per-file-ignores]
"kotti/tests/**" = ["F841"]  # local variable assigned but unused (common in tests)

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Critical: remove `--flake8` from pytest addopts in `pytest.ini`.** Linting must run separately from tests (as a CI step, pre-commit hook, or `uv run ruff check .`), not baked into pytest.

Confidence: HIGH — ruff is the dominant Python linter/formatter as of 2024-2025; replacing flake8+isort+black is the standard migration path.

### Test Runner

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | `>=8.0` | Test runner | Current stable; Kotti already uses pytest — this is a version upgrade, not a tool change |
| **pytest-cov** | `>=5.0` | Coverage | Stays; well-maintained |
| **WebTest** | latest | Integration test client | Stays |
| **pyquery** | latest | HTML parsing in tests | Stays |

**Remove from test dependencies:**
- `mock` — use `unittest.mock` from stdlib (Python 3.3+)
- `pytest-flake8` — replaced by ruff as separate step
- `pytest-virtualenv` — unlikely to be needed with uv-managed envs; audit usage before removing
- `tox` — remove from `tests_require`; it's a runner, not a test library

**pytest configuration moves to `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
addopts = [
    "--ignore=kotti/templates/",
    "--capture=no",
    "--strict-markers",
    "--tb=native",
    "--cov=kotti",
    "--cov-report=term-missing",
]
testpaths = ["src/kotti/tests"]  # after src layout migration
python_files = ["test_*.py"]
markers = [
    "user: mark test to be run as the given user",
    "slow: mark test to be run only with --runslow option",
]
```

Note: `--strict` is deprecated; replace with `--strict-markers`.

Confidence: HIGH — pytest 8.x is current stable, migration from pytest.ini is mechanical.

### Source Layout

**Adopt: `src/` layout**

```
kotti/                    (repo root)
├── src/
│   └── kotti/            (package — moves from kotti/ at root)
│       ├── __init__.py
│       ├── resources.py
│       └── tests/        (moves from kotti/tests/)
├── docs/
├── pyproject.toml        (single config file)
├── uv.lock
└── README.rst
```

**Why src layout:**
- Prevents the package from being accidentally importable without installation (avoids "works on my machine" bugs)
- `find_packages()` can pick up top-level test directories by mistake — src layout eliminates this
- Required by several modern tools (hatchling handles it with zero config)
- Industry standard as of 2022+

**Migration path:**
1. `mkdir -p src && git mv kotti src/kotti`
2. Update `pyproject.toml`: `packages = [{include = "kotti", from = "src"}]`
3. Update all CI commands to install with `uv sync`
4. Update pytest `testpaths` to point into `src/`
5. Verify entry points still resolve (they will — setuptools/hatchling handle this)

Confidence: HIGH — src layout is the standard; hatchling supports it natively.

### pyproject.toml Structure

Full consolidation: `setup.py` + `setup.cfg` + `tox.ini` + `pytest.ini` → single `pyproject.toml`.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "Kotti"
version = "2.0.10.dev0"  # or dynamic via hatchling
description = "A high-level, Pythonic web application framework based on Pyramid and SQLAlchemy."
readme = "README.rst"
license = {text = "BSD-derived (http://www.repoze.org/LICENSE.txt)"}
authors = [{name = "Kotti Developers", email = "kotti@googlegroups.com"}]
keywords = ["kotti", "web", "cms", "pylons", "pyramid", "sqlalchemy"]
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Framework :: Pyramid",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "Babel",
    "Chameleon>=2.7.4",
    "alembic>=1.8",
    "bcrypt",
    "nh3",                    # replaces bleach (deprecated)
    "colander>=1.3.2",
    "deform==2.0.14",
    "docopt",
    "fanstatic>=1.0.0",
    "filedepot",
    "formencode>=2.0.0a",
    "html2text",
    "iso8601>=0.1.13",
    # js.* packages stay for now (fanstatic out-of-scope)
    "lingua>=1.3",
    "pyramid>=1.9,<2",
    "pyramid_beaker",
    "pyramid_chameleon",
    "pyramid_deform>=0.2a3",
    "pyramid_mailer",
    "pyramid_tm",
    "pyramid_zcml>=1.1.0",
    "repoze.lru",
    "repoze.workflow>=1.0b1",
    "repoze.zcml>=1.0b1",
    "sqlalchemy>=1.4.16",
    "sqlalchemy-utils>=0.37.6",
    "transaction>=1.1.0",
    "unidecode",
    "waitress",
    "zope.deprecation",
    "zope.interface",
    "zope.sqlalchemy",
]

[project.optional-dependencies]
testing = [
    "WebTest",
    "Pillow",
    "pyquery",
    "pytest>=8",
    "pytest-cov>=5",
    "zope.testbrowser>=5.0.0",
]
development = [
    "pipdeptree",
    "pyramid_debugtoolbar",
    "ruff>=0.6",
]
docs = [
    "Sphinx",
    "docutils",
    "repoze.sphinx.autointerface",
    "sphinx-rtd-theme",
]

[project.urls]
Homepage = "https://kotti.pylonsproject.org/"

[project.entry-points."paste.app_factory"]
main = "kotti:main"

[project.entry-points."fanstatic.libraries"]
kotti = "kotti.fanstatic:lib_kotti"

[project.scripts]
kotti-migrate = "kotti.migrate:kotti_migrate_command"
kotti-reset-workflow = "kotti.workflow:reset_workflow_command"
kotti-migrate-storage = "kotti.filedepot:migrate_storages_command"

[project.entry-points."pytest11"]
kotti = "kotti.tests"

[tool.hatch.build.targets.sdist]
include = [
    "src/kotti",
    "README.rst",
    "AUTHORS.txt",
    "CHANGES.txt",
]

[tool.hatch.build.targets.wheel]
packages = ["src/kotti"]
```

Note: `MANIFEST.in` becomes unnecessary — hatchling's sdist target handles include/exclude declaratively.

Confidence: HIGH — PEP 621 (project metadata in pyproject.toml) is a finalized standard; all tools support it.

### CI: GitHub Actions

**Update from:**
- `actions/checkout@v2`, `actions/setup-python@v2` (outdated)
- Python matrix: 3.6, 3.7, 3.8, 3.9, 3.10 (three of these are EOL)
- `pip install -e ".[testing]"` (slow, no lockfile)

**Update to:**
- `actions/checkout@v4`, `actions/setup-python@v5`
- Python matrix: 3.10, 3.11, 3.12, 3.13
- `uv sync --extra testing` (fast, reproducible)
- Separate lint job: `uv run ruff check . && uv run ruff format --check .`

```yaml
# Example: .github/workflows/sqlite.yml (updated)
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra development
      - run: uv run ruff check .
      - run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --extra testing
      - run: uv run pytest
```

Confidence: HIGH for structure; MEDIUM for exact `astral-sh/setup-uv` action version (verify at https://github.com/astral-sh/setup-uv/releases).

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build backend | hatchling | setuptools | Setuptools works fine but requires more pyproject.toml boilerplate; hatchling is zero-config for src layout |
| Build backend | hatchling | flit | flit is minimal but poorly suited to projects with entry points beyond `console_scripts` |
| Linter | ruff | flake8 + isort + black | Three separate tools, slower, more config; ruff supersedes all three |
| Package manager | uv | pip + pip-tools | pip-tools gives lockfiles but no venv management, no speed improvement |
| Package manager | uv | poetry | poetry has its own resolver with known incompatibilities; uv follows pip semantics |
| Layout | src/ | flat (current) | Flat layout has subtle import-before-install bugs; src layout is the industry standard |
| Version pin strategy | `>=X` bounds | exact pins in pyproject.toml | Exact pins in project metadata cause install conflicts; lock via `uv.lock` instead |

---

## Key Dependency Changes

| Old | New | Reason |
|-----|-----|--------|
| `bleach>=4,<5` + `bleach-allowlist` | `nh3` | bleach is deprecated (2023); nh3 is its Rust-based successor by the same ecosystem |
| `mock` | `unittest.mock` (stdlib) | mock is stdlib since Python 3.3; the backport package is unnecessary |
| `pytest-flake8` | `ruff` (separate CI step) | pytest-flake8 is unmaintained; linting belongs in CI, not baked into pytest |
| `setuptools_git>=0.3` | (remove) | Modern setuptools + hatchling handle VCS file inclusion via `[tool.hatch.build]` |
| `check-manifest` | (remove) | MANIFEST.in replaced by hatchling build config |
| `iso8601` | `datetime` (stdlib) | Python 3.11+ has `datetime.fromisoformat()` that handles ISO 8601; verify usage first |
| `docopt` | `argparse` (stdlib) or `click` | docopt is unmaintained; verify usage before replacing |

Note on `bleach → nh3`: nh3 has a different API. It does not have a drop-in compatibility shim. Migration requires updating all call sites in `kotti/sanitizers.py`. This is not a one-line change but is straightforward.

---

## Installation (Post-Migration)

```bash
# Install uv (one time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up dev environment
git clone https://github.com/Kotti/Kotti
cd Kotti
uv sync --extra testing --extra development

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format --check .

# Build package
uv build
```

---

## Migration Sequence (Dependency Order)

The following order minimizes risk and keeps the package installable at each step:

1. **Add `pyproject.toml` (parallel to setup.py)** — hatchling reads both; start migrating metadata
2. **Remove `setup.py` and `setup.cfg`** — once pyproject.toml is complete and CI passes
3. **Move to src layout** — mechanical file move + path updates
4. **Add `uv.lock`** — `uv lock` generates it; commit to repo
5. **Replace pytest.ini + tox.ini** — move config into `pyproject.toml`, delete old files
6. **Add ruff, remove pytest-flake8** — add ruff to CI, remove from test deps
7. **Remove mock, replace with unittest.mock** — grep-and-replace across test files
8. **Replace bleach with nh3** — update `kotti/sanitizers.py` call sites
9. **Update GH Actions** — new action versions, new Python matrix, uv-based install
10. **Drop MANIFEST.in** — after confirming sdist includes correct files

Each step is independently testable. Steps 1-4 are the highest risk (packaging changes). Steps 5-9 are mechanical.

---

## Sources

- PEP 517 (build system interface), PEP 518 (build dependencies), PEP 621 (project metadata) — finalized Python standards
- hatchling documentation: https://hatch.pypa.io/latest/
- uv documentation: https://docs.astral.sh/uv/
- ruff documentation: https://docs.astral.sh/ruff/
- nh3 (bleach replacement): https://nh3.readthedocs.io/
- Python packaging user guide: https://packaging.python.org/en/latest/
- src layout rationale: https://hynek.me/articles/testing-packaging/

**Confidence notes:**
- Tool recommendations (hatchling, uv, ruff, pytest 8): HIGH — these are the dominant tools as of mid-2025 with no credible alternatives displacing them
- Specific version numbers (uv 0.5+, ruff 0.6+, pytest 8+): MEDIUM — versions stated are from training knowledge (cutoff Aug 2025); verify latest via `pip index versions <package>` or the project's GitHub releases before pinning in CI
- nh3 as bleach replacement: HIGH — bleach officially deprecated in favor of nh3 by the same maintainers
- src layout adoption: HIGH — industry consensus since 2021-2022, no meaningful dissent
