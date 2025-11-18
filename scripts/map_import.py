"""
AUPAT Map Import Module
Handles importing maps from various formats (CSV, GeoJSON, KML)
with two modes: Full Import and Reference Mode.

Version: 0.1.3
Last Updated: 2025-11-17
"""

import csv
import json
import logging
import math
import re
import sqlite3
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from io import StringIO, BytesIO

logger = logging.getLogger(__name__)

# State abbreviation mapping
STATE_ABBREV_MAP = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY'
}

# Valid US state abbreviations
VALID_STATES = set(STATE_ABBREV_MAP.values())


def normalize_state(state_str: str) -> Optional[str]:
    """
    Normalize state input to 2-letter abbreviation.

    Args:
        state_str: State name or abbreviation

    Returns:
        2-letter state code or None if invalid
    """
    if not state_str:
        return None

    state_clean = state_str.strip().lower()

    # Check if already 2-letter code
    if len(state_clean) == 2 and state_clean.upper() in VALID_STATES:
        return state_clean.upper()

    # Check if full state name
    return STATE_ABBREV_MAP.get(state_clean)


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.

    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Args:
        s1, s2: Strings to compare

    Returns:
        Edit distance (number of changes needed)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_match_names(name1: str, name2: str, threshold: int = 3) -> bool:
    """
    Check if two location names are similar using fuzzy matching.

    Args:
        name1, name2: Names to compare
        threshold: Maximum edit distance to consider a match

    Returns:
        True if names are similar
    """
    if not name1 or not name2:
        return False

    # Normalize names
    n1 = name1.strip().lower()
    n2 = name2.strip().lower()

    # Exact match
    if n1 == n2:
        return True

    # Check Levenshtein distance
    distance = levenshtein_distance(n1, n2)
    return distance <= threshold


