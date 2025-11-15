# AUPAT - AI Collaboration Guide

## Project Overview

AUPAT (Abandoned Upstate Project Archive Tool) is a bulletproof digital asset management system designed to organize, catalog, and archive location-based media collections with a focus on long-term data integrity and professional engineering standards.

**Core Function**: Organize photos, videos, documents, and URLs by geographic location with hardware-based categorization, metadata extraction, deduplication, and comprehensive relationship tracking.

**Current Status**: Planning phase. Comprehensive documentation complete. No code implementation yet.

---

## Project Context for AI Collaboration

### Implementation Status

**What Exists**:
- Complete documentation for all components in logseq/pages/
- Comprehensive methodology in claudecode.md
- Architecture design and specifications
- Database schema definitions
- Workflow designs

**What Doesn't Exist Yet**:
- No Python scripts implemented (13 scripts documented, 0 written)
- No JSON configuration files created (14 files documented, 0 created)
- No database created
- No folder structure created (scripts/, data/, user/, backups/, logs/)
- No tests written
- No web interface

**Critical**: When working on this project, always verify actual file existence before referencing implementation. The gap between documentation and implementation is 100%.

---

## Core Engineering Principles

Follow these principles in order of importance:

1. **BPA - Best Practices Always**: Never compromise on industry standards
2. **BPL - Bulletproof Longterm**: Code must survive years without modification
3. **KISS - Keep It Simple Stupid**: Simplicity trumps cleverness
4. **FAANG PE - FAANG Personal Edition**: Production-grade without enterprise bloat
5. **WWYDD - What Would You Do Differently**: Challenge fundamentally flawed approaches
6. **NEE - No Emojis Ever**: Professional documentation only
7. **No Self-Credit**: Don't credit tools or AI in code/docs

---

## The 9-Step Bulletproof Workflow

When performing any development task (bug fix, new feature, refactor, troubleshooting):

**Step 1**: Audit the code against .md files and implementation guides. Verify all .py scripts are complete and ready.

**Step 2**: Draft a clear plan to update all necessary files.

**Step 3**: Audit the plan. It must follow KISS, FAANG PE, BPL principles, plus best practices for Python and linked programs. Update the plan.

**Step 4**: Review all related .py, .md, .json, and .pdf files again. Re-audit the plan to ensure it remains accurate and error-free. Update as needed.

**Step 5**: Write an in-depth update guide aimed at a less-experienced coder.

**Step 6**: Audit the implementation guide for clarity and completeness.

**Step 7**: Audit that guide and refine it with clear explanations of the core logic.

**Step 8**: Write or update the code accordingly.

**Step 9**: Test the code end-to-end to confirm it works as intended.

**See claudecode.md for detailed breakdown of each step.**

---

## Project Structure

### Intended Folder Structure

```
/Users/bryant/Documents/tools/aupat/
├── scripts/              # All .py scripts
│   ├── db_migrate.py     # Database schema creation/updates
│   ├── db_import.py      # Import locations via CLI/web
│   ├── db_organize.py    # Extract metadata, categorize media
│   ├── db_folder.py      # Create folder structure
│   ├── db_ingest.py      # Move files to archive locations
│   ├── db_verify.py      # Verify integrity, cleanup staging
│   ├── db_identify.py    # Generate JSON exports per location
│   ├── database_cleanup.py  # Maintenance and integrity checks
│   ├── backup.py         # Database backups
│   ├── gen_uuid.py       # UUID4 generation
│   ├── gen_sha.py        # SHA256 hashing
│   ├── name.py           # File naming conventions
│   └── folder.py         # Folder creation utilities
├── data/                 # All .json configuration files
│   ├── locations.json
│   ├── sub-locations.json
│   ├── images.json
│   ├── videos.json
│   ├── documents.json
│   ├── urls.json
│   ├── versions.json
│   ├── camera_hardware.json
│   ├── approved_ext.json
│   ├── ignored_ext.json
│   ├── live_videos.json
│   ├── folder.json
│   └── name.json
├── user/                 # User configuration
│   └── user.json         # Database paths and settings
├── venv/                 # Python virtual environment (gitignored)
├── backups/              # Database backups (gitignored)
├── logs/                 # Application logs (gitignored)
├── logseq/               # Documentation (current home of all .md files)
├── claude.md             # This file
├── claudecode.md         # Development methodology
├── project-overview.md   # Complete technical reference
└── .gitignore
```

---

## Technology Stack

- **Language**: Python 3
- **Database**: SQLite with JSON1 extension
- **Metadata Tools**: exiftool (images), ffprobe (videos)
- **Text Normalization**: unidecode, libpostal, dateutil
- **Frontend** (Stage 2): Web application (framework TBD)
- **Deployment** (Stage 3): Docker
- **Mobile** (Stage 4): Mobile app with Docker backend

---

## Database Requirements

### Always Required

- **Transaction Safety**: Wrap all modifications in BEGIN/COMMIT/ROLLBACK
- **Foreign Keys**: PRAGMA foreign_keys = ON at connection start
- **Error Handling**: Try/except for all database operations
- **Backups**: Automated backup before schema changes or bulk operations
- **Verification**: Verify operations succeeded before cleanup

### Schema Enforcement

- UUID4 for all primary identifiers (loc_uuid, sub_uuid, etc.)
- SHA256 for all file hashing (collision detection required)
- Foreign key relationships between tables
- JSON1 for complex fields (hardware metadata, relationships)
- Version tracking for schema changes

---

## Core Workflows

### Import Pipeline (Run in Order)

