# Implementation Plan: P0 and P1 Foundational Components

## Objective

Create bulletproof foundational infrastructure for logging, error handling, transaction safety, resume capability, and validation that ALL 13 AUPAT scripts will depend on.

---

## Success Criteria

1. All P0 and P1 components implemented and tested
2. Zero scripts can run without using these foundational components
3. All components follow BPA, BPL, KISS, FAANG PE principles
4. Comprehensive error handling with graceful failure modes
5. Full resume capability for long-running operations
6. Production-grade logging with rotation and structured output
7. All database operations wrapped in transaction safety
8. All inputs validated before processing

---

## Folder Structure Changes

### New Folders to Create
```
aupat/
├── scripts/                    # (to be created)
│   ├── common/                # Shared foundational modules
│   │   ├── __init__.py
│   │   ├── logging_config.py  # P0-1: Comprehensive logging framework
│   │   ├── database.py        # P0-2: Transaction safety wrapper
│   │   ├── exceptions.py      # P0-3: Custom exception types
│   │   ├── validation.py      # P0-4: Input validation utilities
│   │   ├── verification.py    # P0-5, P0-6: Backup & operation verification
│   │   ├── checkpoints.py     # P1-7: Resume/checkpoint system
│   │   ├── failure_log.py     # P1-8: Structured failure logging
│   │   ├── rollback.py        # P1-9: Filesystem rollback utilities
│   │   ├── progress.py        # P1-10: Progress tracking
│   │   ├── retry.py           # P1-11: Retry logic with backoff
│   │   └── preflight.py       # P1-12: Pre-flight checks
│   └── (13 main scripts will go here)
├── logs/                       # (to be created, gitignored)
│   ├── main.log               # General application logs
│   ├── error.log              # Error-level logs only
│   ├── failure.log            # Structured failure records (JSON lines)
│   ├── transaction.log        # Database transaction audit trail
│   └── archive/               # Rotated log files
└── data/
    ├── checkpoint_state.db    # SQLite database for resume state
    └── (existing JSON files)
```

---

## File-by-File Implementation Plan

### P0-1: Comprehensive Logging Framework
**File**: `scripts/common/logging_config.py`

**Purpose**:
- Centralized logging configuration for all scripts
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log rotation to prevent disk bloat
- Structured logging with consistent format
- Context injection (script name, function, line number)

**Implementation**:
```python
# Features to implement:
1. Configure Python logging module with custom formatters
2. Multiple handlers:
   - FileHandler for main.log (INFO+)
   - FileHandler for error.log (ERROR+)
   - RotatingFileHandler (max 10MB per file, keep 10 backups)
   - Optional StreamHandler for console output
3. Custom formatter with timestamp, level, script, function, line, message
4. Context manager for adding operation context to logs
5. Utility functions: get_logger(script_name), log_function_entry/exit
6. Integration with failure_log for ERROR+ events
```

**Format**:
```
2025-11-15 14:23:45,123 | INFO | db_import.py:142:import_location | Starting location import: loc_name='Factory XYZ'
2025-11-15 14:23:45,456 | DEBUG | db_import.py:156:_generate_uuid | Generated UUID: abc12345-6789-...
2025-11-15 14:23:46,789 | ERROR | db_import.py:201:_copy_files | Failed to copy file: /path/to/image.jpg - PermissionError: [Errno 13]
```

**Dependencies**:
- Python logging, logging.handlers modules
- pathlib for log directory creation

**Testing**:
- Test log rotation after 10MB
- Test multi-level filtering (DEBUG to main.log, ERROR to error.log)
- Test context injection
- Test concurrent logging from multiple scripts

---

### P0-2: Transaction Safety Wrapper
**File**: `scripts/common/database.py`

**Purpose**:
- Wrap all database operations in BEGIN/COMMIT/ROLLBACK
- Enforce PRAGMA foreign_keys = ON
- Automatic rollback on exception
- Transaction logging for audit trail
- Connection pooling if needed

**Implementation**:
```python
# Core components:
1. Database connection manager with context manager
   - __enter__: connect, enable foreign keys, begin transaction
   - __exit__: commit on success, rollback on exception

2. Transaction decorator for functions
   @transactional
   def my_database_operation(conn, ...):
       # operations here
       # auto-commit on return, auto-rollback on exception

3. Nested transaction support (savepoints)
   with transaction(conn) as tx:
       # operation 1
       with tx.savepoint():
           # operation 2 (can rollback independently)

4. Transaction logging
   - Log BEGIN with timestamp, script, operation name
   - Log COMMIT with timestamp, rows affected, duration
   - Log ROLLBACK with timestamp, exception type, full traceback

5. Connection configuration
   - PRAGMA foreign_keys = ON
   - PRAGMA journal_mode = WAL (write-ahead logging)
   - PRAGMA synchronous = NORMAL (balance safety/performance)
   - Set busy_timeout for handling locks

6. Verification utilities
   - verify_foreign_keys_enabled()
   - verify_transaction_active()
   - get_transaction_state()
```

