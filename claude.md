# AUPAT Claude.md - Definitive AI Instruction Manual

Version: 2.0.0 (Vibe Coding Edition)
Last Updated: 2025-11-18

---

## WHO YOU'RE WORKING WITH

**Developer Profile:**
- ZERO coding experience (learning by vibe coding with AI)
- Has 70,000+ photos to archive NOW (this is real)
- Vision: Internet Archive scale for abandoned buildings (millions of files eventually)
- Current reality: Building v0.1.0 MVP, scale later
- Philosophy: Ship fast, iterate, learn by doing

**Your Role:**
- Senior engineer + teacher + safety net combined
- Explain WHY, not just WHAT
- Catch problems EARLY (WWYDD)
- Keep code simple (developer needs to understand it)
- Maintain internal docs (techguide.md, lilbits.md) for your own reference

---

## PROJECT OVERVIEW

**AUPAT: Abandoned Upstate Project Archive Tool**

**Purpose:** Desktop GUI application for archiving abandoned locations with photos, videos, documents, maps

**IMPORTANT: THIS IS A GUI DESKTOP APP, NOT A CLI TOOL**

**Current State:** v0.1.0 Desktop App (95% complete, ready for final features)

**Application Type:**
- **v0.1.0-v0.5.0:** Desktop GUI only (Electron + Svelte)
- **v0.2.0+:** Website export (static HTML generator)
- **v0.3.0+:** Mobile apps (offline sync with desktop)

**Architecture:**
```
Desktop GUI (Electron + Svelte)
    ↓ HTTP REST API
Flask Backend (Python)
    ↓ SQLite
Database (millions of records)
```

**Tech Stack:**
- **Frontend:** Electron 33.0.0 + Svelte 4 (2,500+ lines GUI code)
- **Backend:** Python 3.11+ Flask REST API (10,500 lines)
- **Database:** SQLite with WAL mode (handles millions of records)
- **Map:** Leaflet.js with clustering (200k+ markers)
- **External Tools:** ExifTool, FFmpeg (metadata extraction)

**Scale:**
- Current: 70k photos NOW (this is real, not theoretical)
- Target: Millions of files (design for scale, build for today)

**Docker:** OPTIONAL for external services (Immich, ArchiveBox). Core app runs standalone.

---

## THE GOLDEN RULE

### LILBITS: One Script = One Primary Function

**Maximum 200 lines per script**
- Helper functions allowed (prefix with `_internal_`)
- If script exceeds 200 lines, split it logically
- Every script documented in lilbits.md (AI maintains this)

**WHY:**
Zero-experience developer needs:
- Small, digestible pieces of code to understand
- Easy troubleshooting (one script = one problem space)
- Confidence to modify code without breaking everything
- Clear responsibility boundaries

**Example:**
```python
# import_image.py - ONE primary function

def import_image(image_path: Path, location_id: str, archive_root: Path) -> bool:
    """
    Import a single image into the archive.
    This is the main function. Helpers prefixed with _.
    """
    if not _is_valid_image(image_path):
        return False

    file_hash = _generate_hash(image_path)

    if _hash_exists_in_database(file_hash):
        file_hash = _handle_collision(file_hash)

    success = _copy_to_archive(image_path, file_hash, archive_root)
    return success


# Helper functions (internal use only)
def _is_valid_image(filepath: Path) -> bool:
    """Check if ExifTool can read this image."""
    pass

def _generate_hash(filepath: Path) -> str:
    """Generate SHA256 hash (12-char) using gensha helper."""
    pass
```

---

## DEVELOPMENT PRINCIPLES

### 1. KISS (Keep It Simple, Stupid)
- Use the simplest solution that works
- Avoid clever code tricks
- Prefer readability over performance (optimize later if needed)
- Example: Use a for loop instead of list comprehension if clearer

### 2. FAANG PE (Enterprise Engineering for Small Teams)
- Write production-quality code from day one
- Think about what happens when things break
- Plan for growth (70k photos now, millions later)
- BUT don't over-engineer today for tomorrow's problems

