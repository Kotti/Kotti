# External Integrations

**Analysis Date:** 2026-02-27

## APIs & External Services

**Email / SMTP:**
- pyramid_mailer service for sending transactional emails
  - SDK/Client: `pyramid_mailer.mailer.Mailer`
  - Configuration: `mail.default_sender` in ini files (e.g., `yourname@yourhost`)
  - SMTP settings: Standard SMTP configuration via Pyramid/Paste Deploy

## Data Storage

**Databases:**
- SQLite (default for development)
  - Connection: `sqlalchemy.url = sqlite:///%(here)s/Kotti.db`
  - Client: SQLAlchemy with SQLite dialect
  - Location: `kotti/sqla.py` (Base ORM setup), `kotti/__init__.py` (session management)

- PostgreSQL (supported for production)
  - Connection: `sqlalchemy.url = postgresql://[user]:[password]@localhost:5432/[dbname]`
  - Client: `psycopg2-binary` adapter
  - Driver detection: `kotti/alembic/versions/*` checks `conn.engine.dialect.name == 'postgresql'`

- MySQL/MariaDB (supported for production)
  - Connection: `sqlalchemy.url = mysql://root@localhost:3306/[dbname]`
  - Client: `mysqlclient` adapter
  - Driver detection: `kotti/filedepot.py` checks `conn.engine.dialect.name == "mysql"` for LONGBLOB type

**File Storage:**
- Database-backed storage (default):
  - Backend: `kotti.filedepot.DBFileStorage`
  - Implementation: `kotti/filedepot.py:DBStoredFile` - stores blobs directly in database
  - Configuration: `kotti.depot.0.backend = kotti.filedepot.DBFileStorage`

- Local filesystem storage (optional):
  - Backend: `depot.io.local.LocalFileStorage`
  - Configuration example in `development.ini` (commented out)
  - Storage path: `%(here)s/filestore` or custom location

- Depot Manager: Central file storage abstraction via `filedepot` library
  - Mount point: `kotti.depot_mountpoint = /depot` (configurable)
  - Wraps uploads: `pyramid` WSGI wrapper around file serving if `kotti.depot_replace_wsgi_file_wrapper = True`

**Caching:**
- Beaker cache/session integration via `pyramid_beaker`
  - Session factory: `pyramid_beaker.session_factory_from_settings`
  - Configuration: Standard Beaker session settings in ini files
  - No separate external cache service used (uses in-process/file-based)

## Authentication & Identity

**Auth Provider:**
- Custom local authentication (database-backed principals)
  - Implementation: `kotti/security.py:Principal` model stores users in database
  - Location: `kotti/security.py` (Principal model), `kotti/__init__.py` (auth policy factories)

**Authentication Policy:**
- AuthTkt (Authentication Ticket) from Pyramid
  - Factory: `kotti.authtkt_factory()` in `kotti/__init__.py`
  - Configuration: `kotti.authn_policy_factory = kotti.authtkt_factory`
  - Hash algorithm: SHA512
  - Secret: `kotti.secret2` setting (defaults to `kotti.secret`)
  - Callback: `list_groups_callback` for principal group resolution

**Authorization Policy:**
- ACL (Access Control List) from Pyramid
  - Factory: `kotti.acl_factory()` in `kotti/__init__.py`
  - Configuration: `kotti.authz_policy_factory = kotti.acl_factory`
  - Uses resource-based ACLs stored in database

**Principal Storage:**
- Database table: `principals` (auto-generated from `kotti.security.Principal` model)
  - Fields: `id`, `name` (unique), `password` (bcrypt hashed), `active`, `confirm_token`
  - Location: `kotti/resources.py` and `kotti/security.py`

**Group Management:**
- LocalGroup model for role-based access
  - Location: `kotti/resources.py`
  - Principal groups retrieved via `kotti.security.get_principals().get_groups(userid)`

## Monitoring & Observability

**Error Tracking:**
- No external error tracking service integrated
- Exception handling relies on Pyramid's built-in mechanisms
- Request logging configurable via Python logging in ini files

