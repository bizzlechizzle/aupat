# REFINED Implementation Plan: P0 and P1 Foundations

## Changes from Original Plan

Based on audit findings (see PLAN_AUDIT_P0_P1.md), this refined plan includes:

1. ✅ Refactored validation.py to use validator classes (KISS improvement)
2. ✅ Added checkpoint database backup mechanism (BPL improvement)
3. ✅ Added disk space monitoring for logs (BPL improvement)
4. ✅ Added performance testing requirements (FAANG PE improvement)
5. ✅ Added design rationale documentation (clarity improvement)

---

## Key Design Improvements

### 1. Validation Module Organization

**Original**: 11 individual functions
**Refined**: 4 validator classes with grouped methods

**Benefit**: Clearer organization, easier imports, maintains simplicity

```python
# Before:
from common.validation import validate_file_path, validate_directory_path, validate_uuid, validate_sha256, ...

# After:
from common.validation import PathValidator, IdentifierValidator, FormatValidator, ConfigValidator

# Usage:
PathValidator.validate_file('/path/to/file')
IdentifierValidator.validate_uuid('abc-123-...')
```

### 2. Checkpoint Resilience

**Added**: Checkpoint database backup and recovery

```python
class CheckpointManager:
    def __init__(self, checkpoint_db_path: Path, backup_interval: int = 100):
        self.checkpoint_db_path = checkpoint_db_path
        self.backup_path = checkpoint_db_path.parent / 'checkpoint_state.backup.db'
        self.operations_since_backup = 0
        self.backup_interval = backup_interval  # Backup every N operations

    def update_progress(self, checkpoint_id: str, current: int, last_item: Any):
        # Update progress
        self.operations_since_backup += 1

        # Periodic backup
        if self.operations_since_backup >= self.backup_interval:
            self._backup_checkpoint_db()
            self.operations_since_backup = 0

    def _backup_checkpoint_db(self):
        # Create backup of checkpoint database
        shutil.copy2(self.checkpoint_db_path, self.backup_path)

    def recover_from_backup(self):
        # If checkpoint DB corrupted, restore from backup
        if self.backup_path.exists():
            shutil.copy2(self.backup_path, self.checkpoint_db_path)
```

### 3. Log Disk Space Monitoring

**Added**: Disk space checks for log directory

```python
# In preflight.py
def check_log_disk_space(log_dir: Path, min_free_mb: int = 100) -> bool:
    """
    Check available space in log directory.
    Default minimum: 100MB free
    """
    stat = shutil.disk_usage(log_dir)
    free_mb = stat.free / (1024 * 1024)

    if free_mb < min_free_mb:
        raise InsufficientSpaceError(
            f"Log directory has only {free_mb:.1f}MB free, need at least {min_free_mb}MB"
        )

    # Warn if below 500MB
    if free_mb < 500:
        logger.warning(f"Log directory has only {free_mb:.1f}MB free")

    return True

# In all scripts:
preflight.add_check('log_disk_space', lambda: check_log_disk_space(Path('logs')))
```

### 4. Performance Testing Requirements

**Added**: Mandatory performance benchmarks

All foundational components must pass performance tests:

```python
# tests/test_performance.py

def test_logging_overhead():
    """Logging should add < 1% overhead"""
    # Test 10,000 log writes
    # Measure time with vs without logging
    # Assert overhead < 1%

def test_checkpoint_overhead():
    """Checkpoint updates should add < 2% overhead"""
    # Test 1,000 checkpoint updates
    # Measure time with vs without checkpoints
    # Assert overhead < 2%

def test_transaction_overhead():
    """Transaction wrapper should add < 1% overhead"""
    # Test 1,000 database operations
    # Measure time with vs without transaction wrapper
    # Assert overhead < 1%

def test_validation_performance():
    """Validation should take < 1ms per operation"""
    # Test all validators
    # Assert each completes in < 1ms

def test_progress_tracking_overhead():
    """Progress tracking should add < 0.5% overhead"""
    # Test 10,000 progress updates
    # Assert overhead < 0.5%
```

---

## Updated Module Specifications

### P0-4: Refactored Validation Module

**File**: `scripts/common/validation.py`