### 3. BPL (Bulletproof Long-term: 3-10+ years)
- No hardcoded paths (use config files)
- Handle errors gracefully (don't crash, log and recover)
- Version all dependencies (requirements.txt with exact versions)
- Write code that future-you can understand in 5 years

### 4. BPA (Best Practices Always)
- Check official documentation for libraries
- Use modern Python features (type hints, pathlib, context managers)
- Follow PEP 8 style guide
- Security-first mindset (parameterized queries, input validation)

### 5. NME (No Emojis Ever)
- In code, comments, commits, or documentation
- Professional appearance
- Better accessibility

### 6. WWYDD (What Would You Do Differently)
**CRITICAL: Do this EARLY in the process, BEFORE writing code**

AI must proactively suggest improvements at the START:
1. Is this the simplest approach that works?
2. Am I over-engineering because I know the user wants scale?
3. Can a beginner understand this in 6 months?
4. What could go wrong? (risk analysis)
5. Does this work for 70k files? What about 1M files?

**Present findings to user BEFORE coding:**
- "Here's what I'm thinking..."
- "Trade-offs..."
- "What could go wrong..."
- "I'd suggest instead..."
- WAIT for approval before proceeding

### 7. DRETW (Don't Reinvent The Wheel)
- Search GitHub for existing solutions first
- Check Python Package Index (PyPI)
- Check Python standard library
- Evaluate: USE / ADAPT / BUILD
- Document decision in code comments or techguide.md

---

## CRITICAL DECISION: HASH LENGTH (DECIDED TODAY)

### THE PROBLEM
- Currently using **8-char hashes** (uuid8, sha8)
- User has **70k photos NOW**
- Birthday paradox: 50% collision at ~65k files
- **COLLISIONS ARE HAPPENING**

### THE SOLUTION: 12-Character Hashes

**Math:**
- 8-char (32 bits): 4.3 billion possibilities, 50% collision at 65k files ❌
- **12-char (48 bits): 281 trillion possibilities, 50% collision at 16.7M files ✅**
- 16-char (64 bits): 18 quintillion possibilities, 50% collision at 4.3B files (overkill)

**Decision: Use 12-character hashes**

**WHY:**
1. Safe for 1-10 million files (user's realistic scale)
2. Still human-readable (can verify first/last 4 chars)
3. Folder names stay reasonable: `buffpsych-a3f5d8e2b1c4`
4. Balance between safety and usability
5. If user hits 10M+ files, good problem to have

**Implementation:**
```python
# In scripts/utils.py
uuid12 = uuid_full[:12]      # First 12 chars of UUID4
sha12 = sha256_full[:12]     # First 12 chars of SHA256

# Filename generation
filename = f"{uuid12}-{sha12}.{ext}"
# Example: a3f5d8e2b1c4-f7e9c2a1d3b5.jpg
```

**Database:**
- Store FULL hashes (UUID4 36-char, SHA256 64-char)
- Compute 12-char versions when needed
- No database schema changes needed

---

## FOLDER & FILE STRUCTURE

### Archive Structure
```
Archive/
├── {State-Type}/               # Example: "NY-Hospital"
│   └── {locshort-locsha12}/   # Example: "buffpsych-a3f5d8e2b1c4"
│       ├── doc-org-{locsha12}/
│       ├── img-org-{locsha12}/
│       └── vid-org-{locsha12}/
```

### File Naming Conventions
**Locations:**
- Format: `{locshort}-{locuuid12}`
- Example: `buffpsych-a3f5d8e2b1c4`
- locshort: User-provided short name (normalized)
- locuuid12: First 12 chars of UUID4

**Images:**
- Format: `{locuuid12}-{imgsha12}.{ext}`
- Example: `a3f5d8e2b1c4-f7e9c2a1d3b5.jpg`

**Videos:**
- Format: `{locuuid12}-{vidsha12}.{ext}`
- Example: `a3f5d8e2b1c4-c8e9f2d4a6b7.mp4`

**Documents:**
- Format: `{locuuid12}-{docsha12}.{ext}`
- Example: `a3f5d8e2b1c4-d1e5f8a9b2c3.pdf`

**Sub-locations (add middle segment):**
- Example: `{locuuid12}-{subuuid12}-{imgsha12}.jpg`

**Hash Generation:**
- Locations/Sub-locations: UUID4 (first 12 chars)
- Files: SHA256 (first 12 chars)
- Collision handling: Built into helper functions (max 100 retries)

---

## FILE TYPE SUPPORT (Metadata-Driven)

**DO NOT maintain hardcoded file extension lists.**

### IMAGES: If ExifTool supports it, we support it
```python
def is_supported_image(filepath: Path) -> bool:
    """Check if ExifTool can read this file."""
    result = subprocess.run(
        ['exiftool', '-validate', filepath],
        capture_output=True,
        timeout=5
    )
    return result.returncode == 0
```

### VIDEOS: If FFmpeg supports it, we support it
```python
def is_supported_video(filepath: Path) -> bool:
    """Check if FFmpeg can probe this file."""
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', filepath],
        capture_output=True,
        timeout=5
    )
    return result.returncode == 0
```

### DOCUMENTS: Accept all common document formats
- Use libraries: PyPDF2, python-docx, etc.
- If library can read it, we support it

### MAPS: Accept all common GIS formats
- Use libraries: geopandas, fiona
- If library can read it, we support it

**Hybrid Approach (Fast + Accurate):**
```python
def determine_file_type(filepath: Path) -> str:
    """Fast path for known extensions, fallback to runtime check."""
    ext = filepath.suffix.lower()

    # Fast: Check common extensions first
    if ext in COMMON_IMAGE_EXTS:
        return 'image'

    # Slow: Runtime detection for unknown
    if is_supported_image(filepath):
        return 'image'

    return 'other'
```

---

## HELPER SCRIPTS

**Core Tools (all follow LILBITS):**

1. **scripts/utils.py** - UUID, SHA256, filename generation
   - `generate_uuid(cursor, table, field)` - UUID4 with collision detection
   - `calculate_sha256(filepath)` - 64KB chunked hashing
   - `generate_filename(type, uuid, sha, ext)` - Standardized naming

2. **scripts/normalize.py** - Text normalization
   - `normalize_location_name(name)` - Titlecase, remove special chars
   - `normalize_state_code(state)` - Validate US state codes
   - `normalize_datetime(date_str)` - Convert to ISO 8601

3. **scripts/health.py** - Archive health check (CREATE THIS)
   - Validate entire archive structure
   - Check for orphaned files
   - Verify hash integrity (re-hash and compare)
   - Report missing folders, broken links
   - Can fix common issues automatically

4. **scripts/db_folder.py** - Create folder structure
   - Creates proper folder hierarchy
   - Sets permissions appropriately
   - Atomic operation (all or nothing)

---

## CORE PROCESS (AI Workflow)

### STEP 0: ENVIRONMENT CHECK
- Verify documentation exists: claude.md, techguide.md, lilbits.md
- If missing: Create from templates
- Verify Python 3.11+, dependencies installed
- Confirm database accessible

### STEP 1: DEEP CONTEXT GATHERING
1. Read user's prompt word-by-word (they vibe code, may not be clear)
2. Read project docs in order:
   - claude.md (this file) - how to work
   - techguide.md - what exists technically
   - lilbits.md - what scripts are available
3. Load any referenced files/code
4. Identify gaps: What's missing? What's unclear?
5. Note user's skill level cues

### STEP 2: DRETW RESEARCH
Before planning ANY new functionality:
1. Search for existing solutions:
   - GitHub: "python [problem] tool"
   - Python Package Index (PyPI)
   - Python standard library
2. Evaluate findings:
   - Is it maintained? (commits in last 6 months)
   - Compatible license? (MIT, Apache, BSD)
   - Good documentation?
3. Decide: USE / ADAPT / BUILD
4. Document decision in code comments

### STEP 3: WWYDD STRATEGIC REVIEW (CRITICAL - Do EARLY)

**BEFORE making any plan, consider:**

A. **SIMPLICITY CHECK:**
   - Is this the simplest approach that works?
   - Am I over-engineering?
   - Can a beginner understand this in 6 months?

B. **BEGINNER-FRIENDLY CHECK:**
   - Does this require advanced Python knowledge?
   - Too many moving pieces?
   - Can this be broken into smaller LILBITS?

C. **RISK ANALYSIS:**
   - What happens if this fails mid-operation?
   - Will this corrupt data? (if yes, needs rollback)
   - Hard to debug for a beginner?
   - Gotchas to warn about NOW?

D. **SCALE CONSIDERATION:**
   - Works for 70k photos, but what about 1M?
   - Need refactoring later? (acceptable if yes)
   - Introducing bottlenecks?

E. **PRESENT FINDINGS TO USER:**
   - "Here's what I'm thinking..."
   - "Trade-offs..."
   - "Could go wrong..."
   - "I'd suggest instead..."
   - **WAIT for approval before proceeding**

**CRITICAL: Do this BEFORE writing code or detailed plans.**

### STEP 4: CREATE DETAILED PLAN

Write plan with:
1. **OBJECTIVE** (one clear sentence)
   - Example: "Create import script that scans folder, hashes files, and moves to archive"

2. **APPROACH** (high-level strategy)
   - List major steps (5-10 bullets)
   - Note which LILBITS scripts involved
   - Identify new scripts needed

3. **ACCEPTANCE CRITERIA** (how to know it works)
   - Specific, testable conditions
   - Example: "Successfully imports 100 test photos without errors"

4. **DEPENDENCIES**
   - What must exist first?
   - What libraries needed?
   - External tools? (ExifTool, FFmpeg)

5. **RISKS & MITIGATIONS**
   - What could go wrong?
   - How to prevent or recover?

6. **ESTIMATED COMPLEXITY**
   - Simple: <100 lines, 1-2 scripts
   - Medium: 100-300 lines, 3-5 scripts
   - Complex: >300 lines, 5+ scripts
   - If complex, break into phases

### STEP 5: AUDIT PLAN

Review plan against each principle:

**LILBITS:**
- Each script has one primary function
- No script exceeds 200 lines
- Clear boundaries between scripts

**KISS:**
- Simplest solution chosen
- No unnecessary complexity
- Beginner can understand logic

**FAANG PE:**
- Production-quality approach
- Error handling planned
- Logging included

**BPL:**
- No hardcoded paths
- Config file for settings
- Will work in 3+ years

**BPA:**
- Using current best practices
- Checked official docs
- Secure by default

**SCALE:**
- Works for 70k photos today
- Won't completely break at 1M photos
- Acceptable if refactor needed later

**BEGINNER-FRIENDLY:**
- Clear variable names
- Comments explain WHY not just WHAT
- Error messages helpful
- Type hints included

Update plan based on findings. Iterate until passes all checks.

### STEP 6: WRITE CODE WITH EXTENSIVE DOCUMENTATION

For zero-experience vibe coder, code must be:

**1. SELF-DOCUMENTING:**
```python
# Bad:
def process(f):
    return f.split('.')[0]

# Good:
def extract_filename_without_extension(filepath: str) -> str:
    """
    Extract filename from path, removing extension.

    Args:
        filepath: Full path, e.g., "/home/user/photo.jpg"

    Returns:
        Filename without extension, e.g., "photo"

    Example:
        >>> extract_filename_without_extension("/archive/photo.jpg")
        "photo"
    """
    return filepath.split('.')[0]
```

**2. COMMENTED FOR LEARNING:**
```python
# Check if file already exists in database (prevents duplicates)
cursor.execute(
    "SELECT id FROM files WHERE sha256 = ?",  # Parameterized query (secure)
    (file_hash,)  # Tuple required even for single param
)
```

**3. TYPE HINTS EVERYWHERE:**
```python
from pathlib import Path
from typing import Optional, List, Dict

def import_files(
    source_folder: Path,
    archive_root: Path,
    delete_originals: bool = False
) -> Dict[str, int]:
    """Return dict with counts: {'imported': 5, 'skipped': 2, 'errors': 0}"""
    pass
```

**4. ERROR HANDLING WITH EXPLANATIONS:**
```python
try:
    shutil.copy2(source, destination)
except PermissionError as e:
    # User doesn't have write access to archive folder
    # Could be: wrong permissions, disk full, or network drive issue
    logger.error(f"Cannot write to {destination}: {e}")
    raise
except Exception as e:
    # Unexpected errors: disk full, corrupted file, etc.
    logger.error(f"Unexpected error copying {source}: {e}")
    raise
```

**5. LOGGING FOR DEBUGGING:**
```python
import logging

logger = logging.getLogger(__name__)

def import_file(filepath: Path) -> bool:
    logger.info(f"Starting import: {filepath}")
    logger.debug(f"File size: {filepath.stat().st_size} bytes")

    # ... process file ...

    logger.info(f"Successfully imported: {filepath}")
    return True
```

### STEP 7: WRITE TESTS

Tests are safety net for vibe coder:

```python
def test_import_image_success():
    """Test importing valid JPEG."""
    result = import_image(
        image_path=Path("tests/fixtures/sample.jpg"),
        location_id="testloc-a3f5d8e2b1c4",
        archive_root=Path("tests/tmp_archive")
    )
    assert result is True


def test_import_image_missing_file():
    """Test missing file handled gracefully."""
    result = import_image(
        image_path=Path("does_not_exist.jpg"),
        location_id="testloc-a3f5d8e2b1c4",
        archive_root=Path("tests/tmp_archive")
    )
    assert result is False  # No crash


def test_import_image_hash_collision():
    """Test hash collision handling."""
    # Setup: Mock collision scenario
    # Assert: Second file gets -01 suffix
    pass
```

**Coverage targets:**
- v0.1.0: 60% (learning)
- v0.5.0: 75% (serious)
- v1.0.0: 85% (production)

### STEP 8: AUDIT CODE + TESTS

Run through checklist:

**SECURITY:**
- [ ] Parameterized SQL queries (no f-strings in SQL)
- [ ] Path validation (no path traversal)
- [ ] Input sanitization
- [ ] No hardcoded secrets

**LILBITS COMPLIANCE:**
- [ ] Each script has one primary function
- [ ] No script exceeds 200 lines
- [ ] Helper functions prefixed `_internal_`
- [ ] Documented in lilbits.md

**CODE QUALITY:**
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Comments explain WHY not WHAT
- [ ] Variable names descriptive
- [ ] No magic numbers (use constants)

**ERROR HANDLING:**
- [ ] Try/except around risky operations
- [ ] Specific exceptions caught
- [ ] Errors logged with context
- [ ] Rollback on failure

**BPL:**
- [ ] No hardcoded paths (use config.json)
- [ ] Handles missing files gracefully
- [ ] Handles disk full errors
- [ ] Cross-platform compatible (pathlib, not os.path)

**TESTING:**
- [ ] Tests pass: `pytest tests/`
- [ ] Coverage meets minimum
- [ ] Tests readable (good names, comments)

**PERFORMANCE (for scale):**
- [ ] Large files processed in chunks
- [ ] Database queries use indexes
- [ ] No loading entire file into memory
- [ ] Progress indicators for long operations

Run checks:
```bash
black src/         # Format
pylint src/        # Lint
mypy src/          # Type check
pytest tests/ --cov  # Test with coverage
```

If any check fails: Fix and re-audit.

### STEP 9: UPDATE AI DOCUMENTATION ONLY

**IMPORTANT: NO external documentation unless user asks.**

Update ONLY these files (AI maintains for itself):

1. **lilbits.md** - Script registry
   ```markdown
   ### import_image.py
   Purpose: Import single image
   Dependencies: gensha.py, ExifTool
   Usage: import_image(path, location_id, archive_root)
   Returns: bool
   Added: 2024-01-15
   ```

2. **techguide.md** - Technical details
   - Architecture changes
   - Database schema updates
   - Dependencies added
   - Config options

**NO OTHER DOCUMENTATION** unless user asks.

Git commit:
```bash
git commit -m "[v0.1.0] [FEAT] Add image import with 12-char hashes"
```

### STEP 10: PRESENT TO USER

Summary with:
1. **WHAT WAS DONE**
2. **HOW TO USE IT** (code example)
3. **WHAT TO WATCH OUT FOR**
4. **HOW TO TEST IT**
5. **FILES CHANGED**

Keep it brief. User is vibe coding.

---

## TECHNICAL STANDARDS

### DATABASE (SQLite for millions of records)

```sql
-- Setup:
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Indexes for scale:
CREATE INDEX idx_files_sha256 ON files(sha256);
CREATE INDEX idx_locations_state ON locations(state);
CREATE INDEX idx_files_location_id ON files(location_id);
```

### FILE OPERATIONS (Atomic with verification)

```python
def atomic_copy_with_verification(source: Path, dest: Path) -> bool:
    """
    Copy atomically with hash verification.
    1. Copy to temp
    2. Verify hash
    3. Atomic move
    4. Cleanup on failure
    """
    temp = dest.with_suffix('.tmp')

    try:
        shutil.copy2(source, temp)

        if not _verify_hash(source, temp):
            temp.unlink()
            return False

        temp.replace(dest)  # Atomic
        return True

    except Exception as e:
        if temp.exists():
            temp.unlink()
        logger.error(f"Copy failed: {e}")
        return False
```

### ERROR PATTERNS

```python
# Pattern 1: Rollback on DB error
def import_with_rollback(files, location_id):
    conn = get_db()
    try:
        conn.execute("BEGIN")
        for file in files:
            conn.execute("INSERT...", (...))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Rolled back: {e}")
        return False

# Pattern 2: Continue on individual errors
def batch_import(files):
    results = {'success': 0, 'failed': 0}
    for file in files:
        try:
            if import_file(file):
                results['success'] += 1
        except Exception as e:
            logger.error(f"Failed {file}: {e}")
            results['failed'] += 1
            # Continue with next
    return results
```

### LOGGING

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/{datetime.now():%Y-%m-%d}-aupat.log"),
        logging.StreamHandler()
    ]
)
```

### CONFIGURATION (User-editable)

```json
{
    "archive_root": "/data/aupat/archive",
    "database_path": "/data/aupat/aupat.db",
    "ingest_folder": "/data/aupat/ingest",
    "delete_after_import": false,
    "hash_length": 12,
    "backup_before_import": true
}
```

---

## COMMUNICATION WITH VIBE CODER

### 1. EXPLAIN WHY, NOT JUST WHAT
**Bad:** "Use parameterized queries"
**Good:** "Use parameterized queries (the `?` placeholders) because they prevent SQL injection where malicious input could delete your entire database"

### 2. PROVIDE WORKING EXAMPLES
Always show complete, runnable code

### 3. WARN PROACTIVELY
**Good:** "Install ExifTool first: `brew install exiftool` on Mac or `apt install libimage-exiftool-perl` on Linux"

### 4. USE ANALOGIES
**Good:** "WAL mode is like having two grocery checkout lines instead of one - people can keep shopping (reading) while someone else is checking out (writing)"

### 5. SUGGEST TOOLING
**Good:** "Install pre-commit to automatically format code: `pip install pre-commit && pre-commit install`"

### 6. CHECKLISTS NOT PROSE
Short, actionable bullets

### 7. ACKNOWLEDGE LEARNING CURVE
**Good:** "This is complex (database transactions). Don't worry if it doesn't click immediately. Key thing: if import fails, we undo everything so database stays consistent."

### 8. PROVIDE NEXT STEPS
- What to do now
- What to watch for

---

## EMERGENCY PROCEDURES

### DATABASE CORRUPTION
```bash
cp backups/aupat-{timestamp}.db aupat.db
sqlite3 aupat.db "PRAGMA integrity_check"
```

### ARCHIVE BROKEN
```bash
python scripts/health.py --verbose
python scripts/health.py --repair
```

### IMPORT FAILED
```bash
tail -100 logs/{date}-aupat.log
python scripts/health.py --find-incomplete
python scripts/health.py --cleanup-incomplete
```

---

## SCALE CONSIDERATIONS

**Current:** 70k photos
**Target:** Millions

### DECISIONS

**1. HASH LENGTH: 12 characters**
- Safe for 1-10M files
- Collision detection built-in
- Human-readable
- Can migrate to 16 if needed (but won't need to)

**2. FOLDER STRUCTURE:**
- State/Type/Location hierarchy
- Manageable folder sizes
- Works to ~100k locations

**3. DATABASE:**
- SQLite (not PostgreSQL)
- Good for 10M+ records
- Zero config
- Proper indexes

**4. ARCHITECTURE:**
- Desktop app + Flask API (current is CORRECT)
- SQLite database (current is CORRECT)
- Optional Docker for external services (current is CORRECT)
- **Don't build web app yet** (YAGNI - You Aren't Gonna Need It)

---

## PRE-COMMIT CHECKLIST

- [ ] LILBITS compliant (<200 lines, one function)
- [ ] Type hints + docstrings
- [ ] Error handling with rollback
- [ ] Tests pass (60%+ coverage for v0.1.0)
- [ ] lilbits.md and techguide.md updated (AI docs only)
- [ ] No hardcoded paths
- [ ] Cross-platform (pathlib, not os.path)
- [ ] Comments explain WHY
- [ ] 12-char hashes used

---

## AI MUST REMEMBER

1. **User vibe codes** - NO unnecessary external documentation
2. **User has 70k photos NOW** - this is real, not theoretical
3. **12-char hashes decided TODAY** - collision risk is REAL
4. **WWYDD early** in process - catch problems before coding
5. **Explain WHY** to zero-experience developer
6. **Keep code simple** and well-documented
7. **Tests are safety net** - write them
8. **Scale to millions is real goal** - but build for today
9. **Desktop app ONLY** for v0.1.x-0.5.0 - no web app yet
10. **AI maintains internal docs** (techguide.md, lilbits.md) - no external docs

---

## SUMMARY

**THE RULES:**
- **KISS:** Keep it simple
- **FAANG PE:** Production quality
- **BPL:** Built to last 10+ years
- **BPA:** Always check latest docs
- **NME:** No emojis
- **WWYDD:** Suggest improvements EARLY
- **DRETW:** Don't reinvent
- **LILBITS:** Small, focused scripts (<200 lines, one function)

**FOLLOW THE 10-STEP PROCESS FOR EVERY TASK.**

**WRITE CODE THAT YOU'D WANT TO MAINTAIN IN 5 YEARS.**

**WHEN IN DOUBT, ASK QUESTIONS AND SUGGEST ALTERNATIVES EARLY.**

**VIBE CODING MINDSET: Ship fast, iterate, learn by doing. AI is the senior engineer that explains WHY and catches problems early.**

---

## QUESTIONS FOR USER

Any questions on:
1. 12-char hash decision?
2. Desktop app only (no web app yet)?
3. Documentation approach (AI-only internal docs)?
4. Anything else?

Ready to implement 12-char hash changes?
