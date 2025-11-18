"""
AUPAT Structured Logging Configuration

Provides centralized JSON logging with correlation IDs and structured fields.
New scripts should use this module for consistent, parseable log output.

Usage:
    from scripts.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Processing started", extra={"location_id": "abc123", "file_count": 10})

Configuration:
    LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT environment variable (json or text, default: text for backward compatibility)

Version: 1.0.0
Last Updated: 2025-11-18
"""

import logging
import os
import sys
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Try to import pythonjsonlogger, fall back to standard logging if not available
try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGING_AVAILABLE = True
except ImportError:
    JSON_LOGGING_AVAILABLE = False

# Global correlation ID for request tracing
_correlation_id: Optional[str] = None


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record):
        record.correlation_id = _correlation_id or "N/A"
        return True


class SensitiveDataFilter(logging.Filter):
    """
    Redact sensitive data from log records.

    Redacts common sensitive field names in log messages and extra data.
    """

    SENSITIVE_KEYS = {
        'password', 'token', 'api_key', 'secret', 'auth', 'authorization',
        'cookie', 'session', 'credential', 'private_key', 'access_key'
    }

    def filter(self, record):
        # Redact sensitive keys in extra data
        if hasattr(record, '__dict__'):
            for key in list(record.__dict__.keys()):
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    setattr(record, key, '[REDACTED]')

        # Basic message redaction (simple pattern matching)
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for sensitive in self.SENSITIVE_KEYS:
                if sensitive in msg.lower():
                    # Don't try to parse, just warn that sensitive data might be present
                    record.msg = msg + " [WARNING: May contain sensitive data]"
                    break

        return True


def get_log_level() -> int:
    """Get log level from environment variable or default to INFO."""
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_format() -> str:
    """Get log format from environment variable (json or text)."""
    return os.getenv('LOG_FORMAT', 'text').lower()


def setup_json_handler(level: int = logging.INFO) -> logging.Handler:
    """
    Create a JSON log handler.

    Args:
        level: Logging level

    Returns:
        logging.Handler configured for JSON output
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if JSON_LOGGING_AVAILABLE:
        # JSON formatter with structured fields
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(correlation_id)s',
            rename_fields={
                'asctime': 'timestamp',
                'name': 'logger',
                'levelname': 'level',
                'correlation_id': 'correlation_id'
            }
        )
    else:
        # Fallback to standard formatter that mimics JSON structure
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", '
            '"message": "%(message)s", "correlation_id": "%(correlation_id)s"}'
        )

    handler.setFormatter(formatter)

    # Add filters
    handler.addFilter(CorrelationIdFilter())
    handler.addFilter(SensitiveDataFilter())

    return handler


def setup_text_handler(level: int = logging.INFO) -> logging.Handler:
    """
    Create a text log handler (traditional format).

    Args:
        level: Logging level

    Returns:
        logging.Handler configured for text output
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler.setFormatter(formatter)

    # Still add filters for consistency
    handler.addFilter(CorrelationIdFilter())
    handler.addFilter(SensitiveDataFilter())

    return handler


def get_logger(name: str, level: Optional[int] = None, force_json: bool = False) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
        force_json: Force JSON format regardless of environment setting

    Returns:
        logging.Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing file", extra={"filename": "test.jpg", "size_bytes": 1024})
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        log_level = level or get_log_level()
        log_format = get_log_format()

        # Use JSON format if forced or configured
        if force_json or log_format == 'json':
            handler = setup_json_handler(log_level)
        else:
            handler = setup_text_handler(log_level)

        logger.addHandler(handler)
        logger.setLevel(log_level)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger


@contextmanager
def correlation_context(correlation_id: str):
    """
    Context manager for setting correlation ID.

    Usage:
        with correlation_context("req-123-456"):
            logger.info("Processing request")  # Will include correlation_id="req-123-456"

    Args:
        correlation_id: Unique identifier for request/operation tracing
    """
    global _correlation_id
    old_id = _correlation_id
    _correlation_id = correlation_id
    try:
        yield
    finally:
        _correlation_id = old_id


def set_correlation_id(correlation_id: str):
    """
    Set global correlation ID.

    Args:
        correlation_id: Unique identifier for request/operation tracing
    """
    global _correlation_id
    _correlation_id = correlation_id


def clear_correlation_id():
    """Clear global correlation ID."""
    global _correlation_id
    _correlation_id = None


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_id


# Convenience function for getting logger with default settings
def init_logging(module_name: str = "aupat", json_format: bool = False) -> logging.Logger:
    """
    Initialize logging for a module.

    Args:
        module_name: Name of the module
        json_format: Whether to use JSON format

    Returns:
        Configured logger

    Example:
        logger = init_logging(__name__, json_format=True)
    """
    return get_logger(module_name, force_json=json_format)


# Example usage (for documentation)
if __name__ == '__main__':
    # Text logging example
    logger = get_logger(__name__)
    logger.info("Starting AUPAT")
    logger.info("Processing location", extra={"location_id": "abc123", "loc_name": "Abandoned Hospital"})

    print("\n" + "=" * 70 + "\n")

    # JSON logging example
    json_logger = get_logger("aupat.api", force_json=True)
    json_logger.info("API request received")
    json_logger.info("Database query",
                     extra={"table": "locations", "query_time_ms": 45, "rows_returned": 10})

    print("\n" + "=" * 70 + "\n")

    # Correlation ID example
    with correlation_context("req-abc-123"):
        logger.info("Request started")
        logger.info("Processing upload", extra={"file_name": "photo.jpg", "size_kb": 1024})
        logger.info("Request completed")

    print("\n" + "=" * 70 + "\n")

    # Sensitive data redaction example
    logger.info("User login", extra={"username": "test", "password": "secret123"})  # password will be redacted

    print("\n" + "=" * 70 + "\n")
    print("Note: Set LOG_FORMAT=json environment variable to enable JSON logging by default")
    print("Note: Set LOG_LEVEL=DEBUG environment variable to change log level")
