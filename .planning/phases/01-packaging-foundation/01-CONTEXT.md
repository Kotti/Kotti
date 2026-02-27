# Phase 1: Packaging Foundation - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace setup.py/setup.cfg with pyproject.toml as single source of truth, adopt src layout (src/kotti/), and commit uv.lock. All six entry points must work, all non-Python assets must be in the published wheel. Old config files (setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini) are deleted.

</domain>

<decisions>
## Implementation Decisions

### Build backend
- RESEARCH NEEDED: Investigate whether uv can serve as a build backend (user reports seeing uv-only build workflows). If not, confirm hatchling is the right choice vs alternatives (flit-core, setuptools).
- Current requirement PKG-02 says hatchling — researcher should validate or recommend alternative

### Dependency groups
- Split extras: [dev], [test], [docs] as separate groups in pyproject.toml
- [dev] is a superset that includes [test] + [docs] — developers install `.[dev]`, CI installs granularly
- Use modern short names ([dev], [test], [docs]) but keep old names ([development], [testing]) as deprecated aliases
- RESEARCH NEEDED: Check current extras_require in setup.cfg for any user-facing extras that must be preserved for compatibility
- Deferred: Adding explicit [postgres]/[mysql] extras (see Deferred Ideas)

### Version management
- Static version string in pyproject.toml: `version = "2.1.0.dev0"`
- Bump from 2.0.10dev0 to 2.1.0.dev0 to signal the modernization milestone
- `kotti.__version__` exposed at runtime via `importlib.metadata.version("kotti")` for backwards compatibility
- The .dev0 suffix keeps it as a pre-release

### Transition cleanup
- Clean break: delete setup.py, setup.cfg, MANIFEST.in, pytest.ini, tox.ini in one commit
- Drop tox entirely — test commands use `uv run pytest` directly, CI workflow replaces tox matrices
- Migrate pytest configuration to [tool.pytest.ini_options] in pyproject.toml
- Dedicated commit for src layout move (`git mv kotti/ src/kotti/`) to preserve file history

### Lock file
- uv.lock covers base package + all extras (dev, test, docs) — full reproducibility
- CI uses `uv sync --locked` — fails if lock is stale, forcing explicit updates
- Lock targets `requires-python = ">=3.10"` for multi-version resolution

### Claude's Discretion
- Exact pyproject.toml section ordering and formatting
- hatchling configuration details for package data inclusion (.pt, .po, .mo, .zcml, alembic)
- How to handle the MANIFEST.in rules during migration to hatchling's inclusion config
- Commit ordering beyond the dedicated src layout move commit

</decisions>

<specifics>
## Specific Ideas

- User wants to investigate uv-only build workflows (no separate build backend) — saw this pattern somewhere. Researcher must confirm feasibility.
- Old extra names must remain as deprecated aliases for backwards compatibility
- The src layout move should be a clean `git mv` for reviewable history

</specifics>

<deferred>
## Deferred Ideas

- Adding explicit [postgres] and [mysql] extras for database-specific dependencies — would be new capability, evaluate in a future phase
- tox replacement patterns (if anyone externally uses tox with Kotti) — document in migration guide if needed

</deferred>

---

*Phase: 01-packaging-foundation*
*Context gathered: 2026-02-27*