def parse_csv_map(file_content: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse CSV map file.

    Expected columns (flexible):
    - name (required)
    - lat, latitude (optional)
    - lon, lng, longitude (optional)
    - state (optional)
    - type (optional)
    - address, street_address (optional)
    - city (optional)
    - zip, zip_code (optional)
    - notes, description (optional)

    Args:
        file_content: CSV file content as string

    Returns:
        Tuple of (locations list, errors list)
    """
    locations = []
    errors = []

    try:
        # Parse CSV
        reader = csv.DictReader(StringIO(file_content))

        # Normalize column names
        if not reader.fieldnames:
            errors.append("CSV has no header row")
            return locations, errors

        for idx, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Extract name (required)
                name = (row.get('name') or row.get('Name') or
                       row.get('location') or row.get('Location') or '').strip()

                if not name:
                    errors.append(f"Row {idx}: Missing required 'name' field")
                    continue

                # Extract GPS coordinates
                lat_str = (row.get('lat') or row.get('latitude') or
                          row.get('Lat') or row.get('Latitude') or '').strip()
                lon_str = (row.get('lon') or row.get('lng') or row.get('longitude') or
                          row.get('Lon') or row.get('Lng') or row.get('Longitude') or '').strip()

                lat = float(lat_str) if lat_str else None
                lon = float(lon_str) if lon_str else None

                # Validate GPS bounds
                if lat is not None and (lat < -90 or lat > 90):
                    errors.append(f"Row {idx}: Invalid latitude {lat} (must be -90 to 90)")
                    lat = None

                if lon is not None and (lon < -180 or lon > 180):
                    errors.append(f"Row {idx}: Invalid longitude {lon} (must be -180 to 180)")
                    lon = None

                # Extract state
                state_raw = (row.get('state') or row.get('State') or '').strip()
                state = normalize_state(state_raw) if state_raw else None

                # Extract other fields
                location_type = (row.get('type') or row.get('Type') or '').strip()
                street_address = (row.get('address') or row.get('street_address') or
                                row.get('Address') or row.get('Street Address') or '').strip()
                city = (row.get('city') or row.get('City') or '').strip()
                zip_code = (row.get('zip') or row.get('zip_code') or
                           row.get('Zip') or row.get('ZIP') or '').strip()
                notes = (row.get('notes') or row.get('description') or
                        row.get('Notes') or row.get('Description') or '').strip()

                # Create location dict
                location = {
                    'name': name,
                    'lat': lat,
                    'lon': lon,
                    'state': state,
                    'type': location_type or None,
                    'street_address': street_address or None,
                    'city': city or None,
                    'zip_code': zip_code or None,
                    'notes': notes or None,
                    'original_data': json.dumps(dict(row))
                }

                locations.append(location)

            except ValueError as e:
                errors.append(f"Row {idx}: Invalid number format - {e}")
            except Exception as e:
                errors.append(f"Row {idx}: Parsing error - {e}")

    except Exception as e:
        errors.append(f"CSV parsing failed: {e}")

    return locations, errors


def parse_geojson_map(file_content: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse GeoJSON map file.

    Expected structure:
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]  # NOTE: GeoJSON uses [lon, lat] order!
                },
                "properties": {
                    "name": "Location Name",
                    "state": "AZ",
                    "type": "industrial",
                    ...
                }
            }
        ]
    }

    Args:
        file_content: GeoJSON file content as string

    Returns:
        Tuple of (locations list, errors list)
    """
    locations = []
    errors = []

    try:
        data = json.loads(file_content)

        # Validate GeoJSON structure
        if data.get('type') != 'FeatureCollection':
            errors.append("Invalid GeoJSON: Missing 'FeatureCollection' type")
            return locations, errors

        features = data.get('features', [])
        if not features:
            errors.append("GeoJSON has no features")
            return locations, errors

        for idx, feature in enumerate(features):
            try:
                # Extract geometry
                geometry = feature.get('geometry', {})
                coords = geometry.get('coordinates', [])

                # GeoJSON uses [lon, lat] order (not [lat, lon]!)
                lon, lat = None, None
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]

                # Validate GPS bounds
                if lat is not None and (lat < -90 or lat > 90):
                    errors.append(f"Feature {idx}: Invalid latitude {lat}")
                    lat = None

                if lon is not None and (lon < -180 or lon > 180):
                    errors.append(f"Feature {idx}: Invalid longitude {lon}")
                    lon = None

                # Extract properties
                props = feature.get('properties', {})
                name = props.get('name') or props.get('title') or ''

                if not name:
                    errors.append(f"Feature {idx}: Missing 'name' property")
                    continue

                # Extract state
                state_raw = props.get('state') or props.get('State') or ''
                state = normalize_state(state_raw) if state_raw else None

                # Create location dict
                location = {
                    'name': name.strip(),
                    'lat': lat,
                    'lon': lon,
                    'state': state,
                    'type': props.get('type') or None,
                    'street_address': props.get('address') or props.get('street_address') or None,
                    'city': props.get('city') or None,
                    'zip_code': props.get('zip_code') or props.get('zip') or None,
                    'notes': props.get('notes') or props.get('description') or None,
                    'original_data': json.dumps(feature)
                }

                locations.append(location)

            except Exception as e:
                errors.append(f"Feature {idx}: Parsing error - {e}")

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
    except Exception as e:
        errors.append(f"GeoJSON parsing failed: {e}")

    return locations, errors