**Example Usage**:
```python
from common.database import DatabaseConnection, transactional

# Method 1: Context manager
with DatabaseConnection('/path/to/db.sqlite') as conn:
    conn.execute("INSERT INTO locations ...")
    # auto-commit on exit, auto-rollback on exception

# Method 2: Decorator
@transactional
def import_location(conn, loc_data):
    conn.execute("INSERT INTO locations ...")
    conn.execute("INSERT INTO images ...")
    # auto-commit on return
```

**Dependencies**:
- sqlite3 module
- logging_config.py for transaction logging
- exceptions.py for custom database exceptions

**Testing**:
- Test auto-commit on success
- Test auto-rollback on exception
- Test foreign key enforcement
- Test nested transactions (savepoints)
- Test database locked scenario (busy_timeout)
- Test transaction log entries created

---

### P0-3: Custom Exception Types
**File**: `scripts/common/exceptions.py`

**Purpose**:
- Define specific exception types for AUPAT operations
- Enable precise error handling (catch specific exceptions)
- Include context in exceptions (file paths, UUIDs, etc.)
- Distinguish recoverable vs. fatal errors

**Implementation**:
```python
# Exception hierarchy:

class AupatError(Exception):
    """Base exception for all AUPAT errors"""
    def __init__(self, message, recoverable=False, context=None):
        self.message = message
        self.recoverable = recoverable
        self.context = context or {}
        super().__init__(message)

# Database exceptions
class DatabaseError(AupatError):
    """Base for database errors"""
    pass

class TransactionError(DatabaseError):
    """Transaction commit/rollback failed"""
    pass

class ForeignKeyError(DatabaseError):
    """Foreign key constraint violation"""
    pass

class UniqueConstraintError(DatabaseError):
    """Unique constraint violation (e.g., UUID collision)"""
    pass

# Filesystem exceptions
class FilesystemError(AupatError):
    """Base for filesystem errors"""
    pass

class InsufficientSpaceError(FilesystemError):
    """Not enough disk space"""
    pass

class PermissionError(FilesystemError):
    """Insufficient filesystem permissions"""
    pass

class ChecksumMismatchError(FilesystemError):
    """SHA256 verification failed"""
    def __init__(self, file_path, expected_sha, actual_sha):
        super().__init__(
            f"SHA256 mismatch for {file_path}",
            recoverable=False,
            context={'file_path': file_path, 'expected': expected_sha, 'actual': actual_sha}
        )

# Validation exceptions
class ValidationError(AupatError):
    """Input validation failed"""
    pass

class InvalidUUIDError(ValidationError):
    """UUID format invalid"""
    pass

class InvalidPathError(ValidationError):
    """File path invalid or doesn't exist"""
    pass

class InvalidConfigError(ValidationError):
    """Configuration file invalid"""
    pass

# External tool exceptions
class ExternalToolError(AupatError):
    """External tool execution failed"""
    pass

class ExiftoolError(ExternalToolError):
    """exiftool execution failed"""
    pass

class FfprobeError(ExternalToolError):
    """ffprobe execution failed"""
    pass

# Resume/checkpoint exceptions
class CheckpointError(AupatError):
    """Checkpoint state corruption or load failure"""
    pass

# Backup exceptions
class BackupError(AupatError):
    """Backup creation or verification failed"""
    pass
```

**Dependencies**: None

**Testing**:
- Test exception instantiation with context
- Test recoverable flag
- Test exception inheritance
- Test exception message formatting

---

### P0-4: Input Validation Utilities
**File**: `scripts/common/validation.py`

**Purpose**:
- Validate all user inputs before processing
- Sanitize inputs for SQL injection, path traversal
- Type checking and format verification
- Fail early with clear error messages