```python
"""
Input validation utilities for AUPAT.

Design Rationale:
- Grouped into classes for organization (KISS audit improvement)
- Static methods (no state needed, pure functions)
- Clear separation of concerns (paths, identifiers, formats, configs)
- Easy selective imports (import specific validator class)

Why Classes Instead of Functions:
- Better organization (11 functions → 4 classes)
- Clearer namespacing (PathValidator.validate_file vs validate_file_path)
- Easier to extend (add methods to appropriate class)
- Maintains simplicity (static methods = no complex state)
"""

from pathlib import Path
from typing import Optional
import re
import urllib.parse
import json
import shutil

from .exceptions import (
    ValidationError,
    InvalidUUIDError,
    InvalidPathError,
    InvalidConfigError,
    InsufficientSpaceError
)

# Optional dependency with fallback
try:
    from unidecode import unidecode
    HAS_UNIDECODE = True
except ImportError:
    HAS_UNIDECODE = False

# Optional dependency with fallback
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class PathValidator:
    """Validates filesystem paths and disk space."""

    @staticmethod
    def validate_file(path: str, must_exist: bool = True) -> Path:
        """
        Validate file path.

        Args:
            path: File path to validate
            must_exist: If True, verify file exists

        Returns:
            Absolute Path object

        Raises:
            InvalidPathError: If path invalid, doesn't exist, or not readable
        """
        # Convert to Path object
        p = Path(path).resolve()

        # Check for path traversal (should be prevented by resolve())
        # But double-check no symlinks escape intended directory
        if not str(p).startswith(str(Path.cwd().resolve())):
            # Allow absolute paths, but log for audit
            pass

        if must_exist:
            if not p.exists():
                raise InvalidPathError(f"File does not exist: {p}")

            if not p.is_file():
                raise InvalidPathError(f"Path is not a file: {p}")

            if not os.access(p, os.R_OK):
                raise InvalidPathError(f"File not readable: {p}")

        return p

    @staticmethod
    def validate_directory(
        path: str,
        must_exist: bool = True,
        must_be_writable: bool = False
    ) -> Path:
        """
        Validate directory path.

        Args:
            path: Directory path to validate
            must_exist: If True, verify directory exists
            must_be_writable: If True, verify directory is writable

        Returns:
            Absolute Path object

        Raises:
            InvalidPathError: If path invalid or permissions insufficient
        """
        p = Path(path).resolve()

        if must_exist:
            if not p.exists():
                raise InvalidPathError(f"Directory does not exist: {p}")

            if not p.is_dir():
                raise InvalidPathError(f"Path is not a directory: {p}")

        if must_be_writable:
            if not os.access(p, os.W_OK):
                raise InvalidPathError(f"Directory not writable: {p}")

        return p

    @staticmethod
    def check_disk_space(path: Path, required_bytes: int) -> bool:
        """
        Check available disk space.

        Args:
            path: Path to check (any path on target filesystem)
            required_bytes: Minimum required bytes

        Returns:
            True if sufficient space

        Raises:
            InsufficientSpaceError: If not enough space available
        """
        stat = shutil.disk_usage(path)

        if stat.free < required_bytes:
            raise InsufficientSpaceError(
                f"Insufficient disk space: {stat.free:,} bytes available, "
                f"{required_bytes:,} bytes required"
            )

        return True


class IdentifierValidator:
    """Validates UUIDs, SHA256 hashes, and SQL identifiers."""

    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    SHA256_PATTERN = re.compile(r'^[0-9a-f]{64}$', re.IGNORECASE)

    SQL_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """
        Validate UUID4 format.

        Args:
            uuid_str: UUID string to validate

        Returns:
            Normalized UUID (lowercase)

        Raises:
            InvalidUUIDError: If format invalid
        """
        uuid_normalized = uuid_str.strip().lower()

        if not IdentifierValidator.UUID_PATTERN.match(uuid_normalized):
            raise InvalidUUIDError(f"Invalid UUID4 format: {uuid_str}")

        return uuid_normalized

    @staticmethod
    def validate_sha256(sha_str: str) -> str:
        """
        Validate SHA256 hash format.

        Args:
            sha_str: SHA256 hash string to validate

        Returns:
            Normalized SHA256 (lowercase)

        Raises:
            ValidationError: If format invalid
        """
        sha_normalized = sha_str.strip().lower()

        if not IdentifierValidator.SHA256_PATTERN.match(sha_normalized):
            raise ValidationError(
                f"Invalid SHA256 format: {sha_str} "
                f"(expected 64 hex characters)"
            )

        return sha_normalized

    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column name).

        Args:
            identifier: SQL identifier to sanitize

        Returns:
            Validated identifier

        Raises:
            ValidationError: If identifier contains invalid characters
        """
        identifier = identifier.strip()

        if not IdentifierValidator.SQL_IDENTIFIER_PATTERN.match(identifier):
            raise ValidationError(
                f"Invalid SQL identifier: {identifier} "
                f"(must start with letter/underscore, contain only alphanumeric/underscore)"
            )

        # Additional check: not a SQL keyword
        SQL_KEYWORDS = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'TABLE',
            'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'TRUE', 'FALSE'
        }

        if identifier.upper() in SQL_KEYWORDS:
            raise ValidationError(f"SQL identifier cannot be a keyword: {identifier}")

        return identifier


class FormatValidator:
    """Validates data formats (location names, states, extensions, URLs)."""

    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'PR'  # DC and Puerto Rico
    }

    @staticmethod
    def validate_location_name(name: str) -> str:
        """
        Validate location name.

        Args:
            name: Location name to validate

        Returns:
            Normalized location name

        Raises:
            ValidationError: If name invalid
        """
        name = name.strip()

        if len(name) < 1 or len(name) > 255:
            raise ValidationError(
                f"Location name must be 1-255 characters, got {len(name)}"
            )

        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            raise ValidationError(
                f"Location name contains invalid characters: {name}"
            )

        # Normalize unicode if available
        if HAS_UNIDECODE:
            name = unidecode(name)

        return name

    @staticmethod
    def validate_state_code(state: str) -> str:
        """
        Validate US state code.

        Args:
            state: State code (2 letters)

        Returns:
            Uppercase state code

        Raises:
            ValidationError: If not a valid state code
        """
        state = state.strip().upper()

        if len(state) != 2:
            raise ValidationError(f"State code must be 2 characters, got: {state}")

        if state not in FormatValidator.US_STATES:
            raise ValidationError(f"Invalid US state code: {state}")

        return state

    @staticmethod
    def validate_extension(ext: str) -> str:
        """
        Validate file extension.

        Args:
            ext: File extension (with or without leading dot)

        Returns:
            Lowercase extension without dot

        Raises:
            ValidationError: If extension invalid
        """
        ext = ext.strip().lower()

        # Remove leading dot if present
        if ext.startswith('.'):
            ext = ext[1:]

        # Check alphanumeric only
        if not re.match(r'^[a-z0-9]+$', ext):
            raise ValidationError(f"Invalid file extension: {ext}")

        if len(ext) < 1 or len(ext) > 10:
            raise ValidationError(
                f"File extension must be 1-10 characters, got: {ext}"
            )

        return ext

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            Normalized URL

        Raises:
            ValidationError: If URL format invalid
        """
        url = url.strip()

        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as e:
            raise ValidationError(f"Failed to parse URL: {url} - {e}")

        # Verify scheme
        if parsed.scheme not in ('http', 'https'):
            raise ValidationError(
                f"URL must use http or https scheme, got: {parsed.scheme}"
            )

        # Verify domain exists
        if not parsed.netloc:
            raise ValidationError(f"URL missing domain: {url}")

        return url


class ConfigValidator:
    """Validates configuration files."""

    @staticmethod
    def validate_json_file(
        file_path: Path,
        schema: Optional[dict] = None
    ) -> dict:
        """
        Validate JSON configuration file.

        Args:
            file_path: Path to JSON file
            schema: Optional JSON schema for validation

        Returns:
            Parsed JSON data

        Raises:
            InvalidConfigError: If file invalid or doesn't match schema
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise InvalidConfigError(f"Config file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise InvalidConfigError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise InvalidConfigError(f"Failed to load {file_path}: {e}")

        # Validate against schema if provided
        if schema is not None:
            if HAS_JSONSCHEMA:
                try:
                    jsonschema.validate(data, schema)
                except jsonschema.ValidationError as e:
                    raise InvalidConfigError(
                        f"JSON schema validation failed for {file_path}: {e.message}"
                    )
            else:
                # jsonschema not available, skip schema validation
                logger.warning(
                    f"jsonschema library not available, skipping schema validation for {file_path}"
                )

        return data
```

