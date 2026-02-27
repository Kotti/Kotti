# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- Python 3.6, 3.7, 3.8, 3.9, 3.10 - Server-side CMS framework and application logic

**Secondary:**
- JavaScript - Client-side interactivity (included via fanstatic resource management)
- HTML/Template - Chameleon templates for view rendering

## Runtime

**Environment:**
- Python 3.6+ (Python 3.10 support verified via GitHub workflows)

**Package Manager:**
- pip - Python package installation
- Lockfile: `requirements.txt` (pinned versions)

## Frameworks

**Core:**
- Pyramid 1.10.8 - Web framework (WSGI-based, used as `paste.app_factory`)
- SQLAlchemy 1.4.36 - Object-relational mapper and SQL toolkit
- Chameleon 3.10.0 - Template engine for server-side rendering

**Web Components:**
- pyramid_beaker - Session management via Beaker session factory
- pyramid_chameleon - Chameleon template integration for Pyramid
- pyramid_deform - Integration of Deform form library with Pyramid
- pyramid_mailer - Email sending capabilities
- pyramid_tm - Transaction management integration
- pyramid_zcml - ZCML configuration support for Pyramid
- pyramid_debugtoolbar - Development debugging toolbar

**Forms & Validation:**
- colander 1.8.3 - Schema validation library
- deform 2.0.14 - Web form generation and processing
- FormEncode 2.0.1 - HTML form validation
- formencode - Email validation via `Email()` validator

**Security:**
- bcrypt 3.2.2 - Password hashing
- Pyramid's built-in authentication (`AuthTktAuthenticationPolicy`)
- Pyramid's built-in authorization (`ACLAuthorizationPolicy`)

**Database:**
- zope.sqlalchemy - Integrates SQLAlchemy with Zope transaction management
- transaction 3.0.1 - Transaction management

**File Upload & Storage:**
- filedepot 0.8.0 - File upload handling
- depot - Storage abstraction layer for file uploads

**Frontend Assets:**
- fanstatic 1.2 - Static resource (CSS/JS) management and bundling
- Bootstrap 3.3.4 - CSS framework (via js.bootstrap)
- jQuery 1.9.1 - JavaScript library (via js.jquery)
- jQuery UI 1.10.3 - UI widgets (via js.jqueryui)
- Select2 4.0.4 - Enhanced select dropdowns
- TinyMCE 4.5.4 - Rich text editor
- Angular 1.1.4 - Front-end framework (included as dependency)

**HTML Processing:**
- bleach 4.1.0 - HTML sanitization (XSS protection)
- bleach-allowlist 1.0.3 - Predefined safe HTML tag lists
- html2text 2020.1.16 - HTML to plain text conversion

**Internationalization:**
- Babel 2.10.1 - Internationalization/localization library
- lingua 4.15.0 - i18n utilities
- translationstring 1.4 - Message translation support
- Unidecode 1.3.4 - Unicode to ASCII transliteration
- anyascii 0.3.1 - Character encoding conversion

**Testing:**
- pytest 6+ - Test runner
- pytest-cov - Coverage plugin for pytest
- pytest-flake8 - Flake8 linting integration
- pytest-virtualenv - Virtual environment management for tests
- WebTest - HTTP testing library
- mock - Mocking library (Python < 3.3)
- Pillow - Image processing for thumbnail filter tests
- pyquery - jQuery-like syntax for XML/HTML manipulation
- zope.testbrowser 5.0.0+ - Browser-like testing interface

**Build & Development:**
- setuptools - Package building and distribution
- setuptools_git - Git integration for setuptools
- alembic 1.7.7 - Database migration management
- pip-selfcheck.json - Pip version checking

**Database Drivers (optional, installed per-environment):**
- psycopg2-binary - PostgreSQL adapter
- mysqlclient - MySQL/MariaDB adapter
- (SQLite built-in to Python)

**Build/CI:**
- GitHub Actions (`.github/workflows/` - sqlite.yml, postgres.yml, mysql.yml)
- Scrutinizer-CI (`.scrutinizer.yml` - code quality checks)

## Configuration

**Environment:**
- Configured via Paste Deployment ini files (`app.ini`, `development.ini`)
- Settings injected through Pyramid Configurator
- Environment variables supported but not required (optional sensitive data)

**Build Configuration:**
- `setup.py` - Package metadata and dependencies
- `setup.cfg` - Additional setup options
- `pytest.ini` - Pytest configuration with coverage and flake8 settings
- `tox.ini` - Testing across Python versions and database backends
- `.coveragerc` - Coverage measurement configuration
- `.scrutinizer.yml` - Code quality analysis configuration

**Database:**
- SQLAlchemy URL format: `sqlalchemy.url` setting in ini files
- Default: SQLite (`sqlite:///%(here)s/Kotti.db`)
- Supports MySQL, PostgreSQL, SQLite
- Migration management via Alembic (`kotti/alembic/`)

## Platform Requirements

**Development:**
- Python 3.6-3.10
- pip and setuptools
- Build tools for C extensions (bcrypt, psycopg2, mysqlclient)

**Production:**
- Python 3.6-3.10
- Database server (SQLite, PostgreSQL, or MySQL)
- WSGI application server (Waitress included, default)
- Mail SMTP server access (for pyramid_mailer)

**Testing:**
- All development requirements plus test dependencies
- PostgreSQL or MySQL running for integration tests (tox)
- pytest with plugins

## Key Dependencies Analysis

**Critical for CMS Operation:**
- `pyramid` - Core web framework
- `sqlalchemy` - ORM and database abstraction
- `colander` + `deform` - Form handling and validation
- `bcrypt` - Secure password storage

**Security-related:**
- `bleach` + `bleach-allowlist` - HTML sanitization (prevents XSS)
- `pyramid` authentication/authorization built-ins

**File Management:**
- `filedepot` - Abstraction over file storage backends
- Supports database storage (`DBFileStorage`) or local filesystem (`LocalFileStorage`)

**Email:**
- `pyramid_mailer` - Message queue and SMTP integration

**Static Resources:**
- `fanstatic` - Static file bundling and versioning

---

*Stack analysis: 2026-02-27*