**Implementation**:
```python
# Validation functions:

1. validate_uuid(uuid_str: str) -> bool:
   - Check format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
   - Verify version 4 UUID
   - Raise InvalidUUIDError if invalid

2. validate_sha256(sha_str: str) -> bool:
   - Check length: 64 hex characters
   - Verify hex characters only
   - Raise ValueError if invalid

3. validate_file_path(path: str, must_exist: bool = True) -> Path:
   - Convert to absolute path
   - Check for path traversal attempts (../, symlinks)
   - Verify existence if must_exist=True
   - Verify readable permissions
   - Raise InvalidPathError if invalid

4. validate_directory_path(path: str, must_exist: bool = True, must_be_writable: bool = False) -> Path:
   - Same as validate_file_path
   - Verify it's a directory, not a file
   - Check writable if must_be_writable=True
   - Raise InvalidPathError if invalid

5. validate_location_name(name: str) -> str:
   - Strip whitespace
   - Check length (1-255 characters)
   - Check for valid characters (letters, numbers, hyphens, underscores, spaces)
   - Normalize unicode (unidecode)
   - Raise ValidationError if invalid

6. validate_state_code(state: str) -> str:
   - Check length: 2 characters
   - Convert to uppercase
   - Verify against valid US state codes
   - Raise ValidationError if invalid

7. validate_extension(ext: str) -> str:
   - Strip leading dot if present
   - Convert to lowercase
   - Check alphanumeric only
   - Raise ValidationError if invalid

8. validate_url(url: str) -> str:
   - Parse URL with urllib.parse
   - Verify scheme (http/https)
   - Verify domain exists
   - Raise ValidationError if invalid

9. validate_json_file(file_path: Path, schema: dict = None) -> dict:
   - Load JSON file
   - Validate against schema if provided (jsonschema library)
   - Raise InvalidConfigError if invalid

10. sanitize_sql_identifier(identifier: str) -> str:
    - Verify alphanumeric + underscore only
    - Prevent SQL injection in table/column names
    - Raise ValidationError if invalid

11. validate_disk_space(path: Path, required_bytes: int) -> bool:
    - Check available space on filesystem
    - Raise InsufficientSpaceError if not enough space
```

**Dependencies**:
- pathlib
- re (regex)
- urllib.parse
- shutil (for disk space check)
- unidecode
- jsonschema (optional, for JSON schema validation)
- exceptions.py

**Testing**:
- Test each validator with valid inputs
- Test each validator with invalid inputs
- Test path traversal prevention
- Test SQL injection prevention
- Test unicode normalization
- Test disk space calculation

---

### P0-5: Backup Verification
**File**: `scripts/common/verification.py` (Part 1)

**Purpose**:
- Verify backups succeeded before destructive operations
- Verify backup integrity (file exists, readable, size > 0)
- Verify backup contains expected data

**Implementation**:
```python
# Backup verification functions:

1. verify_backup_exists(backup_path: Path) -> bool:
   - Check file exists
   - Check file size > 0
   - Check file readable
   - Raise BackupError if invalid

2. verify_backup_integrity(backup_path: Path, original_db_path: Path) -> bool:
   - Open backup SQLite database
   - Verify database opens without corruption
   - Compare table count to original
   - Compare row counts to original (approximate)
   - Verify PRAGMA integrity_check passes
   - Raise BackupError if checks fail

3. verify_backup_recent(backup_path: Path, max_age_seconds: int = 300) -> bool:
   - Check file modification time
   - Verify backup is less than max_age_seconds old
   - Raise BackupError if too old (stale backup)

4. create_and_verify_backup(db_path: Path, backup_dir: Path) -> Path:
   - Call backup.py to create backup
   - Verify backup creation succeeded
   - Verify backup integrity
   - Return backup path
   - Raise BackupError if any step fails
```

---

### P0-6: Post-Operation Verification
**File**: `scripts/common/verification.py` (Part 2)

**Purpose**:
- Verify database operations succeeded
- Verify filesystem operations succeeded
- Verify expected state matches actual state

**Implementation**:
```python
# Post-operation verification functions:

1. verify_database_insert(conn, table: str, expected_count: int, filter_clause: str = None) -> bool:
   - Query database for inserted rows
   - Compare count to expected
   - Raise TransactionError if mismatch

2. verify_database_update(conn, table: str, expected_count: int, filter_clause: str = None) -> bool:
   - Query database for updated rows
   - Compare count to expected
   - Raise TransactionError if mismatch

3. verify_file_copied(source: Path, destination: Path) -> bool:
   - Check destination exists
   - Compare file sizes
   - Compare SHA256 hashes
   - Raise FilesystemError if mismatch

4. verify_file_moved(source: Path, destination: Path) -> bool:
   - Check source no longer exists
   - Check destination exists
   - Raise FilesystemError if verification fails

5. verify_directory_created(path: Path) -> bool:
   - Check directory exists
   - Check directory is writable
   - Raise FilesystemError if failed

6. verify_sha256(file_path: Path, expected_sha: str) -> bool:
   - Calculate SHA256 of file
   - Compare to expected
   - Raise ChecksumMismatchError if mismatch

7. verify_foreign_keys_satisfied(conn) -> bool:
   - Run PRAGMA foreign_key_check
   - Raise ForeignKeyError if violations found

8. verify_database_constraints(conn, table: str) -> bool:
   - Check for NULL values in NOT NULL columns
   - Check for constraint violations
   - Raise DatabaseError if violations found
```

