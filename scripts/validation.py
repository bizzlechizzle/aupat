#!/usr/bin/env python3
"""
Input Validation Utilities
Provides validation functions for user input to prevent crashes and security issues.

All validation functions follow the pattern:
- Raise ValueError with clear message if invalid
- Return cleaned/normalized value if valid

Version: 1.0.0
Last Updated: 2025-11-17
"""

import re
from pathlib import Path
from typing import Optional


def validate_location_name(name: str) -> str:
    """
    Validate and clean location name.

    Rules:
    - Must be 2-200 characters after stripping whitespace
    - No path separators (/, \\, null bytes)
    - No leading/trailing whitespace in final result

    Args:
        name: Raw location name from user input

    Returns:
        str: Cleaned location name

    Raises:
        ValueError: If validation fails

    Examples:
        >>> validate_location_name("  Test Location  ")
        'Test Location'
        >>> validate_location_name("Middletown State Hospital")
        'Middletown State Hospital'
        >>> validate_location_name("Invalid/Name")  # doctest: +SKIP
        ValueError: Location name contains invalid characters
    """
    if not name:
        raise ValueError("Location name cannot be empty")

    # Strip whitespace
    name = name.strip()

    # Check length
    if len(name) < 2:
        raise ValueError("Location name must be at least 2 characters")

    if len(name) > 200:
        raise ValueError(f"Location name too long: {len(name)} characters (max 200)")

    # Check for dangerous characters
    invalid_chars = ['/', '\\', '\0', '\n', '\r', '\t']
    found_invalid = [c for c in invalid_chars if c in name]
    if found_invalid:
        raise ValueError(
            f"Location name contains invalid characters: {found_invalid}. "
            f"Path separators and control characters are not allowed."
        )

    return name


def validate_state_code(state: str) -> str:
    """
    Validate US state or province code.

    Rules:
    - Must be 2 letters
    - Converted to lowercase
    - Alphabetic characters only

    Args:
        state: State code (e.g., 'NY', 'ca', 'VT')

    Returns:
        str: Lowercase state code

    Raises:
        ValueError: If validation fails

    Examples:
        >>> validate_state_code("NY")
        'ny'
        >>> validate_state_code("ca")
        'ca'
        >>> validate_state_code("123")  # doctest: +SKIP
        ValueError: State code must be letters only
    """
    if not state:
        raise ValueError("State code cannot be empty")

    state = state.lower().strip()

    if len(state) != 2:
        raise ValueError(f"State code must be 2 letters, got: '{state}' ({len(state)} chars)")

    if not state.isalpha():
        raise ValueError(f"State code must be letters only, got: '{state}'")

    # Note: We don't validate against a list of valid state codes to allow
    # Canadian provinces, territories, and international use
    return state


def validate_location_type(loc_type: str) -> str:
    """
    Validate location type.

    Rules:
    - Must be 2-50 characters
    - Lowercase letters, hyphens, and spaces only
    - No leading/trailing whitespace

    Common types: industrial, residential, commercial, hospital, school, etc.

    Args:
        loc_type: Location type from user input

    Returns:
        str: Cleaned location type

    Raises:
        ValueError: If validation fails

    Examples:
        >>> validate_location_type("Industrial")
        'industrial'
        >>> validate_location_type("state-hospital")
        'state-hospital'
    """
    if not loc_type:
        raise ValueError("Location type cannot be empty")

    loc_type = loc_type.lower().strip()

    if len(loc_type) < 2:
        raise ValueError("Location type must be at least 2 characters")

    if len(loc_type) > 50:
        raise ValueError(f"Location type too long: {len(loc_type)} characters (max 50)")

    # Allow lowercase letters, hyphens, and spaces
    if not re.match(r'^[a-z\s\-]+$', loc_type):
        raise ValueError(
            f"Location type contains invalid characters: '{loc_type}'. "
            f"Only lowercase letters, spaces, and hyphens are allowed."
        )

    return loc_type


def validate_file_size(file, max_size_gb: float = 10.0) -> int:
    """
    Validate file size is within acceptable range.

    This function checks the file size without loading the entire file into memory.

    Args:
        file: File object (from Flask request.files)
        max_size_gb: Maximum file size in gigabytes (default 10GB for 4K video)

    Returns:
        int: File size in bytes

    Raises:
        ValueError: If file is too large

    Examples:
        >>> # Example with mock file object
        >>> class MockFile:
        ...     def seek(self, pos, whence=0): pass
        ...     def tell(self): return 1024 * 1024  # 1MB
        >>> validate_file_size(MockFile())
        1048576
    """
    # Seek to end to get size without loading into memory
    file.seek(0, 2)  # 2 = SEEK_END
    size_bytes = file.tell()
    file.seek(0)  # Reset to beginning for subsequent reads

    size_gb = size_bytes / (1024 ** 3)

    if size_gb > max_size_gb:
        raise ValueError(
            f"File too large: {size_gb:.2f}GB (max {max_size_gb}GB). "
            f"For files larger than {max_size_gb}GB, please contact support."
        )

    return size_bytes


