#!/usr/bin/env python3
"""
AUPAT Helper: Generate UUID4 (12-character)

LILBITS: One Script = One Primary Function
Purpose: Generate unique UUID4 and return first 12 characters

Why UUID4?
- Cryptographically random (not sequential)
- Globally unique across systems
- No database lookup needed for generation
- 122 bits of randomness

Why 12 characters?
- 12 chars from UUID4 (removing hyphens) = 48 bits
- Same collision resistance as 12-char SHA256
- Consistent naming scheme across project

Version: 1.0.0
Date: 2025-11-18
"""

import sys
import uuid
from typing import Optional


def generate_uuid4(length: int = 12) -> str:
    """
    Generate random UUID4 and return first N characters.

    UUID4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx (36 chars with hyphens)
    We remove hyphens and take first N characters.

    Args:
        length: Number of characters to return (default: 12)

    Returns:
        str: First N characters of UUID4 (lowercase hex, no hyphens)

    Raises:
        ValueError: If length invalid

    Example:
        >>> generate_uuid4()
        'a3f5d8e2b1c4'
        >>> generate_uuid4(length=8)
        'a3f5d8e2'
        >>> generate_uuid4(length=16)
        'a3f5d8e2b1c4f9e7'

    Technical Details:
        - Algorithm: UUID4 (RFC 4122)
        - Randomness: 122 bits (out of 128 total)
        - Without hyphens: 32 hex characters
        - 12-char = 48 bits = 281 trillion possibilities
        - Collision probability at 16.7M: 50%
    """
    # Validate length
    if length < 1 or length > 32:
        raise ValueError(f"Length must be 1-32, got: {length}")

    # Generate UUID4
    new_uuid = uuid.uuid4()

    # Convert to string, remove hyphens, take first N chars
    uuid_str = str(new_uuid).replace('-', '')

    return uuid_str[:length]


def generate_with_collision_check(
    cursor,
    table_name: str,
    uuid_field: str = 'loc_uuid',
    length: int = 12,
    max_attempts: int = 100
) -> str:
    """
    Generate UUID with database collision checking.

    Generates UUID and checks if it already exists in database.
    If collision detected, tries again (up to max_attempts).

    Args:
        cursor: SQLite database cursor
        table_name: Table to check for collisions
        uuid_field: Field name to check (default: 'loc_uuid')
        length: UUID length (default: 12)
        max_attempts: Maximum retry attempts (default: 100)

    Returns:
        str: Unique UUID (verified against database)

    Raises:
        RuntimeError: If can't generate unique UUID after max_attempts

    Example:
        >>> import sqlite3
        >>> conn = sqlite3.connect('aupat.db')
        >>> cursor = conn.cursor()
        >>> uuid = generate_with_collision_check(cursor, 'locations')
        'a3f5d8e2b1c4'

    Technical Details:
        - With 12-char UUIDs, collision is EXTREMELY rare
        - Expected attempts before collision: ~4.3 million
        - 100 attempts should be more than enough
        - If you hit 100 attempts, something is very wrong
    """
    for attempt in range(max_attempts):
        # Generate new UUID
        new_uuid = generate_uuid4(length)

        # Check if exists in database
        try:
            cursor.execute(
                f"SELECT 1 FROM {table_name} WHERE {uuid_field} = ? LIMIT 1",
                (new_uuid,)
            )
            result = cursor.fetchone()

            if result is None:
                # UUID doesn't exist - we're good!
                return new_uuid

            # Collision detected - try again
            print(f"WARNING: UUID collision detected (attempt {attempt + 1}): {new_uuid}")

        except Exception as e:
            raise RuntimeError(f"Database error during collision check: {e}") from e

    # If we get here, we failed after max_attempts
    raise RuntimeError(
        f"Failed to generate unique UUID after {max_attempts} attempts. "
        f"This should be EXTREMELY rare. Check your database."
    )


def _cli():
    """
    Command-line interface for genuuid.py

    Usage:
        python genuuid.py [length]

    Examples:
        python genuuid.py
        python genuuid.py 16
    """
    length = int(sys.argv[1]) if len(sys.argv) > 1 else 12

    try:
        new_uuid = generate_uuid4(length)
        print(f"UUID4 ({length}-char): {new_uuid}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _cli()
