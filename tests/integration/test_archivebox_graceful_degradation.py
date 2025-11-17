"""
Integration Test: ArchiveBox Graceful Degradation

Tests that Phase B correctly handles ArchiveBox v0.7.3 which lacks REST API.
Verifies:
- URL is saved to database even when ArchiveBox fails
- Status remains 'pending' for manual/background retry
- HTTP response is 201 Created (not 500 Error)
- Error is logged but doesn't crash the system

This test runs against the actual Docker environment.
"""

import json
import requests
import sqlite3
import pytest

# Configuration (from Docker environment)
API_BASE_URL = "http://localhost:5001"
DB_PATH = "/Users/bryant/Documents/tools/aupat/data/aupat.db"


class TestArchiveBoxGracefulDegradation:
    """
    Integration tests for Phase B ArchiveBox integration.

    These tests verify the system handles ArchiveBox v0.7.3 API incompatibility
    gracefully without data loss or system failure.
    """

    def test_url_saved_despite_archivebox_failure(self):
        """
        Test that URL is saved to database even when ArchiveBox archiving fails.

        This is the critical "fail-safe" behavior of Phase B.
        """
        # Create test location
        test_loc_uuid = "test-integration-loc-001"

        # Verify location exists or create it
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT loc_uuid FROM locations WHERE loc_uuid = ?",
            (test_loc_uuid,)
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (test_loc_uuid, "Integration Test Location", "city", "NY", 42.0, -73.0, "2025-01-01", "2025-01-01")
            )
            conn.commit()
        conn.close()

        # Archive a URL
        response = requests.post(
            f"{API_BASE_URL}/api/locations/{test_loc_uuid}/urls",
            json={
                "url": "https://httpbin.org/get",
                "title": "Integration Test URL",
                "description": "Testing graceful degradation"
            },
            headers={"Content-Type": "application/json"}
        )

        # Verify HTTP response
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert data["url"] == "https://httpbin.org/get"
        assert data["url_title"] == "Integration Test URL"
        assert data["archive_status"] == "pending"  # Should be 'pending' due to ArchiveBox failure
        assert data["archivebox_snapshot_id"] is None  # No snapshot created

        # Verify database state
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url, archive_status, archivebox_snapshot_id FROM urls WHERE url_uuid = ?",
            (data["url_uuid"],)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "URL not found in database"
        assert row[0] == "https://httpbin.org/get"
        assert row[1] == "pending"
        assert row[2] is None

    def test_multiple_urls_independent_failures(self):
        """
        Test that multiple URLs can be archived independently.
        Each failure is isolated - one failure doesn't prevent others from being saved.
        """
        test_loc_uuid = "test-integration-loc-002"

        # Create location
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loc_uuid FROM locations WHERE loc_uuid = ?",
            (test_loc_uuid,)
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (test_loc_uuid, "Multi-URL Test Location", "city", "CA", 37.0, -122.0, "2025-01-01", "2025-01-01")
            )
            conn.commit()
        conn.close()

        # Archive multiple URLs
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml"
        ]

        url_uuids = []
        for url in urls:
            response = requests.post(
                f"{API_BASE_URL}/api/locations/{test_loc_uuid}/urls",
                json={"url": url},
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 201
            data = response.json()
            url_uuids.append(data["url_uuid"])

        # Verify all URLs saved
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE url_uuid IN ({})".format(','.join('?' * len(url_uuids))),
            url_uuids
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3, f"Expected 3 URLs saved, got {count}"

    def test_invalid_url_still_validated(self):
        """
        Test that invalid URLs are rejected BEFORE any archiving attempt.
        This ensures validation logic still works despite ArchiveBox issues.
        """
        test_loc_uuid = "test-integration-loc-003"

        # Create location
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loc_uuid FROM locations WHERE loc_uuid = ?",
            (test_loc_uuid,)
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (test_loc_uuid, "Validation Test Location", "park", "TX", 30.0, -97.0, "2025-01-01", "2025-01-01")
            )
            conn.commit()
        conn.close()

        # Try to archive without URL
        response = requests.post(
            f"{API_BASE_URL}/api/locations/{test_loc_uuid}/urls",
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "url is required" in data["error"]

    def test_system_stability_under_repeated_failures(self):
        """
        Test that system remains stable when ArchiveBox consistently fails.
        Simulates production scenario where ArchiveBox is misconfigured.
        """
        test_loc_uuid = "test-integration-loc-004"

        # Create location
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loc_uuid FROM locations WHERE loc_uuid = ?",
            (test_loc_uuid,)
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO locations (loc_uuid, loc_name, type, state, lat, lon, loc_add, loc_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (test_loc_uuid, "Stability Test Location", "museum", "MA", 42.0, -71.0, "2025-01-01", "2025-01-01")
            )
            conn.commit()
        conn.close()

        # Archive 10 URLs rapidly
        for i in range(10):
            response = requests.post(
                f"{API_BASE_URL}/api/locations/{test_loc_uuid}/urls",
                json={"url": f"https://httpbin.org/delay/{i}"},
                headers={"Content-Type": "application/json"}
            )
            # System should remain stable
            assert response.status_code == 201, f"Request {i} failed with {response.status_code}"

        # Verify all 10 URLs saved
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE loc_uuid = ?",
            (test_loc_uuid,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 10, f"Expected >=10 URLs, got {count}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
