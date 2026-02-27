# Architecture Patterns: Python Package Modernization

**Domain:** Modernizing a complex Python CMS package (Kotti) with WSGI entry points, plugin system, console scripts, and test plugins
**Researched:** 2026-02-27
**Overall Confidence:** HIGH — pyproject.toml specification is stable and well-documented; src layout migration is a well-understood pattern

---

## Recommended Architecture

### Target Structure After Modernization

```
Kotti/
├── src/
│   └── kotti/
│       ├── __init__.py          # WSGI entry point (main), includeme hook
│       ├── alembic/             # Database migrations
│       ├── browser/             # (if refactored, currently kotti/views/)
│       ├── fanstatic.py         # fanstatic library registration
│       ├── filedepot.py         # File storage
│       ├── locale/              # i18n translation files
│       ├── migrate.py           # kotti-migrate console script target
│       ├── resources.py         # SQLAlchemy models, Node hierarchy
│       ├── security.py          # Auth, principals, ACL
│       ├── static/              # Static assets (fanstatic served)
│       ├── templates/           # Chameleon .pt templates
│       ├── tests/               # Test package (pytest11 entry point)
│       ├── traversal.py         # NodeTreeTraverser
│       ├── views/               # View layer
│       └── workflow.py          # kotti-reset-workflow console script target
├── docs/
├── pyproject.toml               # Single source of truth for packaging + tools
├── README.rst
├── AUTHORS.txt
├── CHANGES.txt
└── uv.lock                      # Lockfile (replaces requirements.txt)
```

The flat `kotti/` package directory moves to `src/kotti/`. Everything else (docs, config files, CI) stays at the repo root.

---

## Component Boundaries

| Component | Current Location | Post-Migration Location | Change Required |
|-----------|-----------------|------------------------|-----------------|
| Package source | `kotti/` | `src/kotti/` | Physical move only |
| Entry points | `setup.py entry_points={}` | `pyproject.toml [project.entry-points.*]` | Config translation |
| Build config | `setup.py` + `setup.cfg` | `pyproject.toml [build-system]` + `[project]` | Rewrite |
| Tool config | `pytest.ini`, `.coveragerc`, `tox.ini` | `pyproject.toml [tool.*]` | Consolidate |
| Dev dependencies | `tests_require`, `development_requires` | `pyproject.toml [project.optional-dependencies]` | Config translation |
| Package manifest | `MANIFEST.in` | `pyproject.toml` + `[tool.setuptools.package-data]` | Config translation |
| Lock file | `requirements.txt` | `uv.lock` | Replace with uv |

---

## Patterns to Follow

### Pattern 1: pyproject.toml Entry Points

The `[project.entry-points]` table in pyproject.toml is the canonical way to declare all entry point groups. Each group becomes a sub-table.

**Current `setup.py` entry_points:**
```python
entry_points={
    'paste.app_factory': [
        'main = kotti:main',
    ],
    'fanstatic.libraries': [
        'kotti = kotti.fanstatic:lib_kotti',
    ],
    'console_scripts': [
        'kotti-migrate = kotti.migrate:kotti_migrate_command',
        'kotti-reset-workflow = kotti.workflow:reset_workflow_command',
        'kotti-migrate-storage = kotti.filedepot:migrate_storages_command',
    ],
    'pytest11': [
        'kotti = kotti.tests',
    ],
}
```

**Equivalent `pyproject.toml`:**
```toml
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

**Key rules:**
- `console_scripts` maps to `[project.scripts]` (special shorthand)
- All other groups use `[project.entry-points."group.name"]`
- Groups with dots in the name must be quoted
- Values use string format `"module.path:callable"` (colon separator, not equals)
- The `pytest11` group registers conftest/fixtures for test plugins — identical mechanism

**Confidence: HIGH** — This is specified in PEP 517/518/621 and PyPA packaging guides.

---

### Pattern 2: Build Backend Choice

For Kotti's requirements, **setuptools** remains the correct build backend. Alternatives (hatch, flit, pdm) are excellent for pure-Python projects but setuptools handles Kotti's needs:

- `include_package_data = true` for templates, static files, locale directories
- MANIFEST.in-equivalent file inclusion rules
- Complex extras_require groups (testing, development, docs)
- The `setuptools_git` dependency can be dropped — setuptools now auto-discovers files in git repos

**pyproject.toml build-system section:**
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"
```