1. **db_migrate.py**: Create/update database schema
2. **db_import.py**: Import location and media to staging
3. **db_organize.py**: Extract metadata, categorize by hardware
4. **db_folder.py**: Create organized folder structure
5. **db_ingest.py**: Move files from staging to archive
6. **db_verify.py**: Verify SHA256, cleanup staging
7. **db_identify.py**: Generate master JSON per location
8. **database_cleanup.py**: Maintenance and integrity checks

### Hardware Categorization

- **Images**: DSLR, Phone, Drone, GoPro, Film, Other (via EXIF Make/Model)
- **Videos**: Camera, Phone, Drone, GoPro, Dash Cam, Other (via ffprobe metadata)
- **Special Cases**: Live photos (match image/video pairs by name/location)

### File Naming Convention

- Images: `loc_uuid8-img_sha8.ext` or `loc_uuid8-sub_uuid8-img_sha8.ext`
- Videos: `loc_uuid8-vid_sha8.ext` or `loc_uuid8-sub_uuid8-vid_sha8.ext`
- Documents: `loc_uuid8-doc_sha8.ext` or `loc_uuid8-sub_uuid8-doc_sha8.ext`

Where uuid8 = first 8 chars of UUID, sha8 = first 8 chars of SHA256

---

## Documentation Reference Map

### When Working On...

**Database Schema**:
- Read: logseq/pages/locations.json.md, images.json.md, videos.json.md, documents.json.md, urls.json.md, sub-locations.json.md, versions.json.md
- Reference: project-overview.md (Database Design section)

**Import Pipeline**:
- Read: logseq/pages/db_import.py.md, db_organize.py.md, db_folder.py.md, db_ingest.py.md, db_verify.py.md, db_identify.py.md
- Reference: project-overview.md (Python Scripts section)

**Metadata Extraction**:
- Read: logseq/pages/db_organize.py.md, camera_hardware.json.md, live_videos.json.md
- Reference: project-overview.md (Data Integrity Features section)

**File Organization**:
- Read: logseq/pages/folder.json.md, name.json.md, db_folder.py.md
- Reference: project-overview.md (Organizational Features section)

**Database Migration**:
- Read: logseq/pages/db_migrate.py.md, versions.json.md
- Reference: All schema .json.md files

**Utilities**:
- Read: logseq/pages/gen_uuid.py.md, gen_sha.py.md, backup.py.md, name.py.md
- Reference: project-overview.md (Python Scripts - Utilities section)

**Development Methodology**:
- Read: claudecode.md (always)
- Reference: This file for project context

---

## Staged Development Plan

### Stage 1: CLI Import Tool (Current Focus)
- Implement all 13 Python scripts
- Create all 14 JSON configuration files
- Build database schema
- Test import pipeline end-to-end
- Write comprehensive tests

### Stage 2: Web Application
- Build web interface for import
- Mobile-responsive design
- Location autocomplete
- Batch upload capabilities

### Stage 3: Dockerization
- Containerize web application
- Automated backups
- Data persistence
- Easy deployment

### Stage 4: Mobile Application
- Native mobile app
- Connects to Docker backend
- Field import capabilities
- Offline mode

---

## Common Tasks Guide

### Starting a New Script Implementation

1. Read logseq/pages/[script_name].md for complete specifications
2. Read all related .json.md files for schema/config dependencies
3. Follow 9-step workflow in claudecode.md
4. Verify against project principles (BPA, BPL, KISS, FAANG PE)
5. Test thoroughly before marking complete

### Creating JSON Configuration Files

1. Read logseq/pages/[json_name].md for schema definition
2. Verify field names match database schema exactly
3. Include version tracking where applicable
4. Validate JSON syntax
5. Document structure in corresponding .md file

### Database Operations

1. Always enable foreign keys: `PRAGMA foreign_keys = ON`
2. Wrap modifications in transactions
3. Backup before schema changes
4. Verify operations succeeded
5. Log all operations for debugging
6. Test rollback procedures

### Troubleshooting

1. Read error messages completely
2. Check logs for detailed context
3. Verify input data format and validity
4. Isolate failing component
5. Test in isolation
6. Verify assumptions (file exists, database writable, etc.)
7. Fix root cause, not symptoms
8. Document issue and solution
9. Add test to prevent regression

---

## Critical Reminders

### Before Any Code Implementation

- [ ] Have I read ALL relevant .md documentation files?
- [ ] Have I followed the 9-step workflow?
- [ ] Does this follow BPA, BPL, KISS, FAANG PE?
- [ ] Have I implemented proper error handling?
- [ ] Have I included transaction safety for database operations?
- [ ] Have I written tests?
- [ ] Is the code bulletproof for long-term use?

### Before Committing Code

- [ ] No emojis anywhere
- [ ] No tool attribution or self-credit
- [ ] All functions have docstrings
- [ ] Type hints on all function parameters
- [ ] Input validation implemented
- [ ] Error handling complete
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Code reviewed against checklist in claudecode.md

---

## Data Integrity Above All

In this project, data integrity is paramount. When in doubt:

1. Fail safely rather than risk corruption
2. Verify before deleting source files
3. Backup before destructive operations
4. Test rollback procedures
5. Log everything for audit trails
6. Prioritize correctness over speed

Data loss is unacceptable. Code must be bulletproof.

---

## Quick Reference Links

- **Methodology**: claudecode.md
- **Technical Specs**: project-overview.md
- **All Documentation**: logseq/pages/
- **Schema Definitions**: logseq/pages/[table_name].json.md
- **Script Specifications**: logseq/pages/[script_name].py.md

---

## Version

- v1.0 - Initial AI collaboration guide

---

**Remember**: This is a planning-phase project. All documentation is complete and accurate. No implementation exists yet. Verify actual file existence before referencing code. Follow the 9-step workflow religiously. Build bulletproof systems that will last years.
