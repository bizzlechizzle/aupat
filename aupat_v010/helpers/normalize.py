#!/usr/bin/env python3
"""
AUPAT Helper: Normalize Text

LILBITS: One Script = One Primary Function
Purpose: Normalize location names, types, and other text fields

Why normalize?
- Consistent database entries (no duplicates from spacing/case)
- Filesystem-safe names (no special characters in folder names)
- Better search and autocomplete

Version: 1.0.0
Date: 2025-11-18
"""

import re
import sys
from typing import Optional


# Valid US state codes (USPS two-letter abbreviations)
VALID_STATES = {
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
    'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
    'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
    'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
    'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
    'dc', 'pr', 'vi', 'gu', 'as', 'mp'  # Territories
}


def normalize_location_name(name: str) -> str:
    """
    Normalize location name for consistent storage.

    Steps:
    1. Strip whitespace
    2. Title case (First Letter Uppercase)
    3. Remove extra spaces

    Args:
        name: Raw location name

    Returns:
        str: Normalized location name

    Example:
        >>> normalize_location_name("  buffalo psychiatric center  ")
        'Buffalo Psychiatric Center'
        >>> normalize_location_name("BUFFALO psych")
        'Buffalo Psych'

    Technical Details:
        - Preserves spaces for readability
        - Title case for consistency
        - Used for database storage and display
    """
    if not name:
        return ""

    # Strip and collapse multiple spaces
    name = ' '.join(name.split())

    # Title case
    return name.title()


def normalize_short_name(name: str) -> str:
    """
    Normalize short name for filesystem use.

    Steps:
    1. Lowercase
    2. Replace spaces with hyphens
    3. Remove special characters (keep letters, numbers, hyphens)
    4. Collapse multiple hyphens

    Args:
        name: Raw short name

    Returns:
        str: Filesystem-safe short name

    Example:
        >>> normalize_short_name("Buffalo Psych Center")
        'buffalo-psych-center'
        >>> normalize_short_name("Buffalo's Psych (1970s)")
        'buffalos-psych-1970s'

    Technical Details:
        - Used in folder names: Archive/NY-Hospital/buffalo-psych-a3f5/
        - Only lowercase letters, numbers, hyphens
        - No spaces (hyphens instead)
        - No special characters (apostrophes, parentheses removed)
    """
    if not name:
        return ""

    # Lowercase
    name = name.lower()

    # Replace spaces with hyphens
    name = name.replace(' ', '-')

    # Remove special characters (keep letters, numbers, hyphens)
    name = re.sub(r'[^a-z0-9-]', '', name)

    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)

    # Strip leading/trailing hyphens
    return name.strip('-')


def normalize_state_code(state: str) -> str:
    """
    Normalize and validate US state code.

    Args:
        state: State code (2 letters) or name

    Returns:
        str: Lowercase 2-letter state code

    Raises:
        ValueError: If invalid state code

    Example:
        >>> normalize_state_code("NY")
        'ny'
        >>> normalize_state_code("new york")
        Traceback: ValueError: Invalid state code...
        >>> normalize_state_code("California")
        Traceback: ValueError: Invalid state code...

    Technical Details:
        - Accepts only 2-letter USPS codes
        - Returns lowercase for consistency
        - Does NOT convert state names to codes (too ambiguous)
        - User must provide 2-letter code
    """
    if not state:
        raise ValueError("State code cannot be empty")

    # Lowercase and strip
    state = state.lower().strip()

    # Must be 2 characters
    if len(state) != 2:
        raise ValueError(
            f"State code must be 2 letters (got: '{state}'). "
            f"Use USPS codes: NY, CA, TX, etc."
        )

    # Validate against known states
    if state not in VALID_STATES:
        raise ValueError(
            f"Invalid state code: '{state}'. "
            f"Must be valid USPS code (NY, CA, TX, etc.)"
        )

    return state


def normalize_location_type(loc_type: str) -> str:
    """
    Normalize location type.

    Steps:
    1. Lowercase
    2. Remove spaces (replace with hyphens)
    3. Remove special characters

    Args:
        loc_type: Raw location type

    Returns:
        str: Normalized type (lowercase, hyphens, no spaces)

    Example:
        >>> normalize_location_type("Industrial Complex")
        'industrial-complex'
        >>> normalize_location_type("Residential (House)")
        'residential-house'

    Technical Details:
        - Used in folder structure: Archive/ny-industrial/
        - Also used in database for filtering/searching
        - Common types: industrial, residential, hospital, etc.
    """
    if not loc_type:
        return ""

    # Same as short name normalization
    return normalize_short_name(loc_type)


def _cli():
    """
    Command-line interface for normalize.py

    Usage:
        python normalize.py <type> <value>

    Types:
        name       - Location name (title case)
        short      - Short name (filesystem-safe)
        state      - State code (validate)
        type       - Location type (filesystem-safe)

    Examples:
        python normalize.py name "buffalo psychiatric center"
        python normalize.py short "Buffalo Psych Center"
        python normalize.py state "NY"
        python normalize.py type "Industrial Complex"
    """
    if len(sys.argv) < 3:
        print("Usage: python normalize.py <type> <value>")
        print("Types: name, short, state, type")
        sys.exit(1)

    norm_type = sys.argv[1]
    value = sys.argv[2]

    try:
        if norm_type == 'name':
            result = normalize_location_name(value)
        elif norm_type == 'short':
            result = normalize_short_name(value)
        elif norm_type == 'state':
            result = normalize_state_code(value)
        elif norm_type == 'type':
            result = normalize_location_type(value)
        else:
            print(f"ERROR: Unknown type '{norm_type}'")
            sys.exit(1)

        print(f"Input:  {value}")
        print(f"Output: {result}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _cli()