**Dependencies**:
- sqlite3
- pathlib
- hashlib (for SHA256)
- exceptions.py
- logging_config.py

**Testing**:
- Test backup verification with valid backup
- Test backup verification with corrupted backup
- Test backup verification with missing backup
- Test post-operation verification with successful operations
- Test post-operation verification with failed operations
- Test SHA256 verification with matching/mismatching files

---

### P1-7: Resume/Checkpoint System
**File**: `scripts/common/checkpoints.py`

**Purpose**:
- Track progress of long-running operations
- Enable resume from last successful checkpoint
- Store checkpoint state in separate database
- Clear checkpoints on successful completion

**Implementation**:
```python
# Checkpoint database schema:
CREATE TABLE checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    script_name TEXT NOT NULL,
    operation_name TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'pending', 'in_progress', 'completed', 'failed'
    progress_data TEXT,    -- JSON: {current: 100, total: 1000, last_item: 'abc123'}
    started_at TEXT,
    updated_at TEXT,
    completed_at TEXT,
    error_message TEXT
);

CREATE INDEX idx_checkpoints_script_op ON checkpoints(script_name, operation_name);

# Checkpoint manager class:

class CheckpointManager:
    def __init__(self, checkpoint_db_path: Path):
        # Initialize connection to checkpoint database

    def create_checkpoint(self, script: str, operation: str, total_items: int) -> str:
        # Create new checkpoint, return checkpoint_id

    def load_checkpoint(self, script: str, operation: str) -> dict:
        # Load existing checkpoint or return None

    def update_progress(self, checkpoint_id: str, current: int, last_item: Any):
        # Update progress data

    def mark_completed(self, checkpoint_id: str):
        # Mark checkpoint as completed

    def mark_failed(self, checkpoint_id: str, error: str):
        # Mark checkpoint as failed

    def clear_checkpoint(self, checkpoint_id: str):
        # Delete checkpoint after successful completion

    def should_resume(self, script: str, operation: str) -> tuple[bool, dict]:
        # Check if resume needed, return (should_resume, progress_data)

# Context manager for checkpoint operations:

class CheckpointedOperation:
    def __init__(self, checkpoint_mgr, script, operation, total_items):
        self.checkpoint_mgr = checkpoint_mgr
        self.script = script
        self.operation = operation
        self.total_items = total_items
        self.checkpoint_id = None

    def __enter__(self):
        # Check if resume needed
        should_resume, progress = self.checkpoint_mgr.should_resume(self.script, self.operation)
        if should_resume:
            self.checkpoint_id = progress['checkpoint_id']
            return progress  # Return progress data for resume
        else:
            self.checkpoint_id = self.checkpoint_mgr.create_checkpoint(
                self.script, self.operation, self.total_items
            )
            return {'current': 0, 'total': self.total_items}

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.checkpoint_mgr.mark_completed(self.checkpoint_id)
            self.checkpoint_mgr.clear_checkpoint(self.checkpoint_id)
        else:
            self.checkpoint_mgr.mark_failed(self.checkpoint_id, str(exc_val))

    def update(self, current: int, last_item: Any):
        self.checkpoint_mgr.update_progress(self.checkpoint_id, current, last_item)
```

**Example Usage**:
```python
from common.checkpoints import CheckpointManager, CheckpointedOperation

checkpoint_mgr = CheckpointManager(Path('data/checkpoint_state.db'))

with CheckpointedOperation(checkpoint_mgr, 'db_organize', 'extract_metadata', total_items=1000) as progress:
    start_from = progress['current']  # 0 if new, or last checkpoint if resuming

    for i in range(start_from, progress['total']):
        # Process item i

        # Update checkpoint every 10 items
        if i % 10 == 0:
            progress.update(current=i, last_item=item_id)
```

**Dependencies**:
- sqlite3
- pathlib
- json
- datetime
- logging_config.py
- database.py (for transaction safety)

**Testing**:
- Test checkpoint creation
- Test checkpoint resume
- Test checkpoint clear on success
- Test checkpoint persist on failure
- Test concurrent checkpoint operations

---

