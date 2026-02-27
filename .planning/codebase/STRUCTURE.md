# Codebase Structure

**Analysis Date:** 2026-02-27

## Directory Layout

```
Kotti/
├── kotti/                          # Main package
│   ├── __init__.py                 # WSGI entry point, configuration
│   ├── resources.py                # Core content/node models (970 lines)
│   ├── security.py                 # Authentication, authorization (574 lines)
│   ├── traversal.py                # Tree traverser optimization (250 lines)
│   ├── events.py                   # Event system & lifecycle (583 lines)
│   ├── sqla.py                     # SQLAlchemy type extensions
│   ├── request.py                  # Request subclass with permission override
│   ├── util.py                     # Utilities (translation, rendering, helpers)
│   ├── filedepot.py                # File upload storage management (729 lines)
│   ├── populate.py                 # Bootstrap: admin user, root node
│   ├── migrate.py                  # Alembic migration runner
│   ├── workflow.py                 # State machine for content workflow
│   ├── message.py                  # Flash messages
│   ├── sanitizers.py               # HTML sanitization
│   ├── fanstatic.py                # Static asset bundling
│   ├── url_normalizer.py           # URL slug generation
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/               # Migration files
│   │
│   ├── views/                      # View/presentation layer (3507 lines total)
│   │   ├── __init__.py             # Base view class
│   │   ├── util.py                 # Renderer globals, template API (529 lines)
│   │   ├── form.py                 # Base form views, schema handling (281 lines)
│   │   ├── view.py                 # Content viewing views
│   │   ├── login.py                # Authentication views (384 lines)
│   │   ├── users.py                # User/group management views (656 lines)
│   │   ├── navigation.py           # Navigation menu rendering
│   │   ├── cache.py                # HTTP cache policy chooser (135 lines)
│   │   ├── file.py                 # File viewing/download
│   │   ├── slots.py                # Template slot system (146 lines)
│   │   │
│   │   └── edit/                   # Content editing views
│   │       ├── __init__.py
│   │       ├── actions.py          # Edit actions (604 lines)
│   │       ├── content.py          # Content edit form schemas (172 lines)
│   │       ├── default_views.py    # Default edit view configurations
│   │       └── upload.py           # File upload handling (167 lines)
│   │
│   ├── templates/                  # Chameleon templates
│   │   ├── master-bare.pt          # Base layout template
│   │   ├── master.pt               # Full layout with navigation
│   │   ├── login.pt                # Login form
│   │   ├── editor-bar.pt           # Edit mode toolbar
│   │   ├── messages.pt             # Flash message display
│   │   ├── view/                   # View mode templates
│   │   ├── edit/                   # Edit mode templates
│   │   ├── deform/                 # Custom deform widget templates
│   │   ├── http-errors/            # Error page templates (403, 404, etc)
│   │   ├── site-setup/             # Site setup wizard templates
│   │   └── *.pt                    # Various specific templates
│   │
│   ├── static/                     # Static assets (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── locale/                     # Internationalization files
│   │   ├── en/                     # English strings
│   │   ├── de/                     # German
│   │   ├── fr_FR/                  # French
│   │   ├── it/                     # Italian
│   │   ├── ja/                     # Japanese
│   │   ├── ko/                     # Korean
│   │   ├── pl/                     # Polish
│   │   ├── pt/                     # Portuguese
│   │   ├── sv/                     # Swedish
│   │   └── ...                     # Other languages
│   │
│   └── tests/                      # Test suite (32 test files)
│       ├── conftest.py             # Pytest configuration, fixtures
│       ├── test_resources.py       # Content model tests
│       ├── test_security.py        # Security/ACL tests
│       ├── test_traversal.py       # Traversal optimization tests
│       ├── test_views_*.py         # View-specific tests
│       ├── test_events.py          # Event system tests
│       └── ...
│
├── docs/                           # Sphinx documentation
├── .github/
│   └── workflows/                  # GitHub Actions CI/CD
├── development.ini                 # Development server config
├── app.ini                         # Production app config template
├── setup.py                        # Package metadata & dependencies
├── pytest.ini                      # Pytest configuration
├── tox.ini                         # Testing environments config
├── README.rst                      # Project overview
└── CHANGES.txt                     # Changelog
```

## Directory Purposes

**`kotti/`:**
- Purpose: Main Python package containing all Kotti framework code
- Contains: Models, views, configuration, utilities, tests
- Key files: `__init__.py` (entry point), `resources.py` (data models), `views/` (HTTP handlers)

**`kotti/resources.py`:**
- Purpose: SQLAlchemy models for content hierarchy and metadata
- Contains: `Node`, `Content`, `Document`, `File`, `Principal`, `LocalGroup`, `Tag`, `TypeInfo`
- Key entry point: Base classes for custom content types

**`kotti/security.py`:**
- Purpose: Authentication, authorization, user/group management
- Contains: `Principal` model, ACL utilities, permission checking, groups callback
- Extends: Pyramid's security infrastructure

**`kotti/views/`:**
- Purpose: HTTP request handlers organized by function
- Contains: View classes, form handling, cache management, UI logic
- Pattern: pyramid_deform for forms, Chameleon for templates

**`kotti/views/edit/`:**
- Purpose: Content editing interface (add, edit, delete, workflow)
- Contains: Edit views, form schemas, upload handling
- Key files: `actions.py` (edit workflow), `content.py` (schemas)

**`kotti/templates/`:**
- Purpose: HTML templates (Chameleon/ZPT format)
- Contains: Layout templates, view components, error pages
- Pattern: Inheritance-based template structure with master.pt as base

