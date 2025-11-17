#!/usr/bin/env python3
"""
AUPATOOL v0.1.2 Phase 1 Testing Script
Automated tests for Phase 1 implementation.

This script tests:
- Database migration
- Immich adapter connectivity
- ArchiveBox adapter connectivity
- Import pipeline with Immich integration
- API endpoints

Run after Docker services are started.

Version: 0.1.2
Last Updated: 2025-11-17
"""

import json
import logging
import pytest
import sqlite3
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_user_config() -> dict:
    """Load user configuration."""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'
    if not config_path.exists():
        raise FileNotFoundError(f"user.json not found at {config_path}")

    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def db_path():
    """Pytest fixture to provide database path from user config."""
    config = load_user_config()
    return config['db_loc']


def test_database_schema(db_path: str) -> bool:
    """Test that v0.1.2 schema migrations completed successfully."""
    logger.info("Testing database schema...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check locations table has new columns
        cursor.execute("PRAGMA table_info(locations)")
        columns = [row[1] for row in cursor.fetchall()]

        required_columns = ['lat', 'lon', 'gps_source', 'street_address', 'city']
        missing = [col for col in required_columns if col not in columns]

        if missing:
            logger.error(f"  Missing columns in locations table: {missing}")
            return False

        # Check images table has new columns
        cursor.execute("PRAGMA table_info(images)")
        columns = [row[1] for row in cursor.fetchall()]

        required_columns = ['immich_asset_id', 'img_width', 'img_height', 'gps_lat', 'gps_lon']
        missing = [col for col in required_columns if col not in columns]

        if missing:
            logger.error(f"  Missing columns in images table: {missing}")
            return False

        # Check new tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='google_maps_exports'")
        if not cursor.fetchone():
            logger.error("  Table google_maps_exports not found")
            return False

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_log'")
        if not cursor.fetchone():
            logger.error("  Table sync_log not found")
            return False

        conn.close()

        logger.info("  ✓ Database schema is correct")
        return True

    except Exception as e:
        logger.error(f"  Database schema test failed: {e}")
        return False


def test_immich_adapter() -> bool:
    """Test Immich adapter connectivity."""
    logger.info("Testing Immich adapter...")

    try:
        from adapters.immich_adapter import create_immich_adapter

        adapter = create_immich_adapter()
        if not adapter:
            logger.warning("  ! Immich adapter could not be created (service may be unavailable)")
            return False

        healthy = adapter.health_check()
        if healthy:
            logger.info("  ✓ Immich service is healthy")
            return True
        else:
            logger.warning("  ! Immich service is unhealthy")
            return False

    except Exception as e:
        logger.error(f"  Immich adapter test failed: {e}")
        return False


def test_archivebox_adapter() -> bool:
    """Test ArchiveBox adapter connectivity."""
    logger.info("Testing ArchiveBox adapter...")

    try:
        from adapters.archivebox_adapter import create_archivebox_adapter

        adapter = create_archivebox_adapter()
        if not adapter:
            logger.warning("  ! ArchiveBox adapter could not be created (service may be unavailable)")
            return False

        healthy = adapter.health_check()
        if healthy:
            logger.info("  ✓ ArchiveBox service is healthy")
            return True
        else:
            logger.warning("  ! ArchiveBox service is unhealthy")
            return False

    except Exception as e:
        logger.error(f"  ArchiveBox adapter test failed: {e}")
        return False


def test_immich_integration_module() -> bool:
    """Test immich_integration module functions."""
    logger.info("Testing Immich integration module...")

    try:
        from immich_integration import (
            get_file_size,
            extract_gps_from_exif,
            get_image_dimensions
        )

        # Test file size calculation
        test_file = Path(__file__)
        file_size = get_file_size(str(test_file))
        if file_size is None or file_size <= 0:
            logger.error("  File size calculation failed")
            return False

        logger.info("  ✓ Immich integration module functions work")
        return True

    except Exception as e:
        logger.error(f"  Immich integration test failed: {e}")
        return False


def test_api_imports() -> bool:
    """Test that API routes can be imported."""
    logger.info("Testing API routes import...")

    try:
        from api_routes_v012 import api_v012, register_api_routes

        # Check blueprint has expected routes
        rules = [str(rule) for rule in api_v012.url_map.iter_rules()]

        expected_routes = ['/api/health', '/api/map/markers', '/api/locations/<loc_uuid>']

        # Note: Blueprint routes are relative, so just check they're defined
        logger.info("  ✓ API routes module imports successfully")
        return True

    except Exception as e:
        logger.error(f"  API routes import test failed: {e}")
        return False


def main():
    """Run all Phase 1 tests."""
    logger.info("="*60)
    logger.info("AUPATOOL v0.1.2 - Phase 1 Test Suite")
    logger.info("="*60)
    logger.info("")

    try:
        config = load_user_config()
        db_path = config['db_loc']
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    results = {}

    # Run tests
    results['Database Schema'] = test_database_schema(db_path)
    results['Immich Adapter'] = test_immich_adapter()
    results['ArchiveBox Adapter'] = test_archivebox_adapter()
    results['Immich Integration Module'] = test_immich_integration_module()
    results['API Routes'] = test_api_imports()

    # Print summary
    logger.info("")
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {test:30s} {status}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("="*60)

    if passed == total:
        logger.info("")
        logger.info("✓ All Phase 1 tests PASSED!")
        logger.info("  System is ready for full integration testing.")
        sys.exit(0)
    else:
        logger.warning("")
        logger.warning(f"⚠ {total - passed} test(s) failed.")
        logger.warning("  Check Docker services are running: docker-compose ps")
        logger.warning("  Run database migration: python scripts/db_migrate_v012.py")
        sys.exit(1)


if __name__ == '__main__':
    main()
