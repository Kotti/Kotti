# KOTTI CMS MODERNIZATION REPORT
**Analysis Date:** 2025-11-27
**Current Version:** 2.0.10dev0
**Repository:** https://github.com/Kotti/Kotti

## EXECUTIVE SUMMARY

Kotti is a mature Python-based CMS framework built on Pyramid and SQLAlchemy. While it demonstrates solid architecture and good test coverage, it requires significant modernization to remain competitive and maintainable in 2025. The project shows signs of technical debt accumulation, particularly in frontend technologies, dependency management, and modern Python practices.

**Health Score: 5.5/10** - Production-stable but aging rapidly

---

## 1. CRITICAL MODERNIZATION NEEDS

### 1.1 Python Version Support ⚠️ URGENT
**Status:** Severely outdated

**Current State:**
- Supports: Python 3.6-3.10 (setup.py:143-147)
- Python 3.6: End-of-life since December 2021
- Python 3.7: End-of-life since June 2023
- Python 3.8: End-of-life approaching (October 2024)
- Current runtime: Python 3.11.14
- No Python 3.11+ support declared

**Impact:**
- Security vulnerabilities from EOL Python versions
- Missing performance improvements from modern Python
- Inability to leverage new language features
- Package ecosystem compatibility issues

**Recommendation:**
- **IMMEDIATE:** Drop Python 3.6, 3.7 support
- **HIGH PRIORITY:** Add Python 3.11, 3.12, 3.13 support
- **STRATEGIC:** Set minimum to Python 3.10+ for 2025
- Update CI/CD matrices to test all supported versions

---

### 1.2 Frontend Technologies 🔴 CRITICAL
**Status:** Dangerously outdated with security risks

**Current State:**
```python
# setup.py:33-42
'js.angular',                      # Angular 1.x (dead framework)
'js.bootstrap>=3.0.0',            # Bootstrap 3 (EOL 2019)
'js.jquery<2.0.0.dev',            # jQuery 1.9.1 (2013, SECURITY RISK)
'js.jquery_form',
'js.jquery_tablednd',
'js.jquery_timepicker_addon',
'js.jqueryui>=1.8.24',            # jQueryUI 1.x (ancient)
'js.jqueryui_tagit',
'js.html5shiv',                   # No longer needed
```

**Security Vulnerabilities:**
- **jQuery 1.9.1** (requirements.txt:25): Multiple CVEs
  - CVE-2020-11023 (XSS in .html() method)
  - CVE-2020-11022 (XSS vulnerability)
  - CVE-2015-9251 (XSS in $.ajax)
- **Bootstrap 3.3.4**: No security support since 2019
- **AngularJS 1.x**: Officially dead (no LTS since 2022)

**Asset Management:**
- Uses **Fanstatic** - obsolete asset management system (last updated 2020)
- No modern build pipeline (Webpack, Vite, esbuild)
- Minimal JS: only 3 files (contents.js, upload.js)
- Manual minification (5 minified assets found)

**Recommendations:**
1. **IMMEDIATE (Security Fix):**
   - Upgrade jQuery to 3.7.x minimum
   - Remove AngularJS entirely (barely used)
   - Upgrade Bootstrap to 5.x

2. **STRATEGIC (Complete Overhaul):**
   - Replace Fanstatic with modern asset pipeline (Vite/Rollup)
   - Adopt vanilla JavaScript or lightweight framework (Alpine.js/htmx)
   - Implement proper frontend build system with npm/pnpm
   - Add package.json for frontend dependency management
   - Use ES6+ modules, remove jQuery dependency

---

### 1.3 Packaging & Build System 📦 HIGH PRIORITY
**Status:** Using outdated practices

**Current State:**
- Uses setup.py only (no pyproject.toml found)
- setup.py:94-96 uses setuptools_git (obsolete)
- No modern build backend (hatchling, pdm-build, etc.)
- Pinned dependencies in requirements.txt (anti-pattern for libraries)

