"""
Unit tests for immich_integration.py

Tests:
- GPS extraction from EXIF
- Image dimension extraction
- Video metadata extraction
- File size calculation
- Media processing pipeline
- Location GPS update logic
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from immich_integration import (
    get_file_size,
    extract_gps_from_exif,
    get_image_dimensions,
    get_video_dimensions,
    _parse_gps_coordinate,
    process_media_for_immich,
    update_location_gps,
    upload_to_immich
)


def test_get_file_size(tmp_path):
    """Test file size calculation."""
    test_file = tmp_path / "test.txt"
    test_data = b"A" * 1024  # 1KB
    test_file.write_bytes(test_data)

    size = get_file_size(str(test_file))

    assert size == 1024


def test_get_file_size_nonexistent():
    """Test file size returns None for missing files."""
    size = get_file_size('/nonexistent/file.txt')

    assert size is None


def test_parse_gps_coordinate_dms_format():
    """Test GPS coordinate parsing from degrees/minutes/seconds."""
    # Test North latitude
    lat = _parse_gps_coordinate("42 deg 45' 23.4\" N")
    assert lat is not None
    assert abs(lat - 42.7565) < 0.001  # 42.7565 degrees

    # Test South latitude (negative)
    lat = _parse_gps_coordinate("42 deg 45' 23.4\" S")
    assert lat is not None
    assert abs(lat + 42.7565) < 0.001  # -42.7565 degrees

    # Test East longitude
    lon = _parse_gps_coordinate("73 deg 56' 18.6\" E")
    assert lon is not None
    assert abs(lon - 73.9385) < 0.001

    # Test West longitude (negative)
    lon = _parse_gps_coordinate("73 deg 56' 18.6\" W")
    assert lon is not None
    assert abs(lon + 73.9385) < 0.001


def test_parse_gps_coordinate_decimal():
    """Test GPS coordinate parsing from decimal format."""
    lat = _parse_gps_coordinate("42.7565")
    assert lat is not None
    assert abs(lat - 42.7565) < 0.001


def test_parse_gps_coordinate_invalid():
    """Test GPS coordinate parsing handles invalid input."""
    assert _parse_gps_coordinate("invalid") is None
    assert _parse_gps_coordinate("") is None
    assert _parse_gps_coordinate(None) is None


@patch('subprocess.run')
def test_extract_gps_from_exif_success(mock_run):
    """Test GPS extraction from EXIF data."""
    # Mock exiftool output
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '[{"GPSLatitude": 42.7565, "GPSLongitude": -73.9385}]'
    mock_run.return_value = mock_result

    gps = extract_gps_from_exif('/path/to/image.jpg')

    assert gps is not None
    assert abs(gps[0] - 42.7565) < 0.001
    assert abs(gps[1] + 73.9385) < 0.001


@patch('subprocess.run')
def test_extract_gps_from_exif_no_gps(mock_run):
    """Test GPS extraction when no GPS data present."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '[{}]'
    mock_run.return_value = mock_result

    gps = extract_gps_from_exif('/path/to/image.jpg')

    assert gps is None


@patch('subprocess.run')
def test_extract_gps_from_exif_timeout(mock_run):
    """Test GPS extraction handles timeout."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired('exiftool', 10)

    gps = extract_gps_from_exif('/path/to/image.jpg')

    assert gps is None


@patch('PIL.Image.open')
def test_get_image_dimensions(mock_open):
    """Test image dimension extraction."""
    mock_img = MagicMock()
    mock_img.size = (6000, 4000)
    mock_open.return_value.__enter__.return_value = mock_img

    dims = get_image_dimensions('/path/to/image.jpg')

    assert dims == (6000, 4000)


@patch('PIL.Image.open')
def test_get_image_dimensions_error(mock_open):
    """Test image dimension extraction handles errors."""
    mock_open.side_effect = Exception("Cannot read image")

    dims = get_image_dimensions('/path/to/corrupt.jpg')

    assert dims is None


@patch('subprocess.run')
def test_get_video_dimensions(mock_run):
    """Test video dimension and duration extraction."""
    # Mock ffprobe output
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '''{
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "duration": "45.5"
            }
        ],
        "format": {
            "duration": "45.5"
        }
    }'''
    mock_run.return_value = mock_result

    info = get_video_dimensions('/path/to/video.mp4')

    assert info is not None
    assert info[0] == 1920
    assert info[1] == 1080
    assert abs(info[2] - 45.5) < 0.1


@patch('subprocess.run')
def test_get_video_dimensions_no_video_stream(mock_run):
    """Test video dimension extraction when no video stream present."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"streams": [], "format": {}}'
    mock_run.return_value = mock_result

    info = get_video_dimensions('/path/to/audio.mp3')

    assert info is None


