# Domain Pitfalls: Python Project Modernization

**Project:** Kotti CMS Modernization
**Domain:** Open-source Python package modernization (PyPI-published, existing users)
**Researched:** 2026-02-27
**Confidence:** HIGH — based on direct codebase inspection plus established Python packaging knowledge

---

## Critical Pitfalls

Mistakes that cause rewrites, broken installs, or broken production deployments for existing users.

---

### Pitfall 1: pkg_resources Removal Breaks Version Lookup and Alembic Script Discovery

**What goes wrong:** Kotti uses `pkg_resources` in two critical places:
1. `kotti/__init__.py` line 164: `pkg_resources.require("Kotti")[0].version` — exposed as `get_version()`, used in templates and debug output
2. `kotti/migrate.py` line 57: `pkg_resources.resource_filename("kotti", "alembic")` — discovers the Alembic migration script directory at runtime

When migrating to pyproject.toml and/or the src layout, if `pkg_resources` is replaced with `importlib.metadata` and `importlib.resources` without understanding the behavioral differences, the Alembic `KOTTI_SCRIPT_DIR` path will break because `importlib.resources` uses a different API for path-like access to package data.

**Why it happens:** `pkg_resources.resource_filename()` returns a filesystem path string. The `importlib.resources` equivalent (`importlib.resources.files("kotti").joinpath("alembic")`) returns a `Traversable`, not a string path. Code that passes the result to `os.path.join()` or string operations will silently fail or raise `TypeError`.

**Consequences:**
- `kotti-migrate` console script fails on any installation
- Alembic migrations cannot find their scripts, breaking database upgrade workflows
- `get_version()` raises `PackageNotFoundError` if the package is not installed (e.g., editable install in development without a build step)

**Prevention:**
- Replace `pkg_resources.resource_filename("kotti", "alembic")` with:
  ```python
  from importlib.resources import files
  KOTTI_SCRIPT_DIR = str(files("kotti") / "alembic")
  ```
  Or use `importlib.resources.as_file()` context manager for temporary path access.
- Replace `pkg_resources.require("Kotti")[0].version` with:
  ```python
  from importlib.metadata import version
  def get_version():
      return version("Kotti")
  ```
- Do the same in `docs/conf.py` which also uses `pkg_resources.get_distribution("Kotti").version`
- Test the `kotti-migrate list_all` and `kotti-migrate upgrade_all` commands explicitly after this change — not just `pytest`

**Detection:** After migration, run `kotti-migrate list_all` in a fresh virtualenv. If it errors with `TypeError` or `AttributeError`, the resource path API is wrong.

**Phase:** Packaging migration phase (setup.py → pyproject.toml)

---

### Pitfall 2: pyramid.compat Removal Breaks on Pyramid 1.x Retention

**What goes wrong:** Kotti imports from `pyramid.compat` in three production files:
- `kotti/sqla.py`: `from pyramid.compat import json`
- `kotti/traversal.py`: `from pyramid.compat import decode_path_info`, `from pyramid.compat import is_nonstr_iter`
- `kotti/views/edit/default_views.py`: `from pyramid.compat import map_`

`pyramid.compat` was removed in Pyramid 2.0. The project currently pins `pyramid>=1.9,<2`, so these imports work today. If any modernization step causes the upper bound to be dropped or Pyramid 2.0 to be installed, **the application will fail to import entirely** — a hard crash, not a deprecation warning.

**Why it happens:** Upgrading to Pyramid 2.0 is explicitly out of scope for this milestone, but well-intentioned dependency unpinning ("let's not use `<2`") or a transitive dependency upgrade can accidentally pull it in.

**Consequences:**
- `ImportError: cannot import name 'json' from 'pyramid.compat'` on startup
- Complete application failure — no graceful degradation

**Prevention:**
- Keep the `pyramid>=1.9,<2` upper bound strictly in pyproject.toml; do not relax it during this milestone
- Document this constraint explicitly in pyproject.toml with a comment: `# Pyramid 2.0 removed pyramid.compat; upgrade is a separate milestone`
- Before replacing `pyramid.compat` imports, ensure you are committed to Pyramid 2.0 (a separate milestone)
- Replacements when that time comes: `json` → `import json`, `decode_path_info` → `urllib.parse.unquote_to_bytes`, `is_nonstr_iter` → custom check, `map_` → `map`