**Issues:**
- Not PEP 517/518 compliant
- Missing build isolation
- Hard to maintain reproducible builds
- Incompatible with modern pip workflows

**Recommendations:**
1. Create pyproject.toml with modern build backend
2. Use dynamic versioning
3. Move from setup.py to declarative configuration
4. Separate dev/test/docs requirements properly
5. Use dependency groups (PEP 735) or extras properly

---

## 2. DEPENDENCY MODERNIZATION

### 2.1 Core Framework Dependencies

**Pyramid Framework:**
- Current: `pyramid>=1.9,<2` (setup.py:45)
- Latest: Pyramid 2.0 (released 2021)
- **Action:** Upgrade to Pyramid 2.x
- **Risk:** Medium (some API changes)
- **Benefit:** Better typing, performance improvements

**SQLAlchemy:**
- Current: `sqlalchemy>=1.4.16` (setup.py:55)
- Latest: SQLAlchemy 2.0.x (major improvements)
- **Status:** Partially compatible (setup.py:55 shows 1.4 support added in 2021)
- **Action:** Full SQLAlchemy 2.0 migration
- **Risk:** High (significant API changes)
- **Benefit:** Better typing, async support, performance

**Deform:**
- Current: Pinned to `deform==2.0.14` (setup.py:26)
- Reason: Version 2.0.15 breaks compatibility
- **Issue:** Stuck on old version due to js.deform issues
- **Action:** Fork or replace form library, or contribute fix upstream

### 2.2 Security Dependencies

**Bleach:**
- Current: `bleach>=4,<5` (setup.py:23)
- Latest: 6.x available
- **Action:** Upgrade to latest bleach version
- **Test:** Ensure sanitizers still work (kotti/sanitizers.py)

**bcrypt:**
- Current: `bcrypt` (setup.py:22)
- Status: Good (replaced unmaintained py-bcrypt in 2.0.9)
- **Action:** Add version constraint, verify latest compatibility

---

## 3. CODE QUALITY & MODERN PRACTICES

### 3.1 Type Hints
**Status:** Partial adoption

**Current State:**
- Only 31 occurrences of `from typing import` across 8 files
- Found in: resources.py (5), filedepot.py (6), security.py (8)
- Most codebase lacks type annotations

**Impact:**
- Harder to maintain and refactor
- IDE support limited
- Runtime type checking impossible
- No mypy integration detected

**Recommendations:**
1. Add mypy to test suite (pytest-mypy)
2. Gradually add type hints (start with public APIs)
3. Use Protocol for duck-typing interfaces
4. Add py.typed marker for PEP 561 compliance
5. Target gradual typing (not full coverage immediately)

### 3.2 Code Style & Linting
**Current State:**
```ini
# pytest.ini:16-18
flake8-ignore =
    *.py E122 E123 E125 E128 E203 E251 E501 E711 E713 E714 E402 F821 W503
    tests/*.py F841
```

**Issues:**
- 35 instances of `# noqa` comments (code smell suppression)
- Extensive flake8 ignores indicate code quality issues
- No black/ruff configuration found
- Line length set to 88 (good) but E501 ignored (bad)
- W503 ignored (outdated - not needed post-2019)

**Recommendations:**
1. **IMMEDIATE:** Adopt Black formatter
2. **HIGH:** Add Ruff (replaces flake8, much faster)
3. Clean up ignored errors systematically
4. Add pre-commit hooks for formatting
5. Remove outdated W503 ignore

### 3.3 Testing Infrastructure
**Status:** Good foundation, needs modernization

**Strengths:**
- 32 test files found
- pytest-based (pytest.ini:1)
- Coverage enabled (--cov=kotti)
- Multi-database testing (PostgreSQL, MySQL, SQLite)
- Good CI/CD coverage (3 database workflows)

**Weaknesses:**
- GitHub Actions using v2 (latest is v4)
- Tox config outdated (tox.ini:2 targets py36-py38 only)
- No async test support
- No property-based testing (Hypothesis)
- Commented-out flake8 in CI (.github/workflows/postgres.yml:46-51)

