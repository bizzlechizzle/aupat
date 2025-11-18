#!/usr/bin/env python3
"""
Generate SHA256 hash for files (first 12 characters).

Usage:
    from scripts.gensha import generate_file_hash
    hash12 = generate_file_hash('/path/to/file.jpg')

LILBITS: One function - generate file hash
"""

import hashlib
from pathlib import Path


def generate_file_hash(file_path: str | Path, length: int = 12) -> str:
    """
    Generate SHA256 hash of file (first N characters).

    Args:
        file_path: Path to file
        length: Number of characters to return (default 12)

    Returns:
        First N characters of SHA256 hash (lowercase)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    # Read file in chunks for memory efficiency (handles large videos)
    sha256_hash = hashlib.sha256()

    with open(file_path, 'rb') as f:
        # Read in 64kb chunks
        for chunk in iter(lambda: f.read(65536), b''):
            sha256_hash.update(chunk)

    # Return first N characters
    return sha256_hash.hexdigest()[:length].lower()


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: gensha.py <file_path> [length]")
        sys.exit(1)

    file_path = sys.argv[1]
    length = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    try:
        hash_val = generate_file_hash(file_path, length)
        print(f"SHA256 ({length} chars): {hash_val}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