### P1-8: Structured Failure Logging
**File**: `scripts/common/failure_log.py`

**Purpose**:
- Log failures in structured JSON format
- Separate failure log from general logs
- Include full context for debugging
- Categorize failures (recoverable vs fatal)
- Enable failure analysis and reporting

**Implementation**:
```python
# Failure log schema (JSON lines format):
{
    "timestamp": "2025-11-15T14:23:45.123456",
    "script": "db_organize.py",
    "function": "extract_metadata",
    "operation": "exiftool_extraction",
    "severity": "ERROR",  # WARNING, ERROR, CRITICAL
    "recoverable": true,
    "error_type": "ExiftoolError",
    "error_message": "exiftool returned exit code 1",
    "traceback": "Traceback (most recent call last)...",
    "context": {
        "file_path": "/path/to/image.jpg",
        "img_uuid": "abc12345-...",
        "loc_uuid": "def67890-..."
    },
    "recovery_action": "Skip file and continue",
    "user_action_required": false
}

# Failure logger class:

class FailureLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path

    def log_failure(
        self,
        script: str,
        function: str,
        operation: str,
        error: Exception,
        context: dict = None,
        recoverable: bool = False,
        recovery_action: str = None,
        user_action_required: bool = False
    ):
        # Create structured failure record
        # Write as JSON line to failure.log
        # Also log to main error log

    def get_failures(
        self,
        script: str = None,
        severity: str = None,
        recoverable: bool = None,
        since: datetime = None
    ) -> list[dict]:
        # Query failures from log file
        # Return filtered list of failure records

    def clear_failures(self, before: datetime):
        # Archive old failures
        # Keep recent failures only

# Context manager for failure handling:

class FailureContext:
    def __init__(
        self,
        failure_logger: FailureLogger,
        script: str,
        function: str,
        operation: str,
        context: dict = None,
        recoverable: bool = False
    ):
        self.failure_logger = failure_logger
        self.script = script
        self.function = function
        self.operation = operation
        self.context = context or {}
        self.recoverable = recoverable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failure_logger.log_failure(
                script=self.script,
                function=self.function,
                operation=self.operation,
                error=exc_val,
                context=self.context,
                recoverable=self.recoverable
            )

            if not self.recoverable:
                # Re-raise fatal errors
                return False
            else:
                # Suppress recoverable errors (logged but don't crash)
                return True
```

**Example Usage**:
```python
from common.failure_log import FailureLogger, FailureContext

failure_logger = FailureLogger(Path('logs/failure.log'))

with FailureContext(
    failure_logger,
    script='db_organize',
    function='extract_metadata',
    operation='exiftool_extraction',
    context={'file_path': str(file_path), 'img_uuid': img_uuid},
    recoverable=True
):
    # Call exiftool - if it fails, log to failure log and continue
    run_exiftool(file_path)
```

**Dependencies**:
- json
- datetime
- pathlib
- traceback
- logging_config.py

**Testing**:
- Test failure logging with recoverable errors
- Test failure logging with fatal errors
- Test failure log file format (valid JSON lines)
- Test failure querying and filtering
- Test failure log rotation

---

### P1-9: Filesystem Rollback Utilities
**File**: `scripts/common/rollback.py`

**Purpose**:
- Track filesystem operations for potential rollback
- Undo file copy/move operations on failure
- Clean up partial directory structures
- Maintain manifest of operations for cleanup

**Implementation**:
```python
# Rollback manager class:

class FilesystemRollback:
    def __init__(self):
        self.operations = []  # List of operations to rollback

    def track_copy(self, source: Path, destination: Path):
        # Track file copy - rollback = delete destination
        self.operations.append({
            'type': 'copy',
            'source': source,
            'destination': destination,
            'rollback': lambda: destination.unlink(missing_ok=True)
        })

    def track_move(self, source: Path, destination: Path):
        # Track file move - rollback = move back to source
        self.operations.append({
            'type': 'move',
            'source': source,
            'destination': destination,
            'rollback': lambda: shutil.move(str(destination), str(source))
        })

    def track_mkdir(self, path: Path):
        # Track directory creation - rollback = remove if empty
        self.operations.append({
            'type': 'mkdir',
            'path': path,
            'rollback': lambda: path.rmdir() if path.exists() and not any(path.iterdir()) else None
        })

    def track_delete(self, path: Path, backup_path: Path = None):
        # Track file deletion - rollback = restore from backup if exists
        if backup_path:
            self.operations.append({
                'type': 'delete',
                'path': path,
                'backup': backup_path,
                'rollback': lambda: shutil.copy2(str(backup_path), str(path))
            })

    def rollback(self):
        # Execute rollback operations in reverse order
        for op in reversed(self.operations):
            try:
                op['rollback']()
                logger.info(f"Rolled back {op['type']}: {op.get('destination') or op.get('path')}")
            except Exception as e:
                logger.error(f"Failed to rollback {op['type']}: {e}")

        self.operations.clear()

    def commit(self):
        # Clear operations (commit successful)
        self.operations.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred - rollback
            self.rollback()
        else:
            # Success - commit
            self.commit()
```

