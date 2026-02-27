# Feature Landscape

**Domain:** Python open-source CMS framework modernization (PyPI-published)
**Researched:** 2026-02-27
**Confidence:** MEDIUM — Based on established Python ecosystem patterns as of August 2025, project files, and existing codebase analysis. External verification was unavailable during this research session; key claims are grounded in well-stabilized Python community standards.

---

## Table Stakes

Features users (maintainers and downstream package consumers) expect from a modern Python open-source project. Missing these = project feels abandoned or unusable on current toolchains.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **pyproject.toml** as single source of truth | PEP 517/518/621 standard since Python 3.11 era; pip, uv, and build tools all expect it | Low | Replace setup.py + setup.cfg + pytest.ini + tox.ini → one file |
| **src layout** | Prevents accidental import of uninstalled package during testing; pip install -e . works correctly | Low | Move `kotti/` → `src/kotti/` |
| **Modern build backend** (hatchling or setuptools >=61) | setuptools_git is unmaintained; MANIFEST.in is no longer required with git-aware backends | Low | setuptools >=61 with `[tool.setuptools.packages.find]` is simplest migration path |
| **Python version classifiers current** (3.10–3.13) | PyPI users filter by Python version; outdated classifiers mislead; 3.6–3.9 are EOL | Low | Update `Programming Language :: Python :: 3.X` classifiers in pyproject.toml |
| **Drop EOL Python versions** (3.6–3.9) | 3.6 EOL Dec 2021; 3.7 EOL Jun 2023; 3.8 EOL Oct 2024; 3.9 EOL Oct 2025 | Low | Also enables use of `match`, `X | Y` union syntax, `tomllib`, etc. |
| **Replace bleach with nh3** | bleach 6.x is deprecated (Mozilla announced end-of-life); nh3 is the community-endorsed Rust-backed replacement | Medium | API differs: `bleach.clean()` → `nh3.clean()`; `bleach-allowlist` patterns must be converted to nh3's `tags`/`attributes` dicts |
| **Replace mock with unittest.mock** | `mock` was stdlib since Python 3.3; separate `mock` package is redundant and signals outdated test suite | Low | Mechanical `import mock` → `from unittest import mock` replacement |
| **Replace pytest-flake8 with ruff** | pytest-flake8 is unmaintained and incompatible with pytest 7+; ruff is the community standard for linting | Low | Remove pytest-flake8 from test deps; add ruff as dev/CI dep; configure in pyproject.toml |
| **GitHub Actions matrix updated** (ubuntu-latest + Python 3.10–3.13) | ubuntu-18.04 and ubuntu-20.04 runners are deprecated; Python 3.6–3.9 runners being removed | Low | Update workflow YAML `python-version:` matrix; update `runs-on:` |
| **Ruff for formatting** | black + isort replaced by ruff format; single tool config in pyproject.toml | Low | `ruff format` is a drop-in; configure `[tool.ruff]` in pyproject.toml |
| **Remove setuptools_git** | Obsolete; modern setuptools auto-detects git-tracked files without a plugin | Low | Remove from setup_requires and install_requires |
| **Remove check-manifest** | Replaced by properly configured pyproject.toml with `[tool.setuptools.package-data]` | Low | Delete MANIFEST.in if present; configure package data in pyproject.toml |
| **stdlib unittest.mock** | Part of Python 3.3+; mock package only needed for Python 2 | Low | Dependency on `mock` PyPI package is removed |
| **Deprecation warnings for API changes** | OSS users depending on public API must have a migration path; `DeprecationWarning` is the Python convention | Medium | Use `warnings.warn("...", DeprecationWarning, stacklevel=2)` for any removed/changed public symbols |
| **Sphinx config up to date** | RTD now requires `conf.py` or `pyproject.toml` sphinx config; old RTD YAML format deprecated | Low | Update `docs/conf.py`; update `.readthedocs.yaml` to v2 format |

---

## Differentiators

