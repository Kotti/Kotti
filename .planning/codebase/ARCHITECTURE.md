# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Hierarchical Resource Tree with Traversal-Based Routing

Kotti is a Pyramid-based CMS framework that implements a hierarchical document/content tree model. It uses SQLAlchemy for persistence and combines Pyramid's traversal-based routing with a custom optimized node tree traverser to efficiently navigate nested content structures. The architecture emphasizes security (ACL-based), extensibility through configurators and plugins, and content type customization.

**Key Characteristics:**
- **Traversal-based routing**: URL paths map directly to node hierarchy (e.g., `/about/team/` traverses to node tree)
- **SQLAlchemy ORM**: All persistence through declarative SQLAlchemy models
- **Pyramid integration**: Leverages Pyramid's security policies, event system, and configuration
- **Event-driven architecture**: Observable events at node lifecycle stages (insert, update, delete)
- **ACL-based security**: Context-aware permissions with local group assignments
- **Plugin architecture**: Extensible through includeme hooks and configuration dictionaries

## Layers

**Persistence Layer (SQLAlchemy Models):**
- Purpose: Define content types, relationships, and database schema
- Location: `kotti/resources.py`, `kotti/security.py`, `kotti/sqla.py`
- Contains: `Node`, `Content`, `Document`, `File`, `Principal`, `LocalGroup`, `Tag` classes
- Depends on: SQLAlchemy, transaction, zope.sqlalchemy
- Used by: Views, events system, traversal, security checks

**Traversal & Routing Layer:**
- Purpose: Map HTTP requests to resource nodes efficiently with single optimized DB query
- Location: `kotti/traversal.py`
- Contains: `NodeTreeTraverser` class implementing Pyramid's `ITraverser` interface
- Depends on: Pyramid traversal, SQLAlchemy, Node resources
- Used by: Request dispatch, view selection

**Security Layer:**
- Purpose: Authentication, authorization, user/group management, permission checks
- Location: `kotti/security.py`, `kotti/request.py`
- Contains: `Principal` model, ACL management, permission checking, authentication policy
- Depends on: Pyramid security, bcrypt, SQLAlchemy
- Used by: View rendering, resource access control, API methods

**View Layer:**
- Purpose: Handle HTTP request/response and content rendering
- Location: `kotti/views/` (multiple modules)
- Contains: View classes, form handling, cache management, user management, login, navigation
- Depends on: Pyramid views, deform forms, Chameleon templates
- Used by: HTTP routing, form processing, UI rendering

**Event System:**
- Purpose: Emit and subscribe to object lifecycle events (insert, update, delete)
- Location: `kotti/events.py`
- Contains: Event classes (`ObjectInsert`, `ObjectUpdate`, `ObjectDelete`), dispatcher
- Depends on: SQLAlchemy events, venusian (decorator scanning)
- Used by: Object change tracking, cache invalidation, workflow transitions

**Configuration & Initialization:**
- Purpose: Application bootstrap, configuration resolution, plugin inclusion
- Location: `kotti/__init__.py`, `kotti/populate.py`
- Contains: `main()`, `base_configure()`, default settings, plugin loading
- Depends on: Pyramid, pkg_resources, alembic
- Used by: WSGI entry point, setting resolution

## Data Flow

**Request → View → Response:**

1. **Request arrives** at WSGI server (Waitress)
2. **Traversal phase**: `NodeTreeTraverser` converts URL path to single SQL query, loads context node and ancestors
3. **Security check**: Permission evaluated based on context node's ACL and user's groups
4. **View lookup**: Pyramid locates view callable based on context type, request method, and name
5. **View execution**: View class instantiated with (context, request), processes form data if present
6. **Template rendering**: Chameleon template rendered with view data
7. **Response sent**: Rendered HTML returned to client

**Object Lifecycle with Events:**

1. **Object modification** (e.g., `DBSession.add(node)`)
2. **SQLAlchemy event triggered** (before_flush, after_insert)
3. **Kotti event dispatcher** emits matching ObjectEvent (e.g., `ObjectInsert`)
4. **Subscribers notified** via event handlers
5. **Post-processing**: Cache invalidation, workflow transitions, audit logging
6. **Transaction committed**

**State Management:**
- **Session state**: Request-scoped via Beaker session middleware
- **Database state**: Managed by SQLAlchemy ORM with transaction context
- **Cache state**: LRU caching for principals, role lookups via `repoze.lru`
- **Authentication state**: AuthTkt session cookie policy with callback-based group lookup

## Key Abstractions