**Example Usage**:
```python
from common.rollback import FilesystemRollback

with FilesystemRollback() as rollback:
    # Copy file
    shutil.copy2(source, destination)
    rollback.track_copy(source, destination)

    # Create directory
    new_dir.mkdir(parents=True)
    rollback.track_mkdir(new_dir)

    # Move file
    shutil.move(temp_file, final_location)
    rollback.track_move(temp_file, final_location)

    # If any operation fails, all tracked operations are rolled back
```

**Dependencies**:
- pathlib
- shutil
- logging_config.py

**Testing**:
- Test rollback of copy operation
- Test rollback of move operation
- Test rollback of mkdir operation
- Test commit (no rollback on success)
- Test partial rollback on multi-operation failure

---

### P1-10: Progress Tracking
**File**: `scripts/common/progress.py`

**Purpose**:
- Display real-time progress for long operations
- Show files processed, time elapsed, ETA
- Update console output without excessive logging
- Integrate with checkpoint system

**Implementation**:
```python
# Progress tracker class:

class ProgressTracker:
    def __init__(
        self,
        total: int,
        operation_name: str,
        update_interval: int = 10  # Update every N items
    ):
        self.total = total
        self.current = 0
        self.operation_name = operation_name
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update = 0

    def update(self, increment: int = 1, item_name: str = None):
        self.current += increment

        # Update every N items or on completion
        if self.current - self.last_update >= self.update_interval or self.current == self.total:
            self._print_progress(item_name)
            self.last_update = self.current

    def _print_progress(self, item_name: str = None):
        elapsed = time.time() - self.start_time
        percent = (self.current / self.total) * 100
        rate = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / rate if rate > 0 else 0

        progress_msg = (
            f"{self.operation_name}: {self.current}/{self.total} ({percent:.1f}%) | "
            f"Rate: {rate:.1f} items/sec | "
            f"Elapsed: {self._format_time(elapsed)} | "
            f"ETA: {self._format_time(eta)}"
        )

        if item_name:
            progress_msg += f" | Current: {item_name}"

        logger.info(progress_msg)

    def _format_time(self, seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"

    def complete(self):
        self.current = self.total
        self._print_progress()
        logger.info(f"{self.operation_name} completed in {self._format_time(time.time() - self.start_time)}")
```

**Example Usage**:
```python
from common.progress import ProgressTracker

progress = ProgressTracker(total=1000, operation_name="Extracting metadata")

for i, file in enumerate(files):
    # Process file
    extract_metadata(file)

    # Update progress
    progress.update(increment=1, item_name=file.name)

progress.complete()
```

**Dependencies**:
- time
- logging_config.py

**Testing**:
- Test progress updates at intervals
- Test ETA calculation
- Test rate calculation
- Test time formatting
- Test completion

---

### P1-11: Retry Logic with Backoff
**File**: `scripts/common/retry.py`

**Purpose**:
- Retry transient failures (database locks, network timeouts)
- Exponential backoff to avoid overwhelming resources
- Maximum retry limits
- Logging of retry attempts

**Implementation**:
```python
# Retry decorator:

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger=None
):
    """
    Decorator to retry function on exception with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiply delay by this factor after each retry
        exceptions: Tuple of exception types to catch and retry
        logger: Logger instance for logging retry attempts
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        # Max retries reached - re-raise
                        if logger:
                            logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    # Log retry attempt
                    if logger:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                    # Wait before retry
                    time.sleep(delay)

                    # Exponential backoff
                    delay *= backoff_factor

        return wrapper
    return decorator

# Retry context manager:

class RetryContext:
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.attempt = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, self.exceptions):
            if self.attempt < self.max_retries:
                delay = self.initial_delay * (self.backoff_factor ** self.attempt)
                logger.warning(f"Retry attempt {self.attempt + 1}/{self.max_retries} after {delay:.1f}s")
                time.sleep(delay)
                self.attempt += 1
                return True  # Suppress exception, will retry
            else:
                logger.error(f"Max retries ({self.max_retries}) reached")
                return False  # Re-raise exception
```