**Recommendations:**
1. Update GitHub Actions to v4
2. Update tox.ini for Python 3.10+
3. Add Hypothesis for property-based testing
4. Enable linting in CI (currently disabled)
5. Add security scanning (bandit, safety)

---

## 4. ARCHITECTURE & DESIGN PATTERNS

### 4.1 Current Architecture
**Framework:** Pyramid (WSGI-based)
- Traversal-based routing (kotti/traversal.py)
- SQLAlchemy ORM with Zope transaction manager
- Chameleon templates (49 .pt files)
- Fanstatic asset management

**Code Size:**
- 5,425 lines in main Python files (kotti/*.py)
- Reasonable size for a framework
- Well-structured with clear separation

### 4.2 Async Support
**Status:** None detected

**Current State:**
- No `async def` or `@asyncio` decorators found
- WSGI-only (waitress server)
- Synchronous database access only

**Future Consideration:**
- SQLAlchemy 2.0 supports async
- Pyramid supports ASGI via pyramid_asgi
- **Decision Point:** Is async needed for CMS workload?
- **Recommendation:** Stay synchronous unless specific use case emerges

### 4.3 Database Migrations
**Status:** Using Alembic (good)

- Alembic directory present (kotti/alembic/)
- Version-controlled migrations
- Stamp heads support (kotti/migrate.py:74)
- **Strength:** Proper migration management

---

## 5. DEPLOYMENT & OPERATIONS

### 5.1 Containerization
**Status:** Missing

- No Dockerfile found
- No docker-compose.yml
- No container registry integration

**Recommendations:**
1. Add multi-stage Dockerfile
2. Create docker-compose for local dev
3. Add to GitHub Container Registry
4. Document container deployment

### 5.2 CI/CD Pipeline
**Current State:**
- GitHub Actions workflows for 3 databases
- Matrix testing across Python versions
- Coverage reporting to Coveralls
- Multiple code quality badges (Codacy, CodeClimate, Scrutinizer)

**Issues:**
- Actions using deprecated versions (checkout@v2, setup-python@v2)
- Linting disabled in CI
- No release automation detected
- No security scanning

**Recommendations:**
1. Update all actions to v4/v5
2. Add security scanning (CodeQL, Dependabot)
3. Add release automation (changelog, PyPI upload)
4. Enable linting in CI
5. Add SAST tools (semgrep, bandit)

### 5.3 Observability
**Status:** Unknown

- No mention of logging configuration
- No APM integration detected
- No metrics/monitoring setup documented

**Recommendations:**
1. Document logging best practices
2. Add OpenTelemetry instrumentation
3. Provide example monitoring configs
4. Add health check endpoints

---

## 6. DOCUMENTATION & DEVELOPER EXPERIENCE

### 6.1 Documentation
**Status:** Well-documented

**Strengths:**
- Sphinx documentation (docs/)
- Read the Docs integration (rtd.txt)
- API documentation (docs/api/)
- Contributing guide (docs/contributing.rst)
- Multiple language support (11 locales)

**Gaps:**
- Todo list exists (docs/todo.txt) but unclear priority
- No modern contribution workflow (GitHub Actions/bots)
- No automated docs deployment verification

### 6.2 Developer Onboarding
**Current Setup:**
- development.ini for local setup
- Makefile for common tasks
- tox for testing

**Missing:**
- No .devcontainer for VS Code
- No GitHub Codespaces configuration
- No modern task runner (invoke, make replacement)
- No pre-commit configuration

**Recommendations:**
1. Add .devcontainer for instant dev environment
2. Add pre-commit hooks configuration
3. Add GitHub Codespaces support
4. Create developer quick-start guide
5. Add example .env file

---

## 7. SECURITY ASSESSMENT

### 7.1 Known Issues
1. **jQuery 1.9.1** - Multiple XSS vulnerabilities
2. **Bootstrap 3.x** - No longer receiving security updates
3. **AngularJS** - Dead framework, no security support
4. **Python 3.6-3.7** - EOL versions with known CVEs

### 7.2 Security Practices
**Current:**
- bcrypt for password hashing (good)
- Bleach for HTML sanitization (setup.py:23-24)
- AuthTkt with SHA-512 (kotti/__init__.py:34-36)

**Missing:**
- No Dependabot configuration
- No security.txt file
- No automated vulnerability scanning
- No SBOM generation
- No secret scanning

**Recommendations:**
1. **IMMEDIATE:** Enable Dependabot
2. Add security scanning to CI
3. Create SECURITY.md
4. Add security.txt (RFC 9116)
5. Regular security audits with pip-audit

---

## 8. STRATEGIC ROADMAP

### Phase 1: Security & Compliance (IMMEDIATE - 0-2 months)
**Priority: CRITICAL**

1. **Week 1-2: Frontend Security**
   - Upgrade jQuery to 3.7.x
   - Upgrade Bootstrap to 5.x
   - Remove AngularJS
   - Audit for other vulnerable dependencies

2. **Week 3-4: Python Support**
   - Drop Python 3.6, 3.7
   - Add Python 3.11, 3.12 support
   - Update CI matrices
   - Update documentation

3. **Week 5-8: Security Infrastructure**
   - Enable Dependabot
   - Add security scanning to CI
   - Create SECURITY.md
   - Run full security audit

**Expected Outcome:** Remove all critical security vulnerabilities

---

### Phase 2: Modernize Build & Tooling (2-4 months)
**Priority: HIGH**

1. **Build System**
   - Create pyproject.toml
   - Migrate from setup.py
   - Implement PEP 517/518
   - Add modern build backend (hatchling)

2. **Code Quality**
   - Add Black formatter
   - Migrate flake8 → Ruff
   - Add pre-commit hooks
   - Clean up # noqa comments

3. **CI/CD**
   - Update GitHub Actions to v4
   - Enable linting in CI
   - Add release automation
   - Update tox.ini

4. **Type Hints**
   - Add mypy to test suite
   - Type hint public APIs
   - Add py.typed marker

**Expected Outcome:** Modern, maintainable codebase

---

### Phase 3: Framework Upgrades (4-8 months)
**Priority: MEDIUM-HIGH**

1. **Pyramid 2.0**
   - Audit breaking changes
   - Update code for compatibility
   - Update tests
   - Update documentation

2. **SQLAlchemy 2.0**
   - Assess migration effort
   - Update query patterns
   - Update type hints
   - Test thoroughly across all databases

3. **Dependency Updates**
   - Unpin deform or find alternative
   - Update bleach to 6.x
   - Review all dependencies
   - Update requirements

**Expected Outcome:** Modern framework versions

---

### Phase 4: Frontend Modernization (6-10 months)
**Priority: MEDIUM**

**Option A: Conservative (Recommended for stability)**
- Keep minimal JavaScript approach
- Remove Fanstatic → simple asset pipeline
- Use vanilla ES6+ modules
- Keep server-rendered templates
- Add htmx for dynamic interactions

**Option B: Progressive (More effort, better UX)**
- Add modern build system (Vite)
- Adopt Alpine.js for interactivity
- Implement web components
- Keep Chameleon for SSR
- Progressive enhancement approach

**Option C: Radical (High risk/reward)**
- SPA frontend (React/Vue/Svelte)
- REST API backend
- Complete decoupling
- Modern developer experience
- **Risk:** Major rewrite, ecosystem disruption

**Recommendation:** Start with Option A, evaluate Option B based on user feedback

---

### Phase 5: Developer Experience (Ongoing)
**Priority: MEDIUM**

1. **Development Environment**
   - Add .devcontainer
   - GitHub Codespaces support
   - Docker Compose for local dev

2. **Documentation**
   - Update all examples
   - Add video tutorials
   - Improve API docs
   - Create migration guides

3. **Community**
   - Modernize contribution workflow
   - Add GitHub templates
   - Improve issue triage
   - Regular releases

---

## 9. RISKS & CHALLENGES

### 9.1 Breaking Changes
**Risk:** User disruption from modernization

**Mitigation:**
- Semantic versioning (3.0 for breaking changes)
- Detailed migration guides
- Deprecation warnings (not immediate removal)
- LTS support for 2.x line

### 9.2 Resource Constraints
**Risk:** Small contributor base (see CONTRIBUTORS.txt)

**Mitigation:**
- Prioritize security over features
- Automate where possible
- Focus on high-impact changes
- Seek community involvement

### 9.3 Ecosystem Compatibility
**Risk:** Add-on breakage

**Mitigation:**
- Survey popular add-ons
- Provide upgrade helpers
- Test against known extensions
- Version compatibility matrix

---

## 10. COMPETITIVE ANALYSIS

### vs. Modern CMSs
**Wagtail (Django-based):**
- Modern frontend (React)
- Active development
- Larger community
- **Gap:** Wagtail pulls ahead on UX

**Django CMS:**
- Similar age/maturity
- Better plugin ecosystem
- More contributors
- **Gap:** Community size

**Kotti Strengths:**
- Pyramid's flexibility
- Clean architecture
- Lightweight core
- SQLAlchemy power

**Kotti Weaknesses:**
- Aging frontend
- Smaller ecosystem
- Slower release cadence

---

## 11. RECOMMENDATIONS SUMMARY

### IMMEDIATE (This Month)
1. ✅ **Upgrade jQuery** to 3.7.x (SECURITY)
2. ✅ **Drop Python 3.6/3.7** support
3. ✅ **Enable Dependabot**
4. ✅ **Upgrade Bootstrap** to 5.x
5. ✅ **Remove AngularJS**

### HIGH PRIORITY (Next 3 Months)
1. 📦 **Create pyproject.toml**
2. 🐍 **Add Python 3.11/3.12 support**
3. 🔍 **Add Ruff + Black**
4. 🔒 **Security scanning in CI**
5. ⬆️ **Update GitHub Actions**

### MEDIUM PRIORITY (3-6 Months)
1. 🏗️ **Upgrade Pyramid to 2.x**
2. 📝 **Add type hints to APIs**
3. 🎨 **Modernize frontend build**
4. 🐳 **Add Docker support**
5. 📊 **SQLAlchemy 2.0 migration**

### STRATEGIC (6-12 Months)
1. 🚀 **Complete frontend overhaul**
2. 📚 **Documentation refresh**
3. 🤝 **Community growth initiatives**
4. 🔄 **Release automation**
5. 📈 **Performance optimization**

---

## 12. CONCLUSION

Kotti is a **solid, well-architected CMS framework** with good bones but suffering from deferred maintenance. The codebase is clean and well-tested, but **critical dependencies are dangerously outdated**, particularly on the frontend.

**Key Verdict:**
- **Architecture:** 8/10 - Well-designed, Pyramid + SQLAlchemy foundation is solid
- **Code Quality:** 7/10 - Clean but could use modern tooling
- **Security:** 3/10 - Critical vulnerabilities in frontend dependencies
- **Modernization:** 4/10 - Behind the curve on Python/JS best practices
- **Sustainability:** 5/10 - Needs more contributors and faster iteration

**Viability Assessment:**
- **Short-term (1 year):** ⚠️ Needs immediate security fixes
- **Medium-term (2-3 years):** ⚡ Can compete if modernized
- **Long-term (5+ years):** ❓ Depends on community growth

**Go/No-Go Recommendation:**
**GO** - But with aggressive Phase 1-2 execution. The project is worth saving and has unique value in the Pyramid ecosystem, but requires commitment to modernization.

---

**Report prepared by:** Claude (Sonnet 4.5)
**Analysis basis:** Repository state as of commit 904f9b6
**Date:** 2025-11-27
**Next review recommended:** After Phase 1 completion
