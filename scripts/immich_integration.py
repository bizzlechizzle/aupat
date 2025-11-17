"""
Immich Integration Module for AUPAT Import Pipeline
Handles photo/video uploads to Immich during import process.

This module provides:
- Immich upload integration for import pipeline
- GPS extraction from EXIF data
- Image/video dimension extraction
- File size calculation
- Graceful degradation if Immich unavailable

Version: 0.1.2
Last Updated: 2025-11-17
"""

import logging
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Try to import PIL, but make it optional
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.warning("Pillow not available - image dimension extraction will be skipped")
    PIL_AVAILABLE = False

# Import Immich adapter
try:
    from adapters.immich_adapter import create_immich_adapter, ImmichError
    IMMICH_AVAILABLE = True
except ImportError:
    logger.warning("Immich adapter not available - imports will skip Immich upload")
    IMMICH_AVAILABLE = False


def get_immich_adapter():
    """
    Get configured Immich adapter instance.

    Returns:
        ImmichAdapter instance or None if unavailable
    """
    if not IMMICH_AVAILABLE:
        return None

    try:
        adapter = create_immich_adapter()

        # Test connectivity
        if not adapter.health_check():
            logger.warning("Immich service is not healthy - uploads will be skipped")
            return None

        return adapter
    except Exception as e:
        logger.warning(f"Failed to initialize Immich adapter: {e}")
        return None


def upload_to_immich(file_path: str, immich_adapter=None) -> Optional[str]:
    """
    Upload file to Immich and return asset ID.

    Args:
        file_path: Path to file to upload
        immich_adapter: ImmichAdapter instance (or None to auto-create)

    Returns:
        Asset ID (UUID) if successful, None otherwise
    """
    if immich_adapter is None:
        immich_adapter = get_immich_adapter()

    if immich_adapter is None:
        logger.debug(f"Skipping Immich upload (service unavailable): {Path(file_path).name}")
        return None

    try:
        asset_id = immich_adapter.upload(file_path)
        logger.info(f"Uploaded to Immich: {Path(file_path).name} -> {asset_id}")
        return asset_id
    except ImmichError as e:
        logger.warning(f"Immich upload failed for {Path(file_path).name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading to Immich: {e}")
        return None


def extract_gps_from_exif(file_path: str) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from image/video EXIF data.

    Args:
        file_path: Path to media file

    Returns:
        Tuple of (latitude, longitude) if found, None otherwise
    """
    try:
        # Use exiftool to extract GPS data
        result = subprocess.run(
            ['exiftool', '-json', '-GPSLatitude', '-GPSLongitude', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        if not data:
            return None

        exif = data[0]
        lat = exif.get('GPSLatitude')
        lon = exif.get('GPSLongitude')

        if lat is None or lon is None:
            return None

        # Convert from string format if needed
        if isinstance(lat, str):
            lat = _parse_gps_coordinate(lat)
        if isinstance(lon, str):
            lon = _parse_gps_coordinate(lon)

        if lat and lon:
            lat_float = float(lat)
            lon_float = float(lon)

            # Validate GPS coordinates are in valid range
            if not (-90.0 <= lat_float <= 90.0):
                logger.warning(f"Invalid latitude {lat_float} for {Path(file_path).name}")
                return None
            if not (-180.0 <= lon_float <= 180.0):
                logger.warning(f"Invalid longitude {lon_float} for {Path(file_path).name}")
                return None

            logger.debug(f"Extracted GPS: {lat_float}, {lon_float} from {Path(file_path).name}")
            return (lat_float, lon_float)

        return None

    except subprocess.TimeoutExpired:
        logger.warning(f"exiftool timed out for {file_path}")
        return None
    except Exception as e:
        logger.debug(f"GPS extraction failed for {Path(file_path).name}: {e}")
        return None


def _parse_gps_coordinate(coord_str: str) -> Optional[float]:
    """
    Parse GPS coordinate from exiftool string format.

    Args:
        coord_str: Coordinate string (e.g., "42 deg 45' 23.4\" N")

    Returns:
        Float coordinate or None if parsing fails
    """
    try:
        # Remove direction letters
        coord_str = coord_str.replace('N', '').replace('S', '').replace('E', '').replace('W', '').strip()

        # Parse degrees, minutes, seconds
        parts = coord_str.replace('deg', '').replace("'", '').replace('"', '').split()

        if len(parts) >= 3:
            deg = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])

            # Convert to decimal degrees
            decimal = deg + (minutes / 60.0) + (seconds / 3600.0)

            # Handle negative (South/West)
            if 'S' in coord_str or 'W' in coord_str:
                decimal = -decimal

            return decimal

        # Try direct float conversion
        return float(coord_str)

    except Exception as e:
        logger.debug(f"Failed to parse GPS coordinate '{coord_str}': {e}")
        return None


def get_image_dimensions(file_path: str) -> Optional[Tuple[int, int]]:
    """
    Get image dimensions (width, height).

    Args:
        file_path: Path to image file

    Returns:
        Tuple of (width, height) if successful, None otherwise
    """
    if not PIL_AVAILABLE:
        logger.debug("Pillow not available - cannot extract image dimensions")
        return None

    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception as e:
        logger.debug(f"Failed to get dimensions for {Path(file_path).name}: {e}")
        return None


def get_video_dimensions(file_path: str) -> Optional[Tuple[int, int, float]]:
    """
    Get video dimensions and duration using ffprobe.

    Args:
        file_path: Path to video file

    Returns:
        Tuple of (width, height, duration_seconds) if successful, None otherwise
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            return None

        width = video_stream.get('width')
        height = video_stream.get('height')

        # Get duration
        duration = None
        if 'format' in data:
            duration = data['format'].get('duration')
        if duration is None and 'duration' in video_stream:
            duration = video_stream.get('duration')

        if width and height:
            return (int(width), int(height), float(duration) if duration else None)

        return None

    except subprocess.TimeoutExpired:
        logger.warning(f"ffprobe timed out for {file_path}")
        return None
    except Exception as e:
        logger.debug(f"Failed to get video metadata for {Path(file_path).name}: {e}")
        return None


