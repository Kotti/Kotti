# Testing Patterns

**Analysis Date:** 2026-02-27

## Test Framework

**Runner:**
- pytest 6+ (`pytest>=6` in requirements)
- Config: `pytest.ini` at project root

**Assertion Library:**
- pytest assertions (standard `assert` statements)
- Exceptions tested with `pytest.raises()`

**Run Commands:**
```bash
pytest                              # Run all tests in kotti/ directory
pytest --runslow                    # Include slow/scaffolding tests
pytest -k test_name                 # Run tests matching pattern
pytest --cov=kotti --cov-report=term-missing  # With coverage report
pytest -v                           # Verbose output
pytest kotti/tests/test_util.py     # Run specific test file
```

**Additional Tools:**
- Coverage: pytest-cov with coverage.py
- Linting integrated: pytest-flake8
- Mock library: `from mock import Mock, patch` (compatible with unittest.mock)
- Web testing: WebTest TestApp and zope.testbrowser

## Test File Organization

**Location:**
- Co-located alongside source code: Tests in `kotti/tests/` directory parallel to source
- Separate test module per source module: `test_util.py` tests `util.py`, `test_resources.py` tests `resources.py`
- Functional tests in `kotti/tests/test_functional.py`, `test_node_views.py`

**Naming:**
- Test file pattern: `test_*.py` (e.g., `test_util.py`, `test_node.py`, `test_security.py`)
- Test class pattern: `Test<Feature>` (e.g., `TestNode`, `TestLogin`, `TestForbidden`)
- Test method pattern: `test_<scenario>` (e.g., `test_it`, `test_root_acl`, `test_max_length_40`)

**Structure:**
```
kotti/tests/
├── __init__.py              # Fixture definitions (major fixtures here)
├── conftest.py              # pytest configuration and simple fixtures
├── test_util.py
├── test_node.py
├── test_functional.py
├── test_security.py
└── ... other test modules
```

## Test Structure

**Suite Organization:**
```python
# Pytest function-based test (modern style - preferred)
class TestRequestCache:
    @property
    def cache_decorator(self):
        from kotti.util import request_cache
        return request_cache

    def test_it(self, dummy_request):
        from kotti.util import clear_cache
        called = []

        @self.cache_decorator(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        assert len(called) == 1
```

**Setup patterns:**
- Fixture injection via function parameters: `def test_root_acl(self, db_session, root):`
- Class-based organization with setUp method (legacy, deprecated):
  ```python
  class TestTitleToName:
      def setUp(self):
          from pyramid.threadlocal import get_current_registry
          r = get_current_registry()
          settings = r.settings = {}
          settings["kotti.url_normalizer"] = [url_normalizer]
  ```

**Teardown pattern:**
- Handled by pytest fixture cleanup (yield_fixture)
- Manual transaction cleanup via `transaction.abort()` and `transaction.commit()`
- Deprecated unittest-style classes: `UnitTestBase`, `FunctionalTestBase` with `setUp`/`tearDown` methods

**Assertion pattern:**
```python
# Direct assertions
assert len(called) == 1
assert ace in root.__acl__[1:-1]
assert title_to_name("Foo Bar") == "foo-bar"

# Exception assertions
from pytest import raises
with raises(AttributeError):
    root._get_acl()
```

## Fixtures and Test Data

**Fixture definitions in `kotti/tests/__init__.py`:**

Major fixtures (with dependencies):
- `custom_settings` - Overridable session-scoped settings fixture
- `unresolved_settings` - Resolved test settings (session scope)
- `settings` - Final application settings (session scope)
- `connection` - SQLAlchemy engine connection (session scope)
- `content` - Default test content created via populator (function scope)
- `db_session` - Active database session with savepoint rollback (function scope)
- `config` - Pyramid Configurator with test settings
- `setup_app` - WSGI application instance
- `app` - Full test app with fixtures (function scope)
- `root` - Kotti's root node object
- `dummy_request` - Pyramid DummyRequest for testing
- `dummy_mailer` - DummyMailer for email testing
- `workflow` - Kotti's workflow system initialized
- `browser` - zope.testbrowser.Browser for functional tests
- `webtest` - WebTest TestApp wrapper
- `filedepot` - Configured file storage for tests
- `depot_tween` - Depot middleware for file uploads
- `mock_filedepot` - Mock file depot (not db-integrated)
- `no_filedepots` - Cleared depot configuration

**Fixture location:**
- Primary fixtures: `kotti/tests/__init__.py` (60+ lines of fixture definitions)
- Simple fixtures: `kotti/tests/conftest.py` (app, extra_principals)
- Module-specific fixtures: In individual test modules or conftest.py in subdirectories

**Custom test data pattern:**

Mixin pattern for test-specific setup:
```python
class TestRequestCache:
    @property
    def cache_decorator(self):
        from kotti.util import request_cache
        return request_cache
```

Extra principals fixture:
```python
@fixture
def extra_principals(db_session):
    from kotti.security import get_principals
    P = get_principals()
    P["bob"] = dict(name="bob", title="Bob")
    P["frank"] = dict(name="frank", title="Frank")
    P["group:bobsgroup"] = dict(name="group:bobsgroup", title="Bob's Group")
    return P
```

## Mocking

**Framework:** mock library (compatible with unittest.mock)

**Patterns:**

Basic mocking:
```python
from mock import Mock, patch

# Create mock objects
func = Mock()
closer = Mock()

# Patch external dependencies
with patch("kotti.util.docopt") as docopt:
    docopt.return_value = {"<config_uri>": "app.ini"}
    assert docopt.call_count == 1
```