Features beyond basic modernization that improve developer experience and project health. Not strictly required, but raise the quality bar.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **uv as package manager** | 10–100x faster than pip; lockfile support; replaces pip-tools; first-class pyproject.toml | Low | Drop-in for `pip install`; document in CONTRIBUTING.md; CI can use `uv sync` |
| **Optional[int] → int \| None syntax** | Python 3.10+ union syntax is cleaner; `Union[int, "NoneType"]` is actively wrong | Low | Mechanical; enables dropping `from __future__ import annotations` in many cases |
| **Sphinx furo or pydata-sphinx-theme** | sphinx_rtd_theme is stagnant; furo is the modern standard for open-source Python docs | Low | Change `html_theme` in conf.py; update docs_require |
| **Ruff lint rules beyond flake8** | ruff covers flake8, isort, pyupgrade, bugbear, and more in one pass | Low | Enable `I` (isort), `UP` (pyupgrade), `B` (bugbear) rule sets in ruff config |
| **pyupgrade-style modernization** | Replace old Python patterns: `super(Foo, self)` → `super()`, old-style `%` formatting, etc. | Low | ruff UP rules automate this; run once with `--fix` |
| **Bare except cleanup** | `except:` → `except Exception:` with logging; reduces silent failures | Low | Two files identified: alembic/env.py, views/cache.py |
| **Modern type annotation style** | Replace `Union[X, None]` with `Optional[X]`, replace `Union[X, Y]` with `X \| Y` on 3.10+ | Low | Mechanical; ruff UP007 rule automates it |
| **Consolidated CI workflow** | Single GitHub Actions workflow with matrix over Python version + DB backend reduces duplication | Medium | Currently 3 separate workflows (sqlite, postgres, mysql); can be one with matrix strategy |
| **pre-commit hooks** | Automates ruff, trailing whitespace, end-of-file fixes on every commit | Low | `.pre-commit-config.yaml`; document in CONTRIBUTING.md |
| **Dependabot or Renovate for deps** | Automated PRs for outdated dependencies; standard for maintained OSS | Low | Add `.github/dependabot.yml`; configure for pip and GitHub Actions |
| **CHANGELOG format standardization** | keepachangelog.com format (`Added/Changed/Deprecated/Removed/Fixed/Security`) is widely adopted | Low | Rename/restructure CHANGES.txt |
| **Publish via Trusted Publisher (PyPI OIDC)** | Eliminates PyPI API tokens from secrets; GitHub Actions OIDC is the modern standard | Medium | Configure on PyPI project page + add release workflow |
| **tox.ini → tox 4 + pyproject.toml** | tox 4 supports pyproject.toml natively; old tox.ini format and Python 3.6 envs can be removed | Low | Update `[tox]` → `[tool.tox]` in pyproject.toml or keep tox.ini with 4.x syntax |

---

## Anti-Features

Things to deliberately NOT do during this modernization milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Upgrading Pyramid 1.x → 2.x** | Major API surface changes; Pyramid 2.0 changed authentication/authorization policy APIs; deserves its own milestone | Keep `pyramid>=1.9,<2` pin; document Pyramid upgrade as separate milestone |
| **Replacing pyramid_beaker sessions** | Requires evaluating pyramid_session_redis or custom session factory; risk of auth regressions | Leave in place; note as tech debt |
| **Removing ZCML support** | Breaks existing plugins that use `pyramid_zcml`; no deprecation path yet | Leave in place; document removal in future major version notes |
| **Replacing FormEncode** | Used only for email validation; colander is already present but replacement is non-trivial and risky | Leave FormEncode; document as future simplification |
| **Adding new CMS features** | This is modernization, not feature development | Reject any feature requests for this milestone |
| **Pinning all transitive deps** | Overly restrictive pinning breaks downstream consumers who install Kotti alongside other packages | Pin only direct deps where necessary; use minimum version (`>=`) not exact (`==`) except where documented breakage exists (e.g. `deform==2.0.14`) |
| **Using bleach 5.x/6.x** | bleach 6.x itself deprecated by Mozilla; no point migrating to it | Go directly to nh3 |
| **Removing Python 3.10 support** | 3.10 is still actively maintained (EOL Oct 2026); dropping it reduces user base unnecessarily | Support 3.10–3.13 |
| **Mass type annotation addition** | Full type annotation of a legacy codebase is out of scope; would bloat the diff and risk regressions | Fix only the known-wrong `Union[X, "NoneType"]` patterns; add annotations incrementally in future milestones |
| **Removing entry points without deprecation** | paste.app_factory, fanstatic.libraries, console_scripts, pytest11 entry points have downstream dependents | Never remove silently; deprecate first if needed |
| **Formatting entire codebase in one commit** | Giant reformatting commits destroy git blame and make code review impossible | Do formatting as first isolated commit so all subsequent commits are reviewable |

