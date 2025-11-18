# AUPAT Project TODO List

Version: 1.0.0
Last Updated: 2025-11-18

This document tracks all identified tasks, gaps, and improvements for the AUPAT project. Tasks are prioritized as High, Medium, or Low.

---

## TABLE OF CONTENTS

1. [Critical Issues (High Priority)](#critical-issues-high-priority)
2. [Important Improvements (Medium Priority)](#important-improvements-medium-priority)
3. [Nice to Have (Low Priority)](#nice-to-have-low-priority)
4. [Completed Tasks](#completed-tasks)
5. [Long-term Roadmap](#long-term-roadmap)

---

## CRITICAL ISSUES (High Priority)

### 1. Consolidate Startup Scripts

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Medium
**Estimated Time:** 4 hours

**Problem:**
- 4 different startup scripts with inconsistent configuration
- start_aupat.sh uses port 5002
- start_server.sh uses port 5000
- No clear guidance on which to use

**Solution:**
Create unified launch.sh script with mode flags:
- `./launch.sh --dev` - Full stack development (backend + desktop)
- `./launch.sh --api` - API server only
- `./launch.sh --docker` - Docker Compose full stack
- `./launch.sh --status` - Show running services
- `./launch.sh --stop` - Stop all services

**Files to modify:**
- Create: /home/user/aupat/launch.sh
- Update: /home/user/aupat/README.md (update startup instructions)
- Archive: start_aupat.sh, start_server.sh (keep for backward compatibility)

**Dependencies:** None

**Acceptance criteria:**
- Single script handles all launch modes
- Consistent port configuration (5002 for dev, 5001 for docker)
- Clear help text with examples
- PID file management
- Health check integration

---

### 2. Fix Blueprint Registration in app.py

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Low
**Estimated Time:** 30 minutes

**Problem:**
- api_routes_bookmarks.py blueprint NOT registered in app.py
- api_maps.py blueprint NOT registered in app.py
- Endpoints defined but not accessible

**Solution:**
Add blueprint registrations to app.py:

```python
from scripts.api_routes_bookmarks import bookmarks_bp
from scripts.api_maps import api_maps

app.register_blueprint(bookmarks_bp, url_prefix='/api')
app.register_blueprint(api_maps)
```

**Files to modify:**
- /home/user/aupat/app.py (add imports and registrations)

**Testing:**
```bash
# Start server
./launch.sh --api

# Test bookmarks endpoint
curl http://localhost:5002/api/bookmarks

# Test maps endpoint
curl http://localhost:5002/api/maps/exports
```

**Acceptance criteria:**
- Both blueprints registered
- Endpoints respond correctly
- No 404 errors
- Tests pass

---

### 3. Fix Hardcoded Database Path

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Low
**Estimated Time:** 15 minutes

**Problem:**
- api_routes_bookmarks.py line 38 uses hardcoded path 'data/aupat.db'
- Will fail if run from different directory
- Inconsistent with other modules

**Solution:**
Replace hardcoded path with config:

```python
# OLD (line 38)
conn = sqlite3.connect('data/aupat.db')

# NEW
from flask import current_app
conn = sqlite3.connect(current_app.config['DB_PATH'])
```

**Files to modify:**
- /home/user/aupat/scripts/api_routes_bookmarks.py (line 38)

**Testing:**
```bash
# Test from different directory
cd /tmp
python /home/user/aupat/app.py  # Should work
```

**Acceptance criteria:**
- Uses config['DB_PATH']
- Works from any directory
- Tests pass

---

### 4. Fix Import Path in immich_integration.py

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Low
**Estimated Time:** 15 minutes

**Problem:**
- immich_integration.py uses relative import: `from adapters.immich_adapter`
- Should be: `from scripts.adapters.immich_adapter`
- Fails when run from project root

**Solution:**
Update import statement:

```python
# OLD
from adapters.immich_adapter import create_immich_adapter, ImmichError

# NEW
from scripts.adapters.immich_adapter import create_immich_adapter, ImmichError
```

**Files to modify:**
- /home/user/aupat/scripts/immich_integration.py (import statements)

**Testing:**
```bash
# Test import from project root
cd /home/user/aupat
python -c "from scripts.immich_integration import get_immich_adapter"
```

**Acceptance criteria:**
- Correct import path
- No ImportError
- Tests pass

---

### 5. Create Comprehensive Health Check System

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** High
**Estimated Time:** 6 hours

**Problem:**
- Current health check only checks database connectivity
- Doesn't verify:
  - File system write capability
  - Disk space
  - External tools (exiftool, ffmpeg)
  - Database performance
  - External services

**Solution:**
Create /home/user/aupat/scripts/health_check.py:

**Features:**
- Database connectivity check
- Database write test
- File system access check
- Disk space check (warn if <1GB)
- exiftool availability check
- ffmpeg availability check
- Immich service health (if configured)
- ArchiveBox service health (if configured)
- Return detailed status JSON

**API Integration:**
- Update GET /api/health to use comprehensive checks
- Add GET /api/health/detailed for full report

**CLI Usage:**
```bash
# Run health check
python scripts/health_check.py

# Output: JSON with all check results
```

**Files to create:**
- /home/user/aupat/scripts/health_check.py

**Files to modify:**
- /home/user/aupat/scripts/api_routes_v012.py (update health endpoints)
- /home/user/aupat/lilbits.md (document new script)

**Dependencies:**
- shutil (disk space)
- subprocess (tool checks)

**Acceptance criteria:**
- All checks implemented
- JSON output with pass/fail for each
- Integration with API endpoints
- CLI tool works standalone
- Documentation updated

---

### 6. Fix Hardcoded macOS Paths

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Medium
**Estimated Time:** 2 hours

**Problem:**
- com.aupat.worker.plist has hardcoded user paths: `/Users/bryant/...`
- Won't work on other machines

**Solution:**
Create template file and generation script:

1. Create com.aupat.worker.plist.template with placeholders:
```xml
<key>ProgramArguments</key>
<array>
    <string>{{PYTHON_PATH}}</string>
    <string>{{SCRIPT_PATH}}/scripts/archive_worker.py</string>
</array>
<key>WorkingDirectory</key>
<string>{{WORKING_DIR}}</string>
```

2. Create generate_plist.py script to fill in actual paths

3. Update documentation with setup instructions

**Files to create:**
- /home/user/aupat/com.aupat.worker.plist.template
- /home/user/aupat/scripts/generate_plist.py

**Files to modify:**
- /home/user/aupat/README.md (update macOS service setup)
- /home/user/aupat/com.aupat.worker.plist (mark as generated, add to .gitignore)

**Acceptance criteria:**
- Template file created
- Generator script works
- Documentation updated
- Works on any machine

---

### 7. Add Transaction Boundaries

**Status:** Done (2025-11-18)
**Priority:** High
**Complexity:** Medium
**Estimated Time:** 4 hours

**Problem:**
- Multi-step database operations lack explicit transactions
- Risk of data inconsistency if process crashes

**Solution:**
Add BEGIN/COMMIT blocks to critical operations:

**Scripts to update:**
- db_import_v012.py (wrap import loop)
- db_organize.py (wrap metadata updates)
- db_ingest.py (wrap file moves + DB updates)
- map_import.py (wrap location imports)
- api_routes_v012.py (wrap location creates/updates)

**Pattern to follow:**
```python
conn.execute("BEGIN")
try:
    # operations
    conn.commit()
except Exception as e:
    conn.rollback()
    logger.error(f"Transaction failed: {e}")
    raise
```

**Files to modify:**
- /home/user/aupat/scripts/db_import_v012.py
- /home/user/aupat/scripts/db_organize.py
- /home/user/aupat/scripts/db_ingest.py
- /home/user/aupat/scripts/map_import.py
- /home/user/aupat/scripts/api_routes_v012.py

**Testing:**
- Interrupt operations mid-run
- Verify no partial data in database
- Verify rollback works correctly

**Acceptance criteria:**
- All multi-step operations wrapped
- Proper error handling
- Tests verify rollback behavior
- No partial data on failure

---

## IMPORTANT IMPROVEMENTS (Medium Priority)

### 8. Create Production Deployment Guide

**Status:** Not Started
**Priority:** Medium
**Complexity:** Medium
**Estimated Time:** 6 hours

**What to document:**
- Security hardening checklist
- Environment variables configuration
- Reverse proxy setup (nginx)
- SSL/TLS certificate setup
- Systemd service files for Linux
- Firewall configuration
- Backup automation
- Log rotation
- Monitoring setup
- Performance tuning
- Scaling considerations

**File to create:**
- /home/user/aupat/docs/PRODUCTION_DEPLOYMENT.md

**Include examples for:**
- nginx configuration
- systemd service files
- Backup cron jobs
- Log rotation config

**Acceptance criteria:**
- Complete deployment guide
- Security checklist included
- All configurations provided
- Tested on clean server

---

### 9. Add Database Migration Orchestrator

**Status:** Not Started
**Priority:** Medium
**Complexity:** Medium
**Estimated Time:** 4 hours

**Problem:**
- No clear migration execution order
- No version tracking
- Manual execution required

**Solution:**
Create /home/user/aupat/scripts/migrate.py orchestrator:

**Features:**
- Detect current schema version
- Run required migrations in order
- Skip already-applied migrations
- Rollback on error
- Version tracking in database

**Usage:**
```bash
# Show current version
python scripts/migrate.py --status

# Migrate to latest
python scripts/migrate.py --upgrade

# Migrate to specific version
python scripts/migrate.py --upgrade v0.1.4
```

**Files to create:**
- /home/user/aupat/scripts/migrate.py

**Database changes:**
- Enhance versions table to track migrations

**Acceptance criteria:**
- Auto-detects version
- Runs migrations in correct order
- Tracks applied migrations
- Idempotent (safe to re-run)
- Documentation updated

---

### 10. Add Structured Logging (JSON)

**Status:** Not Started
**Priority:** Medium
**Complexity:** Medium
**Estimated Time:** 4 hours

**Problem:**
- Text-based logging hard to parse
- No structured fields
- No correlation IDs
- No centralized configuration

**Solution:**
Implement JSON logging with python-json-logger:

**Features:**
- JSON formatted logs
- Correlation IDs for request tracing
- Structured fields (timestamp, level, module, function)
- Configurable log levels per module
- Sensitive data redaction

**Files to create:**
- /home/user/aupat/scripts/logging_config.py

**Files to modify:**
- All Python scripts (use centralized logger)

**Configuration:**
- Add logging config to user.json
- Environment variable for log level

**Acceptance criteria:**
- All logs in JSON format
- Correlation IDs work
- Sensitive data redacted
- Centralized configuration
- Documentation updated

---

### 11. Generate OpenAPI/Swagger Spec

**Status:** Not Started
**Priority:** Medium
**Complexity:** Low
**Estimated Time:** 2 hours

**Problem:**
- No interactive API documentation
- Hard for frontend developers to explore

**Solution:**
Use flask-swagger-ui to generate OpenAPI spec:

1. Add OpenAPI decorators to endpoints
2. Generate spec from code
3. Serve Swagger UI at /api/docs

**Dependencies:**
- flask-swagger-ui
- flasgger (or similar)

**Files to modify:**
- /home/user/aupat/requirements.txt (add dependencies)
- /home/user/aupat/app.py (add Swagger UI)
- /home/user/aupat/scripts/api_routes_v012.py (add OpenAPI decorators)

**Endpoint:**
- GET /api/docs - Swagger UI interface

**Acceptance criteria:**
- Swagger UI accessible
- All endpoints documented
- Try-it-out works
- Schemas defined

---

### 12. Add Type Hints to Python Code

**Status:** Not Started
**Priority:** Medium
**Complexity:** High
**Estimated Time:** 12 hours

**Problem:**
- No type hints in Python code
- Harder to maintain
- Limited IDE autocomplete

**Solution:**
Add type hints to all functions:

**Modules to update (priority order):**
1. scripts/utils.py (most imported)
2. scripts/normalize.py (most imported)
3. scripts/adapters/*.py
4. scripts/api_routes_v012.py
5. All other scripts

**Also add:**
- mypy to CI/CD pipeline
- mypy.ini configuration file

**Example:**
```python
from typing import Optional, Dict, Any, List

def get_location(uuid: str) -> Optional[Dict[str, Any]]:
    """Get location by UUID."""
    pass
```

**Files to create:**
- /home/user/aupat/mypy.ini

**Files to modify:**
- All .py files in /home/user/aupat/scripts/
- /home/user/aupat/.github/workflows/test.yml (add mypy check)

**Acceptance criteria:**
- All functions have type hints
- mypy passes with no errors
- CI/CD runs mypy
- Documentation updated

---

### 13. Implement API Pagination

**Status:** Done (2025-11-18)
**Priority:** Medium
**Complexity:** Low
**Estimated Time:** 3 hours

**Problem:**
- /api/locations might return thousands of records
- Can cause memory issues and slow UI

**Solution:**
Add pagination to list endpoints:

**Endpoints to update:**
- GET /api/locations
- GET /api/search
- GET /api/locations/{uuid}/images
- GET /api/bookmarks

**Pagination parameters:**
- limit (default: 50, max: 500)
- offset (default: 0)

**Response format:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 1234,
    "has_more": true
  }
}
```

**Files to modify:**
- /home/user/aupat/scripts/api_routes_v012.py
- /home/user/aupat/scripts/api_routes_bookmarks.py

**Acceptance criteria:**
- Pagination works
- Default limits enforced
- Total count returned
- has_more flag accurate
- Desktop app updated to handle pagination

---

### 14. Complete Mobile App or Mark as Experimental

**Status:** Not Started
**Priority:** Medium
**Complexity:** Very High
**Estimated Time:** 40+ hours

**Problem:**
- Mobile app has minimal implementation (3 files only)
- Many features missing
- Unclear scope

**Decision needed:**
Option A: Complete full mobile app
Option B: Mark as experimental/proof-of-concept
Option C: Create simplified companion app

**If completing (Option A):**
- Implement all planned features
- Add comprehensive testing
- Update documentation

**If marking experimental (Option B):**
- Update mobile/README.md with clear status
- Document what's implemented vs. planned
- Provide roadmap if future development planned

**If simplified (Option C):**
- Focus on core features: view locations, add photos
- Skip advanced features
- Clear scope documentation

**Files affected:**
- /home/user/aupat/mobile/* (many)
- /home/user/aupat/mobile/README.md
- /home/user/aupat/README.md

**Recommendation:** Start with Option B (mark as experimental), then decide if Option C is worthwhile

---

### 15. Archive v0.1.0 Directory

**Status:** Not Started
**Priority:** Medium
**Complexity:** Low
**Estimated Time:** 1 hour

**Problem:**
- /archive/v0.1.0/ contains 526K of dead code
- Never imported by current code
- Confuses developers

**Solution:**
Move to separate repository or document clearly:

**Option A: Move to separate repo**
1. Create aupat-archive repository
2. Move archive/v0.1.0/ contents
3. Add README explaining it's historical
4. Delete from main repo

**Option B: Document as historical**
1. Add archive/README.md with clear warning
2. Add .gitignore to exclude from some operations
3. Keep for reference

**Files to modify:**
- /home/user/aupat/archive/README.md (create)
- /home/user/aupat/README.md (note about archive)

**Recommendation:** Option A (separate repo) to keep main repo clean

---

## NICE TO HAVE (Low Priority)

### 16. Add Performance Tests

**Status:** Not Started
**Priority:** Low
**Complexity:** Medium
**Estimated Time:** 8 hours

**What to test:**
- API endpoint response times
- Database query performance
- Large dataset handling
- Concurrent user simulation

**Tools:**
- locust or k6 for load testing
- pytest-benchmark for Python benchmarks

**Files to create:**
- /home/user/aupat/tests/performance/test_api_performance.py
- /home/user/aupat/tests/performance/locustfile.py

**Acceptance criteria:**
- Performance baseline documented
- Regression tests in CI/CD
- Performance targets defined

---

### 17. Add Database ER Diagram

**Status:** Not Started
**Priority:** Low
**Complexity:** Low
**Estimated Time:** 2 hours

**What to create:**
- Entity-Relationship diagram
- Table relationships clearly shown
- Field types and constraints

**Tools:**
- dbdiagram.io (web-based)
- Draw.io
- Mermaid diagram

**File to create:**
- /home/user/aupat/docs/DATABASE_SCHEMA.md (with diagram)

---

### 18. Add Backup/Restore Documentation

**Status:** Not Started
**Priority:** Low
**Complexity:** Low
**Estimated Time:** 2 hours

**What to document:**
- Backup procedures
- Restore procedures
- Automated backup setup
- Testing restore process
- Disaster recovery plan

**File to create:**
- /home/user/aupat/docs/BACKUP_RECOVERY.md

---

### 19. Implement Request Rate Limiting

**Status:** Not Started
**Priority:** Low
**Complexity:** Low
**Estimated Time:** 2 hours

**What to add:**
- Rate limiting on API endpoints
- Configurable limits per endpoint
- Return 429 status code when exceeded

**Dependencies:**
- flask-limiter

**Files to modify:**
- /home/user/aupat/requirements.txt
- /home/user/aupat/app.py

---

### 20. Add Monitoring/Metrics

**Status:** Not Started
**Priority:** Low
**Complexity:** High
**Estimated Time:** 12 hours

**What to implement:**
- Prometheus metrics endpoint
- Request count, latency, errors
- Database query metrics
- Custom business metrics

**Dependencies:**
- prometheus-flask-exporter

**Files to create:**
- /home/user/aupat/docs/MONITORING.md

**Endpoint:**
- GET /metrics (Prometheus format)

---

## COMPLETED TASKS

### Documentation Overhaul (2025-11-18)
- Created claude.md with core principles and processes
- Created lilbits.md documenting all scripts
- Created comprehensive codebase audit
- Created dependency map documentation
- Created this todo.md

### Codebase Analysis (2025-11-18)
- Complete file exploration and audit
- Dependency mapping (all 27 Python files)
- Identified critical issues and gaps
- No circular dependencies found

### Critical Fixes (2025-11-18)
- Fixed blueprint registration in app.py (api_routes_bookmarks, api_maps now accessible)
- Fixed hardcoded database path in api_routes_bookmarks.py (now uses current_app.config)
- Fixed import path in immich_integration.py (changed from relative to absolute import)
- Created unified launch.sh script (consolidates 4 different startup methods)
- Created comprehensive health_check.py script (database, filesystem, tools, services)
- Fixed hardcoded macOS paths by creating template system (com.aupat.worker.plist.template + generate_plist.py)
- Added transaction boundaries to all multi-step database operations (db_import_v012.py, db_organize.py, db_ingest.py, map_import.py, api_routes_v012.py)
- Added startup external tool availability checks in app.py (warns if exiftool/ffmpeg missing with install instructions)

---

## LONG-TERM ROADMAP

### Phase 1: Critical Fixes (Est: 2 weeks)
- Tasks 1-7 from Critical Issues section
- Goal: Stable, production-ready core

### Phase 2: Documentation & Quality (Est: 2 weeks)
- Tasks 8-12 from Important Improvements
- Goal: Professional-grade documentation and code quality

### Phase 3: Performance & Scale (Est: 1 week)
- Tasks 13, 16, 19, 20
- Goal: Handle larger datasets and more users

### Phase 4: Mobile & Extensions (Est: 6+ weeks)
- Task 14 (mobile app decision and implementation)
- Additional features from IMPLEMENTATION_STATUS.md

---

## TASK TRACKING

### How to Update This File

When starting a task:
1. Change Status to "In Progress"
2. Add assignee if applicable
3. Note start date

When completing a task:
1. Change Status to "Done"
2. Note completion date
3. Move to Completed Tasks section
4. Update related documentation

### Task Status Values
- Not Started
- In Progress
- Blocked (note blocker)
- Done
- Won't Fix (note reason)

---

## PRIORITY DEFINITIONS

**High Priority:**
- Breaks functionality
- Security issue
- Blocks other work
- Affects user experience significantly

**Medium Priority:**
- Improves maintainability
- Enhances developer experience
- Adds important features
- Performance improvements

**Low Priority:**
- Nice to have features
- Documentation improvements
- Minor optimizations
- Future enhancements

---

## REFERENCES

- claude.md: Development rules and processes
- lilbits.md: Script documentation
- techguide.md: Technical architecture
- docs/dependency_map.md: File dependencies
- CODEBASE_AUDIT_COMPLETE.md: Complete audit report

---

End of TODO list. Last updated: 2025-11-18