Or using the newer setuptools PEP 517 backend directly:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

**Drop `setuptools_git`** — modern setuptools (68+) uses `git ls-files` automatically when building sdists from a git repository. The `setup_requires = ['setuptools_git>=0.3']` line becomes unnecessary.

**Confidence: HIGH** — setuptools 68+ stable behavior, documented.

---

### Pattern 3: src Layout Migration for Existing Package

The src layout prevents importing the local package directory during testing (importlib machinery picks up the installed package instead), catching issues that flat layout hides.

**Migration steps:**
1. `mkdir src && git mv kotti src/kotti` — physical relocation
2. Update `pyproject.toml` to declare find_packages with `where = "src"`:
   ```toml
   [tool.setuptools.packages.find]
   where = ["src"]
   ```
3. Remove any `sys.path` manipulation in `setup.py` (none present in Kotti)
4. Update import in any `conftest.py` or `pytest.ini` that uses `testpaths`
5. Update CI commands if they reference `kotti/` paths directly

**What does NOT change:**
- All Python imports (`from kotti import ...`, `import kotti`) — unchanged
- Entry point references (`kotti:main`, `kotti.fanstatic:lib_kotti`) — unchanged
- Template paths that use `pkg_resources` or `importlib.resources` — unchanged
- Alembic migration scripts that import kotti models — unchanged (after install)

**Confidence: HIGH** — This is a well-documented migration with no Kotti-specific complications.

---

### Pattern 4: uv Integration

uv replaces pip and pip-tools. It reads pyproject.toml natively and generates `uv.lock`.

**Developer workflow after migration:**
```bash
# Install project with all dev extras
uv sync --extra testing --extra development

# Add a dependency
uv add some-package

# Run tests
uv run pytest

# Run a console script
uv run kotti-migrate

# Build sdist/wheel
uv build
```

**CI workflow after migration:**
```yaml
- uses: astral-sh/setup-uv@v4
- run: uv sync --extra testing
- run: uv run pytest
```

**`uv.lock` characteristics:**
- Replaces `requirements.txt` for reproducibility
- Cross-platform compatible (unlike pip-tools locks)
- Committed to git for reproducible CI
- `uv sync` is the equivalent of `pip install -r requirements.txt`

**Confidence: HIGH** — uv is stable (1.x) as of 2025; astral-sh/setup-uv is the canonical GHA action.

---

### Pattern 5: Consolidating Tool Configuration

All tool config that currently lives in separate files moves to `pyproject.toml`:

| Current File | Section in pyproject.toml | Notes |
|---|---|---|
| `pytest.ini` | `[tool.pytest.ini_options]` | Direct translation |
| `.coveragerc` | `[tool.coverage.run]` + `[tool.coverage.report]` | Direct translation |
| `setup.cfg` (mypy, flake8) | `[tool.mypy]`, `[tool.ruff]` | ruff replaces flake8 |
| `tox.ini` | Can stay or move to `pyproject.toml [tool.tox]` | tox 4+ supports pyproject.toml |

**Ruff replaces flake8 + isort + pyupgrade:**
```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]  # pycodestyle, pyflakes, isort, pyupgrade
```

**Confidence: HIGH** — ruff's config format is stable and well-documented.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Keeping setup.py Alongside pyproject.toml

**What:** Maintaining both `setup.py` and `pyproject.toml` during migration as a "transition state"
**Why bad:** Setuptools gives priority to `pyproject.toml` but will also read `setup.py`. The interaction is confusing, metadata can conflict, and it creates a false sense of partial completion.
**Instead:** Do the migration atomically in one commit. The migration is mechanical and can be prepared in a branch. Keep `setup.py` only if you need a custom build hook (Kotti does not).

---

### Anti-Pattern 2: Forgetting MANIFEST.in Equivalents