---

## Feature Dependencies

```
pyproject.toml
  └─→ src layout (restructure must happen together with build backend change)
  └─→ ruff config (tool.ruff section)
  └─→ pytest config (tool.pytest.ini_options replaces pytest.ini)
  └─→ tox config (tool.tox or updated tox.ini)

Replace bleach → nh3
  └─→ Remove bleach-allowlist (allowlist patterns are embedded in nh3 call sites)
  └─→ Audit every bleach.clean() call site for API differences

Drop mock package
  └─→ Update all test imports (unittest.mock is stdlib, no new dep needed)

Remove pytest-flake8
  └─→ Add ruff as dev dependency
  └─→ Update CI to run `ruff check` and `ruff format --check` separately from pytest

Update Python classifiers
  └─→ Update GitHub Actions matrix (must stay in sync)
  └─→ Update tox envlist (must stay in sync)

Sphinx config update
  └─→ Update .readthedocs.yaml to v2 format (required by RTD)
  └─→ Optionally update sphinx theme (independent but natural to do together)
```

---

## MVP Recommendation

For this modernization milestone, prioritize in this order:

**Phase 1 — Packaging foundation (do first, everything else builds on this):**
1. Migrate setup.py → pyproject.toml with hatchling or setuptools >=61
2. Adopt src layout
3. Consolidate tool config (pytest, ruff, tox) into pyproject.toml

**Phase 2 — Dependency modernization (high-value, low-risk):**
4. Replace bleach + bleach-allowlist with nh3
5. Replace mock with unittest.mock (test deps only)
6. Remove setuptools_git, check-manifest
7. Declare Python 3.10–3.13; drop 3.6–3.9 classifiers

**Phase 3 — Tooling and CI (developer experience):**
8. Replace pytest-flake8 with ruff
9. Update GitHub Actions matrix (Python versions, ubuntu-latest)
10. Add ruff format pass (isolated commit)

**Phase 4 — Code quality (surgical fixes):**
11. Fix bare except handlers (2 files)
12. Fix Union[X, "NoneType"] → Optional[X] patterns (5 files)
13. Emit deprecation warnings for any changed public APIs

**Phase 5 — Docs:**
14. Update Sphinx conf.py + .readthedocs.yaml to RTD v2 format
15. Optionally update sphinx theme (furo recommended)

**Defer:**
- Trusted Publisher PyPI OIDC setup (good practice but not blocking)
- Dependabot configuration (good practice but not blocking)
- pre-commit hooks (developer convenience, not blocking release)
- Consolidated CI matrix workflow (current 3-workflow approach works)

---

## Sources

- Project analysis: `/Users/disko/Projects/ipn/Kotti/setup.py` (direct read)
- Codebase audit: `/Users/disko/Projects/ipn/Kotti/.planning/codebase/CONCERNS.md` (direct read)
- Project scope: `/Users/disko/Projects/ipn/Kotti/.planning/PROJECT.md` (direct read)
- bleach deprecation: bleach 6.1.0 release notes (Mozilla announced end-of-maintenance); MEDIUM confidence (training data, no live verification)
- nh3 as replacement: PyPI community consensus; ammonia Rust crate is the underlying library; MEDIUM confidence
- PEP 517/518/621 (pyproject.toml): official Python packaging authority docs; HIGH confidence (stable standards)
- src layout best practices: Hynek Schlawack's "Testing & Packaging" (canonical reference); HIGH confidence
- pytest-flake8 deprecation: incompatible with pytest 7+, maintainer archived repo; HIGH confidence (well-known)
- RTD v2 config format: ReadTheDocs deprecated v1 YAML format (announced 2023); HIGH confidence
- Python EOL dates: python.org/downloads (3.8 Oct 2024, 3.9 Oct 2025, 3.10 Oct 2026); HIGH confidence
- ruff as flake8/black replacement: astral-sh/ruff GitHub + Python community adoption; HIGH confidence
- uv as pip replacement: astral-sh/uv; HIGH confidence for capability claims
