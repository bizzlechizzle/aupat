#!/usr/bin/env python3
"""
Generate UUID4 identifiers (first 12 characters).

Usage:
    from scripts.genuuid import generate_uuid
    uuid12 = generate_uuid()

LILBITS: One function - generate UUID
"""

import uuid


def generate_uuid(length: int = 12) -> str:
    """
    Generate UUID4 identifier (first N characters).

    Args:
        length: Number of characters to return (default 12)

    Returns:
        First N characters of UUID4 (lowercase, no dashes)

    Example:
        >>> uid = generate_uuid()
        >>> len(uid)
        12
        >>> uid = generate_uuid(8)
        >>> len(uid)
        8
    """
    # Generate UUID4, remove dashes, take first N chars, lowercase
    return str(uuid.uuid4()).replace('-', '')[:length].lower()


def main():
    """CLI interface for testing."""
    import sys

    length = int(sys.argv[1]) if len(sys.argv) > 1 else 12

    try:
        uuid_val = generate_uuid(length)
        print(f"UUID4 ({length} chars): {uuid_val}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