**Example Usage**:
```python
from common.retry import retry_with_backoff

# Decorator usage:
@retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    exceptions=(sqlite3.OperationalError,),
    logger=logger
)
def database_operation():
    # May fail with database locked error
    conn.execute("INSERT INTO ...")

# Context manager usage:
for attempt in range(max_retries):
    try:
        # Operation that might fail
        break
    except TransientError as e:
        if attempt < max_retries - 1:
            delay = 2 ** attempt
            time.sleep(delay)
        else:
            raise
```

**Dependencies**:
- time
- functools
- logging_config.py

**Testing**:
- Test retry on transient failure
- Test max retries reached
- Test exponential backoff timing
- Test different exception types
- Test success on first attempt (no retry)
- Test success on second attempt (one retry)

---

### P1-12: Pre-Flight Checks
**File**: `scripts/common/preflight.py`

**Purpose**:
- Verify prerequisites before running operations
- Check disk space, permissions, dependencies
- Fail early with clear error messages
- Prevent partial failures due to missing prerequisites

**Implementation**:
```python
# Pre-flight check functions:

1. check_disk_space(path: Path, required_bytes: int) -> bool:
   - Get available space on filesystem
   - Compare to required bytes
   - Raise InsufficientSpaceError if not enough
   - Log available vs required

2. check_file_readable(path: Path) -> bool:
   - Verify file exists
   - Verify read permissions
   - Raise PermissionError if not readable

3. check_directory_writable(path: Path) -> bool:
   - Verify directory exists
   - Verify write permissions
   - Try creating test file
   - Raise PermissionError if not writable

4. check_external_tool(tool_name: str, min_version: str = None) -> bool:
   - Check tool exists in PATH (shutil.which)
   - Run tool --version to get version
   - Compare to min_version if specified
   - Raise ExternalToolError if missing or wrong version

5. check_database_connection(db_path: Path) -> bool:
   - Try connecting to database
   - Verify database not corrupted (PRAGMA integrity_check)
   - Verify database writable
   - Raise DatabaseError if issues found

6. check_config_files(config_paths: list[Path]) -> bool:
   - Verify all config files exist
   - Verify valid JSON
   - Raise InvalidConfigError if missing or invalid

7. estimate_required_space(files: list[Path], operation: str = 'copy') -> int:
   - Calculate total size of files
   - Multiply by factor based on operation:
     - 'copy': 1x (need space for copies)
     - 'move': 0x (no extra space needed)
     - 'organize': 1.5x (temporary space for reorganization)
   - Return required bytes

# Pre-flight check manager:

class PreflightChecker:
    def __init__(self, script_name: str):
        self.script_name = script_name
        self.checks_passed = []
        self.checks_failed = []

    def add_check(self, check_name: str, check_func: callable):
        try:
            check_func()
            self.checks_passed.append(check_name)
            logger.info(f"Pre-flight check passed: {check_name}")
        except Exception as e:
            self.checks_failed.append((check_name, str(e)))
            logger.error(f"Pre-flight check FAILED: {check_name} - {e}")

    def verify_all(self, raise_on_failure: bool = True):
        if self.checks_failed:
            failure_msg = f"Pre-flight checks failed for {self.script_name}:\n"
            for check_name, error in self.checks_failed:
                failure_msg += f"  - {check_name}: {error}\n"

            if raise_on_failure:
                raise PreflightError(failure_msg)
            else:
                logger.warning(failure_msg)
                return False

        logger.info(f"All pre-flight checks passed for {self.script_name} ({len(self.checks_passed)} checks)")
        return True
```

**Example Usage**:
```python
from common.preflight import PreflightChecker, check_disk_space, check_external_tool

preflight = PreflightChecker('db_organize')

# Add checks
preflight.add_check(
    'disk_space',
    lambda: check_disk_space(archive_path, required_bytes=10_000_000_000)
)
preflight.add_check(
    'exiftool_available',
    lambda: check_external_tool('exiftool', min_version='12.0')
)
preflight.add_check(
    'ffprobe_available',
    lambda: check_external_tool('ffprobe')
)
preflight.add_check(
    'database_writable',
    lambda: check_directory_writable(db_path.parent)
)

# Verify all checks passed
preflight.verify_all(raise_on_failure=True)

# Proceed with operation...
```

**Dependencies**:
- pathlib
- shutil
- subprocess
- sqlite3
- exceptions.py
- validation.py
- logging_config.py

**Testing**:
- Test disk space check with sufficient/insufficient space
- Test file permissions checks
- Test external tool detection
- Test database connection check
- Test config file validation
- Test pre-flight failure raises exception