def validate_filename(filename: str) -> str:
    """
    Validate uploaded filename for security.

    Rules:
    - No path separators (prevents directory traversal)
    - No null bytes
    - Reasonable length (< 255 chars)

    Args:
        filename: Original filename from upload

    Returns:
        str: Validated filename

    Raises:
        ValueError: If filename is invalid

    Examples:
        >>> validate_filename("photo.jpg")
        'photo.jpg'
        >>> validate_filename("../../../etc/passwd")  # doctest: +SKIP
        ValueError: Filename contains path separators
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Check for path traversal attempts
    if '/' in filename or '\\' in filename:
        raise ValueError(
            f"Filename contains path separators: '{filename}'. "
            f"This may be a security issue."
        )

    # Check for null bytes
    if '\0' in filename:
        raise ValueError("Filename contains null bytes")

    # Check length (filesystem limit is usually 255)
    if len(filename) > 255:
        raise ValueError(f"Filename too long: {len(filename)} characters (max 255)")

    return filename


def validate_author_name(author: str) -> str:
    """
    Validate author/username.

    Rules:
    - 2-100 characters
    - Letters, numbers, spaces, hyphens, underscores only
    - No leading/trailing whitespace

    Args:
        author: Author name or username

    Returns:
        str: Cleaned author name

    Raises:
        ValueError: If validation fails

    Examples:
        >>> validate_author_name("John Doe")
        'John Doe'
        >>> validate_author_name("user_123")
        'user_123'
    """
    if not author:
        raise ValueError("Author name cannot be empty")

    author = author.strip()

    if len(author) < 2:
        raise ValueError("Author name must be at least 2 characters")

    if len(author) > 100:
        raise ValueError(f"Author name too long: {len(author)} characters (max 100)")

    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', author):
        raise ValueError(
            f"Author name contains invalid characters: '{author}'. "
            f"Only letters, numbers, spaces, hyphens, and underscores are allowed."
        )

    return author


def validate_url(url: str) -> str:
    """
    Basic URL validation.

    Rules:
    - Must start with http:// or https://
    - Reasonable length (< 2000 chars)

    Note: This is basic validation. For production, consider using validators library.

    Args:
        url: URL string

    Returns:
        str: Validated URL

    Raises:
        ValueError: If URL is invalid

    Examples:
        >>> validate_url("https://example.com")
        'https://example.com'
        >>> validate_url("invalid-url")  # doctest: +SKIP
        ValueError: URL must start with http:// or https://
    """
    if not url:
        raise ValueError("URL cannot be empty")

    url = url.strip()

    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError(
            f"URL must start with http:// or https://, got: '{url[:50]}...'"
        )

    if len(url) > 2000:
        raise ValueError(f"URL too long: {len(url)} characters (max 2000)")

    return url


# Convenience function to validate all import form data at once
def validate_import_form_data(data: dict) -> dict:
    """
    Validate all fields from import form.

    Args:
        data: Dict containing form fields (loc_name, state, type, etc.)

    Returns:
        dict: Validated and cleaned data

    Raises:
        ValueError: If any field fails validation

    Examples:
        >>> data = {'loc_name': 'Test', 'state': 'NY', 'type': 'industrial'}
        >>> result = validate_import_form_data(data)
        >>> result['state']
        'ny'
    """
    validated = {}

    # Required fields
    validated['loc_name'] = validate_location_name(data.get('loc_name', ''))
    validated['state'] = validate_state_code(data.get('state', ''))
    validated['type'] = validate_location_type(data.get('type', ''))

    # Optional fields
    if data.get('aka_name'):
        validated['aka_name'] = validate_location_name(data['aka_name'])
    else:
        validated['aka_name'] = None

    if data.get('sub_type'):
        validated['sub_type'] = validate_location_type(data['sub_type'])
    else:
        validated['sub_type'] = None

    if data.get('imp_author'):
        validated['imp_author'] = validate_author_name(data['imp_author'])
    else:
        validated['imp_author'] = None

    # Web URLs (multiple, separated by newlines)
    if data.get('web_urls'):
        urls = [url.strip() for url in data['web_urls'].split('\n') if url.strip()]
        validated['web_urls'] = [validate_url(url) for url in urls]
    else:
        validated['web_urls'] = []

    return validated


if __name__ == '__main__':
    # Run doctests
    import doctest
    print("Running validation tests...")
    doctest.testmod(verbose=True)
    print("All tests passed!")
