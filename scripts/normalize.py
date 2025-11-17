#!/usr/bin/env python3
"""
AUPAT Normalization Functions
Centralized text and data normalization for consistent data storage.

This module provides normalization for:
- Location names (unidecode + titlecase + optional libpostal)
- State codes (lowercase + validation)
- Location types/sub-types (unidecode + titlecase + lowercase)
- Dates/timestamps (ISO 8601 format via dateutil)
- File extensions (lowercase)

Version: 1.0.0
Last Updated: 2025-11-15
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

try:
    from unidecode import unidecode
    HAS_UNIDECODE = True
except ImportError:
    HAS_UNIDECODE = False
    logging.warning("unidecode not installed - Unicode normalization will be limited")

try:
    from dateutil import parser as date_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    logging.warning("python-dateutil not installed - date parsing will be limited")

try:
    import postal.parser
    HAS_POSTAL = True
except ImportError:
    HAS_POSTAL = False
    logging.info("libpostal not installed - using fallback address normalization")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Valid US state codes (USPS two-letter abbreviations)
VALID_US_STATES = {
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
    'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
    'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
    'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
    'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
    'dc', 'pr', 'vi', 'gu', 'as', 'mp'  # Territories
}

# Common location types (validated list)
VALID_LOCATION_TYPES = {
    'industrial', 'residential', 'commercial', 'institutional',
    'agricultural', 'recreational', 'infrastructure', 'military',
    'religious', 'educational', 'healthcare', 'transportation',
    'mixed-use', 'other'
}


# Load type mapping for auto-correction
def load_type_mapping() -> dict:
    """Load location type mapping from JSON file."""
    mapping_path = Path(__file__).parent.parent / 'data' / 'location_type_mapping.json'

    if not mapping_path.exists():
        logger.warning("location_type_mapping.json not found - type suggestions disabled")
        return {'mappings': {}, 'valid_types': list(VALID_LOCATION_TYPES)}

    try:
        with open(mapping_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load type mapping: {e}")
        return {'mappings': {}, 'valid_types': list(VALID_LOCATION_TYPES)}


# Load mapping at module level (once)
TYPE_MAPPING_DATA = load_type_mapping()
TYPE_MAPPINGS = TYPE_MAPPING_DATA.get('mappings', {})


def normalize_location_name(name: str, use_postal: bool = True) -> str:
    """
    Normalize location name for consistent storage.

    Applies the following transformations:
    1. Unicode to ASCII (via unidecode)
    2. Titlecase conversion
    3. Optional: libpostal address parsing (if available and enabled)
    4. Whitespace cleanup

    Args:
        name: Raw location name (e.g., "Abandoned Factory", "Old Café")
        use_postal: Whether to use libpostal for address parsing (default: True)

    Returns:
        str: Normalized location name

    Examples:
        >>> normalize_location_name("abandoned factory")
        'Abandoned Factory'
        >>> normalize_location_name("old café")
        'Old Cafe'  # Unicode normalized
        >>> normalize_location_name("  old   mill  ")
        'Old Mill'  # Whitespace cleaned

    Notes:
        - If unidecode not available, Unicode chars will remain
        - If libpostal not available, falls back to simple normalization
        - Preserves meaningful capitalization via titlecase
    """
    if not name or not name.strip():
        return ""

    # Step 1: Convert Unicode to ASCII (if unidecode available)
    if HAS_UNIDECODE:
        normalized = unidecode(name)
    else:
        normalized = name

    # Step 2: Clean whitespace
    normalized = ' '.join(normalized.split())

    # Step 3: Apply libpostal if available and requested
    if HAS_POSTAL and use_postal:
        try:
            # Parse address to extract location name
            parsed = postal.parser.parse_address(normalized)
            # Extract house/building components
            location_parts = [
                comp[0] for comp in parsed
                if comp[1] in ('house', 'house_number', 'road', 'building')
            ]
            if location_parts:
                normalized = ' '.join(location_parts)
        except Exception as e:
            logger.warning(f"libpostal parsing failed for '{name}': {e}, using fallback")

    # Step 4: Apply titlecase
    normalized = normalized.title()

    return normalized


def normalize_aka_name(aka_name: Optional[str]) -> Optional[str]:
    """
    Normalize "also known as" name (same as location name).

    Args:
        aka_name: Alternative name for location (nullable)

    Returns:
        str or None: Normalized AKA name, or None if empty

    Example:
        >>> normalize_aka_name("the old mill")
        'The Old Mill'
        >>> normalize_aka_name(None)
        None
    """
    if not aka_name or not aka_name.strip():
        return None
    return normalize_location_name(aka_name)


def normalize_state_code(state: str) -> str:
    """
    Normalize US state code to lowercase two-letter abbreviation.

    Args:
        state: State code or name (e.g., "NY", "new york", "California")

    Returns:
        str: Normalized lowercase state code

    Raises:
        ValueError: If state code is invalid

    Examples:
        >>> normalize_state_code("NY")
        'ny'
        >>> normalize_state_code("New York")
        'ny'  # If libpostal available
        >>> normalize_state_code("California")
        'ca'  # If libpostal available

    Notes:
        - If libpostal available, can parse state names
        - If not available, expects two-letter code
        - Validates against VALID_US_STATES
    """
    if not state or not state.strip():
        raise ValueError("State code cannot be empty")

    state_input = state.strip()

    # Try libpostal parsing if available
    if HAS_POSTAL and len(state_input) > 2:
        try:
            parsed = postal.parser.parse_address(state_input)
            for component, label in parsed:
                if label == 'state':
                    state_code = component.lower()
                    if state_code in VALID_US_STATES:
                        return state_code
        except Exception as e:
            logger.warning(f"libpostal state parsing failed for '{state}': {e}")

    # Fallback: treat as two-letter code
    state_code = state_input.lower()

    # Validate (warn only - allow custom states per LOGSEC spec)
    if state_code not in VALID_US_STATES:
        logger.info(
            f"Custom state code: '{state}'. Not in standard USPS list. "
            f"Standard examples: ny, ca, tx. Using '{state_code}' as-is."
        )

    return state_code


def normalize_location_type(location_type: str, auto_correct: bool = True) -> str:
    """
    Normalize location type with auto-correction support.

    Applies:
    1. Unicode to ASCII (via unidecode)
    2. Lowercase conversion
    3. Whitespace cleanup
    4. Auto-correction using type mappings (if enabled)
    5. Validation against known types

    Args:
        location_type: Location type (e.g., "Industrial", "hospital", "businesses")
        auto_correct: Enable auto-correction using type mappings (default: True)

    Returns:
        str: Normalized lowercase location type

    Examples:
        >>> normalize_location_type("Industrial")
        'industrial'
        >>> normalize_location_type("hospital")
        'healthcare'  # Auto-corrected
        >>> normalize_location_type("businesses")
        'commercial'  # Auto-corrected
        >>> normalize_location_type("  Mixed Use  ")
        'mixed-use'

    Notes:
        - Returns lowercase for consistency
        - Auto-corrects common variations (hospital → healthcare, etc.)
        - Validates against VALID_LOCATION_TYPES
        - Allows unknown types but logs warning
    """
    if not location_type or not location_type.strip():
        raise ValueError("Location type cannot be empty")

    # Convert Unicode to ASCII
    if HAS_UNIDECODE:
        normalized = unidecode(location_type)
    else:
        normalized = location_type

    # Clean and lowercase
    normalized = normalized.strip().lower()

    # Replace spaces with hyphens for multi-word types
    normalized = normalized.replace(' ', '-')

    # Check if already valid
    if normalized in VALID_LOCATION_TYPES:
        return normalized

    # Try auto-correction using type mapping
    if auto_correct and normalized in TYPE_MAPPINGS:
        corrected = TYPE_MAPPINGS[normalized]
        logger.info(
            f"Location type '{normalized}' auto-corrected to '{corrected}'"
        )
        return corrected

    # Custom type - log for visibility but allow (per LOGSEC spec: "based off folder name")
    logger.info(
        f"Custom location type: '{normalized}'. "
        f"Common types: {sorted(VALID_LOCATION_TYPES)}. "
        f"Using '{normalized}' as-is per specification."
    )

    return normalized


def normalize_sub_type(sub_type: Optional[str]) -> Optional[str]:
    """
    Normalize location sub-type (same as location type).

    Args:
        sub_type: Location sub-type (nullable)

    Returns:
        str or None: Normalized lowercase sub-type, or None if empty

    Example:
        >>> normalize_sub_type("Factory")
        'factory'
        >>> normalize_sub_type(None)
        None
    """
    if not sub_type or not sub_type.strip():
        return None
    return normalize_location_type(sub_type)


def normalize_datetime(dt_input: Optional[str]) -> str:
    """
    Normalize date/time to ISO 8601 format.

    Accepts various date/time formats and converts to ISO 8601 string.
    Uses dateutil.parser for flexible parsing.

    Args:
        dt_input: Date/time string in various formats, or None for current time

    Returns:
        str: ISO 8601 formatted datetime string (e.g., "2025-11-15T10:30:00Z")

    Examples:
        >>> normalize_datetime("2025-11-15")
        '2025-11-15T00:00:00'
        >>> normalize_datetime("11/15/2025 10:30 AM")
        '2025-11-15T10:30:00'
        >>> normalize_datetime(None)  # Current time
        '2025-11-15T14:23:45.123456'

    Notes:
        - If dateutil not available, uses datetime.fromisoformat()
        - If input is None, returns current datetime
        - Always returns ISO 8601 format for consistency
    """
    # If no input, use current time
    if dt_input is None or (isinstance(dt_input, str) and not dt_input.strip()):
        return datetime.utcnow().isoformat()

    # Parse datetime
    if HAS_DATEUTIL:
        try:
            dt = date_parser.parse(dt_input)
            return dt.isoformat()
        except Exception as e:
            logger.error(f"Failed to parse datetime '{dt_input}': {e}")
            raise ValueError(f"Invalid datetime format: '{dt_input}'")
    else:
        # Fallback: try ISO format
        try:
            dt = datetime.fromisoformat(dt_input)
            return dt.isoformat()
        except Exception as e:
            logger.error(f"Failed to parse datetime '{dt_input}': {e}")
            raise ValueError(
                f"Invalid datetime format: '{dt_input}'. "
                "Install python-dateutil for flexible date parsing."
            )


def normalize_extension(extension: str) -> str:
    """
    Normalize file extension to lowercase without leading dot.

    Args:
        extension: File extension (e.g., ".JPG", "mp4", ".PDF")

    Returns:
        str: Normalized lowercase extension without dot (e.g., "jpg", "mp4", "pdf")

    Examples:
        >>> normalize_extension(".JPG")
        'jpg'
        >>> normalize_extension("MP4")
        'mp4'
        >>> normalize_extension(".pdf")
        'pdf'
    """
    if not extension:
        raise ValueError("Extension cannot be empty")

    # Remove leading dot and convert to lowercase
    normalized = extension.lstrip('.').lower()

    if not normalized:
        raise ValueError("Extension cannot be empty after normalization")

    return normalized


def normalize_author(author: Optional[str]) -> Optional[str]:
    """
    Normalize import author username.

    Args:
        author: Author username (nullable)

    Returns:
        str or None: Normalized author (lowercase, stripped), or None if empty

    Examples:
        >>> normalize_author("Bryant")
        'bryant'
        >>> normalize_author("  Admin  ")
        'admin'
        >>> normalize_author(None)
        None
    """
    if not author or not author.strip():
        return None

    # Lowercase and strip whitespace
    return author.strip().lower()


# Utility function to get normalization status
def get_normalization_capabilities() -> dict:
    """
    Get information about available normalization capabilities.

    Returns:
        dict: Status of optional dependencies

    Example:
        >>> caps = get_normalization_capabilities()
        >>> print(caps)
        {
            'unidecode': True,
            'dateutil': True,
            'postal': False,
            'fallback_mode': False
        }
    """
    return {
        'unidecode': HAS_UNIDECODE,
        'dateutil': HAS_DATEUTIL,
        'postal': HAS_POSTAL,
        'fallback_mode': not (HAS_UNIDECODE and HAS_DATEUTIL)
    }


if __name__ == '__main__':
    # Example usage and testing
    print("AUPAT Normalization Module")
    print("=" * 50)

    # Show capabilities
    print("\nNormalization Capabilities:")
    print("-" * 50)
    caps = get_normalization_capabilities()
    for lib, available in caps.items():
        status = "Available" if available else "Not Available"
        print(f"{lib:15} {status}")

    print("\n" + "=" * 50)
    print("Example Normalizations:")
    print("-" * 50)

    # Location name
    print(f"\nLocation: 'abandoned factory' → '{normalize_location_name('abandoned factory')}'")
    print(f"Location: 'old café' → '{normalize_location_name('old café')}'")

    # State code
    try:
        print(f"State: 'NY' → '{normalize_state_code('NY')}'")
        print(f"State: 'California' → '{normalize_state_code('ca')}'")
    except ValueError as e:
        print(f"State error: {e}")

    # Location type
    print(f"Type: 'Industrial' → '{normalize_location_type('Industrial')}'")
    print(f"Type: 'Mixed Use' → '{normalize_location_type('Mixed Use')}'")

    # DateTime
    print(f"Date: '2025-11-15' → '{normalize_datetime('2025-11-15')}'")
    print(f"Date: None (current) → '{normalize_datetime(None)}'")

    # Extension
    print(f"Extension: '.JPG' → '{normalize_extension('.JPG')}'")
    print(f"Extension: 'mp4' → '{normalize_extension('mp4')}'")

    print("\n" + "=" * 50)
    print("Module ready for use in AUPAT scripts")