**Detection:** After any dependency change, run `python -c "import kotti"` in a clean environment to catch import errors immediately.

**Phase:** Dependencies update phase — treat Pyramid version pin as a hard constraint, not a target

---

### Pitfall 3: src Layout Migration Breaks Entry Points and pytest11 Plugin

**What goes wrong:** Kotti has four entry points that are resolved by package name at install time:
```
paste.app_factory = kotti:main
fanstatic.libraries = kotti = kotti.fanstatic:lib_kotti
console_scripts = kotti-migrate, kotti-reset-workflow, kotti-migrate-storage
pytest11 = kotti = kotti.tests
```

Moving source files from `kotti/` at the project root to `src/kotti/` requires build backend configuration (`[tool.setuptools.packages.find] where = ["src"]`) AND a reinstall of the package. If the package is installed in editable mode without reinstalling after the layout change, the old flat-layout path remains registered in the `.pth` file, creating an import ambiguity where two `kotti` packages may be visible.

**Why it happens:** Editable installs create path entries pointing to the package location. After moving to src layout, an old `pip install -e .` before the layout change leaves a stale `.pth` file pointing to the project root, where `kotti/` no longer exists (or coexists with `src/kotti/`). Python resolves whichever it finds first.

**Consequences:**
- `pytest --co` discovers no tests (pytest11 plugin not loaded from correct path)
- `kotti-migrate` runs but cannot find `kotti.alembic` (wrong package root)
- Fanstatic library entry point fails to resolve at server startup
- CI works while local dev is broken (or vice versa) depending on install state

**Prevention:**
- When moving to src layout, explicitly uninstall and reinstall: `pip uninstall Kotti && pip install -e .`
- With uv: `uv pip install -e .` handles this correctly
- Verify with `python -c "import kotti; print(kotti.__file__)"` — must show path inside `src/`
- The `pytest.ini` `addopts` includes `kotti/` as the test path — this must be updated to `src/kotti/` after the layout change, or tests won't be discovered
- The `--ignore=kotti/templates/` option in pytest.ini must also be updated to `--ignore=src/kotti/templates/`

**Detection:** After layout migration, `python -c "import kotti; print(kotti.__file__)"` should show `src/kotti/__init__.py`. Any path not containing `src/` indicates the old install is still active.

**Phase:** Packaging migration phase — do layout migration and entry-point verification together

---

### Pitfall 4: bleach → nh3 Is Not a Drop-In Replacement

**What goes wrong:** The migration plan lists `bleach → nh3` as a "drop-in replacement," but the APIs are substantially different:

- `bleach.clean(html, tags=..., attributes=..., styles=..., strip=True)` — positional/keyword args API
- `nh3.clean(html, tags=..., attributes=..., strip_comments=True)` — no `styles` parameter; `attributes` takes `dict[str, set[str]]` not `dict[str, list]` or callable

Current `kotti/sanitizers.py` uses `bleach.clean()` with:
1. `attributes=lambda self, key, value: True` — a callable that always returns True; nh3 does not support callable `attributes`
2. `styles=all_styles` — nh3 has no `styles` argument; CSS handling is done differently

Additionally, `bleach_allowlist` is a companion library to `bleach` that provides curated tag/attribute lists. It has no direct equivalent for nh3. The lists themselves (like `generally_xss_safe`, `markdown_tags`, `markdown_attrs`) would need to be manually maintained or sourced differently.

**Why it happens:** `nh3` is the recommended sanitizer after bleach's deprecation, but it was rewritten in Rust (via ammonia) and has a deliberately simpler API that doesn't replicate bleach's more complex features.

**Consequences:**
- `xss_protection()` sanitizer silently drops CSS style attributes it should preserve (or crashes trying to use unsupported API)
- `minimal_html()` loses style handling
- Existing content sanitized with bleach may be re-sanitized differently when fetched (if sanitize-on-read is added), causing data mutations