**Dependencies**:
- pathlib (standard library)
- re (standard library)
- urllib.parse (standard library)
- json (standard library)
- shutil (standard library)
- os (standard library)
- unidecode (optional, with fallback)
- jsonschema (optional, with fallback)
- exceptions.py

**Testing**:
- Test all validators with valid inputs
- Test all validators with invalid inputs
- Test path traversal prevention
- Test SQL keyword prevention
- Test unicode normalization (with and without unidecode)
- Test JSON schema validation (with and without jsonschema)
- Test performance (< 1ms per validation)

---

## Updated Testing Requirements

### Performance Benchmarks (MANDATORY)

All components must meet performance targets:

| Component | Maximum Overhead | Test Method |
|-----------|------------------|-------------|
| Logging | < 1% | 10,000 log writes |
| Transaction wrapper | < 1% | 1,000 DB operations |
| Checkpoint updates | < 2% | 1,000 updates |
| Validation | < 1ms per call | All validators |
| Progress tracking | < 0.5% | 10,000 updates |
| Failure logging | < 2ms per log | 1,000 failures |

### Test Coverage Requirements

- Unit tests: 100% line coverage for all modules
- Integration tests: All module interactions tested
- Error path tests: All exception types raised and caught
- Edge case tests: Boundary conditions, empty inputs, max values
- Performance tests: All benchmarks passing

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create scripts/common/ directory structure
- [ ] Implement exceptions.py
- [ ] Write unit tests for exceptions.py
- [ ] Implement logging_config.py
- [ ] Write unit tests for logging_config.py
- [ ] Test log rotation
- [ ] Implement database.py
- [ ] Write unit tests for database.py
- [ ] Test transaction rollback
- [ ] Test savepoints
- [ ] Integration test: logging + database + exceptions