Browser/request mocking for authentication:
```python
@user("admin")  # pytest marker that sets authenticated_userid
def test_it(self, browser):
    # Browser is automatically authenticated as "admin"
    browser.open(BASE_URL + "/@@add_file")
```

Database session mocking pattern - savepoints for rollback:
```python
@yield_fixture
def db_session(config, content, connection):
    trans = connection.begin()  # Begin transaction
    from kotti import DBSession
    yield DBSession()
    trans.rollback()  # Rollback after test
    transaction.abort()
```

**What to Mock:**
- External service calls (doctests in docopt, bootstrap)
- File system operations when not testing file handling
- Web service calls (patch pyramid.request, etc.)
- Expensive operations (authentication checks via monkeypatch)

**What NOT to Mock:**
- Database operations (use fixtures with transaction rollback instead)
- Core ORM behavior (test against real SQLAlchemy)
- Pyramid request/response cycle
- Application configuration

## Fixtures and Factories

**Test data factories:**

MemoryFileStorage subclass for testing:
```python
class TestStorage(MemoryFileStorage):
    def __bool__(self):
        # required for test mocking
        return True

    def get(self, file_or_id):
        f = super().get(file_or_id)
        f.last_modified = datetime(2012, 12, 30)
        return f
```

Dummy objects for request handling:
```python
class Dummy(dict):
    # noinspection PyMissingConstructor
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
```

Database fixture with transaction isolation:
```python
@yield_fixture
def filedepot(db_session, depot_tween):
    from depot.manager import DepotManager
    DepotManager._depots = {"filedepot": MagicMock(wraps=TestStorage())}
    DepotManager._default_depot = "filedepot"
    yield DepotManager
    db_session.rollback()
    DepotManager._clear()
```

**Location:**
- Fixtures: `kotti/tests/__init__.py` and `kotti/tests/conftest.py`
- Test data assets: `kotti/tests/` (sendeschluss.jpg, logo.png referenced via `testing.asset()` helper)

## Coverage

**Requirements:** No enforced minimum in pytest.ini, but coverage reports generated

**View Coverage:**
```bash
pytest --cov=kotti --cov-report=term-missing  # Terminal report
pytest --cov=kotti --cov-report=html          # HTML report
```

**Coverage config:** ``.coveragerc`` file
```ini
[run]
omit =
  *test*py
  kotti/alembic/*
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and methods (e.g., `test_it` methods testing single utilities)
- Approach: Pytest classes with fixtures, isolated database session per test
- Example: `TestRequestCache.test_it()` - tests caching decorator in isolation
- Location: `kotti/tests/test_*.py` files

**Integration Tests:**
- Scope: Multiple components working together (e.g., Node ACL integration)
- Approach: Use full db_session fixture with transaction rollback
- Example: `TestNode.test_root_acl()` - tests node persistence and ACL system
- Database operations: Full SQLAlchemy ORM used with transaction isolation
- Location: Most of `kotti/tests/test_*.py` files (integrated with database)

**Functional/E2E Tests:**
- Framework: zope.testbrowser + webtest TestApp
- Scope: Full HTTP request/response cycle through WSGI app
- Approach: Browser fixture for navigation, login, form submission
- Example: `TestUploadFile.test_it()` - tests file upload through web interface
- Auth marker: `@user("admin")` pytest marker pre-authenticates
- Location: `kotti/tests/test_functional.py`

**View tests:**
- Scope: Testing Pyramid view functions and classes
- Pattern: Use `dummy_request` fixture to create request context
- Example: Form view testing with CSRFSchema validation

## Common Patterns

**Async Testing:**
Not used; application is synchronous WSGI.

**Error Testing:**

Exception assertions with pytest.raises:
```python
from pytest import raises

def test_set_and_get_acl(self, db_session, root):
    del root.__acl__
    with raises(AttributeError):
        root._get_acl()
```

HTTP exception testing:
```python
def test_forbidden(self, app):
    app.get("/@@edit", headers={"Accept": "*/json"}, status=403)
```

Database error testing:
```python
def test_unique_constraint(self, db_session, root):
    from kotti.resources import Node
    from sqlalchemy.exc import IntegrityError

    # Try to add two children with the same name to the root node:
    # (test implementation continues...)
```

## Pytest Markers

**Custom markers in pytest.ini:**
```ini
markers =
    user: mark test to be run as the given user
    slow: mark test to be run only with --runslow option
    pep8: pep8 marker
```

**Usage:**
```python
@pytest.mark.user("admin")
def test_login(self, browser):
    # Browser automatically authenticated as admin

@pytest.mark.slow
def test_scaffolding_generation(self):
    # Only run with: pytest --runslow
```

## Special Fixtures

**User Authentication:**
- Marker: `@user("admin")` or `@pytest.mark.user("admin")`
- Sets `DummyRequest.authenticated_userid` to "admin"
- Also pre-authenticates browser fixture

**Transaction Management:**
```python
import transaction

# Begin explicit transaction
transaction.begin()

# Commit changes
transaction.commit()

# Abort changes (rollback)
transaction.abort()
```

## Test Dependencies

**Deprecation note:** Old unittest-style classes are deprecated:
- `UnitTestBase` - Mark as deprecated, use pytest fixtures instead
- `FunctionalTestBase` - Use browser fixture and webtest instead
- `EventTestBase` - Use events fixture instead

Modern approach uses pytest fixtures exclusively.

---

*Testing analysis: 2026-02-27*
