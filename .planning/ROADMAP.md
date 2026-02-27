# Roadmap: Kotti Modernization

## Overview

Kotti is a mature Pyramid-based CMS framework running on deprecated tooling and an EOL Python matrix. This modernization milestone brings the project's packaging, dependencies, CI, code quality, and documentation up to current standards across five phases — each building on the previous, each leaving the package installable and functional for existing users throughout. The dependency chain is strict: packaging must be correct before dependencies can be safely migrated, CI can be updated after both are stable, code quality fixes follow once tooling is authoritative, and documentation lands last when the final structure is known.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Packaging Foundation** - Replace setup.py/setup.cfg with pyproject.toml, adopt src layout, and commit uv.lock (completed 2026-02-27)
- [x] **Phase 2: Runtime Dependency Updates** - Replace bleach with nh3, pkg_resources with importlib, and mock with unittest.mock (completed 2026-02-27)
- [x] **Phase 3: Python Version and CI Modernization** - Update GitHub Actions, add Python 3.10-3.13 matrix, replace pytest-flake8 with ruff (completed 2026-02-27)
- [ ] **Phase 4: Code Quality and Formatting** - Apply ruff formatting, fix bare excepts, modernize type annotations, add pre-commit hooks
- [ ] **Phase 5: Documentation Migration** - Migrate from Sphinx/RST to MkDocs with Material for MkDocs theme

## Phase Details

### Phase 1: Packaging Foundation
**Goal**: The package builds correctly from a single pyproject.toml with src layout, all entry points work, and all non-Python assets are in the published wheel
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, PKG-06, PKG-07, PKG-08
**Success Criteria** (what must be TRUE):
  1. `pip install kotti` from the built wheel works in a fresh virtualenv — no import errors, no missing templates or locale files
  2. All six entry points (paste.app_factory, fanstatic.libraries, 3 console_scripts, pytest11) function correctly after installation
  3. `uv run pytest` passes on the src layout — `kotti.__file__` path contains `src/`
  4. `setup.py` and `setup.cfg` are deleted — only `pyproject.toml` exists as the metadata source
  5. Inspecting the built sdist confirms `.pt`, `.po`, `.mo`, `.zcml`, and alembic scripts are present
**Plans**: TBD

### Phase 2: Runtime Dependency Updates
**Goal**: Deprecated runtime dependencies are replaced with supported equivalents and all CLI entry points continue to work correctly
**Depends on**: Phase 1
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07, DEP-08
**Success Criteria** (what must be TRUE):
  1. `kotti-migrate list_all` and `kotti-migrate upgrade_all` succeed in a fresh virtualenv (not just pytest passing)
  2. Sanitizer characterization tests pass before and after the bleach-to-nh3 switch — output is identical
  3. `pip show mock` returns "not installed" and all test imports resolve from `unittest.mock`
  4. `pyramid>=1.9,<2` and `sqlalchemy>=1.4,<2` pins are maintained — no version relaxation
**Plans:** 2/2 plans complete
- [ ] 02-01-PLAN.md -- Characterization tests, importlib migrations, mock/pin verification
- [ ] 02-02-PLAN.md -- bleach-to-nh3 sanitizer migration, dependency cleanup

### Phase 3: Python Version and CI Modernization
**Goal**: CI runs on Python 3.10-3.13 with current action versions and a consolidated matrix workflow, and ruff is the linting gate
**Depends on**: Phase 2
**Requirements**: PYV-01, PYV-02, PYV-03, PYV-04, CI-01, CI-02, CI-03, CI-04, CI-05
**Success Criteria** (what must be TRUE):
  1. All existing tests pass on Python 3.10, 3.11, 3.12, and 3.13 in CI
  2. A separate ruff lint/format check job runs in CI and fails on known violations (not a pass-through)
  3. CI uses `uv sync` and `uv run pytest` — no pip or tox invocations remain in workflow files
  4. Three separate workflow files are consolidated into one matrix workflow covering Python version × DB backend
  5. Dependabot is configured and opens automated dependency PRs
**Plans:** 1/1 plans complete
- [ ] 03-01-PLAN.md -- Ruff config, consolidated CI matrix workflow, Dependabot

### Phase 4: Code Quality and Formatting
**Goal**: The codebase passes ruff with no violations, type annotation anti-patterns are corrected, and developer tooling is configured for ongoing hygiene
**Depends on**: Phase 3
**Requirements**: LNT-01, LNT-02, LNT-03, LNT-04, LNT-05, LNT-06, CQ-01, CQ-02, CQ-03, CQ-04
**Success Criteria** (what must be TRUE):
  1. `ruff check .` passes with zero violations
  2. `ruff format --check .` passes with zero violations — formatting applied in an isolated first commit
  3. `pre-commit run --all-files` passes cleanly after hooks are configured
  4. Bare `except:` handlers in `alembic/env.py` and `views/cache.py` are replaced with specific exceptions
  5. Any public API changes made during this milestone carry `DeprecationWarning` with a removal target
**Plans**: TBD

### Phase 5: Documentation Migration
**Goal**: Documentation is served by MkDocs with Material for MkDocs theme, builds successfully, and all existing content is preserved
**Depends on**: Phase 4
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):
  1. `mkdocs build` completes with no errors
  2. All documentation content present in the old Sphinx/RST docs appears in the new MkDocs site
  3. API documentation is generated from docstrings (mkdocstrings or equivalent) and accessible in the built site
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Packaging Foundation | 2/2 | Complete   | 2026-02-27 |
| 2. Runtime Dependency Updates | 2/2 | Complete   | 2026-02-27 |
| 3. Python Version and CI Modernization | 1/1 | Complete   | 2026-02-27 |
| 4. Code Quality and Formatting | 0/? | Not started | - |
| 5. Documentation Migration | 0/? | Not started | - |