**Prevention:**
- Before switching, write characterization tests: run `xss_protection()`, `minimal_html()`, and `no_html()` on a comprehensive set of test HTML inputs with bleach, capture outputs, then use these as expected outputs when testing the nh3 implementation
- The callable `attributes` pattern in `xss_protection()` must be replaced with an explicit allowlist of attribute names in nh3's format
- Consider `bleach` → `bleach` (upgrading to 6.x for Python 3.10+ compat) as a lower-risk first step if nh3 API differences prove too large for this milestone
- Check whether `bleach-allowlist` works with newer bleach before abandoning it entirely
- `bleach_allowlist` also needs replacement — either bundle the lists directly or find an equivalent

**Detection:** Run the existing `kotti/tests/test_sanitizers.py` suite after any sanitizer change. A passing test suite does not guarantee identical HTML output — add explicit output-comparison tests.

**Phase:** Dependency replacement phase — treat as a focused sub-task with its own test coverage gate

---

### Pitfall 5: Dropping Python 3.6–3.9 Without Auditing All Compatibility Shims

**What goes wrong:** The codebase was written for Python 3.6+ and accumulated compatibility patterns that are either wrong or unnecessary on Python 3.10+:

1. **`Union[int, "NoneType"]` strings** — The string `"NoneType"` is a forward-reference string that was never valid (NoneType is not importable by that name). These should be `Optional[int]`. On Python 3.10+, the preferred form is `int | None`. Found in: `kotti/security.py`, `kotti/filedepot.py`, `kotti/resources.py`, `kotti/fanstatic.py`.

2. **`declarative_base()` from `sqlalchemy.ext.declarative`** — This import path was deprecated in SQLAlchemy 1.4 and removed in SQLAlchemy 2.0. Used in `kotti/__init__.py` and `kotti/sqla.py`. If SQLAlchemy is upgraded to 2.0+ during this milestone, this breaks.

3. **`sqlalchemy.ext.baked`** — Baked queries (`bakery`, `bake_lazy_loaders()`) were deprecated in SQLAlchemy 1.4 and removed in SQLAlchemy 2.0. Used in `kotti/sqla.py`.

4. **`pytest.yield_fixture`** — Used in `kotti/tests/__init__.py` (line 70). `yield_fixture` was deprecated in pytest 3.0 and removed in pytest 4.0. The current `pytest>=6` requirement allows this to be silently ignored, but when upgrading to latest pytest, this becomes an error.

5. **`--strict` in pytest addopts** — In newer pytest, this flag was renamed to `--strict-markers`. When upgrading pytest, this causes a startup error.

**Why it happens:** These compatibility artifacts accumulate over years of "it works, don't touch it" maintenance. Dropping old Python versions creates an opportunity to clean them up, but the cleanup itself is risky if done carelessly.

**Consequences:**
- SQLAlchemy 2.0 upgrade (not in scope, but might happen via transitive upgrades) causes `ImportError` at startup
- Type checker runs (if added) report errors that are harder to fix than expected
- Test suite fails to start with newer pytest due to `--strict` flag

**Prevention:**
- Pin SQLAlchemy to `>=1.4,<2` for this milestone — explicitly note that SA 2.0 upgrade is a separate effort
- Fix `Union[int, "NoneType"]` → `Optional[int]` as a purely mechanical cleanup (safe, no runtime impact)
- Fix `yield_fixture` → `@fixture` with `yield` as part of the pytest/CI modernization phase
- Fix `--strict` → `--strict-markers` in pytest.ini when updating the test configuration
- Do NOT upgrade SQLAlchemy to 2.0 during this milestone; that requires the baked query removal and declarative_base migration as well

**Detection:** After dropping Python 3.6–3.9 from classifiers and CI, run `python -W error::DeprecationWarning -c "import kotti"` to surface deprecation warnings that will become errors in future dependency versions.

**Phase:** Python version and CI modernization phase — fix shims as part of that phase, not as a separate cleanup

---

## Moderate Pitfalls

Mistakes that cause user-facing breakage or require significant rework.

---

### Pitfall 6: MANIFEST.in Becomes Irrelevant but Non-Obvious Data Inclusion Issues Appear

**What goes wrong:** `MANIFEST.in` controls what gets included in the sdist for setup.py builds. With pyproject.toml and modern setuptools, the equivalent is `[tool.setuptools.package-data]` or `include_package_data = true` with a `.gitattributes` or `MANIFEST.in` that is now secondary.

