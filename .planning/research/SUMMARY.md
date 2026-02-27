# Project Research Summary

**Project:** Kotti — Pyramid-based CMS Framework Modernization
**Domain:** Open-source Python package modernization (PyPI-published, existing user base)
**Researched:** 2026-02-27
**Confidence:** HIGH

## Executive Summary

Kotti is a mature Pyramid/SQLAlchemy-based CMS framework currently running on deprecated tooling: `setup.py` with the unmaintained `setuptools_git`, `pytest-flake8` baked into the test run, an EOL Python matrix (3.6–3.9), outdated GitHub Actions versions, and `bleach` which Mozilla formally deprecated. The recommended approach is a staged modernization that migrates packaging to `pyproject.toml` with hatchling as the build backend, adopts the src layout, replaces four config files with one, and updates the full CI/CD stack to use uv, ruff, and a Python 3.10–3.13 matrix. This is a developer tooling and packaging modernization, not a feature release — the scope boundary is strict.

The migration has a clear dependency order that research has fully mapped out: pyproject.toml creation comes first (everything else builds on it), src layout adoption comes second (requires the build backend to be correct), and dependency/CI cleanup follows as lower-risk mechanical work. The highest-confidence recommendation is to use hatchling as the build backend (hatchling handles Kotti's six entry points natively with zero extra config, unlike flit), ruff to replace flake8+isort+black in one tool, and uv as the package manager with a committed lockfile for reproducible CI.

The primary risks are specific and avoidable: the `pkg_resources` usage in `kotti/__init__.py` and `kotti/migrate.py` must be migrated to `importlib.metadata`/`importlib.resources` before the package migration is complete, or the `kotti-migrate` CLI will break silently. The `bleach → nh3` migration is not a drop-in replacement — `nh3` does not support callable `attributes` or the `styles` parameter that Kotti's `sanitizers.py` currently uses, so characterization tests must be written before switching. Everything else — mock replacement, CI action updates, Python classifier updates — is mechanical and low-risk.

---

## Key Findings

### Recommended Stack

The full modernization stack is a clean, coherent choice: hatchling for building, uv for package management and dev workflow, ruff for linting and formatting, pytest 8+ for testing, and GitHub Actions with the current action versions and Python 3.10–3.13 matrix. All four config files (`setup.py`, `setup.cfg`, `tox.ini`, `pytest.ini`) collapse into a single `pyproject.toml`. The `bleach` library is replaced by `nh3`, and the `mock` package is replaced with the stdlib `unittest.mock`.

**Core technologies:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| hatchling | `>=1.25` | Build backend | Handles all 6 Kotti entry points natively; zero-config src layout; PyPA-backed |
| uv | `>=0.5` | Package manager, lockfile, venv | 10-100x faster than pip; replaces pip, pip-tools, and tox as runner; stable lockfile format |
| ruff | `>=0.6` | Lint + format + import sort | Replaces flake8, isort, black in one Rust-based tool; configures in pyproject.toml |
| pytest | `>=8.0` | Test runner | Current stable; Kotti already uses pytest — version upgrade only |
| nh3 | latest | HTML sanitization | bleach's officially endorsed Rust-based successor (different API, not drop-in) |

**Key dependency changes:**

| Old | New | Reason |
|-----|-----|--------|
| `bleach` + `bleach-allowlist` | `nh3` | bleach deprecated by Mozilla; nh3 is community-endorsed replacement |
| `mock` PyPI package | `unittest.mock` (stdlib) | Backport unnecessary since Python 3.3 |
| `pytest-flake8` | `ruff` (separate CI step) | pytest-flake8 unmaintained; linting belongs in CI, not in pytest |
| `setuptools_git` | (remove) | Modern setuptools + hatchling handle VCS file inclusion natively |
| `check-manifest` | (remove) | MANIFEST.in superseded by hatchling build config |

**Important pins to maintain for this milestone:**
- `pyramid>=1.9,<2` — Pyramid 2.0 removed `pyramid.compat` which Kotti imports in 3 production files
- `sqlalchemy>=1.4,<2` — SQLAlchemy 2.0 removes `declarative_base()` and baked queries used in `kotti/sqla.py`

### Expected Features

This is a modernization milestone, not a feature release. The research is unambiguous about scope boundaries.

**Must have (table stakes for a maintained Python OSS project):**
- `pyproject.toml` as single source of truth — replaces 4 separate config files
- src layout — prevents accidental import of uninstalled package during testing
- Modern build backend (hatchling) — replaces deprecated `setuptools_git`
- Python 3.10–3.13 classifiers and CI matrix — drops all EOL Python versions
- `bleach → nh3` — bleach 6.x is formally deprecated
- `mock → unittest.mock` — backport package unnecessary since Python 3.3
- `pytest-flake8 → ruff` — pytest-flake8 unmaintained and incompatible with pytest 7+
- GitHub Actions updated to current versions — v2 runs on EOL Node 16
- Deprecation warnings for any changed public APIs

**Should have (quality improvements, low effort):**
- uv as package manager with committed `uv.lock`
- ruff for formatting (isolated commit — protects git blame)
- Pre-commit hooks for ruff, trailing whitespace, EOF fixes
- Consolidated CI matrix (3 separate workflows → 1 with matrix strategy)
- Fix bare except handlers (2 files: `alembic/env.py`, `views/cache.py`)
- Fix `Union[int, "NoneType"]` type annotation errors (5 files)
- Updated Sphinx config and `.readthedocs.yaml` to RTD v2 format
- Dependabot or Renovate for automated dependency PRs

**Defer (explicitly out of scope for this milestone):**
- Pyramid 1.x → 2.x upgrade (breaks `pyramid.compat` imports; separate milestone)
- SQLAlchemy 1.4 → 2.0 upgrade (breaks `declarative_base` and baked queries; separate milestone)
- `pyramid_beaker` replacement (auth regression risk)
- ZCML removal (breaks existing plugins)
- FormEncode replacement (non-trivial, risky)
- Full type annotation of the codebase (out of scope; add incrementally)
- Trusted Publisher / PyPI OIDC (good practice, not blocking)
- New CMS features

### Architecture Approach

The migration is purely a config and layout restructuring — no runtime behavior changes, no API changes. The flat `kotti/` package at repo root moves to `src/kotti/`. All six entry points (`paste.app_factory`, `fanstatic.libraries`, three `console_scripts`, and `pytest11`) translate directly to `[project.entry-points.*]` sections in `pyproject.toml`. Non-Python package data (`.pt` templates, `.po`/`.mo` locale files, `.zcml` files, Alembic scripts, static assets) must be explicitly declared in `[tool.hatch.build.targets.wheel]` to avoid publishing broken PyPI sdists. Tool configuration from `pytest.ini`, `.coveragerc`, and `tox.ini` moves to `[tool.pytest.ini_options]`, `[tool.coverage.*]`, and `[tool.ruff.*]` sections.

**Major components and what changes:**

| Component | Change | Risk |
|-----------|--------|------|
| `kotti/` package | Moves to `src/kotti/` | HIGH — requires reinstall; stale editable installs cause silent failures |
| `setup.py` + `setup.cfg` | Replaced by `pyproject.toml` | HIGH — must be atomic; MANIFEST.in equivalent must be verified |
| `pytest.ini` + `tox.ini` | Move config to `pyproject.toml` | LOW — mechanical translation |
| `kotti/__init__.py` | `pkg_resources` → `importlib.metadata` | HIGH — `get_version()` and `kotti-migrate` depend on this |
| `kotti/migrate.py` | `pkg_resources.resource_filename` → `importlib.resources.files` | HIGH — `kotti-migrate` CLI breaks if wrong |
| `kotti/sanitizers.py` | `bleach.clean()` → `nh3.clean()` | MEDIUM — API difference requires new implementation, not search-replace |
| `kotti/tests/*.py` (7 files) | `from mock import X` → `from unittest.mock import X` | LOW — mechanical |

**Migration sequence (dependency-ordered):**
1. Create `pyproject.toml` (parallel with consolidating tool config)
2. Remove `setup.py` + `setup.cfg` (atomic, after verifying sdist contents)
3. Migrate to src layout (highest risk step — requires reinstall verification)
4. Update CI workflows (after src layout, to use `uv sync`)
5. Generate and commit `uv.lock`
6. Replace bleach with nh3 (isolated, with characterization tests)
7. Replace mock, remove pytest-flake8, add ruff CI step (mechanical)
8. Fix compatibility shims (`pkg_resources`, `yield_fixture`, `--strict` flag)

### Critical Pitfalls

1. **`pkg_resources` removal breaks `kotti-migrate` CLI** — `kotti/__init__.py` uses `pkg_resources.require("Kotti")[0].version` and `kotti/migrate.py` uses `pkg_resources.resource_filename("kotti", "alembic")`. The latter returns a filesystem path string; the `importlib.resources` equivalent returns a `Traversable` that is not string-compatible. Migration: replace with `str(files("kotti") / "alembic")` from `importlib.resources`. Test with `kotti-migrate list_all` in a fresh virtualenv — pytest passing is insufficient because this is a CLI entry point, not a unit test.

2. **`bleach → nh3` is not a drop-in replacement** — `kotti/sanitizers.py` uses `attributes=lambda self, key, value: True` (callable form) and a `styles` parameter, neither of which `nh3` supports. Prevention: write characterization tests against current bleach output, then implement the nh3 version to match. The callable `attributes` pattern must be replaced with an explicit allowlist in `nh3`'s `dict[str, set[str]]` format. Treat as a focused sub-task with its own coverage gate.

3. **src layout migration with stale editable installs** — After `git mv kotti src/kotti`, any existing `pip install -e .` leaves a stale `.pth` file pointing to the old package location. The result is silent import-path ambiguity: CI works while local dev is broken (or vice versa). Prevention: always do `pip uninstall Kotti && pip install -e .` after layout change. Verify with `python -c "import kotti; print(kotti.__file__)"` — path must contain `src/`.

4. **MANIFEST.in → package-data must be complete** — Templates (`.pt`), locale files (`.po`, `.mo`), ZCML files, and Alembic scripts are required at runtime. Editable installs work fine without them; installed-from-PyPI packages will be broken. Prevention: build the sdist, inspect it (`tar -tzf dist/Kotti-*.tar.gz | grep -E '\.(pt|po|mo|zcml|ini)$'`), and test in a fresh non-editable virtualenv before any PyPI upload.

5. **Relaxing Pyramid or SQLAlchemy version pins causes import failures** — `pyramid.compat` (removed in Pyramid 2.0) is imported in 3 production files. `sqlalchemy.ext.declarative` and baked queries (removed in SQLAlchemy 2.0) are used in `kotti/sqla.py`. Both pins (`pyramid>=1.9,<2` and `sqlalchemy>=1.4,<2`) must be maintained strictly for this milestone. Do not relax them as part of "cleaning up" the dependency list.

---

## Implications for Roadmap

Based on the combined research, the natural phase structure follows the dependency order established in ARCHITECTURE.md, with pitfall avoidance informing phase gates.

### Phase 1: Packaging Foundation

**Rationale:** Everything else depends on having a working `pyproject.toml` and src layout. This is the highest-risk phase and must be done first so all subsequent phases work from a correct baseline. Cannot run in parallel with anything else — it changes the fundamental structure all other work builds on.

**Delivers:** Single `pyproject.toml` replacing `setup.py` + `setup.cfg` + `pytest.ini` + `tox.ini`; src layout (`src/kotti/`); committed `uv.lock`; verified wheel with all non-Python assets present.

**Addresses from FEATURES.md:**
- `pyproject.toml` as single source of truth
- src layout adoption
- Modern build backend (hatchling)
- Removal of `setuptools_git`, `check-manifest`

**Must avoid:**
- Pitfall 3 (stale editable installs after src layout) — mandatory reinstall + `kotti.__file__` check
- Pitfall 6 (MANIFEST.in → package-data incomplete) — mandatory sdist inspection gate
- Pitfall 12 (setup.cfg leftover) — delete atomically with setup.py
- Pitfall 13 (version string in two places) — remove setup.py entirely, don't keep both

**Phase gate:** `uv run pytest` passes; `kotti-migrate list_all` succeeds in fresh virtualenv; sdist contents verified.

---

### Phase 2: Runtime Dependency Updates

**Rationale:** Dependency replacements that have API implications (`bleach → nh3`, `pkg_resources → importlib`) should be done after packaging is stable but before CI is reconfigured, so failures are clearly attributable to the dependency change and not to tooling changes. These are the two highest-risk individual changes in the project.

**Delivers:** `nh3` replacing `bleach`; `importlib.metadata`/`importlib.resources` replacing `pkg_resources` throughout; `mock` PyPI package removed in favor of `unittest.mock`.

**Addresses from FEATURES.md:**
- `bleach → nh3` replacement
- `mock → unittest.mock` replacement
- Removal of `bleach-allowlist`

**Must avoid:**
- Pitfall 1 (`pkg_resources` removal breaks `kotti-migrate`) — test the CLI directly, not just pytest
- Pitfall 4 (`bleach → nh3` API incompatibility) — write characterization tests first; treat as sub-task
- Pitfall 7 (conditional import fallback in `test_security.py`) — replace all imports and remove the try/except

**Phase gate:** `kotti-migrate list_all` passes; `kotti-migrate upgrade_all` passes on a fresh database; sanitizer characterization tests pass; `pip show mock` returns "not installed" in CI environment.

---

### Phase 3: Python Version and CI Modernization

**Rationale:** CI changes can follow packaging and dependency changes cleanly. With packaging stable and `uv.lock` committed, switching CI to `uv sync` + `uv run pytest` is mechanical. This is also the right phase to update Python classifiers and the GitHub Actions matrix, since these changes must stay in sync.

**Delivers:** GitHub Actions updated to `checkout@v4`, `setup-python@v5`, `astral-sh/setup-uv@v4`; Python matrix 3.10–3.13; Python classifiers updated; tox.ini updated or removed; separate lint job with ruff.

**Addresses from FEATURES.md:**
- GitHub Actions matrix updated
- Python 3.10–3.13 classifiers
- Drop Python 3.6–3.9
- ruff replaces pytest-flake8

**Must avoid:**
- Pitfall 5 (compatibility shims — fix `yield_fixture`, `--strict` → `--strict-markers` in this phase)
- Pitfall 8 (pytest-flake8 removal + ruff addition must be atomic in same commit)
- Pitfall 9 (Node 16 deprecation — update all three workflow files: sqlite.yml, mysql.yml, postgres.yml)
- Pitfall 11 (stale tox.ini with dead Python versions — update or delete)

**Phase gate:** All 4 Python versions pass in CI; separate lint job fails on known violations; ruff coverage equivalent to previous flake8 coverage.

---

### Phase 4: Code Quality Fixes

**Rationale:** With the tooling and packaging stable, surgical code fixes can be applied cleanly. These are isolated, low-risk, and well-bounded changes that improve code health without changing behavior.

**Delivers:** Bare except handlers replaced (2 files); `Union[int, "NoneType"]` → `Optional[int]` fixed (5 files); type annotation style modernized with ruff UP rules; deprecation warnings added for any changed public APIs; ruff format applied in isolated commit.

**Addresses from FEATURES.md:**
- Bare except cleanup (`alembic/env.py`, `views/cache.py`)
- `Union[X, "NoneType"]` → `Optional[X]` modernization
- ruff formatting pass
- Deprecation warnings for API changes

**Must avoid:**
- Giant reformatting commits — formatting must be done as the FIRST isolated commit in this phase so all subsequent commits remain reviewable
- Mass type annotation addition — only fix the known-wrong patterns, not a full annotation pass

**Phase gate:** ruff passes with no violations; all existing tests pass; no behavior changes.

---

### Phase 5: Documentation and Developer Experience

**Rationale:** Low-risk quality improvements that can be done last without blocking anything. The docs and DX improvements are high-value for contributors but do not affect users of the published package.

**Delivers:** Sphinx `conf.py` updated; `.readthedocs.yaml` updated to v2 format; optional: furo sphinx theme replacing sphinx-rtd-theme; pre-commit hooks configured; Dependabot configured; consolidated CI matrix workflow (optional).

**Addresses from FEATURES.md:**
- Sphinx config + RTD v2 format
- Pre-commit hooks (developer convenience)
- Dependabot for automated dependency PRs
- Consolidated CI workflow (optional, current 3-workflow approach works)

**Phase gate:** RTD build passes; pre-commit hooks run cleanly on all files.

---

### Phase Ordering Rationale

- Phase 1 must come first because src layout and pyproject.toml are structural prerequisites — all other tools (uv, ruff, pytest) must be configured against the new layout before CI can be updated.
- Phase 2 must come before Phase 3 because `pkg_resources` replacement affects `kotti-migrate`, which is tested in CI; failing CI before the fix is isolated makes debugging harder.
- Phase 3 (CI) naturally follows Phase 2 because `uv sync` depends on `pyproject.toml` being the authoritative source (Phase 1) and CI must reflect the actual dependency state (Phase 2).
- Phase 4 is decoupled from everything else and could be split across earlier phases, but grouping it here keeps code-quality changes visible and reviewable separately from structural changes.
- Phase 5 is deliberately last — documentation correctness depends on the final package structure, and DX tooling (pre-commit, Dependabot) should reflect the final configuration.

### Research Flags

**Phases with standard patterns (can skip `research-phase` during planning):**
- **Phase 1** — pyproject.toml migration is a well-documented, stable pattern. ARCHITECTURE.md provides the complete pyproject.toml skeleton. Step-by-step migration sequence is fully mapped.
- **Phase 3** — GitHub Actions update is mechanical. Python version matrix change is straightforward.
- **Phase 4** — Code quality fixes are bounded and well-understood.
- **Phase 5** — Documentation config updates are mechanical.

**Phases that may benefit from deeper implementation research:**
- **Phase 2** — The `bleach → nh3` migration requires understanding `nh3`'s exact API for `attributes` handling before implementation begins. Recommend reading nh3 source/docs at implementation time. The `importlib.resources` API for path-like access also has subtleties (Traversable vs. string path) that warrant a focused read of Python docs before modifying `kotti/migrate.py`.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | hatchling, uv, ruff, pytest 8 are dominant tools with no credible challengers as of Aug 2025; specific version numbers (uv 0.5+, ruff 0.6+) should be verified at implementation time |
| Features | HIGH | Based on direct codebase inspection + stable Python packaging standards (PEP 517/518/621); bleach deprecation and nh3 as replacement are well-established |
| Architecture | HIGH | pyproject.toml specification is a finalized standard; src layout migration is a well-understood pattern; entry point translation is mechanical and fully specified |
| Pitfalls | HIGH | Derived from direct codebase inspection of `setup.py`, `kotti/__init__.py`, `kotti/migrate.py`, `kotti/sqla.py`, `kotti/sanitizers.py`, `kotti/tests/__init__.py`, and CI workflows — not from general patterns |

**Overall confidence: HIGH**

### Gaps to Address

- **`nh3` attribute allowlist implementation:** The callable `attributes` pattern in `kotti/sanitizers.py` needs a concrete replacement implementation. Research identified the problem precisely but the specific nh3 attribute dict that preserves Kotti's current HTML sanitization behavior needs to be designed at implementation time. Write characterization tests first.

- **`fanstatic.libraries` entry point with `importlib.metadata`:** ARCHITECTURE.md flags this as MEDIUM confidence — fanstatic 1.x's use of `importlib.metadata` for entry point discovery in editable install mode is not directly verified. Smoke test (start dev server, confirm CSS/JS loads) is the detection mechanism.

- **Specific action version numbers:** `astral-sh/setup-uv` version numbers should be verified at implementation time via the GitHub releases page. The pattern is correct; the exact pinned version may have changed.

- **Pyramid 3.10–3.13 compatibility:** `pyramid>=1.9,<2` compatibility with Python 3.12 and 3.13 is flagged as uncertain by ARCHITECTURE.md. The CI matrix change may surface compatibility issues in Pyramid 1.x dependencies that require pin adjustments not yet identified.

---

## Sources

### Primary (HIGH confidence — direct inspection or finalized standards)

- Kotti codebase direct inspection: `setup.py`, `kotti/__init__.py`, `kotti/migrate.py`, `kotti/sqla.py`, `kotti/sanitizers.py`, `kotti/traversal.py`, `kotti/tests/__init__.py`, `pytest.ini`, `tox.ini`, `.github/workflows/*.yml`
- `.planning/codebase/CONCERNS.md` — existing codebase analysis
- PEP 517 (build system interface), PEP 518 (build dependencies), PEP 621 (project metadata) — finalized Python standards
- Python EOL dates: python.org/downloads (3.8 Oct 2024, 3.9 Oct 2025, 3.10 Oct 2026)
- hatchling documentation: https://hatch.pypa.io/latest/
- uv documentation: https://docs.astral.sh/uv/
- ruff documentation: https://docs.astral.sh/ruff/
- PyPA Packaging Guide: https://packaging.python.org/en/latest/
- src layout rationale: https://hynek.me/articles/testing-packaging/

### Secondary (MEDIUM confidence — community consensus, training knowledge)

- nh3 as bleach replacement: https://nh3.readthedocs.io/
- bleach deprecation: bleach 6.1.0 release notes (Mozilla announced end-of-maintenance)
- Pyramid 2.0 changelog (`pyramid.compat` removal)
- SQLAlchemy 1.4 migration guide + 2.0 changelog (declarative_base, baked queries)
- pytest 4.0 changelog (yield_fixture removed), pytest 6.2 changelog (--strict renamed)
- astral-sh/setup-uv GitHub Action

---

*Research completed: 2026-02-27*
*Ready for roadmap: yes*