**Node (Base Resource):**
- Purpose: Base class for all content items in tree; provides hierarchy, container, ACL
- Examples: `kotti/resources.py` line 253 (`Node` class)
- Pattern: SQLAlchemy declarative base with ABC metaclass; implements `MutableMapping` for container access
- Provides: Tree navigation (`__getitem__`, `children`), ACL storage, metadata (created, modified dates)

**TypeInfo (Content Type Registry):**
- Purpose: Metadata about a content type (e.g., allowed children, icon, editing form schema)
- Examples: `kotti/resources.py` line 379 (`TypeInfo` class)
- Pattern: Class-level attribute on content models; provides schema, validation, creation factory
- Used by: Add/edit views, content type listings

**FormView (Form Handling Base):**
- Purpose: Standard pattern for edit views with form submission, validation, and redirect
- Examples: `kotti/views/form.py` (BaseFormView, derived FormView)
- Pattern: Inherits from pyramid_deform.FormView; binds schema to context object
- Provides: Form rendering, data binding, success/cancel handling

**Event Dispatcher (Plugin Hook):**
- Purpose: Allow plugins to hook into object lifecycle without modifying core code
- Examples: `kotti/events.py` (subscriber registration via @view_config-like decorator)
- Pattern: Use `@listener` decorator to register event handlers
- Example usage: Cache invalidation, workflow state changes, audit logs

**LocalGroup (Context-Aware Roles):**
- Purpose: Assign users/groups to roles at specific context level (not global)
- Examples: `kotti/resources.py` line 205 (`LocalGroup` model)
- Pattern: Junction table linking principals and groups to specific nodes
- Enables: Hierarchical permission delegation

## Entry Points

**WSGI Application Factory:**
- Location: `kotti/__init__.py` line 186 (`main()`)
- Triggers: Called by Paste Deploy / WSGI server at startup
- Responsibilities:
  - Load configuration from INI file
  - Initialize SQLAlchemy engine
  - Configure Pyramid (security, session, auth policies)
  - Load plugins and base includes
  - Return WSGI app callable

**Pyramid Configurator includeme Hook:**
- Location: `kotti/__init__.py` line 258 (`includeme()`)
- Triggers: Automatically called when kotti module is included in Pyramid config
- Responsibilities:
  - Register authentication/authorization policies
  - Set session factory
  - Add translation directories
  - Load workflow ZCML if enabled

**Database Initialization:**
- Location: `kotti/resources.py` (initialize_sql function, get_root)
- Triggers: Called from `main()` during startup
- Responsibilities:
  - Create engine and tables
  - Run Alembic migrations
  - Initialize root node if none exists

**Populators (Post-Startup Hooks):**
- Location: `kotti/populate.py`
- Triggers: Executed by configurators if database is empty
- Responsibilities:
  - Create admin user (populate_users)
  - Populate root and example nodes (populate)

## Error Handling

**Strategy:** Layered error handling with context-aware HTTP exceptions

**Patterns:**
- **Traversal errors**: 404 Not Found when path traversal fails
- **Permission errors**: 403 Forbidden when user lacks required permission
- **Validation errors**: Form re-rendered with error messages (deform)
- **Database errors**: Transaction rollback with user-friendly message
- **Configuration errors**: Logged and raised during startup (fail fast)

Error pages rendered via templates at `kotti/templates/http-errors/`

## Cross-Cutting Concerns

**Logging:**
- Python standard logging (getLogger)
- Key modules: traversal (path resolution), security (permission checks), events (lifecycle)
- No centralized logger; per-module loggers recommended

**Validation:**
- Colander schemas for form data (kotti/views/form.py, edit/content.py)
- SQLAlchemy column constraints for database-level validation
- HTML sanitization for user-generated content via bleach sanitizers

**Authentication:**
- Pyramid's AuthTkt cookie-based authentication
- Custom callback (list_groups_callback) implements group/role lookup
- Token-based password resets via confirm_token on Principal

**Internationalization (i18n):**
- Pyramid's gettext machinery with Babel
- TranslationStringFactory creates localizable strings (_())
- Per-language locale directories: `kotti/locale/{lang}/`
- Runtime localization via request.localizer

**Caching:**
- View caching via HTTP cache headers (cache.py policy chooser)
- Principal lookup caching via request cache decorator
- ORM query result caching via SQLAlchemy query baking (bakery)

**File Uploads:**
- Depot library integration (kotti/filedepot.py)
- Pluggable storage backends (default: database storage)
- Migration tools for storage backend switching

---

*Architecture analysis: 2026-02-27*