**What:** Migrating to pyproject.toml but not declaring non-Python files (templates, locale files, static assets)
**Why bad:** `sdist` builds will be missing `.pt` template files, `.mo`/`.po` locale files, and static assets. The installed package from PyPI will be broken.
**Instead:** Use `[tool.setuptools.package-data]`:
```toml
[tool.setuptools.package-data]
kotti = [
    "templates/**/*.pt",
    "templates/**/*.html",
    "static/**/*",
    "locale/**/*.mo",
    "locale/**/*.po",
    "alembic/**/*.py",
    "alembic/*.ini",
    "*.zcml",
    "workflow.zcml",
]
```
Or use `include-package-data = true` with a `MANIFEST.in` (which setuptools still reads).

**Confidence: HIGH** — This is the most common packaging migration mistake.

---

### Anti-Pattern 3: src Layout Without Installing the Package

**What:** Moving to src/ layout and running tests with `pytest` directly without installing the package (even in editable mode)
**Why bad:** `src/kotti` is not on `sys.path` by default. pytest will fail with `ModuleNotFoundError: No module named 'kotti'`.
**Instead:** Always install in editable mode first: `uv sync` or `pip install -e .`. With uv this is automatic in `uv run pytest`. CI must run `uv sync` before `uv run pytest`.

**Confidence: HIGH** — Fundamental src layout constraint.

---

### Anti-Pattern 4: Dropping `include_package_data` Without Verifying

**What:** Assuming pyproject.toml's auto-discovery handles all the files that `include_package_data = True` + `MANIFEST.in` handled
**Why bad:** setuptools auto-discovery in pyproject.toml mode is more conservative. Files not in explicit `package-data` declarations or `MANIFEST.in` will be excluded from sdist.
**Instead:** After migration, run `python -m build --sdist` and inspect the resulting `.tar.gz` to verify all templates, locales, and static files are present. Do this before publishing to PyPI.

---

### Anti-Pattern 5: Changing Entry Point Names During Migration

**What:** Renaming entry points (e.g., changing `paste.app_factory` key from `main` to `kotti`) to "clean things up"
**Why bad:** Any `development.ini` or `production.ini` that references `use = egg:Kotti#main` will break for all existing users.
**Instead:** Preserve exact entry point names. The migration is purely a config format change; names must be identical.

**Confidence: HIGH** — Paste Deploy resolution is name-sensitive.

---

## Migration Order (Dependencies)

This sequence is critical. Steps with dependencies must be sequential; steps marked "parallel" can be done simultaneously.

```
Step 1: CREATE pyproject.toml (parallel with Step 2)
  ├── [project] metadata (from setup.py header)
  ├── [project.dependencies] (from install_requires)
  ├── [project.optional-dependencies] (from extras_require)
  ├── [project.scripts] (from console_scripts)
  ├── [project.entry-points.*] (all other entry_points)
  └── [build-system] with setuptools>=68

Step 2: CONSOLIDATE tool config (parallel with Step 1)
  ├── pytest config → [tool.pytest.ini_options]
  ├── coverage config → [tool.coverage.*]
  └── ruff config → [tool.ruff.*]

Step 3: REMOVE setup.py + setup.cfg (depends on Step 1 complete)
  ├── Verify pyproject.toml is complete
  ├── Run: python -m build --sdist && tar -tzf dist/*.tar.gz | sort
  ├── Verify all .pt, .po, .mo, .zcml, .ini files present in sdist
  └── Remove setup.py, setup.cfg, setup_requires deps

Step 4: MIGRATE to src layout (depends on Step 3 complete)
  ├── mkdir src && git mv kotti src/kotti
  ├── Add [tool.setuptools.packages.find] where = ["src"]
  ├── pip install -e . (or uv sync)
  └── Run full test suite — must pass before proceeding

Step 5: UPDATE CI (depends on Step 4 complete)
  ├── Add astral-sh/setup-uv action
  ├── Replace pip install with uv sync
  ├── Replace pytest with uv run pytest
  ├── Replace flake8/isort with ruff check + ruff format
  └── Update Python version matrix to 3.10-3.13

Step 6: GENERATE uv.lock (depends on Step 5 complete)
  ├── uv lock
  ├── Commit uv.lock
  └── Verify CI uses uv.lock for reproducibility
```

**Steps 1 and 2 are independent** — can be done in parallel branches or sequentially in one branch.