Kotti's package data includes locale files (`.po`, `.mo`), templates (`.pt` Chameleon templates), static files, Alembic migration scripts, and the workflow ZCML file. These are all required at runtime. If `include_package_data` is not configured correctly in pyproject.toml, the installed package on PyPI will be missing these files — the package installs successfully but fails at runtime with `FileNotFoundError`.

**Why it happens:** Modern setuptools with pyproject.toml still respects `include_package_data = true` when a `MANIFEST.in` exists, but the mental model shifts. Developers may assume file inclusion "just works" and only discover missing files after publishing to PyPI (not in editable installs, where the source tree is used directly).

**Prevention:**
- In pyproject.toml, explicitly list non-Python data with `[tool.setuptools.package-data]`:
  ```toml
  [tool.setuptools.package-data]
  kotti = [
      "locale/**/*",
      "templates/**/*",
      "static/**/*",
      "alembic/**/*",
      "*.zcml",
  ]
  ```
- Or set `include-package-data = true` and keep or update `MANIFEST.in`
- After building a wheel (`python -m build`), inspect it: `unzip -l dist/Kotti-*.whl | grep -E "locale|templates|static|alembic|zcml"` to confirm all expected files are present
- Test the built wheel in a fresh virtualenv before releasing to PyPI

**Detection:** Build a wheel, install it in a fresh venv (not editable), and run `from kotti import main` followed by an application startup. Missing locale files cause silent i18n failures; missing templates cause `TemplateNotFound` at request time.

**Phase:** Packaging migration phase — final gate before any test PyPI upload

---

### Pitfall 7: mock → unittest.mock Import Change Breaks Tests Silently in Some Cases

**What goes wrong:** Six test files import from `mock` (the standalone package):
- `kotti/tests/__init__.py`: `from mock import MagicMock`
- `kotti/tests/test_security.py`: `from mock import patch`
- `kotti/tests/test_views_form.py`: `from mock import MagicMock`, `from mock import patch`
- `kotti/tests/test_tags.py`: `from mock import Mock`
- `kotti/tests/test_security_views.py`: `from mock import Mock`, `from mock import patch`
- `kotti/tests/test_functional.py`: `from mock import patch`
- `kotti/tests/test_message.py`: `from mock import patch`

The standalone `mock` package is a backport of `unittest.mock` and was kept in sync with the stdlib version. For Python 3.10+, `mock` and `unittest.mock` are functionally equivalent, so replacing `from mock import X` with `from unittest.mock import X` is safe. However, `mock` in `tests_require` must also be removed — if it stays and is installed, it may shadow `unittest.mock` in edge cases.

The hidden risk: `kotti/tests/test_security.py` has a conditional import fallback:
```python
try:
    import mock
except ImportError:
    from unittest import mock
```
This pattern will always use the `mock` package as long as it's installed. After removing `mock` from `tests_require`, this fallback correctly falls to `unittest.mock` — but only if `mock` is not installed transitively by another test dependency.

**Prevention:**
- Replace all `from mock import X` with `from unittest.mock import X` across all 7 files
- Remove `mock` from `tests_require` in pyproject.toml
- Remove the try/except import fallback in `test_security.py` — it is no longer needed
- Verify `mock` is not a transitive dependency of any other test package (e.g., older versions of `pytest-mock` pulled it in)

**Detection:** After migration, `pip show mock` in the test virtualenv should show "not installed." If mock is still installed transitively, the try/except in test_security.py will silently use the old package.

**Phase:** Dependency cleanup phase — mechanical, low-risk, but must be complete

---

### Pitfall 8: pytest-flake8 Removal + ruff Addition Causes False Test Suite Green

**What goes wrong:** The current `pytest.ini` has `--flake8` in `addopts`, which means flake8 checks run as part of `pytest`. When `pytest-flake8` is removed from `tests_require`, `pytest` will fail to start if `--flake8` is still in `addopts` — not because tests fail, but because the plugin is missing.

The fix is to remove `--flake8` from `addopts` at the same time as removing `pytest-flake8`. But if ruff is not added to CI as a separate check step at the same time, the result is a CI pipeline that has no linting at all — it appears green but is running fewer checks than before.