**Logs:**
- Standard Python logging framework
- Loggers defined in ini files (e.g., `development.ini`):
  - `kotti` logger - Application-level logging
  - `sqlalchemy.engine` - Database query logging (WARN by default)
  - `root` - Root logger
- Output: Console (stderr) by default

**Debugging:**
- pyramid_debugtoolbar (available in development configuration)
  - Enabled in `development.ini` via `pyramid.includes`
  - Provides request/response inspection and profiling

## CI/CD & Deployment

**Hosting:**
- WSGI application server: Waitress (included)
  - Configuration: `[server:main]` in ini files
  - Entry point: `kotti:main` (paste.app_factory)
  - Location: `kotti/__init__.py:main()`

**CI Pipeline:**
- GitHub Actions (`.github/workflows/`)
  - SQLite workflow: `sqlite.yml` - runs tests on Python 3.6-3.10
  - PostgreSQL workflow: `postgres.yml` - tests with PostgreSQL backend
  - MySQL workflow: `mysql.yml` - tests with MySQL backend
  - Triggers: Pushes to master/testing/stable, pull requests to master
  - Steps: Dependency installation, pytest execution, coverage reporting

- Scrutinizer CI (`.scrutinizer.yml`)
  - Code quality checks: duplicate code detection, code rating
  - Python version: 3.6.3
  - Coverage format: py-cc
  - Excluded paths: `kotti/tests/`, `kotti/alembic/`

**Package Distribution:**
- setuptools + PyPI (implied from setup.py structure)
- Console entry points defined:
  - `kotti-migrate` - Database migration runner
  - `kotti-reset-workflow` - Workflow state reset utility
  - `kotti-migrate-storage` - File storage migration tool

## Environment Configuration

**Required env vars (optional but common):**
- `KOTTI_TEST_DB_STRING` - Test database connection string (defaults to SQLite)
- Application settings in `.ini` files or via environment overrides

**Secrets location:**
- `kotti.secret` - Master secret for authentication (set in ini files)
- `mail.default_sender` - Email sender address (set in ini files)
- SMTP credentials - Via standard Paste Deploy/Python smtp config
- Database passwords - In SQLAlchemy URL string (ini files)

**.env pattern:**
- No `.env` file used - all configuration via ini files
- Secrets should be in environment or ini files not in version control

## Webhooks & Callbacks

**Incoming:**
- No webhook endpoints detected

**Outgoing:**
- Email callbacks via `kotti/message.py`:
  - `send_email()` function sends transactional emails
  - `email_set_password()` sends password reset emails
  - Used in login/registration flow: `kotti/views/login.py`
  - Location: `kotti/message.py:send_email()` and `email_set_password()`

**Event System:**
- Internal event dispatch (not webhooks):
  - Event classes: `ObjectInsert`, `ObjectUpdate`, `ObjectDelete`, `UserDeleted` in `kotti/events.py`
  - Event listeners: Plugin-based via Venusian decorator `@event_listeners(events)` in `kotti/events.py`
  - Used for: Content lifecycle hooks, audit trails, cache invalidation
  - Location: `kotti/events.py` (event system), plugins subscribe via configurators

## Key Integration Patterns

**Plugin Architecture:**
- Configurators: External packages extend via `kotti.configurators` setting
  - Example: `kotti_tinymce.kotti_configure` (optional editor)
  - Implementation: Functions that modify settings dict at startup
  - Location: `kotti/__init__.py:base_configure()` resolves and calls configurators

**Add-on System:**
- ZCML-based configuration via `kotti.zcml_includes`
- Python module imports via `kotti.base_includes`
- Fanstatic library registration for static assets
- All discoverable via entry points in setup.py

**Database Migrations:**
- Alembic integration in `kotti/alembic/`
- Migration configuration: `alembic.ini`
- Migrations auto-generate from model changes
- Supports SQLite, PostgreSQL, MySQL with dialect-specific logic

---

*Integration audit: 2026-02-27*