**Step 3 is the point of no return** — once setup.py is removed, all tooling must work via pyproject.toml.

**Step 4 (src layout) is the highest-risk step** — it changes filesystem layout and requires all consumers (CI, local dev, tox) to install the package before importing.

---

## Risk Areas During Migration

### Risk 1: MANIFEST.in → package-data Incomplete (HIGH RISK)

**What could break:** Published PyPI sdist missing template files, locale files, or ZCML files. Users who install from sdist (not wheel) get a broken install.

**Detection:** Inspect sdist contents before publishing:
```bash
python -m build --sdist
tar -tzf dist/Kotti-*.tar.gz | grep -E '\.(pt|po|mo|zcml|ini)$' | sort
```
Compare against current MANIFEST.in.

**Mitigation:** Keep `MANIFEST.in` alongside `pyproject.toml` initially (setuptools reads both). Remove MANIFEST.in only after verifying sdist contents are correct.

---

### Risk 2: pytest11 Entry Point Breaks Test Discovery (MEDIUM RISK)

**What could break:** The `pytest11 = kotti = kotti.tests` entry point registers Kotti's conftest/fixtures as a pytest plugin. After src layout migration, if the package isn't installed, pytest can't find `kotti.tests`.

**Detection:** Run `pytest --co -q` (collect-only) after migration. If fixtures from `kotti.tests` are not found, the entry point isn't loading.

**Mitigation:** Always ensure `pip install -e .` (or `uv sync`) is run before pytest. In CI, `uv sync --extra testing` must precede `uv run pytest`. Never run `python -m pytest` without installing first.

---

### Risk 3: fanstatic.libraries Entry Point Version Sensitivity (MEDIUM RISK)

**What could break:** `fanstatic>=1.0.0` discovers library entry points at import time using `pkg_resources` or `importlib.metadata`. If the entry point metadata isn't picked up correctly after migration (e.g., editable install mode differences), fanstatic won't find `lib_kotti` and static assets won't be served.

**Detection:** After migration, run the development server and check that CSS/JS assets load. `fanstatic` logs a warning when libraries aren't found.

**Mitigation:** Test fanstatic asset serving as part of the smoke test after Step 4. Editable installs with pyproject.toml use `importlib.metadata` which is correct for fanstatic 1.x.

---

### Risk 4: paste.app_factory Entry Point Name Sensitivity (LOW-MEDIUM RISK)

**What could break:** Any deployment ini file that contains `use = egg:Kotti#main` will break if the `paste.app_factory` entry point key is renamed or the package name changes.

**Detection:** Search existing documentation and example ini files for `egg:Kotti#main` references.

**Mitigation:** The key `main` must be preserved exactly. In pyproject.toml:
```toml
[project.entry-points."paste.app_factory"]
main = "kotti:main"
```
This is a direct translation — no name changes.

---

### Risk 5: setuptools_git Removal Breaks sdist in Non-Git Environments (LOW RISK)

**What:** `setuptools_git` was used to include only git-tracked files in sdists. Without it, setuptools falls back to auto-discovery, which includes everything not in `.gitignore`.

**Detection:** Build sdist in a clean checkout and compare file count to previous builds.

**Mitigation:** Modern setuptools (68+) uses `git ls-files` natively when `git` is available. RTD builds used `setuptools-git` in `docs_require` specifically to handle RTD's non-git environment. After migration, RTD uses `pyproject.toml` natively and this workaround is no longer needed.

---

### Risk 6: Python 3.10-3.13 Compatibility in Dependencies (MEDIUM RISK)

**What could break:** Several dependencies pinned to old versions may not support Python 3.11+. Key suspects:
- `deform==2.0.14` (pinned; newer versions may exist)
- `js.deform==2.0.14` (pinned; matches deform)
- `js.jquery<2.0.0.dev` (heavily pinned)
- `pyramid>=1.9,<2` (Pyramid 1.x; Python 3.11 compatibility uncertain)
- `pyramid_beaker` (unclear Python 3.11+ status)
- `bleach>=4,<5` (deprecated; replacement needed)

**Detection:** Run `uv sync` against Python 3.12. Resolution failures or deprecation warnings identify problem packages.

