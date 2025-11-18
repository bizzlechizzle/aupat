#!/usr/bin/env python3
"""
AUPAT Helper: Generate SHA256 Hash (12-character)

LILBITS: One Script = One Primary Function
Purpose: Calculate SHA256 hash and return first 12 characters

Why 12 characters?
- 8-char: 65k files before collision (TOO SMALL)
- 12-char: 16.7M files before collision (SAFE)
- 16-char: 4.3B files (overkill)

Version: 1.0.0
Date: 2025-11-18
"""

import hashlib
import sys
from pathlib import Path
from typing import Optional


def generate_sha256(filepath: Path, length: int = 12) -> str:
    """
    Calculate SHA256 hash of file and return first N characters.

    Uses chunked reading (64KB at a time) for memory efficiency.
    Works with files of ANY size (even multi-GB videos).

    Args:
        filepath: Path to file to hash
        length: Number of characters to return (default: 12)

    Returns:
        str: First N characters of SHA256 hash (lowercase hex)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
        ValueError: If length invalid

    Example:
        >>> generate_sha256(Path("photo.jpg"))
        'f7e9c2a1d3b5'
        >>> generate_sha256(Path("photo.jpg"), length=16)
        'f7e9c2a1d3b5e8f4'

    Technical Details:
        - Chunk size: 64KB (65536 bytes) - optimal for most systems
        - Hash algorithm: SHA256 (256-bit = 64 hex characters)
        - 12-char = 48 bits = 281 trillion possibilities
        - Memory usage: Constant 64KB regardless of file size
    """
    # Validate inputs
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if not filepath.is_file():
        raise ValueError(f"Path is not a file: {filepath}")

    if length < 1 or length > 64:
        raise ValueError(f"Length must be 1-64, got: {length}")

    # Calculate SHA256 with chunked reading
    sha256_hash = hashlib.sha256()
    chunk_size = 65536  # 64KB chunks (optimal for most systems)

    try:
        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(chunk_size), b''):
                sha256_hash.update(chunk)
    except PermissionError as e:
        raise PermissionError(f"Cannot read file: {filepath}") from e
    except Exception as e:
        raise RuntimeError(f"Error hashing file: {filepath}") from e

    # Get full hash (64 hex characters)
    full_hash = sha256_hash.hexdigest()

    # Return first N characters
    return full_hash[:length]


def _cli():
    """
    Command-line interface for gensha.py

    Usage:
        python gensha.py <filepath> [length]

    Examples:
        python gensha.py photo.jpg
        python gensha.py video.mp4 16
    """
    if len(sys.argv) < 2:
        print("Usage: python gensha.py <filepath> [length]")
        print("Example: python gensha.py photo.jpg 12")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    length = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    try:
        sha_hash = generate_sha256(filepath, length)
        print(f"SHA256 ({length}-char): {sha_hash}")
        print(f"File: {filepath}")
        print(f"Size: {filepath.stat().st_size:,} bytes")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _cli()
