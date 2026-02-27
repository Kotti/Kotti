# Requirements: Kotti Modernization

**Defined:** 2026-02-27
**Core Value:** Keep Kotti installable, functional, and maintainable on modern Python (3.10-3.13) without breaking existing users

## v1 Requirements

Requirements for this modernization milestone. Each maps to roadmap phases.

### Packaging

- [ ] **PKG-01**: Project uses pyproject.toml as single source of truth (replaces setup.py, setup.cfg, pytest.ini, tox.ini)
- [ ] **PKG-02**: Project uses hatchling as build backend
- [ ] **PKG-03**: Project uses src layout (src/kotti/)
- [ ] **PKG-04**: All six entry points (paste.app_factory, fanstatic.libraries, 3 console_scripts, pytest11) work correctly from pyproject.toml
- [ ] **PKG-05**: Non-Python package data (.pt templates, .po/.mo locale files, .zcml, alembic scripts, static assets) included in sdist/wheel
- [ ] **PKG-06**: setuptools_git and check-manifest removed
- [ ] **PKG-07**: setup.py and setup.cfg deleted (not coexisting with pyproject.toml)
- [ ] **PKG-08**: uv used as package manager with committed uv.lock

### Dependencies

- [ ] **DEP-01**: bleach + bleach-allowlist replaced with nh3 for HTML sanitization
- [ ] **DEP-02**: Sanitization behavior preserved (characterization tests pass before and after switch)
- [ ] **DEP-03**: mock PyPI package replaced with stdlib unittest.mock in all test files
- [ ] **DEP-04**: pkg_resources replaced with importlib.metadata for version lookup
- [ ] **DEP-05**: pkg_resources.resource_filename replaced with importlib.resources for Alembic directory discovery
- [ ] **DEP-06**: kotti-migrate CLI works correctly after importlib migration (tested in fresh virtualenv)
- [ ] **DEP-07**: pyramid>=1.9,<2 pin maintained (pyramid.compat dependency)
- [ ] **DEP-08**: sqlalchemy>=1.4,<2 pin maintained (declarative_base/baked queries dependency)

### Python Version

- [ ] **PYV-01**: Python 3.6-3.9 classifiers and support dropped
- [ ] **PYV-02**: Python 3.10-3.13 classifiers declared
- [ ] **PYV-03**: CI test matrix covers Python 3.10, 3.11, 3.12, 3.13
- [ ] **PYV-04**: All tests pass on Python 3.10-3.13

### Linting & Formatting

- [ ] **LNT-01**: ruff configured for linting in pyproject.toml (replaces flake8)
- [ ] **LNT-02**: ruff configured for formatting in pyproject.toml (replaces black/isort)
- [ ] **LNT-03**: pytest-flake8 removed from test dependencies
- [ ] **LNT-04**: Formatting applied in isolated first commit (preserves git blame)
- [ ] **LNT-05**: pyupgrade-style modernizations applied (super(), union syntax, etc.)
- [ ] **LNT-06**: pre-commit hooks configured (.pre-commit-config.yaml)

### CI/CD

- [ ] **CI-01**: GitHub Actions updated to current versions (checkout@v4, setup-python@v5)
- [ ] **CI-02**: CI uses uv for package installation (astral-sh/setup-uv action)
- [ ] **CI-03**: Separate ruff lint/format check job in CI
- [ ] **CI-04**: 3 separate workflow files consolidated into 1 matrix workflow (Python version x DB backend)
- [ ] **CI-05**: Dependabot configured for automated dependency PRs

### Code Quality

- [ ] **CQ-01**: Bare except handlers replaced with specific exceptions (alembic/env.py, views/cache.py)
- [ ] **CQ-02**: Union[int, "NoneType"] patterns replaced with Optional[int] or X | None syntax
- [ ] **CQ-03**: Deprecation warnings added for any changed public APIs
- [ ] **CQ-04**: Code duplication identified and removed where safe

### Documentation

- [ ] **DOC-01**: Documentation migrated from Sphinx/RST to MkDocs with Material for MkDocs theme
- [ ] **DOC-02**: Documentation builds successfully with MkDocs
- [ ] **DOC-03**: All existing documentation content preserved during migration
- [ ] **DOC-04**: API documentation generated (mkdocstrings or equivalent)

## v2 Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Framework Upgrades

- **FWK-01**: Upgrade to Pyramid 2.0 (requires removing pyramid.compat usage, updating auth policies)
- **FWK-02**: Upgrade to SQLAlchemy 2.0 (requires rewriting declarative_base, removing baked queries)
- **FWK-03**: Replace pyramid_beaker with modern session management
- **FWK-04**: Remove ZCML support (with deprecation cycle)
- **FWK-05**: Replace FormEncode with colander for email validation

### Advanced Modernization

- **ADV-01**: Trusted Publisher / PyPI OIDC for releases
- **ADV-02**: Full type annotation coverage
- **ADV-03**: Replace fanstatic/js.* asset pipeline

## Out of Scope

| Feature | Reason |
|---------|--------|
| New CMS features | This is modernization, not feature development |
| Pyramid 2.0 upgrade | Major API changes, deserves dedicated milestone |
| SQLAlchemy 2.0 upgrade | Breaks declarative_base and baked queries, separate milestone |
| Replacing fanstatic/js.* | Frontend overhaul is a separate effort |
| Removing Angular 1.x | Frontend overhaul is a separate effort |
| Full type annotation pass | Out of scope; fix only known-wrong patterns |
| Performance optimization | Separate effort after modernization |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PKG-01 | Phase 1 | Pending |
| PKG-02 | Phase 1 | Pending |
| PKG-03 | Phase 1 | Pending |
| PKG-04 | Phase 1 | Pending |
| PKG-05 | Phase 1 | Pending |
| PKG-06 | Phase 1 | Pending |
| PKG-07 | Phase 1 | Pending |
| PKG-08 | Phase 1 | Pending |
| DEP-01 | Phase 2 | Pending |
| DEP-02 | Phase 2 | Pending |
| DEP-03 | Phase 2 | Pending |
| DEP-04 | Phase 2 | Pending |
| DEP-05 | Phase 2 | Pending |
| DEP-06 | Phase 2 | Pending |
| DEP-07 | Phase 2 | Pending |
| DEP-08 | Phase 2 | Pending |
| PYV-01 | Phase 3 | Pending |
| PYV-02 | Phase 3 | Pending |
| PYV-03 | Phase 3 | Pending |
| PYV-04 | Phase 3 | Pending |
| LNT-01 | Phase 4 | Pending |
| LNT-02 | Phase 4 | Pending |
| LNT-03 | Phase 3 | Pending |
| LNT-04 | Phase 4 | Pending |
| LNT-05 | Phase 4 | Pending |
| LNT-06 | Phase 4 | Pending |
| CI-01 | Phase 3 | Pending |
| CI-02 | Phase 3 | Pending |
| CI-03 | Phase 3 | Pending |
| CI-04 | Phase 3 | Pending |
| CI-05 | Phase 3 | Pending |
| CQ-01 | Phase 4 | Pending |
| CQ-02 | Phase 4 | Pending |
| CQ-03 | Phase 4 | Pending |
| CQ-04 | Phase 4 | Pending |
| DOC-01 | Phase 5 | Pending |
| DOC-02 | Phase 5 | Pending |
| DOC-03 | Phase 5 | Pending |
| DOC-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-27*
*Last updated: 2026-02-27 after roadmap creation*