@patch('subprocess.run')
def test_get_video_dimensions_timeout(mock_run):
    """Test video dimension extraction handles timeout."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 30)

    info = get_video_dimensions('/path/to/video.mp4')

    assert info is None


@patch('immich_integration.upload_to_immich')
@patch('immich_integration.extract_gps_from_exif')
@patch('immich_integration.get_image_dimensions')
@patch('immich_integration.get_file_size')
def test_process_media_for_immich_image(
    mock_file_size,
    mock_dims,
    mock_gps,
    mock_upload
):
    """Test complete media processing for image."""
    # Setup mocks
    mock_upload.return_value = 'asset-123'
    mock_gps.return_value = (42.7565, -73.9385)
    mock_dims.return_value = (6000, 4000)
    mock_file_size.return_value = 15728640

    result = process_media_for_immich('/path/to/image.jpg', 'image')

    assert result['immich_asset_id'] == 'asset-123'
    assert result['gps_lat'] == 42.7565
    assert result['gps_lon'] == -73.9385
    assert result['width'] == 6000
    assert result['height'] == 4000
    assert result['file_size'] == 15728640
    assert result['duration'] is None


@patch('immich_integration.upload_to_immich')
@patch('immich_integration.extract_gps_from_exif')
@patch('immich_integration.get_video_dimensions')
@patch('immich_integration.get_file_size')
def test_process_media_for_immich_video(
    mock_file_size,
    mock_video_info,
    mock_gps,
    mock_upload
):
    """Test complete media processing for video."""
    mock_upload.return_value = 'asset-456'
    mock_gps.return_value = (42.7565, -73.9385)
    mock_video_info.return_value = (1920, 1080, 45.5)
    mock_file_size.return_value = 104857600

    result = process_media_for_immich('/path/to/video.mp4', 'video')

    assert result['immich_asset_id'] == 'asset-456'
    assert result['gps_lat'] == 42.7565
    assert result['gps_lon'] == -73.9385
    assert result['width'] == 1920
    assert result['height'] == 1080
    assert result['duration'] == 45.5
    assert result['file_size'] == 104857600


@patch('immich_integration.upload_to_immich')
def test_process_media_graceful_degradation(mock_upload):
    """Test media processing handles service unavailability."""
    mock_upload.return_value = None  # Immich unavailable

    result = process_media_for_immich('/path/to/image.jpg', 'image')

    assert result['immich_asset_id'] is None
    # Other fields should still be extracted
    assert 'file_size' in result


def test_update_location_gps():
    """Test location GPS update logic."""
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create locations table
    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT,
            lat REAL,
            lon REAL,
            gps_source TEXT
        )
    """)

    # Insert location without GPS
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name)
        VALUES ('loc-1', 'Test Location')
    """)
    conn.commit()

    # Update GPS
    updated = update_location_gps(cursor, 'loc-1', 42.7565, -73.9385)

    assert updated is True

    # Verify GPS was set
    cursor.execute("SELECT lat, lon, gps_source FROM locations WHERE loc_uuid = 'loc-1'")
    row = cursor.fetchone()

    assert abs(row[0] - 42.7565) < 0.001
    assert abs(row[1] + 73.9385) < 0.001
    assert row[2] == 'exif'

    conn.close()


def test_update_location_gps_already_set():
    """Test location GPS update skips if already set."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT,
            lat REAL,
            lon REAL,
            gps_source TEXT
        )
    """)

    # Insert location with GPS already set
    cursor.execute("""
        INSERT INTO locations (loc_uuid, loc_name, lat, lon, gps_source)
        VALUES ('loc-1', 'Test Location', 40.0, -74.0, 'manual')
    """)
    conn.commit()

    # Try to update GPS
    updated = update_location_gps(cursor, 'loc-1', 42.7565, -73.9385)

    assert updated is False

    # Verify original GPS unchanged
    cursor.execute("SELECT lat, lon FROM locations WHERE loc_uuid = 'loc-1'")
    row = cursor.fetchone()

    assert abs(row[0] - 40.0) < 0.001
    assert abs(row[1] + 74.0) < 0.001

    conn.close()


def test_update_location_gps_nonexistent():
    """Test location GPS update handles non-existent location."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE locations (
            loc_uuid TEXT PRIMARY KEY,
            loc_name TEXT,
            lat REAL,
            lon REAL
        )
    """)

    updated = update_location_gps(cursor, 'nonexistent', 42.7565, -73.9385)

    assert updated is False

    conn.close()
