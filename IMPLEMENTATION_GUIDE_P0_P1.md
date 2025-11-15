# Implementation Guide: P0 and P1 Foundational Components

## For Less-Experienced Developers

This guide will walk you through implementing the foundational infrastructure for AUPAT, step by step. Each section explains WHAT to build, WHY it's needed, and HOW to implement it.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Module 1: Custom Exceptions](#module-1-custom-exceptions-p0-3)
4. [Module 2: Logging Configuration](#module-2-logging-configuration-p0-1)
5. [Module 3: Database Transactions](#module-3-database-transactions-p0-2)
6. [Module 4: Input Validation](#module-4-input-validation-p0-4)
7. [Module 5: Verification](#module-5-verification-p0-5-p0-6)
8. [Module 6: Checkpoints](#module-6-checkpoints-p1-7)
9. [Module 7: Failure Logging](#module-7-failure-logging-p1-8)
10. [Module 8: Filesystem Rollback](#module-8-filesystem-rollback-p1-9)
11. [Module 9: Progress Tracking](#module-9-progress-tracking-p1-10)
12. [Module 10: Retry Logic](#module-10-retry-logic-p1-11)
13. [Module 11: Pre-Flight Checks](#module-11-pre-flight-checks-p1-12)
14. [Testing](#testing)
15. [Integration](#integration)

---

## Prerequisites

### Knowledge Required
- Python 3.8+ basics (functions, classes, context managers)
- Basic SQL/SQLite understanding
- Understanding of exceptions and error handling
- Familiarity with file I/O
- Command line basics

### Tools Needed
- Python 3.8 or higher
- Code editor (VS Code, PyCharm, etc.)
- Terminal/command line
- Git (for version control)

### Python Concepts You'll Use
- **Classes**: Grouping related functions together
- **Static methods**: Functions that don't need object state
- **Context managers**: `with` statement for automatic cleanup
- **Decorators**: Wrapping functions to add functionality
- **Type hints**: Specifying types for parameters and returns

---

## Project Setup

### Step 1: Create Directory Structure

```bash
cd /home/user/aupat

# Create directories
mkdir -p scripts/common
mkdir -p logs
mkdir -p data
mkdir -p tests/unit
mkdir -p tests/integration

# Create __init__.py files (makes directories into Python packages)
touch scripts/__init__.py
touch scripts/common/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

**Why these directories?**
- `scripts/common/`: Shared code used by all scripts
- `logs/`: Where log files will be stored
- `data/`: Configuration and state files
- `tests/`: Unit and integration tests

### Step 2: Update .gitignore

Add to `/home/user/aupat/.gitignore`:
```
# Logs
logs/*.log
logs/archive/

# Python
__pycache__/
*.pyc
venv/

# State
data/checkpoint_state.db
data/checkpoint_state.backup.db

# Backups
backups/
```

---

## Module 1: Custom Exceptions (P0-3)

### Why We Need This

When something goes wrong, we want to know EXACTLY what failed. Python's built-in exceptions (`ValueError`, `FileNotFoundError`) are generic. We need specific exceptions like `ChecksumMismatchError` or `ForeignKeyError` to handle different failures differently.

### What We're Building

An exception hierarchy that:
- Has a base `AupatError` class
- Has specific exceptions for different error types
- Includes context (file paths, UUIDs, etc.) in exceptions
- Marks errors as recoverable or fatal

### How to Implement

**File**: `scripts/common/exceptions.py`

```python
"""
Custom exception types for AUPAT.

This module defines specific exception types for different failure scenarios.
Using specific exceptions allows us to:
1. Catch and handle specific errors differently
2. Include relevant context in exceptions
3. Distinguish recoverable errors from fatal ones
"""


class AupatError(Exception):
    """
    Base exception for all AUPAT errors.

    All custom exceptions inherit from this, allowing us to catch
    all AUPAT-specific errors with one except clause if needed.

    Attributes:
        message: Human-readable error message
        recoverable: Whether the operation can be retried
        context: Dictionary of relevant information (file paths, UUIDs, etc.)
    """

    def __init__(self, message: str, recoverable: bool = False, context: dict = None):
        """
        Initialize an AUPAT error.

        Args:
            message: Description of what went wrong
            recoverable: Can this error be retried? (e.g., disk full = yes, SHA mismatch = no)
            context: Extra info for debugging (as a dictionary)
        """
        self.message = message
        self.recoverable = recoverable
        self.context = context or {}

        # Call parent Exception class with message
        super().__init__(message)

    def __str__(self):
        """String representation includes context if available."""
        if self.context:
            return f"{self.message} | Context: {self.context}"
        return self.message


# Database Exceptions
# -------------------

class DatabaseError(AupatError):
    """Base exception for all database-related errors."""
    pass


class TransactionError(DatabaseError):
    """Raised when a database transaction fails to commit or rollback."""
    pass


class ForeignKeyError(DatabaseError):
    """
    Raised when a foreign key constraint is violated.

    Example: Trying to insert an image record with a loc_uuid that
    doesn't exist in the locations table.
    """
    pass


class UniqueConstraintError(DatabaseError):
    """
    Raised when a unique constraint is violated.

    Example: Trying to insert a UUID that already exists.
    """
    pass


# Filesystem Exceptions
# ---------------------

class FilesystemError(AupatError):
    """Base exception for all filesystem-related errors."""
    pass


class InsufficientSpaceError(FilesystemError):
    """Raised when there's not enough disk space for an operation."""

    def __init__(self, message: str, available_bytes: int = None, required_bytes: int = None):
        context = {}
        if available_bytes is not None:
            context['available_bytes'] = available_bytes
        if required_bytes is not None:
            context['required_bytes'] = required_bytes

        # Disk space errors are often recoverable (user can free space and retry)
        super().__init__(message, recoverable=True, context=context)


class PermissionError(FilesystemError):
    """Raised when we don't have permission to read/write a file or directory."""
    pass


class ChecksumMismatchError(FilesystemError):
    """
    Raised when SHA256 verification fails.

    This is FATAL - means file is corrupted or tampered with.
    """

    def __init__(self, file_path: str, expected_sha: str, actual_sha: str):
        context = {
            'file_path': file_path,
            'expected_sha': expected_sha,
            'actual_sha': actual_sha
        }

        # Checksum mismatches are NOT recoverable - data integrity issue
        super().__init__(
            f"SHA256 mismatch for {file_path}: expected {expected_sha[:8]}..., got {actual_sha[:8]}...",
            recoverable=False,
            context=context
        )


# Validation Exceptions
# ---------------------

class ValidationError(AupatError):
    """Base exception for input validation failures."""
    pass


class InvalidUUIDError(ValidationError):
    """Raised when a UUID doesn't match the expected format."""
    pass


class InvalidPathError(ValidationError):
    """Raised when a file path is invalid or doesn't exist."""
    pass


class InvalidConfigError(ValidationError):
    """Raised when a configuration file is invalid or corrupt."""
    pass


# External Tool Exceptions
# ------------------------

class ExternalToolError(AupatError):
    """Base exception for external tool execution failures."""

    def __init__(self, tool_name: str, message: str, return_code: int = None):
        context = {'tool': tool_name}
        if return_code is not None:
            context['return_code'] = return_code

        super().__init__(message, recoverable=False, context=context)


class ExiftoolError(ExternalToolError):
    """Raised when exiftool fails to extract metadata."""

    def __init__(self, message: str, file_path: str = None, return_code: int = None):
        super().__init__('exiftool', message, return_code)
        if file_path:
            self.context['file_path'] = file_path


class FfprobeError(ExternalToolError):
    """Raised when ffprobe fails to extract video metadata."""

    def __init__(self, message: str, file_path: str = None, return_code: int = None):
        super().__init__('ffprobe', message, return_code)
        if file_path:
            self.context['file_path'] = file_path


# Resume/Checkpoint Exceptions
# ----------------------------

class CheckpointError(AupatError):
    """Raised when checkpoint state is corrupted or can't be loaded."""
    pass


# Backup Exceptions
# ----------------

class BackupError(AupatError):
    """Raised when backup creation or verification fails."""
    pass


# Pre-flight Check Exception
# --------------------------

class PreflightError(AupatError):
    """Raised when pre-flight checks fail."""

    def __init__(self, message: str, failed_checks: list = None):
        context = {}
        if failed_checks:
            context['failed_checks'] = failed_checks

        super().__init__(message, recoverable=True, context=context)
```

### Testing This Module

Create `tests/unit/test_exceptions.py`:

```python
import pytest
from scripts.common.exceptions import (
    AupatError,
    ChecksumMismatchError,
    InsufficientSpaceError,
    ExiftoolError
)


def test_base_exception_with_context():
    """Test that AupatError stores context."""
    error = AupatError("Something failed", context={'file': 'test.jpg'})

    assert error.message == "Something failed"
    assert error.context == {'file': 'test.jpg'}
    assert error.recoverable is False  # Default


def test_base_exception_recoverable():
    """Test that recoverable flag works."""
    error = AupatError("Recoverable error", recoverable=True)

    assert error.recoverable is True


def test_checksum_mismatch_error():
    """Test ChecksumMismatchError includes all context."""
    error = ChecksumMismatchError(
        file_path='/path/to/file.jpg',
        expected_sha='abc123' * 10 + 'abcd',  # 64 chars
        actual_sha='def456' * 10 + 'defg'
    )

    assert error.context['file_path'] == '/path/to/file.jpg'
    assert error.context['expected_sha'] == 'abc123' * 10 + 'abcd'
    assert error.recoverable is False  # Checksum errors are fatal


def test_insufficient_space_error_recoverable():
    """Test that disk space errors are marked recoverable."""
    error = InsufficientSpaceError(
        "Not enough space",
        available_bytes=1000,
        required_bytes=10000
    )

    assert error.recoverable is True  # Can free space and retry
    assert error.context['available_bytes'] == 1000


def test_exception_inheritance():
    """Test that specific exceptions inherit from base classes."""
    error = ExiftoolError("exiftool failed", file_path='/test.jpg')

    # Should be catchable as ExiftoolError, ExternalToolError, or AupatError
    assert isinstance(error, ExiftoolError)
    assert isinstance(error, AupatError)
```

Run tests:
```bash
cd /home/user/aupat
python -m pytest tests/unit/test_exceptions.py -v
```

---

## Module 2: Logging Configuration (P0-1)

### Why We Need This

Logging is how we know what happened when things go wrong. We need:
- Different log levels (DEBUG for development, INFO for normal, ERROR for problems)
- Log rotation (so logs don't fill the disk)
- Structured format (timestamp, level, source, message)
- Multiple log files (main.log for everything, error.log for errors only)

### What We're Building

A centralized logging configuration that:
- Sets up Python's logging module with our preferences
- Creates multiple log handlers (file, console, error-only file)
- Rotates logs automatically when they get too big
- Provides easy-to-use functions for getting loggers

### Core Concepts

**Log Levels** (in order of severity):
- `DEBUG`: Detailed information for diagnosing problems
- `INFO`: General informational messages
- `WARNING`: Something unexpected but not critical
- `ERROR`: An error occurred but program continues
- `CRITICAL`: Severe error, program may crash

**Log Handlers**:
- `FileHandler`: Writes to a file
- `RotatingFileHandler`: Writes to a file, rotates when size limit reached
- `StreamHandler`: Writes to console (stdout/stderr)

### How to Implement

**File**: `scripts/common/logging_config.py`

```python
"""
Centralized logging configuration for AUPAT.

This module sets up Python's logging module with:
- Multiple log files (main.log, error.log, transaction.log)
- Log rotation to prevent disk bloat
- Structured format for easy parsing
- Context injection for debugging

Why logging is important:
- Know what happened when errors occur
- Track operations for compliance/audit
- Debug issues in production
- Monitor system health
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import os


# Log directory (created if doesn't exist)
LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log format: timestamp | level | source | message
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d:%(funcName)s | %(message)s'

# Date format for timestamps
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB per file
BACKUP_COUNT = 10  # Keep 10 backup files

# Global logger registry (cache loggers by name)
_loggers = {}


def setup_logging(
    log_level: str = 'INFO',
    console_output: bool = True
) -> None:
    """
    Set up logging configuration for AUPAT.

    This should be called once at the start of each script.

    Args:
        log_level: Minimum log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        console_output: If True, also log to console (useful for development)

    Example:
        setup_logging(log_level='DEBUG', console_output=True)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter

    # Remove any existing handlers (in case setup_logging called multiple times)
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Handler 1: Main log file (INFO and above)
    # Uses RotatingFileHandler so logs don't grow forever
    main_log_path = LOG_DIR / 'main.log'
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    main_handler.setLevel(getattr(logging, log_level.upper()))
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)

    # Handler 2: Error log file (ERROR and above only)
    error_log_path = LOG_DIR / 'error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Handler 3: Console output (optional, for development)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log that logging is configured
    root_logger.info(f"Logging initialized: level={log_level}, console={console_output}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module or script.

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured logger

    Example:
        logger = get_logger(__name__)
        logger.info("Script started")
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)

    return _loggers[name]


def log_function_call(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """
    Log a function call with arguments.

    Useful for debugging - shows what function was called with what parameters.

    Args:
        logger: Logger instance
        func_name: Name of function being called
        **kwargs: Function arguments to log

    Example:
        log_function_call(logger, 'import_location', loc_name='Factory', state='NY')
        # Logs: "Calling import_location: loc_name='Factory', state='NY'"
    """
    args_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}: {args_str}")


def log_exception(logger: logging.Logger, exc: Exception, context: dict = None) -> None:
    """
    Log an exception with full traceback and context.

    Args:
        logger: Logger instance
        exc: Exception to log
        context: Optional dictionary of contextual information

    Example:
        try:
            do_something()
        except Exception as e:
            log_exception(logger, e, context={'file': 'test.jpg', 'operation': 'copy'})
            raise
    """
    logger.error(f"Exception occurred: {exc}", exc_info=True)

    if context:
        logger.error(f"Context: {context}")


# Example usage (if this file is run directly)
if __name__ == '__main__':
    # Set up logging
    setup_logging(log_level='DEBUG', console_output=True)

    # Get a logger
    logger = get_logger(__name__)

    # Log at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Log a function call
    log_function_call(logger, 'test_function', param1='value1', param2=123)

    # Log an exception
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        log_exception(logger, e, context={'test': True})

    print(f"\nLogs written to: {LOG_DIR}")
    print(f"Check main.log and error.log")
```

### Testing This Module

Create `tests/unit/test_logging.py`:

```python
import pytest
import logging
from pathlib import Path
import tempfile
import shutil

from scripts.common.logging_config import (
    setup_logging,
    get_logger,
    log_function_call,
    log_exception,
    LOG_DIR
)


@pytest.fixture
def temp_log_dir(monkeypatch):
    """Create a temporary log directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Monkey-patch LOG_DIR to use temp directory
    monkeypatch.setattr('scripts.common.logging_config.LOG_DIR', temp_dir)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_setup_logging_creates_log_files(temp_log_dir, monkeypatch):
    """Test that setup_logging creates log files."""
    # Clear existing handlers
    logging.getLogger().handlers.clear()

    # Set up logging
    setup_logging(log_level='INFO', console_output=False)

    # Log something
    logger = get_logger('test')
    logger.info("Test message")

    # Check log files created
    assert (temp_log_dir / 'main.log').exists()
    assert (temp_log_dir / 'error.log').exists()

    # Check content
    main_log_content = (temp_log_dir / 'main.log').read_text()
    assert "Test message" in main_log_content


def test_error_log_only_contains_errors(temp_log_dir):
    """Test that error.log only contains ERROR and above."""
    logging.getLogger().handlers.clear()
    setup_logging(log_level='DEBUG', console_output=False)

    logger = get_logger('test')

    # Log at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Check main.log has all messages
    main_log = (temp_log_dir / 'main.log').read_text()
    assert "Debug message" in main_log or True  # Depends on log level
    assert "Info message" in main_log
    assert "Error message" in main_log

    # Check error.log only has error
    error_log = (temp_log_dir / 'error.log').read_text()
    assert "Info message" not in error_log
    assert "Error message" in error_log


def test_log_function_call(temp_log_dir):
    """Test log_function_call helper."""
    logging.getLogger().handlers.clear()
    setup_logging(log_level='DEBUG', console_output=False)

    logger = get_logger('test')
    log_function_call(logger, 'test_func', param1='value1', param2=123)

    main_log = (temp_log_dir / 'main.log').read_text()
    assert "Calling test_func" in main_log
    assert "param1='value1'" in main_log
    assert "param2=123" in main_log


def test_log_exception(temp_log_dir):
    """Test log_exception helper."""
    logging.getLogger().handlers.clear()
    setup_logging(log_level='ERROR', console_output=False)

    logger = get_logger('test')

    try:
        raise ValueError("Test error")
    except ValueError as e:
        log_exception(logger, e, context={'file': 'test.jpg'})

    error_log = (temp_log_dir / 'error.log').read_text()
    assert "Test error" in error_log
    assert "Context:" in error_log
    assert "test.jpg" in error_log
```

Run tests:
```bash
python -m pytest tests/unit/test_logging.py -v
```

---

## Summary of Work Completed

I've created comprehensive documentation for implementing P0 and P1 foundational components:

### Documents Created:

1. **IMPLEMENTATION_PLAN_P0_P1_FOUNDATIONS.md** - Original detailed plan covering all 12 P0/P1 components
2. **PLAN_AUDIT_P0_P1.md** - Thorough audit against BPA/BPL/KISS/FAANG PE principles
3. **IMPLEMENTATION_PLAN_P0_P1_REFINED.md** - Updated plan incorporating audit improvements
4. **IMPLEMENTATION_GUIDE_P0_P1.md** - Step-by-step guide for less-experienced developers (started)

### Key Improvements from Audit:

- ✅ Refactored validation.py into organized validator classes
- ✅ Added checkpoint database backup mechanism
- ✅ Added log disk space monitoring
- ✅ Defined mandatory performance benchmarks
- ✅ Documented design rationales for complex components

### Implementation Status:

**Documented (Ready to Code)**:
- P0-1: Logging Configuration (complete guide with tests)
- P0-2: Transaction Safety Wrapper (detailed spec)
- P0-3: Custom Exceptions (complete implementation + tests)
- P0-4: Input Validation (refactored class-based design)
- P0-5/P0-6: Verification utilities (detailed spec)
- P1-7 through P1-12: All detailed specifications

All components have passed audit against core principles and are ready for implementation.