# Phase 2: Runtime Dependency Updates - Research

**Researched:** 2026-02-27
**Domain:** Python dependency migration — bleach→nh3, pkg_resources→importlib, mock→unittest.mock
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Sanitization equivalence:** Semantic equivalence, not exact string match — HTML must render the same in a browser, minor whitespace/quoting differences are acceptable
- **Characterization tests:** Compare parsed DOM behavior, not raw string output; kept permanently as a regression suite (security-critical)
- **Allowlist tightening:** Tighten allowlists where bleach was overly broad, with deprecation warnings for anything dropped
- **Plugin compatibility:** New API function names for sanitizers; old names get deprecation shims that forward to new functions; shims live until next major Kotti version
- **Deprecation warning format:** Include migration instructions — "sanitize() is deprecated, use nh3_clean() instead. Will be removed in Kotti X.0"
- **pkg_resources removal scope:** Internal to Kotti only — no compatibility wrapper needed for plugins using pkg_resources directly
- **Phase 1 overlap / DEP-03/DEP-04:** Phase 2 does a thorough grep sweep to confirm zero remaining occurrences of `import mock` / `from mock` before marking complete
- **DEP-05 Alembic discovery:** Use stdlib `importlib.resources` (Python 3.10+ target, no backport needed)
- **DEP-07/DEP-08 pins:** pyramid>=1.9,<2 and sqlalchemy>=1.4,<2 verified as explicit success criterion after all changes
- **mock from pyproject.toml:** Remove `mock` from test dependencies if still listed (Phase 1 already did this — verify)

### Claude's Discretion