**Mitigation:** Address dependency upgrades as a separate task after pyproject.toml migration. The packaging migration does not require changing dependency versions — do them separately to isolate failures.

---

## Scalability Considerations

| Concern | Current | After Migration |
|---------|---------|-----------------|
| Build reproducibility | requirements.txt (partial) | uv.lock (complete, cross-platform) |
| Dependency resolution | pip (slow, no lock) | uv (fast, locked) |
| Multi-Python testing | tox + manual matrix | uv + GitHub Actions matrix |
| Local dev setup | `pip install -e .[testing]` | `uv sync --extra testing` |
| CI caching | pip cache | uv cache (faster) |

---

## Full pyproject.toml Skeleton

For reference — the complete structure after migration:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "Kotti"
version = "2.0.10dev0"
description = "A high-level, Pythonic web application framework based on Pyramid and SQLAlchemy."
readme = {file = "README.rst", content-type = "text/x-rst"}
license = {text = "BSD-derived (http://www.repoze.org/LICENSE.txt)"}
authors = [{name = "Kotti Developers", email = "kotti@googlegroups.com"}]
keywords = ["kotti", "web", "cms", "pylons", "pyramid", "sqlalchemy"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Framework :: Pyramid",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
]
requires-python = ">=3.10"
dependencies = [
    "Babel",
    "Chameleon>=2.7.4",
    "alembic>=0.8.0",
    "bcrypt",
    # "bleach>=4,<5",  # DEPRECATED — replace with nh3
    "nh3",            # replacement for bleach
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
    "pytest>=6",
    "pytest-cov",
    "pytest-virtualenv",
    "zope.testbrowser>=5.0.0",
    # "mock",  # REMOVED — use unittest.mock (stdlib since Python 3.3)
    # "pytest-flake8",  # REMOVED — replaced by ruff
]
development = [
    "pipdeptree",
    "pyramid_debugtoolbar",
    "kotti-tinymce>=0.7.0",
    # "check-manifest",  # REMOVED — unnecessary with pyproject.toml
]
docs = [
    "Sphinx",
    "docutils",
    "repoze.sphinx.autointerface",
    "sphinx_rtd_theme",
    "pytest>=6",
]

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

[project.urls]
Homepage = "http://kotti.pylonsproject.org/"
Repository = "https://github.com/Kotti/Kotti"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
kotti = [
    "templates/**/*.pt",
    "templates/**/*.html",
    "static/**/*",
    "locale/**/*.mo",
    "locale/**/*.po",
    "alembic/**/*.py",
    "alembic/alembic.ini",
    "*.zcml",
]

[tool.pytest.ini_options]
testpaths = ["src/kotti/tests"]
addopts = "--cov=kotti --cov-report=term-missing"

[tool.coverage.run]
source = ["kotti"]
branch = true

[tool.coverage.report]
show_missing = true

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
# E = pycodestyle errors
# F = pyflakes
# I = isort
# UP = pyupgrade (e.g., Union[X, Y] -> X | Y)
# B = flake8-bugbear
```

---

## Sources

- PEP 517/518/621 — Python packaging standards (pyproject.toml spec)
- PyPA Packaging Guide — src layout discussion, entry points specification
- setuptools documentation — package discovery, package-data, build backend
- uv documentation (Astral) — sync, lock, run commands
- Paste Deploy documentation — paste.app_factory entry point convention
- pytest documentation — pytest11 entry point plugin registration
- fanstatic documentation — fanstatic.libraries entry point convention

**Confidence levels:**

| Area | Confidence | Basis |
|------|------------|-------|
| pyproject.toml entry points syntax | HIGH | PEP 621 specification, stable since 2021 |
| src layout migration steps | HIGH | Well-documented pattern, no Kotti-specific complications |
| Build backend recommendation (setuptools) | HIGH | Kotti's non-Python assets require setuptools features |
| uv integration | HIGH | uv 1.x is stable; standard GHA pattern |
| Risk: MANIFEST.in → package-data | HIGH | Most common migration failure mode |
| Risk: fanstatic entry point | MEDIUM | fanstatic 1.x behavior with importlib.metadata not directly verified |
| Risk: Python 3.11+ dep compatibility | MEDIUM | Specific dep versions not verified against Python 3.12+ |