**Why it happens:** pytest-flake8 couples linting to test runs. The correct modern approach is to run ruff as a separate CI step, not via pytest. The transition moment — removing pytest-flake8 before adding the ruff CI step — creates a linting blind spot.

**Prevention:**
- In the same PR/commit that removes `pytest-flake8` and `--flake8` from addopts, add the ruff check to the CI workflow:
  ```yaml
  - name: Lint with ruff
    run: ruff check . && ruff format --check .
  ```
- Also move flake8 configuration out of `pytest.ini` and into `pyproject.toml` as ruff configuration
- The `flake8-ignore` settings in `pytest.ini` map to ruff `ignore` rules — translate them explicitly so linting tolerance is preserved

**Detection:** After the change, a PR that introduces a linting violation should still fail CI. If it doesn't, ruff was not wired in correctly.

**Phase:** CI modernization phase — ruff step and pytest-flake8 removal must be atomic

---

### Pitfall 9: GitHub Actions actions/checkout@v2 and actions/setup-python@v2 Are Deprecated

**What goes wrong:** All three CI workflows (`sqlite.yml`, `mysql.yml`, `postgres.yml`) use `actions/checkout@v2` and `actions/setup-python@v2`. These are old action versions that GitHub Actions may deprecate or remove support for. More practically, v2 versions do not support modern features like:
- Node 20 runtime (v2 uses Node 16, which is end-of-life)
- `cache` option for pip/uv in `setup-python@v4+`
- Modern Python version specifiers like `"3.12"` without quotes issues

When GitHub deprecates Node 16 actions, these workflows will emit warnings and eventually fail.