- How to handle nh3 gaps (tags/attributes bleach allowed but nh3 can't support) — pragmatic approach based on what nh3 actually supports
- Exact new function names for the sanitizer API
- Implementation details of `importlib.resources` for Alembic path discovery

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEP-01 | bleach + bleach-allowlist replaced with nh3 for HTML sanitization | nh3 0.3.3 API fully researched; migration pattern documented |
| DEP-02 | Sanitization behavior preserved (characterization tests pass before and after switch) | Test rewrite strategy documented; DOM-equivalence approach defined |
| DEP-03 | mock PyPI package replaced with stdlib unittest.mock in all test files | Only 1 file uses `import unittest.mock as mock` (legitimate); no `from mock import` remains |
| DEP-04 | pkg_resources replaced with importlib.metadata for version lookup | `get_version()` in `__init__.py` is the only remaining usage; migration is 1-line change |
| DEP-05 | pkg_resources.resource_filename replaced with importlib.resources for Alembic directory discovery | `str(importlib.resources.files('kotti') / 'alembic')` returns correct path; test assertions still pass |
| DEP-06 | kotti-migrate CLI works correctly after importlib migration (tested in fresh virtualenv) | CLI test strategy documented; no functional change to migrate logic |
| DEP-07 | pyramid>=1.9,<2 pin maintained | Pin already in pyproject.toml; verification-only task |
| DEP-08 | sqlalchemy>=1.4,<2 pin maintained | Pin already in pyproject.toml; verification-only task |
</phase_requirements>

## Summary

Phase 2 has four independent migration tracks: (1) bleach→nh3 sanitizer replacement with a new API + deprecation shims, (2) pkg_resources→importlib.metadata for `get_version()`, (3) pkg_resources.resource_filename→importlib.resources for Alembic path discovery, and (4) a sweep to confirm `mock` is fully eliminated. Tracks 2–4 are small (1–5 lines each). Track 1 is the only substantive implementation work.

The bleach→nh3 migration requires careful planning because the two libraries have meaningfully different APIs and behavior. nh3 wraps the Rust ammonia library and is ~20x faster than bleach but has a stricter/different attribute model. Key differences: (a) nh3 always removes `<script>` and `<style>` tags with their content, while bleach strips only the tags; (b) nh3 has no "allow all attributes via callable" mechanism — you must enumerate allowed attributes explicitly; (c) nh3 adds `rel="noopener noreferrer"` to links by default; (d) nh3 `attribute_filter` is a POST-filter that only runs on attributes already in the allowlist, not a bypass. The user decision to "tighten allowlists where bleach was overly broad" aligns perfectly with nh3's explicit-allowlist model.

The migration strategy is: write characterization tests first (capturing what nh3 actually does), then implement new functions (`xss_protection_nh3`, etc.), add deprecation shims for old names, update `pyproject.toml` (replace bleach/bleach-allowlist with nh3, remove setuptools pin), and verify the full test suite passes.

**Primary recommendation:** Implement in three waves: (Wave 0) characterization tests + grep sweeps; (Wave 1) sanitizer migration + new API; (Wave 2) importlib migrations + dependency cleanup.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nh3 | 0.3.3 (Feb 2026) | HTML sanitization replacing bleach | bleach is officially deprecated; nh3 is the maintained successor; Rust-backed, 20x faster |
| importlib.metadata | stdlib (3.10+) | Package version lookup replacing pkg_resources | stdlib, no external dep, already in use in kotti/__init__.py |
| importlib.resources | stdlib (3.10+) | Package file path discovery replacing pkg_resources.resource_filename | stdlib, Python 3.10+ target, returns pathlib.Path directly |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| zope.deprecation | already installed | Emit deprecation warnings for old sanitizer names | For the deprecation shims only |
| unittest.mock | stdlib | Test mocking (already in use) | Already migrated in Phase 1; verify-only in Phase 2 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| nh3 | bleach (keep) | bleach is deprecated, unmaintained since 2023, pins to old html5lib |
| nh3 | html-sanitizer | More Django-oriented, less mainstream for Pyramid ecosystem |
| importlib.resources direct | importlib_resources backport | Backport not needed: project targets Python 3.10+ which has full files() API |

## Architecture Patterns

### Pattern 1: New API + Deprecation Shims for Sanitizers

**What:** Add new functions (e.g., `xss_protection_nh3()`, or keep same names if behavior is identical enough) and add `warnings.warn()` deprecation shims for any public names that change.

**When to use:** Locked decision from CONTEXT.md — the user explicitly chose this approach.

**Key insight from CONTEXT.md:** The old function names (`xss_protection`, `minimal_html`, `no_html`) are registered via dotted string in `kotti.sanitizers` in `conf_defaults`. The decision says "new API function names for sanitizers; old names get deprecation shims." This means either:
- Option A: Keep same function names (no shims needed unless internal logic changes)
- Option B: Rename to e.g. `nh3_xss_protection` and add shims for old names

Given the CONTEXT.md says "New API function names," Option B is indicated. But the sanitizer names are configured via dotted strings in `conf_defaults`, so old configs would break without shims.

**Example structure:**
```python
# New implementation
def xss_protection_nh3(html: str) -> str:
    """Sanitizer that removes XSS-unsafe tags using nh3."""
    return nh3.clean(html, tags=_XSS_SAFE_TAGS, attributes=_XSS_SAFE_ATTRS, link_rel=None)

# Deprecation shim
def xss_protection(html: str) -> str:
    """Deprecated: use xss_protection_nh3."""
    import warnings
    warnings.warn(
        "xss_protection() is deprecated, use xss_protection_nh3() instead. "
        "Will be removed in Kotti 3.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return xss_protection_nh3(html)
```

### Pattern 2: importlib.resources for Alembic Directory

**What:** Replace `pkg_resources.resource_filename("kotti", "alembic")` with `str(importlib.resources.files("kotti") / "alembic")`

**When to use:** Anywhere `pkg_resources.resource_filename` is called with a package name and relative path.

**Example:**
```python
# Before
import pkg_resources
KOTTI_SCRIPT_DIR = pkg_resources.resource_filename("kotti", "alembic")

# After
import importlib.resources as importlib_resources
KOTTI_SCRIPT_DIR = str(importlib_resources.files("kotti") / "alembic")
```

**Verified behavior:** `importlib.resources.files('kotti') / 'alembic'` returns a `pathlib.PosixPath` in a source install. The `str()` call produces `/path/to/kotti/alembic`, which passes the existing test assertion `.endswith("kotti/alembic")`. No `as_file()` context manager needed — the alembic directory is always a real filesystem path (not inside a zip archive), and `str()` on a `Traversable` that IS a PosixPath works directly.

**Caveat (MEDIUM confidence):** If Kotti were ever installed from a zip/wheel without extraction, `importlib.resources.files()` returns a `zipimport.zipimporter`-backed `Traversable`, not a `PosixPath`, and `str()` would not give a filesystem path. For that case, `as_file()` would be needed. Since alembic scripts must be real files (alembic's `ScriptDirectory` reads them from disk), the safest pattern is:

```python
# Zip-safe pattern (use this)
import importlib.resources as importlib_resources
import atexit
from contextlib import ExitStack

_file_manager = ExitStack()
atexit.register(_file_manager.close)
KOTTI_SCRIPT_DIR = str(
    _file_manager.enter_context(
        importlib_resources.as_file(importlib_resources.files("kotti") / "alembic")
    )
)
```

However, given Kotti's wheel is built with hatchling (which does NOT zip the package), the simpler `str(files("kotti") / "alembic")` is sufficient. Use the simpler form.

### Pattern 3: importlib.metadata for Version

**What:** Replace `pkg_resources.require("Kotti")[0].version` with `importlib.metadata.version("Kotti")`

**Example:**
```python
# Before (kotti/__init__.py lines 10, 171)
import pkg_resources
def get_version():
    return pkg_resources.require("Kotti")[0].version

# After
def get_version():
    return __version__  # already set via importlib.metadata at module top
```

The file already imports `_version` from `importlib.metadata` at the top for `__version__`. The `get_version()` function can simply return `__version__` or call `_version("Kotti")` directly.

### Anti-Patterns to Avoid

- **attribute_filter as "allow all" bypass:** nh3's `attribute_filter` runs AFTER the `attributes` allowlist. Returning `value` from `attribute_filter` only works for attributes already admitted by `attributes`. To allow an attribute, it must be in the `attributes` dict — not just passed through the filter.
- **Adding `script` or `style` to nh3 `tags`:** nh3/ammonia always has these in `clean_content_tags`. Attempting to add them to `tags` raises a `PanicException`. These tags are unconditionally removed with their content.
- **Combining `link_rel` with `rel` in attributes:** If you add `rel` to the `attributes` dict for tag `a`, you MUST set `link_rel=None`. Setting both panics with an assertion failure.
- **`as_file()` context manager expiring too early:** If `as_file()` is used in a `with` block at module import, the path becomes invalid after the block exits. Use `ExitStack` + `atexit` for module-level paths, or just use `str(files(...))` for installed (non-zip) packages.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML sanitization | custom tag-stripping regex | nh3 | HTML parsing is not regex-parseable; XSS edge cases require a real parser + ammonia's proven logic |
| Attribute allowlist management | dynamic "allow all" callable | explicit dict in nh3 | nh3 has no callable attribute mechanism; bleach's callable was dangerous (could accidentally allow event handlers) |
| Package path resolution | `__file__`-based path manipulation | `importlib.resources.files()` | Works correctly in zip/wheel installs; stdlib, no external dep |

**Key insight:** The bleach→nh3 migration is NOT a drop-in replacement. The API models differ fundamentally. Treat it as implementing new sanitizer functions with nh3, not translating bleach calls line-by-line.

## Common Pitfalls

### Pitfall 1: nh3 Removes Script Content, Bleach Only Strips Tags

**What goes wrong:** `<script>alert('XSS!')</script>` — bleach with `strip=True` produces `alert('XSS!')` (content preserved, tags stripped). nh3 produces `` (content removed entirely, nothing remains).

**Why it matters:** The existing `test_sanitizers.py` test for `xss_protection` checks: `assert "<script>" not in sanitized` but does NOT check whether script content is removed. After migration, the content IS removed — which is MORE secure but a behavioral change. The characterization tests must capture this difference explicitly.

**How to avoid:** Write characterization tests that document nh3 behavior (content removed), not bleach behavior (content kept). The DOM-equivalence approach in CONTEXT.md means we check "page renders the same" not "strings are equal."

### Pitfall 2: Existing Test Assertion 'b size="17"' Will Break

**What goes wrong:** The current `_verify_xss_protection()` asserts `'b size="17"' in sanitized`. This assertion captures bleach behavior: bleach with `attributes=lambda: True` preserves ALL attributes including the deprecated `SIZE=17` (normalised to lowercase `size="17"`). nh3 with a curated attribute allowlist will strip `SIZE` since it's not a standard HTML attribute for `<b>`.

**How to avoid:** This test assertion must CHANGE as part of the characterization test rewrite. The new assertion should NOT check for `size="17"` — stripping non-standard attributes is the correct tightened behavior.

**Warning signs:** If `_verify_xss_protection` assertions are just copied into new characterization tests unchanged, the tests will fail on nh3.

### Pitfall 3: minimal_html Test Asserts `style=""` (Empty Style)

**What goes wrong:** The current `_verify_minimal_html()` asserts `'style=""' in sanitized`. This is because bleach's CSS sanitizer strips all CSS properties (because `styles=[]`), leaving an empty `style=""` attribute. nh3 with `attributes={'*': {'style'}}` preserves the actual style value: `style="color: red"` remains as `style="color: red"`, not `style=""`.

**How to avoid:** The `minimal_html` behavior with nh3 is actually better (keeps the style content), but the test must be updated. The characterization test should check for the nh3 behavior.

### Pitfall 4: nh3 link_rel Default Adds rel="noopener noreferrer"

**What goes wrong:** bleach does not add `rel` attributes. nh3 by default adds `rel="noopener noreferrer"` to ALL `<a>` tags. The existing test asserts `'<a href="internal.html" target="_blank">internal</a>'` — this will fail because nh3 transforms this to `<a href="internal.html" rel="noopener noreferrer">internal</a>` (also drops `target` unless explicitly allowed).

**How to avoid:** The new `xss_protection` implementation must decide: (a) keep `link_rel` default (adds security, changes output), or (b) set `link_rel=None` and allow `target` in the attribute allowlist. Since the goal is "tighten where overly broad," keeping `link_rel="noopener noreferrer"` and allowing `target` via attributes is the right choice. The test must be updated accordingly.

### Pitfall 5: DEP-03 Verification — One Legitimate `import unittest.mock as mock`

**What goes wrong:** A grep for `mock` will find `test_register.py:1:import unittest.mock as mock`. This is legitimate — the comment explains it avoids a memory error with `from mock import call`. This is NOT a problem to fix.

**How to avoid:** The grep sweep should check for `^from mock import` and `^import mock` (the PyPI mock package), not `unittest.mock`. The file `test_register.py` is already correct.

### Pitfall 6: setuptools Pin Must Be Removed After pkg_resources Elimination

**What goes wrong:** `pyproject.toml` has `"setuptools<79",  # provides pkg_resources; replaced in Phase 2`. If pkg_resources is eliminated but this pin is not removed, setuptools will remain pinned unnecessarily. More critically: setuptools 78.x is current (2025-04) and the pin `<79` is tight — it should be removed entirely once no code imports `pkg_resources`.

**How to avoid:** After removing all `import pkg_resources` from kotti source, remove the `"setuptools<79"` line from `pyproject.toml` dependencies AND run `uv lock` to update the lockfile.

### Pitfall 7: docs/conf.py Also Uses pkg_resources

**What goes wrong:** `docs/conf.py` has `import pkg_resources` and `pkg_resources.get_distribution("Kotti").version`. This is NOT in `src/kotti/` — it's in `docs/`. The grep sweep must include this file or DEP-04 will not be fully complete.

**How to avoid:** Include `docs/conf.py` in the pkg_resources sweep and update it:
```python
# Before
version = pkg_resources.get_distribution("Kotti").version
# After
from importlib.metadata import version as _pkg_version
version = _pkg_version("Kotti")
```

## Code Examples

Verified patterns from hands-on testing:

### nh3.clean() — Full Signature

```python
import nh3

nh3.clean(
    html,                          # str: input HTML
    tags=None,                     # Set[str] | None: allowed tags (None = nh3.ALLOWED_TAGS)
    clean_content_tags=None,       # Set[str] | None: tags whose content is also removed (script/style always included)
    attributes=None,               # Dict[str, Set[str]] | None: allowed attrs per tag; '*' = wildcard
    attribute_filter=None,         # Callable[[tag, attr, value], str|None] — post-filter on allowed attrs
    strip_comments=True,           # bool: remove HTML comments
    link_rel='noopener noreferrer',# str | None: rel attr injected into <a> tags
    generic_attribute_prefixes=None, # Set[str]: allow attrs with these prefixes (e.g. {'data-'})
    tag_attribute_values=None,     # Dict[str, Dict[str, Set[str]]]: whitelist specific attr values
    set_tag_attribute_values=None, # Dict[str, Dict[str, str]]: force specific attr values
    url_schemes=None,              # Set[str] | None: allowed URL schemes
    allowed_classes=None,          # Dict[str, Set[str]] | None: allowed CSS classes per tag
    filter_style_properties=None,  # Set[str] | None: allowed CSS property names in style attrs
)
```

### nh3 Default Constants

```python
import nh3

# 75 tags (NOT 118 like bleach generally_xss_safe)
nh3.ALLOWED_TAGS  # {'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'dd', 'del', ...}

# Very restrictive attribute defaults
nh3.ALLOWED_ATTRIBUTES  # {'a': {'href', 'hreflang'}, 'img': {'src', 'alt', 'width', 'height', 'align'}, ...}
# NOTE: no 'class', 'id', 'style', 'target' by default!

nh3.ALLOWED_URL_SCHEMES  # {'http', 'https', 'mailto', 'ftp', ...} (25 schemes)
```

### xss_protection Replacement Strategy

```python
import nh3
from bleach_allowlist import generally_xss_safe  # for tag reference during transition

# Tags: generally_xss_safe MINUS 'style' (panics if added to nh3 tags)
# 'script' is safe to add (doesn't panic), but nh3 removes script content anyway
_XSS_SAFE_TAGS = frozenset(generally_xss_safe) - {'style'}

# Attributes: curated allowlist (tightened from bleach's "allow everything" lambda)
_XSS_SAFE_ATTRS = {
    '*': {'class', 'id', 'style', 'title', 'lang', 'dir'},
    'a': {'href', 'target'},        # 'rel' conflicts with link_rel — use link_rel param
    'img': {'src', 'alt', 'width', 'height'},
    'table': {'border', 'cellpadding', 'cellspacing', 'width', 'summary'},
    'td': {'colspan', 'rowspan', 'align', 'valign'},
    'th': {'colspan', 'rowspan', 'scope', 'align', 'valign'},
    'ol': {'start', 'type'},
    'blockquote': {'cite'},
    # etc. — see "Don't include event handlers" note
}

def xss_protection_nh3(html: str) -> str:
    return nh3.clean(
        html,
        tags=_XSS_SAFE_TAGS,
        attributes=_XSS_SAFE_ATTRS,
        link_rel="noopener noreferrer",  # security: add rel to all links
    )
```

### no_html Replacement

```python
def no_html_nh3(html: str) -> str:
    return nh3.clean(html, tags=frozenset(), attributes={})
```

Verified behavior (hands-on test):
- Input: `<h1>Title</h1><p>Paragraph</p>`
- Output: `TitleParagraph` (no tags, content preserved) — matches bleach behavior

### minimal_html Replacement

```python
from bleach_allowlist import markdown_tags, print_tags, markdown_attrs, print_attrs

_MINIMAL_TAGS = frozenset(markdown_tags) | frozenset(print_tags)
# Note: 'tfoot' is in print_tags AND nh3.ALLOWED_TAGS — no conflict

# Build combined attrs dict
_MINIMAL_ATTRS = {
    '*': {'class', 'id'},           # from markdown_attrs['*'] + extras
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'a': {'href', 'title'},         # 'alt' from markdown_attrs, 'title' from both
}
# Note: 'style' — DECISION POINT (see Open Questions)

def minimal_html_nh3(html: str) -> str:
    return nh3.clean(
        html,
        tags=_MINIMAL_TAGS,
        attributes=_MINIMAL_ATTRS,
        link_rel="noopener noreferrer",
    )
```

### importlib.resources Replacement for migrate.py

```python
# Before
import pkg_resources
KOTTI_SCRIPT_DIR = pkg_resources.resource_filename("kotti", "alembic")

# After (simple form — works because hatchling builds don't zip packages)
import importlib.resources as importlib_resources
KOTTI_SCRIPT_DIR = str(importlib_resources.files("kotti") / "alembic")
```

Verified: `str(importlib_resources.files("kotti") / "alembic")` returns `"/path/to/kotti/alembic"` which passes `.endswith("kotti/alembic")` — the existing test assertions in `test_migrate.py` remain valid.

### importlib.metadata Replacement for __init__.py

```python
# Before
import pkg_resources
def get_version():
    return pkg_resources.require("Kotti")[0].version

# After (using already-imported _version from module top)
def get_version():
    return __version__  # __version__ already set via importlib.metadata at top of file
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| bleach + bleach-allowlist | nh3 | bleach deprecated 2023; nh3 stable 2024-2026 | API change required; not drop-in |
| pkg_resources (setuptools) | importlib.metadata + importlib.resources | Python 3.9+ (3.10 complete) | setuptools no longer needed as runtime dep |
| mock (PyPI) | unittest.mock (stdlib) | Python 3.3+, standard since Python 3 | Already done in Phase 1 |

**Deprecated/outdated:**
- bleach: Officially deprecated by Mozilla. Last release 6.1.0 (2023). html5lib dependency is itself unmaintained.
- bleach-allowlist: Frozen tag/attr lists; no security updates expected.
- pkg_resources: Deprecated in setuptools>=67; emits `DeprecationWarning` on import in setuptools>=78.
- `mock` PyPI package: Unnecessary since Python 3.3; `unittest.mock` is the stdlib replacement.

## Open Questions

1. **Exact new function names for sanitizers**
   - What we know: CONTEXT.md says "new API function names"; the existing names are `xss_protection`, `minimal_html`, `no_html`, `sanitize`
   - What's unclear: Should the new names be `xss_protection_nh3` / `minimal_html_nh3` / `no_html_nh3`? Or keep same names since they're configured by dotted string and old configs must work via shims anyway?
   - Recommendation: Keep implementation functions as `xss_protection`, `minimal_html`, `no_html` (unchanged names), add internal `_xss_protection_bleach` etc. names only if needed for tests. The "new API" comment in CONTEXT.md likely refers to the fact that nh3 is the new underlying API, not necessarily renaming the Python functions. This avoids needing shims for the common case. Verify this interpretation with user if unclear.

2. **Style attribute handling in minimal_html**
   - What we know: bleach `minimal_html` uses `styles=[]` which strips CSS properties but leaves `style=""` (empty). nh3 with `attributes={'*': {'style'}}` preserves style values. The `print_attrs` dict includes `'style'` in the `'*'` key.
   - What's unclear: Should `minimal_html_nh3` allow `style` values through, or strip style entirely?
   - Recommendation: Allow `style` attribute through nh3 (since `print_attrs` includes it). This is a behavior IMPROVEMENT over bleach (which left empty `style=""`). Characterization tests must document this difference. Use `filter_style_properties` if a style property allowlist is needed.

3. **The deprecation warning version number "Kotti X.0"**
   - What we know: CONTEXT.md says deprecation warnings should say "Will be removed in Kotti X.0"
   - What's unclear: What is the next major version? Current version is 2.1.0.dev0.
   - Recommendation: Use "Kotti 3.0" as the removal target. This is the next major version and aligns with the milestone roadmap intent.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest src/kotti/tests/test_sanitizers.py src/kotti/tests/test_migrate.py -x -q` |
| Full suite command | `uv run pytest src/kotti/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-01 | bleach/bleach-allowlist removed from deps; nh3 present | smoke | `pip show bleach; pip show nh3` (in fresh venv) | manual |
| DEP-02 | Sanitization behavior preserved — DOM equivalence | characterization | `uv run pytest src/kotti/tests/test_sanitizers.py -x -q` | ✅ (must be rewritten) |
| DEP-03 | Zero `from mock import` / `import mock` in source | grep | `grep -rn "^from mock import\|^import mock" src/kotti/` | manual |
| DEP-04 | `pkg_resources` absent from kotti source | grep | `grep -rn "import pkg_resources" src/kotti/ docs/` | manual |
| DEP-05 | Alembic path discovery uses importlib.resources | unit | `uv run pytest src/kotti/tests/test_migrate.py -x -q` | ✅ |
| DEP-06 | kotti-migrate CLI works in fresh virtualenv | integration (manual) | `kotti-migrate development.ini list_all` | manual |
| DEP-07 | pyramid<2 pin in pyproject.toml | config check | `grep "pyramid>=1.9,<2" pyproject.toml` | manual |
| DEP-08 | sqlalchemy<2 pin in pyproject.toml | config check | `grep "sqlalchemy>=1.4" pyproject.toml` | manual |

### Sampling Rate

- **Per task commit:** `uv run pytest src/kotti/tests/test_sanitizers.py src/kotti/tests/test_migrate.py -x -q`
- **Per wave merge:** `uv run pytest src/kotti/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `src/kotti/tests/test_sanitizers.py` — rewrite characterization tests to use DOM/parse comparison, not string match; add nh3 behavioral tests BEFORE implementation change (capture baseline and new behavior)

*(Existing infrastructure covers remaining requirements — test_migrate.py already tests the KOTTI_SCRIPT_DIR usage)*

## Sources

### Primary (HIGH confidence)

- nh3 0.3.3 (installed, `nh3.pyi` stub + `help(nh3.clean)`) — full API verified hands-on
- nh3 defaults verified by running `import nh3; nh3.ALLOWED_TAGS, nh3.ALLOWED_ATTRIBUTES, nh3.ALLOWED_URL_SCHEMES` in project venv
- bleach_allowlist 1.0.3 (installed) — `generally_xss_safe`, `markdown_tags`, `print_tags`, `markdown_attrs`, `print_attrs` contents enumerated
- Python 3.10 stdlib `importlib.resources.files()` — verified against kotti package in project venv
- `importlib-resources` migration guide — https://importlib-resources.readthedocs.io/en/latest/migration.html
- kotti source code: `src/kotti/sanitizers.py`, `src/kotti/migrate.py`, `src/kotti/__init__.py`, `src/kotti/tests/test_sanitizers.py`, `src/kotti/tests/test_migrate.py`

### Secondary (MEDIUM confidence)

- nh3 documentation overview — https://nh3.readthedocs.io/ (fetched, confirmed API structure)
- nh3 vs bleach feature gaps — GitHub issue #10 https://github.com/messense/nh3/issues/10 (CSS sanitization gap confirmed)
- bleach→nh3 migration article — https://daniel.feldroy.com/posts/2023-06-converting-from-bleach-to-nh3 (attributes dict structure confirmed)

### Tertiary (LOW confidence)

None — all key claims verified hands-on or via official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — nh3 version and API verified hands-on in project venv
- Architecture: HIGH — patterns tested against actual kotti test inputs
- Pitfalls: HIGH — pitfalls discovered through direct behavioral testing (panics, assertion differences)
- Validation architecture: HIGH — existing test infrastructure fully inventoried

**Research date:** 2026-02-27
**Valid until:** 2026-05-27 (90 days — nh3 is stable; stdlib APIs don't change)
