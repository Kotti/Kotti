# Coding Conventions

**Analysis Date:** 2026-02-27

## Naming Patterns

**Files:**
- Snake case: `util.py`, `resources.py`, `filedepot.py`
- Package directories: lowercase with underscores (`kotti`, `kotti/views`, `kotti/tests`)
- Test files: `test_*.py` (e.g., `test_util.py`, `test_node.py`)

**Functions:**
- Snake case: `get_localizer_for_locale_name()`, `title_to_name()`, `disambiguate_name()`
- Shorthand module-level functions: `_()` for translation, `_to_fieldstorage()` for internal utilities
- Factory functions: `authtkt_factory()`, `acl_factory()`, `beaker_session_factory()`
- Boolean predicates/checks: `has_permission()`, `view_permitted()`

**Variables:**
- Snake case for local variables: `app_iter`, `headerlist`, `base_url`
- Constants in UPPER_CASE: `TRUE_VALUES`, `FALSE_VALUES`, `_CACHE_ATTR`
- Underscore prefix for private/internal variables: `_lru_cache`, `_CACHE_ATTR`
- Abbreviated names acceptable for cache/request objects: `cache`, `request`, `config`

**Classes:**
- PascalCase: `ContainerMixin`, `ObjectEvent`, `Link`, `LinkBase`, `LinkRenderer`, `DummyRequest`
- Mixin suffix for mixins: `ContainerMixin`, `PersistentACLMixin`
- SQL Table names: snake_case in SQLAlchemy (e.g., `__tablename__ = "principals"`)

**Type Hints:**
- Used consistently in function signatures: `def has_permission(permission: str, context: "Node", request: "Request") -> PermitsResult:`
- String forward references for not-yet-defined types: `context: "Node"`
- Return type hints common: `-> Optional["Principal"]`, `-> Dict[str, Any]`

## Code Style

**Formatting:**
- Line length: Flexible, maximum 88 characters is the preference (flake8-max-line-length = 88)
- Indentation: 4 spaces (standard Python)
- No strict line-length enforcement for all code (flexibility in pytest.ini)

**Linting:**
- Tool: pytest-flake8 (runs as part of test suite)
- Config: `pytest.ini` with specific ignored rules
- Max line length: 88 characters for flake8 checks
- Ignored rules: E122, E123, E125, E128, E203, E251, E501 (line length), E711, E713, E714, E402, F821, W503
- Test-specific ignores: F841 (unused variables in tests)

**Import Organization:**

Order of imports (observed pattern):
1. Standard library imports (builtins first)
   - `import os`, `import re`, `from datetime import datetime`
   - `from collections.abc import MutableMapping`
   - `from typing import Any, List, Optional`

2. Third-party framework/library imports
   - `from pyramid.*` imports
   - `from sqlalchemy.*` imports
   - `from zope.*` imports
   - `import colander`, `from deform.*`
   - `from depot.*`

3. Local application imports
   - `from kotti import Base, DBSession, get_settings`
   - `from kotti.resources import Node, Document`
   - `from kotti.util import _, title_to_name`
   - `from kotti.interfaces import IContent`

**Path Aliases:**
- Package imports use full dotted paths: `from kotti.resources import Node`
- Relative imports not used; absolute imports enforced
- Translation string factory: `_ = TranslationStringFactory("Kotti")`

## Error Handling

**Patterns:**
- Catch specific exceptions: `except ValidationFailure as e:`, `except NoResultFound:`, `except ValueError:`
- HTTPException usage for web responses: `from pyramid.httpexceptions import HTTPFound`, `HTTPForbidden`, `HTTPNotFound`
- Return HTTPFound (302) for redirects with `location=` parameter
- Raise custom exceptions for domain logic: `raise Forbidden()`, `raise KeyError("Content of that type is not allowed...")`
- Try-except with fallback logic common:
  ```python
  try:
      return AuthTktAuthenticationPolicy(**kwargs)
  except TypeError:
      # BBB with Pyramid < 1.4
      kwargs.pop("hashalg")
      return AuthTktAuthenticationPolicy(**kwargs)
  ```
- No bare `except:` statements; always specify exception type
- Exception context preserved: `except SQLAlchemyError:`, `except NoResultFound:`