def parse_kml_map(file_content: bytes, is_kmz: bool = False) -> Tuple[List[Dict], List[str]]:
    """
    Parse KML or KMZ map file.

    Supports:
    - KML (Keyhole Markup Language) XML format
    - KMZ (compressed KML in ZIP format)

    Extracts Placemarks with coordinates and metadata.

    Args:
        file_content: File content as bytes (KML XML or KMZ ZIP)
        is_kmz: True if file is KMZ (ZIP compressed), False for KML

    Returns:
        Tuple of (locations list, errors list)
    """
    locations = []
    errors = []

    try:
        # If KMZ, extract KML from ZIP
        if is_kmz:
            try:
                zip_buffer = BytesIO(file_content)
                with zipfile.ZipFile(zip_buffer, 'r') as kmz:
                    # KMZ files typically contain doc.kml
                    kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
                    if not kml_files:
                        errors.append("KMZ file contains no .kml files")
                        return locations, errors

                    # Use the first KML file found (usually doc.kml)
                    kml_content = kmz.read(kml_files[0])
            except zipfile.BadZipFile:
                errors.append("Invalid KMZ file: not a valid ZIP archive")
                return locations, errors
        else:
            kml_content = file_content

        # Parse KML XML
        try:
            root = ET.fromstring(kml_content)
        except ET.ParseError as e:
            errors.append(f"Invalid KML XML: {e}")
            return locations, errors

        # KML uses namespaces, need to handle both with and without namespace
        # Common KML namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        # Find all Placemarks (with or without namespace)
        placemarks = root.findall('.//kml:Placemark', ns)
        if not placemarks:
            # Try without namespace
            placemarks = root.findall('.//Placemark')

        if not placemarks:
            errors.append("No Placemarks found in KML file")
            return locations, errors

        for idx, placemark in enumerate(placemarks):
            try:
                # Extract name
                name_elem = placemark.find('.//kml:name', ns)
                if name_elem is None:
                    name_elem = placemark.find('.//name')

                name = name_elem.text.strip() if name_elem is not None and name_elem.text else None
                if not name:
                    errors.append(f"Placemark {idx}: Missing name")
                    continue

                # Extract coordinates from Point
                point = placemark.find('.//kml:Point/kml:coordinates', ns)
                if point is None:
                    point = placemark.find('.//Point/coordinates')

                lat, lon = None, None
                if point is not None and point.text:
                    # KML coordinates format: "lon,lat,altitude" or "lon,lat"
                    coords_text = point.text.strip()
                    coords_parts = coords_text.split(',')
                    if len(coords_parts) >= 2:
                        try:
                            lon = float(coords_parts[0])
                            lat = float(coords_parts[1])

                            # Validate GPS bounds
                            if lat < -90 or lat > 90:
                                errors.append(f"Placemark {idx} ({name}): Invalid latitude {lat}")
                                lat = None
                            if lon < -180 or lon > 180:
                                errors.append(f"Placemark {idx} ({name}): Invalid longitude {lon}")
                                lon = None
                        except (ValueError, IndexError):
                            errors.append(f"Placemark {idx} ({name}): Invalid coordinates format")

                # Extract description
                desc_elem = placemark.find('.//kml:description', ns)
                if desc_elem is None:
                    desc_elem = placemark.find('.//description')
                description = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else None

                # Extract ExtendedData if available
                extended_data = {}
                extended = placemark.find('.//kml:ExtendedData', ns)
                if extended is None:
                    extended = placemark.find('.//ExtendedData')

                if extended is not None:
                    for data_elem in extended.findall('.//kml:Data', ns):
                        data_name = data_elem.get('name')
                        value_elem = data_elem.find('.//kml:value', ns)
                        if data_name and value_elem is not None and value_elem.text:
                            extended_data[data_name.lower()] = value_elem.text.strip()

                    # Try without namespace too
                    if not extended_data:
                        for data_elem in extended.findall('.//Data'):
                            data_name = data_elem.get('name')
                            value_elem = data_elem.find('.//value')
                            if data_name and value_elem is not None and value_elem.text:
                                extended_data[data_name.lower()] = value_elem.text.strip()

                # Extract metadata from extended data or description
                state_raw = extended_data.get('state') or None
                state = normalize_state(state_raw) if state_raw else None

                location = {
                    'name': name,
                    'lat': lat,
                    'lon': lon,
                    'state': state,
                    'type': extended_data.get('type'),
                    'street_address': extended_data.get('address') or extended_data.get('street_address'),
                    'city': extended_data.get('city'),
                    'zip_code': extended_data.get('zip_code') or extended_data.get('zip'),
                    'notes': description,
                    'original_data': ET.tostring(placemark, encoding='unicode')
                }

                locations.append(location)

            except Exception as e:
                errors.append(f"Placemark {idx}: Parsing error - {e}")

    except Exception as e:
        errors.append(f"KML parsing failed: {e}")

    return locations, errors


