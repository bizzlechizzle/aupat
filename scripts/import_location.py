#!/usr/bin/env python3
"""
Location CRUD operations for AUPAT import workflow.

Handles:
- Creating new locations
- Looking up existing locations (autocomplete)
- Creating sub-locations
- Validating required fields

Usage:
    from scripts.import_location import create_location, lookup_location

LILBITS: One function - location database operations
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from scripts.genuuid import generate_uuid
from scripts.normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_sub_type,
    normalize_datetime,
    normalize_gps
)


def load_config() -> dict:
    """Load user configuration."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config


def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    config = load_config()
    db_path = Path(config['db_loc']) / config['db_name']
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def create_location(
    name: str,
    state: str,
    location_type: str,
    loc_short: Optional[str] = None,
    status: Optional[str] = None,
    explored: Optional[str] = None,
    sub_type: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    county: Optional[str] = None,
    region: Optional[str] = None,
    gps: Optional[str] = None,
    import_author: Optional[str] = None,
    historical: bool = False
) -> Tuple[str, str]:
    """
    Create new location in database.

    Args:
        name: Location name (required)
        state: State code (required)
        location_type: Location type (required)
        loc_short: Short name (optional, generated from name if missing)
        status: Abandoned, Demolished, Rehabbed, etc.
        explored: Interior, Exterior, Un-Documented, N/A
        sub_type: Location sub-type
        street: Street address
        city: City
        zip_code: ZIP code
        county: County
        region: Region
        gps: GPS coordinates (lat, lon)
        import_author: Author username
        historical: Historical checkbox

    Returns:
        Tuple of (loc_uuid, loc_short)

    Raises:
        ValueError: If required fields missing or invalid
    """
    # Validate required fields
    if not name or not name.strip():
        raise ValueError("Location name is required")
    if not state or not state.strip():
        raise ValueError("State is required")
    if not location_type or not location_type.strip():
        raise ValueError("Location type is required")

    # Normalize inputs
    name_norm = normalize_location_name(name)
    state_norm = normalize_state_code(state)
    type_norm = normalize_location_type(location_type)

    # Generate short name if not provided
    if not loc_short:
        # Take first word of name, max 12 chars
        loc_short = name_norm.split()[0][:12].lower()
    else:
        loc_short = loc_short[:12].lower()

    # Normalize optional fields
    sub_type_norm = normalize_sub_type(sub_type) if sub_type else None

    # Parse GPS if provided
    gps_lat, gps_lon = None, None
    if gps:
        gps_parsed = normalize_gps(gps)
        if gps_parsed:
            gps_lat, gps_lon = gps_parsed

    # Generate location UUID
    loc_uuid = generate_uuid(12)

    # Get timestamp
    timestamp = normalize_datetime(None)

    # Insert into database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO locations (
                loc_uuid, loc_name, loc_short, status, explored,
                type, sub_type, street, state, city, zip_code,
                county, region, gps_lat, gps_lon, import_author,
                historical, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loc_uuid, name_norm, loc_short, status, explored,
            type_norm, sub_type_norm, street, state_norm, city, zip_code,
            county, region, gps_lat, gps_lon, import_author,
            1 if historical else 0, timestamp, timestamp
        ))
        conn.commit()
        return (loc_uuid, loc_short)
    finally:
        conn.close()


def lookup_location(name: str) -> List[Dict]:
    """
    Look up existing locations by name (for autocomplete).

    Args:
        name: Partial or full location name

    Returns:
        List of matching location dicts with keys: loc_uuid, loc_name, state, type

    Example:
        >>> results = lookup_location("old mill")
        >>> print(results)
        [{'loc_uuid': 'abc123...', 'loc_name': 'Old Mill', 'state': 'ny', 'type': 'industrial'}]
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT loc_uuid, loc_name, loc_short, state, type
            FROM locations
            WHERE loc_name LIKE ?
            ORDER BY loc_name
            LIMIT 20
        """, (f"%{name}%",))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_sub_location(
    loc_uuid: str,
    sub_name: str,
    sub_short: Optional[str] = None,
    is_primary: bool = False
) -> str:
    """
    Create sub-location for existing location.

    Args:
        loc_uuid: Parent location UUID
        sub_name: Sub-location name
        sub_short: Short name (optional)
        is_primary: Whether this is the primary sub-location

    Returns:
        Sub-location UUID

    Raises:
        ValueError: If location doesn't exist
    """
    if not sub_name or not sub_name.strip():
        raise ValueError("Sub-location name is required")

    # Normalize name
    sub_name_norm = normalize_location_name(sub_name)

    # Generate short name if not provided
    if not sub_short:
        sub_short = sub_name_norm.split()[0][:12].lower()
    else:
        sub_short = sub_short[:12].lower()

    # Generate UUID
    sub_uuid = generate_uuid(12)

    # Get timestamp
    timestamp = normalize_datetime(None)

    # Insert into database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Verify location exists
        cursor.execute("SELECT loc_uuid FROM locations WHERE loc_uuid = ?", (loc_uuid,))
        if not cursor.fetchone():
            raise ValueError(f"Location not found: {loc_uuid}")

        cursor.execute("""
            INSERT INTO sub_locations (
                sub_uuid, loc_uuid, sub_name, sub_short, is_primary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (sub_uuid, loc_uuid, sub_name_norm, sub_short, 1 if is_primary else 0, timestamp))

        conn.commit()
        return sub_uuid
    finally:
        conn.close()


def main():
    """CLI interface for testing."""
    import sys

    if len(sys.argv) < 4:
        print("Usage: import_location.py <command> <args>")
        print("\nCommands:")
        print("  create <name> <state> <type> [loc_short]")
        print("  lookup <name>")
        print("  createsub <loc_uuid> <sub_name> [sub_short] [is_primary]")
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == 'create':
            name = sys.argv[2]
            state = sys.argv[3]
            location_type = sys.argv[4]
            loc_short = sys.argv[5] if len(sys.argv) > 5 else None

            loc_uuid, loc_short = create_location(name, state, location_type, loc_short)
            print(f"Created location: {loc_uuid} ({loc_short})")

        elif cmd == 'lookup':
            name = sys.argv[2]
            results = lookup_location(name)
            print(f"Found {len(results)} locations:")
            for loc in results:
                print(f"  {loc['loc_uuid']}: {loc['loc_name']} ({loc['state']}, {loc['type']})")

        elif cmd == 'createsub':
            loc_uuid = sys.argv[2]
            sub_name = sys.argv[3]
            sub_short = sys.argv[4] if len(sys.argv) > 4 else None
            is_primary = sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else False

            sub_uuid = create_sub_location(loc_uuid, sub_name, sub_short, is_primary)
            print(f"Created sub-location: {sub_uuid}")

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