### Phase 2: Validation & Verification (Week 2)
- [ ] Implement validation.py (refactored with classes)
- [ ] Write unit tests for all validators
- [ ] Test path traversal prevention
- [ ] Test SQL injection prevention
- [ ] Performance test all validators (< 1ms)
- [ ] Implement verification.py
- [ ] Write unit tests for verification functions
- [ ] Test backup verification
- [ ] Test SHA256 verification
- [ ] Integration test: validation + verification + exceptions

### Phase 3: Resilience Features (Week 3)
- [ ] Implement checkpoints.py with backup
- [ ] Write unit tests for checkpoint manager
- [ ] Test checkpoint resume
- [ ] Test checkpoint corruption recovery
- [ ] Performance test checkpoint updates (< 2% overhead)
- [ ] Implement failure_log.py
- [ ] Write unit tests for failure logger
- [ ] Test JSON Lines format
- [ ] Implement rollback.py
- [ ] Write unit tests for rollback manager
- [ ] Test rollback on exception
- [ ] Integration test: checkpoints + failure_log + rollback

### Phase 4: User Experience (Week 4)
- [ ] Implement progress.py
- [ ] Write unit tests for progress tracker
- [ ] Test rate and ETA calculations
- [ ] Performance test progress updates (< 0.5% overhead)
- [ ] Implement retry.py
- [ ] Write unit tests for retry decorator
- [ ] Test exponential backoff
- [ ] Implement preflight.py with log disk space check
- [ ] Write unit tests for pre-flight checks
- [ ] Test disk space estimation
- [ ] Integration test: progress + retry + preflight

### Phase 5: Integration & Performance (Week 5)
- [ ] Run all unit tests (100% coverage)
- [ ] Run all integration tests
- [ ] Run all performance tests (all benchmarks passing)
- [ ] Test complete workflow simulation
- [ ] Test failure scenarios
- [ ] Test resume after interruption
- [ ] Document all modules (docstrings complete)
- [ ] Review against BPA/BPL/KISS/FAANG PE
- [ ] Final audit and approval

---

## Success Criteria

Implementation is complete when:

1. ✅ All 12 modules implemented (P0-1 through P1-12)
2. ✅ 100% unit test coverage
3. ✅ All integration tests passing
4. ✅ All performance benchmarks met
5. ✅ All modules documented with design rationale
6. ✅ Audit against core principles (BPA/BPL/KISS/FAANG PE) = PASS
7. ✅ No fatal flaws identified (WWYDD review)
8. ✅ All dependencies documented
9. ✅ Example usage for each module
10. ✅ Can build first script (db_migrate.py) using foundations

---

## Next Steps After Completion

1. Update script specifications to use foundational components
2. Create template for new scripts (imports, structure, error handling)
3. Implement db_migrate.py as proof-of-concept
4. Validate foundations work in real usage
5. Iterate and improve based on findings
6. Document common patterns discovered
7. Proceed with remaining 12 scripts