def find_duplicates(
    cursor: sqlite3.Cursor,
    location: Dict,
    gps_threshold_meters: float = 50.0
) -> List[Dict]:
    """
    Find potential duplicate locations in database.

    Checks:
    1. Exact name match in same state
    2. GPS proximity (within threshold) + similar name

    Args:
        cursor: Database cursor
        location: Location dict to check
        gps_threshold_meters: GPS distance threshold

    Returns:
        List of potential duplicate location dicts
    """
    duplicates = []

    name = location.get('name')
    state = location.get('state')
    lat = location.get('lat')
    lon = location.get('lon')

    # Query 1: Exact name match in same state
    if name and state:
        cursor.execute(
            """
            SELECT loc_uuid, loc_name, state, lat, lon, type, street_address
            FROM locations
            WHERE loc_name = ? AND state = ?
            LIMIT 10
            """,
            (name, state)
        )
        for row in cursor.fetchall():
            duplicates.append({
                'loc_uuid': row[0],
                'loc_name': row[1],
                'state': row[2],
                'lat': row[3],
                'lon': row[4],
                'type': row[5],
                'street_address': row[6],
                'match_type': 'exact_name',
                'confidence': 1.0
            })

    # Query 2: GPS proximity search (if we have coordinates)
    if lat is not None and lon is not None:
        # Rough bounding box (1 degree ≈ 111km)
        lat_delta = gps_threshold_meters / 111000
        lon_delta = gps_threshold_meters / (111000 * math.cos(math.radians(lat)))

        cursor.execute(
            """
            SELECT loc_uuid, loc_name, state, lat, lon, type, street_address
            FROM locations
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
              AND lat IS NOT NULL
              AND lon IS NOT NULL
            LIMIT 50
            """,
            (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta)
        )

        for row in cursor.fetchall():
            loc_uuid, loc_name, loc_state, loc_lat, loc_lon = row[0:5]

            # Calculate exact distance
            distance = calculate_distance_meters(lat, lon, loc_lat, loc_lon)

            if distance <= gps_threshold_meters:
                # Check if name is similar
                name_similar = fuzzy_match_names(name, loc_name) if name else False

                # Skip if already found as exact name match
                if any(d['loc_uuid'] == loc_uuid for d in duplicates):
                    continue

                duplicates.append({
                    'loc_uuid': row[0],
                    'loc_name': row[1],
                    'state': row[2],
                    'lat': row[3],
                    'lon': row[4],
                    'type': row[5],
                    'street_address': row[6],
                    'match_type': 'gps_proximity',
                    'distance_meters': round(distance, 1),
                    'name_similar': name_similar,
                    'confidence': 0.8 if name_similar else 0.5
                })

    return duplicates


def generate_short_uuid() -> str:
    """Generate 8-character UUID for records."""
    return str(uuid.uuid4())[:8]


