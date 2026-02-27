# Kotti Modernization

## What This Is

A modernization effort for Kotti, a Pyramid-based CMS framework published on PyPI. The goal is to bring the project's packaging, tooling, dependencies, and Python version support up to current standards while preserving backwards compatibility through a deprecation cycle. This is an open source project with existing users.

## Core Value

Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users — every change must go through a deprecation path.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. Inferred from existing codebase. -->

- ✓ Hierarchical content tree with traversal-based routing — existing
- ✓ ACL-based security with local group assignments — existing
- ✓ SQLAlchemy ORM persistence (SQLite, PostgreSQL, MySQL) — existing
- ✓ Content type system with TypeInfo registry — existing
- ✓ Event-driven architecture (insert, update, delete lifecycle) — existing
- ✓ Form handling via colander/deform schemas — existing
- ✓ File upload/storage via filedepot — existing
- ✓ User/group management with role-based permissions — existing
- ✓ Internationalization (i18n) with Babel — existing
- ✓ Plugin architecture via includeme hooks — existing
- ✓ Alembic database migrations — existing
- ✓ Chameleon template rendering — existing
- ✓ Sphinx documentation on RTD — existing
- ✓ PyPI package distribution — existing
- ✓ GitHub Actions CI with multi-DB testing — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Migrate from setup.py to pyproject.toml with modern build backend
- [ ] Adopt src layout
- [ ] Consolidate tool config (ruff, pytest, etc.) into pyproject.toml
- [ ] Use uv as package manager
- [ ] Adopt ruff for linting and formatting
- [ ] Declare Python 3.10-3.13 compatibility, drop 3.6-3.9
- [ ] Replace deprecated dependencies with clear drop-in replacements (e.g., bleach → nh3)
- [ ] Replace mock with unittest.mock throughout tests
- [ ] Replace pytest-flake8 with ruff in test/CI pipeline
- [ ] Modernize CI: update GH Actions, Python 3.10-3.13 test matrix, add ruff checks
- [ ] Modernize Sphinx config and RTD setup
- [ ] Remove code duplication
- [ ] Clean up bare exception handlers and type annotation issues
- [ ] Keep documentation in sync with all changes
- [ ] Ensure deprecation warnings for any breaking changes

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Replacing fanstatic/js.* asset pipeline — too complex, needs its own milestone
- Replacing Angular 1.x — frontend overhaul is a separate effort
- Upgrading to Pyramid 2.0 — major API changes, deserves dedicated milestone
- Replacing pyramid_beaker sessions — requires evaluating alternatives, separate effort
- Removing ZCML support — breaking change for plugins, needs deprecation planning
- Replacing FormEncode with colander — used in email validation, risk of subtle breakage
- Adding new features (rate limiting, API versioning, request tracing) — this is modernization, not feature work
- Performance optimization — separate effort after modernization

## Context

Kotti is a mature Pyramid-based CMS framework (version 2.0.10dev0) published on PyPI. It has an active codebase with:
- ~50+ Python source files across kotti/ package
- Test suite using pytest with SQLite/PostgreSQL/MySQL backends
- Sphinx documentation hosted on RTD
- GitHub Actions CI (separate workflows per DB backend)
- Multiple entry points (paste.app_factory, console_scripts, fanstatic, pytest11)
- Rich plugin ecosystem via includeme hooks

The codebase currently targets Python 3.6-3.10 (classifiers) but tox only tests 3.6-3.8. Many dependencies are pinned to old versions. The build system uses setup.py with setuptools_git. No pyproject.toml exists.

Key deprecated/outdated items identified:
- `bleach` (deprecated, replaced by `nh3` ecosystem)
- `mock` (stdlib `unittest.mock` since Python 3.3)
- `pytest-flake8` (replaced by ruff)
- `setuptools_git` (unnecessary with modern setuptools)
- `check-manifest` (less relevant with pyproject.toml)
- Bare `except:` clauses in alembic/env.py and views/cache.py
- `Union[int, "NoneType"]` patterns instead of `Optional[int]`

## Constraints

- **Backwards compatibility**: Must use deprecation warnings before removing/changing public APIs — existing PyPI users depend on this
- **PyPI publication**: Package must remain installable via pip throughout the process
- **Entry points**: paste.app_factory, fanstatic.libraries, console_scripts, and pytest11 entry points must keep working
- **Plugin compatibility**: includeme hooks and configuration patterns must remain functional
- **Test suite**: All existing tests must pass after changes (or be updated with clear rationale)

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python 3.10-3.13 target | Drop EOL versions, use modern syntax (match, \|, etc.) | — Pending |
| pyproject.toml + src layout | Modern Python packaging standard | — Pending |
| uv as package manager | Fast, modern, replaces pip/pip-tools | — Pending |
| ruff for linting + formatting | Replaces flake8, isort, black — single fast tool | — Pending |
| Deprecation cycle for breaking changes | Protect existing users, standard OSS practice | — Pending |
| Replace bleach with drop-in alternative | bleach is deprecated, nh3 or similar is the path forward | — Pending |

---
*Last updated: 2026-02-27 after initialization*