---

## Implementation Sequence

### Phase 1: Core Infrastructure (P0-1 to P0-3)
1. Create `scripts/common/` directory
2. Implement `exceptions.py` (no dependencies)
3. Implement `logging_config.py` (depends on exceptions)
4. Implement `database.py` (depends on logging, exceptions)
5. Test all three modules integration

### Phase 2: Validation & Verification (P0-4 to P0-6)
6. Implement `validation.py` (depends on exceptions)
7. Implement `verification.py` (depends on exceptions, logging, validation)
8. Test validation and verification utilities

### Phase 3: Resilience Features (P1-7 to P1-9)
9. Implement `checkpoints.py` (depends on database, logging)
10. Implement `failure_log.py` (depends on logging)
11. Implement `rollback.py` (depends on logging)
12. Test resume/checkpoint functionality
13. Test failure logging
14. Test filesystem rollback

### Phase 4: User Experience (P1-10 to P1-12)
15. Implement `progress.py` (depends on logging)
16. Implement `retry.py` (depends on logging)
17. Implement `preflight.py` (depends on validation, exceptions, logging)
18. Test progress tracking
19. Test retry logic
20. Test pre-flight checks

### Phase 5: Integration Testing
21. Create integration tests for all modules
22. Test module interactions
23. Test error propagation
24. Test transaction safety with rollback
25. Test resume after failure scenarios

---

## Testing Strategy

### Unit Tests
- Test each function in isolation
- Mock external dependencies
- Test both success and failure paths
- Test edge cases and boundary conditions

### Integration Tests
- Test module interactions
- Test database transactions with rollback
- Test checkpoint resume functionality
- Test failure logging integration
- Test progress tracking with checkpoints

### End-to-End Tests
- Simulate full script execution with failures
- Test resume after interruption
- Test rollback on failure
- Test audit trail completeness

### Performance Tests
- Test logging performance (no significant overhead)
- Test checkpoint update performance
- Test transaction overhead
- Test progress tracking overhead

---

## Dependencies

### Python Standard Library
- logging, logging.handlers
- sqlite3
- pathlib
- json
- time
- datetime
- functools
- traceback
- hashlib
- shutil
- subprocess
- re
- urllib.parse

### Third-Party Libraries (Optional)
- unidecode (unicode normalization)
- jsonschema (JSON validation)

---

## Risks & Mitigations

### Risk 1: Logging Overhead
**Risk**: Excessive logging slows down operations
**Mitigation**:
- Use appropriate log levels (DEBUG only when needed)
- Rotate logs aggressively
- Batch log writes
- Test performance impact

### Risk 2: Checkpoint Database Corruption
**Risk**: Checkpoint database becomes corrupted, preventing resume
**Mitigation**:
- Use WAL mode for checkpoint database
- Regular PRAGMA integrity_check
- Backup checkpoint database
- Fallback to restart if checkpoint corrupted

### Risk 3: Rollback Failures
**Risk**: Rollback operation fails, leaving partial state
**Mitigation**:
- Log all rollback operations
- Test rollback procedures thoroughly
- Don't delete source files until verification complete
- Manual recovery procedures documented

### Risk 4: Transaction Deadlocks
**Risk**: Multiple scripts accessing database simultaneously cause deadlocks
**Mitigation**:
- Use WAL mode (allows concurrent readers)
- Set busy_timeout appropriately
- Document that only one write operation should run at a time
- Retry logic for locked database

### Risk 5: Disk Space Exhaustion During Operation
**Risk**: Run out of disk space mid-operation
**Mitigation**:
- Pre-flight check for sufficient space
- Monitor space during operation
- Fail gracefully with rollback if space exhausted
- Resume after freeing space

---

## Success Verification

After implementation, verify:

1. All P0 and P1 modules implemented and tested
2. 100% test coverage for all functions
3. All modules follow BPA, BPL, KISS, FAANG PE principles
4. Logging produces readable, actionable output
5. Transaction safety prevents data corruption
6. Checkpoint resume works after interruption
7. Failure logging captures all necessary context
8. Rollback successfully undoes partial operations
9. Progress tracking provides useful feedback
10. Retry logic handles transient failures
11. Pre-flight checks prevent common failure modes
12. Documentation complete for all modules
13. No scripts can run without using these foundations

---

## Next Steps After P0/P1 Completion

1. Update all 13 script specifications to use foundational components
2. Implement first script (db_migrate.py) using foundations
3. Verify foundations work in real-world usage
4. Iterate and improve based on findings
5. Proceed with remaining scripts