**`kotti/tests/`:**
- Purpose: Comprehensive test suite with high coverage
- Contains: 32+ test modules covering models, views, security, events, etc.
- Key fixture: `conftest.py` with pytest configuration and app/DB fixtures

**`kotti/alembic/`:**
- Purpose: Database schema versioning and migrations
- Contains: Migration scripts auto-generated by SQLAlchemy + Alembic
- Usage: Run via `kotti-migrate` command or automatically on app startup

## Key File Locations

**Entry Points:**
- `kotti/__init__.py` (line 186): `main()` - WSGI app factory
- `kotti/__init__.py` (line 258): `includeme()` - Pyramid plugin hook
- `kotti/resources.py`: `initialize_sql()`, `default_get_root()` - DB initialization

**Configuration:**
- `kotti/__init__.py` (line 59-138): `conf_defaults` - Default settings dictionary
- `development.ini`: Development server configuration
- `app.ini`: Production deployment template

**Core Logic:**
- `kotti/resources.py`: Node hierarchy, content types, metadata
- `kotti/security.py`: User/group/permission management
- `kotti/traversal.py`: Optimized path-to-node mapping
- `kotti/events.py`: Lifecycle event system

**Testing:**
- `kotti/tests/conftest.py`: Pytest fixtures and configuration
- `kotti/testing.py`: Test helper utilities, DummyRequest, etc.

## Naming Conventions

**Files:**
- Module files: lowercase with underscores (e.g., `file_depot.py` → `filedepot.py`)
- Template files: hyphenated lowercase (e.g., `editor-bar.pt`, `master-bare.pt`)
- Test files: `test_` prefix (e.g., `test_resources.py`)

**Classes:**
- Content types: PascalCase inheriting from `Content` (e.g., `Document`, `File`)
- View classes: PascalCase ending with "View" (e.g., `AddFormView`, `LoginView`)
- Schema classes: PascalCase ending with "Schema" (e.g., `ContentSchema`, `DocumentSchema`)

**Functions:**
- View callables: lowercase with underscores (e.g., `view_content`, `edit_content`)
- Utility functions: descriptive lowercase with underscores (e.g., `get_paste_items`)
- Event handlers: descriptive of action (e.g., `_on_document_insert`)

**Variables & Constants:**
- Constants: UPPERCASE with underscores (e.g., `TRUE_VALUES`, `SITE_ACL`)
- Local variables: lowercase with underscores
- Private/internal: prefix with `_` (e.g., `_resolve_dotted`)

**Database/ORM:**
- Table names: lowercase plural or descriptive (e.g., `nodes`, `principals`, `local_groups`)
- Column names: lowercase with underscores (e.g., `parent_id`, `creation_date`)

**Settings Keys:**
- Namespace with dots (e.g., `kotti.secret`, `kotti.base_includes`, `pyramid.includes`)

## Where to Add New Code

**New Content Type (e.g., BlogPost):**
- Define model: Add class inheriting from `Content` in `kotti/resources.py` or plugin
- Add schema: Define in `kotti/views/edit/content.py` or separate module
- Register: Set `TypeInfo` with allowed children, schema, icon
- Create view: Add to `kotti/views/view.py` or separate module (use `@view_config`)
- Template: Add to `kotti/templates/view/` for rendering

**New View/Endpoint:**
- Primary code: `kotti/views/{feature}.py` (new file for feature area)
- Tests: `kotti/tests/test_views_{feature}.py`
- Form schema: `kotti/views/edit/content.py` (or feature-specific module)
- Template: `kotti/templates/{view|edit}/{template_name}.pt`
- Decorator: Use Pyramid's `@view_config(context=Resource, request_method='GET', renderer='json')`

**New Utility Function:**
- Shared helpers: `kotti/util.py` (general utilities)
- Domain-specific: Create `kotti/{domain}.py` (e.g., `kotti/sanitizers.py`)
- Test: Corresponding test file in `kotti/tests/`

**Event Handler (Plugin Hook):**
- Create subscriber function decorated with `@listener(ObjectInsert)`
- Location: In plugin code or event registration module
- Called via: Kotti's event dispatcher on object lifecycle events

**Database Migration:**
- Generated: Run `alembic revision --autogenerate` (from development.ini)
- Location: `kotti/alembic/versions/{timestamp}_{description}.py`
- Executed: Automatically on app startup via `initialize_sql()`

## Special Directories

**`kotti/tests/`:**
- Purpose: Test suite
- Generated: No (all committed)
- Committed: Yes
- Key fixture: `conftest.py` (pytest plugin with shared fixtures)

**`kotti/locale/`:**
- Purpose: Internationalization message files
- Generated: Partially (PO files auto-generated from source)
- Committed: Yes (translations)
- Usage: Runtime locale selection based on request

**`kotti/alembic/`:**
- Purpose: Database version control
- Generated: Yes (migration scripts auto-generated)
- Committed: Yes (all migration history)
- Usage: `kotti-migrate` command or automatic on startup

**`kotti/static/`:**
- Purpose: CSS, JavaScript, images served directly
- Generated: No (manually authored or from fanstatic bundles)
- Committed: Yes
- Served via: Pyramid static view at `/static-kotti`

**`kotti/templates/`:**
- Purpose: Chameleon HTML templates
- Generated: No (manually authored)
- Committed: Yes
- Override: Use `pyramid.includes` or asset override config

---

*Structure analysis: 2026-02-27*