def import_locations_to_db(
    cursor: sqlite3.Cursor,
    locations: List[Dict],
    map_id: str,
    import_mode: str = 'full',
    skip_duplicates: bool = True
) -> Dict:
    """
    Import locations into database.

    IMPORTANT: This function does NOT manage transactions. The caller MUST:
    1. Call conn.execute("BEGIN") before calling this function
    2. Call conn.commit() after this function returns successfully
    3. Call conn.rollback() if this function raises an exception

    Args:
        cursor: Database cursor (from connection with active transaction)
        locations: List of location dicts
        map_id: Map import ID
        import_mode: 'full' (import to locations) or 'reference' (import to map_locations)
        skip_duplicates: If True, skip exact duplicates

    Returns:
        Import statistics dict
    """
    stats = {
        'total': len(locations),
        'imported': 0,
        'skipped': 0,
        'duplicates': 0,
        'errors': []
    }

    timestamp = datetime.utcnow().isoformat() + 'Z'

    for location in locations:
        try:
            # Check for duplicates
            if skip_duplicates:
                dupes = find_duplicates(cursor, location)
                if any(d['match_type'] == 'exact_name' for d in dupes):
                    stats['duplicates'] += 1
                    stats['skipped'] += 1
                    continue

            if import_mode == 'full':
                # Import to main locations table
                loc_uuid = generate_short_uuid()

                cursor.execute(
                    """
                    INSERT INTO locations (
                        loc_uuid, loc_name, state, type,
                        lat, lon, gps_source, gps_confidence,
                        street_address, city, zip_code,
                        loc_add, loc_update, source_map_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        loc_uuid,
                        location['name'],
                        location.get('state'),
                        location.get('type'),
                        location.get('lat'),
                        location.get('lon'),
                        'imported' if location.get('lat') else None,
                        0.6 if location.get('lat') else None,  # Medium confidence for imported GPS
                        location.get('street_address'),
                        location.get('city'),
                        location.get('zip_code'),
                        timestamp,
                        timestamp,
                        map_id
                    )
                )

            else:  # reference mode
                # Import to map_locations table
                map_loc_id = generate_short_uuid()

                cursor.execute(
                    """
                    INSERT INTO map_locations (
                        map_loc_id, map_id, name, state, state_abbrev, type,
                        lat, lon, street_address, city, zip_code,
                        notes, original_data, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        map_loc_id,
                        map_id,
                        location['name'],
                        location.get('state'),
                        location.get('state'),  # state_abbrev same as state for now
                        location.get('type'),
                        location.get('lat'),
                        location.get('lon'),
                        location.get('street_address'),
                        location.get('city'),
                        location.get('zip_code'),
                        location.get('notes'),
                        location.get('original_data'),
                        timestamp
                    )
                )

            stats['imported'] += 1

        except Exception as e:
            stats['errors'].append(f"Failed to import '{location.get('name')}': {e}")
            stats['skipped'] += 1

    return stats


def search_reference_maps(
    cursor: sqlite3.Cursor,
    query_name: str,
    query_state: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search reference maps for location matches.

    Args:
        cursor: Database cursor
        query_name: Location name to search for
        query_state: Optional state filter
        limit: Maximum results to return

    Returns:
        List of matching locations from reference maps
    """
    matches = []

    # Search map_locations table
    if query_state:
        cursor.execute(
            """
            SELECT map_loc_id, map_id, name, state, type,
                   lat, lon, street_address, city, zip_code
            FROM map_locations
            WHERE state_abbrev = ?
            ORDER BY name
            LIMIT 100
            """,
            (query_state,)
        )
    else:
        cursor.execute(
            """
            SELECT map_loc_id, map_id, name, state, type,
                   lat, lon, street_address, city, zip_code
            FROM map_locations
            ORDER BY name
            LIMIT 100
            """
        )

    # Fuzzy match against query
    for row in cursor.fetchall():
        if fuzzy_match_names(query_name, row[2]):
            matches.append({
                'map_loc_id': row[0],
                'map_id': row[1],
                'name': row[2],
                'state': row[3],
                'type': row[4],
                'lat': row[5],
                'lon': row[6],
                'street_address': row[7],
                'city': row[8],
                'zip_code': row[9],
                'match_score': 1.0 - (levenshtein_distance(query_name.lower(), row[2].lower()) / max(len(query_name), len(row[2])))
            })

    # Sort by match score and return top results
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches[:limit]