**Prevention:**
- Update to `actions/checkout@v4` and `actions/setup-python@v4` (or `v5`)
- Update Python matrix from `[3.6, 3.7, 3.8, 3.9, "3.10"]` to `["3.10", "3.11", "3.12", "3.13"]`
- Remove the `psycopg2-binary` install in the sqlite workflow (it's there by mistake — `Install dependencies` step in sqlite.yml installs psycopg2-binary for no reason)
- Consider using the `cache: pip` option in setup-python to speed up CI

**Detection:** Run the workflow and check for "Node.js 16 actions are deprecated" warnings in the Actions log.

**Phase:** CI modernization phase

---

### Pitfall 10: Alembic Colon-Notation Script Paths Break After Packaging Changes

**What goes wrong:** Kotti uses colon-notation for Alembic script locations (e.g., `"kotti:alembic"` as the `DEFAULT_LOCATION` in `migrate.py`). This notation is resolved by Alembic using `pkg_resources` internally. After migrating away from `pkg_resources`, there is a risk that Alembic's own use of this notation in `Config.set_main_option("script_location", location)` breaks if the package is not properly installed.

Plugin authors who add their own migration scripts via `kotti.alembic_dirs` settings also use this notation. Packaging changes that affect how `kotti` is discoverable (e.g., moving to src layout without reinstalling) will cause plugins to fail their migration discovery.

**Prevention:**
- After any packaging change, test the full migration workflow end-to-end: create a fresh database, start the app, run `kotti-migrate list_all` and `kotti-migrate upgrade_all`
- Verify plugin-provided migrations still work by testing with at least one add-on package
- Document in CHANGES.txt that plugin authors must reinstall their packages if they use `kotti:alembic`-style migration paths

**Detection:** `kotti-migrate list_all` should return a non-empty list of migration scripts. An empty list or an error is the failure signal.

**Phase:** Packaging migration phase — must be verified before declaring the migration complete

---

## Minor Pitfalls

Issues that cause friction but are recoverable.

---

### Pitfall 11: tox.ini References Dead Python Versions

**What goes wrong:** `tox.ini` currently references Python 3.5 in environment variable setenv blocks (lines 14, 18, 19) and only tests 3.6-3.8, while classifiers claim 3.6-3.10. The tox configuration is inconsistent with actual CI and will confuse contributors.

**Prevention:** Update tox.ini to reflect the new Python 3.10-3.13 matrix, or remove tox.ini entirely in favor of CI-only testing. Keeping a stale tox.ini is worse than removing it.

**Phase:** CI modernization phase

---

### Pitfall 12: setup.cfg Leftover Causes Confusion

**What goes wrong:** `setup.cfg` currently contains only aliases (`dev = develop easy_install ...`) and `check-manifest` configuration. After migrating to pyproject.toml, if `setup.cfg` is not removed, some tools may still read it. setuptools reads from both `setup.cfg` and `pyproject.toml` when both exist, which can cause unexpected merging of configuration.

**Prevention:** Delete `setup.cfg` entirely during the pyproject.toml migration. If `check-manifest` is being removed (it should be, since pyproject.toml + build backends handle this), there is nothing to keep.

**Phase:** Packaging migration phase

---

### Pitfall 13: Version String in Two Places After Partial Migration

**What goes wrong:** The version `'2.0.10dev0'` is currently defined in `setup.py` as a Python string. During migration to pyproject.toml, if the version is set statically in `[project] version = "2.0.10dev0"` but the old `setup.py` is kept temporarily (for backwards compatibility tooling), there will be two authoritative sources that can diverge. Similarly, `get_version()` uses `importlib.metadata` which reads from the installed package — in development with editable installs, this reads from the installed metadata, not the source file.

**Prevention:**
- Remove `setup.py` entirely (or keep only a minimal stub for legacy tools) as soon as `pyproject.toml` is the authoritative source
- Consider using `setuptools-scm` to derive version from git tags, eliminating the in-file version string
- If keeping a static version, use `importlib.metadata.version("Kotti")` consistently everywhere (it reads from installed metadata regardless of editable vs regular install)

**Phase:** Packaging migration phase

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| setup.py → pyproject.toml | MANIFEST.in/package-data not ported, locale/template files missing from wheel | Build wheel, inspect contents before releasing |
| src layout adoption | Entry points and pytest plugin break with stale editable install | Uninstall + reinstall after layout change; check `kotti.__file__` |
| pkg_resources removal | `kotti-migrate` CLI breaks, Alembic script discovery fails | Replace with `importlib.metadata`/`importlib.resources`; test CLI commands directly |
| Python 3.10+ target | `sqlalchemy.ext.declarative` and baked queries break if SA is inadvertently upgraded to 2.0 | Keep SQLAlchemy `<2` pin for this milestone |
| bleach → nh3 | API incompatibility with callable `attributes` and `styles` parameter | Write characterization tests before switching; nh3 is not drop-in |
| mock → unittest.mock | Conditional import fallback in test_security.py silently uses old mock | Replace all imports, remove conditional, remove from deps |
| pytest-flake8 removal | Linting blind spot if ruff not added to CI simultaneously | Atomic change: remove plugin + add ruff CI step in same commit |
| CI GitHub Actions update | Node 16 deprecation warnings become errors | Update to checkout@v4 and setup-python@v4+ |
| Pyramid 1.x pin | Relaxing `<2` causes `pyramid.compat` ImportError | Do NOT relax pyramid version pin in this milestone |
| Alembic colon-paths | Plugin migrations break after packaging changes | End-to-end test `kotti-migrate` CLI after every packaging change |

---

## Sources

**Confidence:** HIGH — findings derived from direct codebase inspection (`setup.py`, `kotti/__init__.py`, `kotti/migrate.py`, `kotti/sqla.py`, `kotti/traversal.py`, `kotti/sanitizers.py`, `kotti/tests/__init__.py`, `pytest.ini`, `tox.ini`, `.github/workflows/*.yml`, `.planning/codebase/CONCERNS.md`).

**Python packaging references** (established, not requiring web verification):
- PEP 517/518: pyproject.toml as the build system declaration
- PEP 660: editable installs with pyproject.toml
- importlib.metadata/importlib.resources: stdlib since Python 3.9 (3.7 for metadata with backport)
- setuptools src layout: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html
- bleach deprecation: bleach 6.x changelog, nh3 0.2.x release notes
- pyramid.compat removal: Pyramid 2.0 changelog
- sqlalchemy.ext.declarative deprecation: SQLAlchemy 1.4 migration guide, removal in 2.0
- sqlalchemy.ext.baked removal: SQLAlchemy 2.0 changelog
- pytest yield_fixture: pytest 4.0 changelog (removed deprecated fixture)
- pytest --strict rename: pytest 6.2 changelog (renamed to --strict-markers)

---

*Pitfalls audit: 2026-02-27*