**Patterns for validation:**
- Colander schema validation with try-except: `except ValidationFailure as e:`
- Form validation returns error dict on failure, redirect on success
- Database integrity errors caught explicitly: `except IntegrityError:`, `except SQLAlchemyError:`

## Logging

**Framework:** Python standard library `print()` or custom logging (checked via usage patterns)

**Patterns:**
- Minimal logging; most code follows direct return or exception raising
- No explicit logger configuration found in main modules
- Event-driven logging via event handlers in `kotti/events.py`
- Status messages returned in template context dicts as `success_message` or `error_message`

## Comments

**When to Comment:**
- Backward compatibility notes: `# BBB with Pyramid < 1.4` (BBB = Backward Backward Compatibility)
- Workarounds and issue references: `# See #428, #427 and #31`, `# XXX need to understand what's happening`
- Complex algorithm explanations: Docstrings preferred over inline comments
- Non-obvious behavior: `# The root is required to have an empty name!`

**Docstrings:**
- Module-level docstrings standard: Start each module file with module documentation
- Include inheritance diagrams in module docstrings:
  ```python
  """
  Module description here.

  Inheritance Diagram
  -------------------

  .. inheritance-diagram:: kotti.resources
  """
  ```
- Class docstrings: Describe purpose and key attributes
  ```python
  class Principal(Base):
      """A minimal 'Principal' implementation.

      The attributes on this object correspond to what one ought to
      implement to get full support by the system.
      """
  ```
- Function docstrings: Include parameter descriptions when non-obvious
  ```python
  def testing_db_url():
      return os.environ.get("KOTTI_TEST_DB_STRING", "sqlite://")
  ```
- Return type hints in docstrings (rtype): `:rtype: pyramid.httpexceptions.HTTPFound or dict`

## Function Design

**Size:** Functions typically 5-30 lines; some utility functions are 1-5 lines

**Parameters:**
- Positional arguments for required parameters: `def has_permission(permission: str, context, request)`
- Keyword arguments used in factories and constructors
- Default arguments common: `def render_view(context, request, name="", secure=True)`
- Decorator parameters passed via closures:
  ```python
  def cache(compute_key, container_factory):
      def decorator(func):
          def replacement(*args, **kwargs):
  ```

**Return Values:**
- Single return value standard: Functions return one object (dict, list, object, or HTTPException)
- Tuple returns in specific cases: `ids, action = info` (unpacking from dict.get())
- None returns for actions without result: `def none_factory(**kwargs): return None`
- HTTPException returns for web routes (HTTPFound, HTTPForbidden, etc.)
- Dictionary returns common for view contexts: `return {}`

**Type Hints:**
- Optional hints with `Optional[Type]`: `Optional[str]`, `Optional[List[str]]`
- Union types with `Union[Type1, Type2]`
- Generic types from typing module: `List[str]`, `Dict[str, Any]`, `Iterable[int]`
- Forward references for circular dependencies: `"Node"`, `"Request"`

## Module Design

**Exports:**
- Public API via module `__all__` is not explicitly used; public items are assumed unless prefixed with `_`
- Private/internal modules marked with underscore: `_resolve_dotted()`, `_inject_mailer`
- Import from other modules into local namespace: `from kotti.util import _` (gettext)

**Barrel Files:**
- Main module `__init__.py` (`kotti/__init__.py`) serves as configuration entry point
- Sub-packages have their own `__init__.py` but minimal re-exports
- Views package uses `views/__init__.py` for view registration
- Tests use `tests/__init__.py` for pytest fixture definitions

## Code Organization Patterns

**Class hierarchies:**
- Mixins used to share behavior: `ContainerMixin(MutableMapping)`, `PersistentACLMixin`
- SQLAlchemy declarative base inheritance: `class Node(Base):`, `class Principal(Base):`
- View class inheritance: Subclass `FormView` for form-based views, `object` for simple views

**Dependency injection:**
- Configuration/settings passed via function arguments
- Request-scoped objects accessed via `get_current_request()` from pyramid.threadlocal
- Registry access via `get_current_registry()` for Pyramid interfaces

**Method organization in classes:**
- `__init__` first
- `__call__` or main methods
- Properties and reified properties
- Helper methods
- Class methods/static methods at end

---

*Convention analysis: 2026-02-27*