def get_file_size(file_path: str) -> Optional[int]:
    """
    Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes, or None if error
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.debug(f"Failed to get file size for {Path(file_path).name}: {e}")
        return None


def process_media_for_immich(
    file_path: str,
    file_type: str,
    immich_adapter=None
) -> Dict:
    """
    Process media file for Immich integration.

    This function:
    1. Uploads file to Immich (if available)
    2. Extracts GPS coordinates from EXIF
    3. Extracts dimensions (width, height)
    4. Calculates file size
    5. Extracts video duration (for videos)

    Args:
        file_path: Path to media file
        file_type: File type ('image' or 'video')
        immich_adapter: ImmichAdapter instance (optional)

    Returns:
        Dictionary with extracted metadata:
        {
            'immich_asset_id': str or None,
            'gps_lat': float or None,
            'gps_lon': float or None,
            'width': int or None,
            'height': int or None,
            'duration': float or None (videos only),
            'file_size': int or None
        }
    """
    result = {
        'immich_asset_id': None,
        'gps_lat': None,
        'gps_lon': None,
        'width': None,
        'height': None,
        'duration': None,
        'file_size': None
    }

    # Upload to Immich
    result['immich_asset_id'] = upload_to_immich(file_path, immich_adapter)

    # Extract GPS
    gps = extract_gps_from_exif(file_path)
    if gps:
        result['gps_lat'], result['gps_lon'] = gps

    # Extract dimensions
    if file_type == 'image':
        dims = get_image_dimensions(file_path)
        if dims:
            result['width'], result['height'] = dims
    elif file_type == 'video':
        video_info = get_video_dimensions(file_path)
        if video_info:
            result['width'], result['height'], result['duration'] = video_info

    # Get file size
    result['file_size'] = get_file_size(file_path)

    return result


def update_location_gps(cursor, loc_uuid: str, gps_lat: float, gps_lon: float) -> bool:
    """
    Update location GPS coordinates if not already set.

    Args:
        cursor: SQLite cursor
        loc_uuid: Location UUID
        gps_lat: Latitude
        gps_lon: Longitude

    Returns:
        True if updated, False if location already has GPS or update failed
    """
    try:
        # Check if location already has GPS
        cursor.execute(
            "SELECT lat, lon FROM locations WHERE loc_uuid = ?",
            (loc_uuid,)
        )
        row = cursor.fetchone()

        if not row:
            logger.warning(f"Location {loc_uuid} not found in database")
            return False

        existing_lat, existing_lon = row

        # Only update if GPS not already set
        if existing_lat is None or existing_lon is None:
            cursor.execute(
                """
                UPDATE locations
                SET lat = ?, lon = ?, gps_source = 'exif'
                WHERE loc_uuid = ?
                """,
                (gps_lat, gps_lon, loc_uuid)
            )
            logger.info(f"Updated location GPS: {loc_uuid} -> ({gps_lat}, {gps_lon})")
            return True
        else:
            logger.debug(f"Location {loc_uuid} already has GPS coordinates")
            return False

    except Exception as e:
        logger.error(f"Failed to update location GPS: {e}")
        return False
