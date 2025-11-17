"""
ArchiveBox Web Archiving Adapter
Provides abstraction layer for ArchiveBox API calls.

This adapter handles:
- Archiving URLs
- Checking archive status
- Extracting media from archived pages
- Webhook handling for completion notifications

Version: 0.1.2
Last Updated: 2025-11-17
"""

import logging
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class ArchiveBoxError(Exception):
    """Base exception for ArchiveBox adapter errors."""
    pass


class ArchiveBoxConnectionError(ArchiveBoxError):
    """Raised when cannot connect to ArchiveBox service."""
    pass


class ArchiveBoxArchiveError(ArchiveBoxError):
    """Raised when archiving fails."""
    pass


class ArchiveBoxAdapter:
    """
    Adapter for ArchiveBox web archiving service.

    Provides methods to:
    - Archive URLs
    - Check archive status
    - Retrieve archived snapshots
    - Extract media from archives
    """

    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize ArchiveBox adapter.

        Args:
            base_url: Base URL of ArchiveBox server (e.g., http://localhost:8001)
            username: Username for authentication (optional)
            password: Password for authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # Set authentication if provided
        if username and password:
            self.session.auth = (username, password)

        logger.info(f"Initialized ArchiveBox adapter: {self.base_url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to ArchiveBox API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/add)
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            ArchiveBoxConnectionError: If cannot connect after retries
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to ArchiveBox at {url}: {e}")
            raise ArchiveBoxConnectionError(f"ArchiveBox service unavailable: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"ArchiveBox API error: {e}")
            raise ArchiveBoxError(f"ArchiveBox API error: {e}")

    def health_check(self) -> bool:
        """
        Check if ArchiveBox service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self._request('GET', '/health/')
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"ArchiveBox health check failed: {e}")
            return False

    def archive_url(
        self,
        url: str,
        depth: int = 0,
        extract: str = 'auto',
        overwrite: bool = False,
        tags: List[str] = None
    ) -> str:
        """
        Archive a URL.

        Args:
            url: URL to archive
            depth: Recursion depth for crawling (0 = single page)
            extract: Extraction methods ('auto', 'wget', 'media', etc.)
            overwrite: Whether to overwrite existing archive
            tags: List of tags to apply to archive

        Returns:
            Snapshot ID (timestamp) of archived URL

        Raises:
            ArchiveBoxArchiveError: If archiving fails
        """
        logger.info(f"Archiving URL: {url}")

        try:
            data = {
                'url': url,
                'depth': depth,
                'extract': extract,
                'overwrite': str(overwrite).lower(),
            }

            if tags:
                data['tags'] = ','.join(tags)

            response = self._request('POST', '/add/', json=data)
            result = response.json()

            snapshot_id = result.get('snapshot_id') or result.get('timestamp')

            if not snapshot_id:
                # Try alternative API structure
                snapshots = result.get('snapshots', [])
                if snapshots:
                    snapshot_id = snapshots[0].get('timestamp')

            if snapshot_id:
                logger.info(f"  Archive created: {snapshot_id}")
                return snapshot_id
            else:
                logger.warning(f"  No snapshot ID in response: {result}")
                return None

        except Exception as e:
            logger.error(f"Archiving failed for {url}: {e}")
            raise ArchiveBoxArchiveError(f"Archive failed: {e}")

    def get_snapshot(self, snapshot_id: str) -> Dict:
        """
        Get snapshot details.

        Args:
            snapshot_id: Snapshot ID (timestamp)

        Returns:
            Dictionary with snapshot metadata
        """
        try:
            response = self._request('GET', f'/api/snapshots/{snapshot_id}')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get snapshot {snapshot_id}: {e}")
            return {}

    def list_snapshots(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        List archived snapshots.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of snapshot dictionaries
        """
        try:
            params = {'limit': limit, 'offset': offset}
            response = self._request('GET', '/api/snapshots', params=params)
            return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []

    def get_archive_status(self, snapshot_id: str) -> str:
        """
        Get archive status.

        Args:
            snapshot_id: Snapshot ID (timestamp)

        Returns:
            Status string ('pending', 'succeeded', 'failed')
        """
        try:
            snapshot = self.get_snapshot(snapshot_id)
            status = snapshot.get('status', 'unknown')

            # Map ArchiveBox statuses to our simplified statuses
            if status in ['succeeded', 'completed']:
                return 'archived'
            elif status in ['failed', 'error']:
                return 'failed'
            else:
                return 'pending'

        except Exception as e:
            logger.error(f"Failed to get status for {snapshot_id}: {e}")
            return 'unknown'

    def get_extracted_media(self, snapshot_id: str) -> List[str]:
        """
        Get list of extracted media files from an archive.

        Args:
            snapshot_id: Snapshot ID (timestamp)

        Returns:
            List of file paths to extracted media
        """
        try:
            snapshot = self.get_snapshot(snapshot_id)

            # ArchiveBox stores extracted files in specific directories
            archive_path = snapshot.get('archive_path', '')

            if not archive_path:
                return []

            # Look for extracted media in common locations
            media_files = []

            # Check wget output directory
            wget_path = os.path.join(archive_path, 'wget')
            if os.path.exists(wget_path):
                media_files.extend(self._find_media_files(wget_path))

            # Check media extraction directory
            media_path = os.path.join(archive_path, 'media')
            if os.path.exists(media_path):
                media_files.extend(self._find_media_files(media_path))

            logger.info(f"Found {len(media_files)} media files in archive {snapshot_id}")
            return media_files

        except Exception as e:
            logger.error(f"Failed to get extracted media for {snapshot_id}: {e}")
            return []

    def get_snapshot_files(self, snapshot_id: str, archivebox_data_dir: str) -> List[Dict]:
        """
        Get media files from ArchiveBox snapshot directory (filesystem-based).

        This method works with ArchiveBox v0.7.3 which lacks REST API for media extraction.
        Directly scans the archive directory for extractable media files.

        Args:
            snapshot_id: ArchiveBox snapshot ID (timestamp)
            archivebox_data_dir: Path to ArchiveBox data directory (e.g., /data/archivebox)

        Returns:
            List of dictionaries with file metadata:
            [{
                'path': '/absolute/path/to/file.jpg',
                'filename': 'file.jpg',
                'type': 'image',  # or 'video'
                'size': 12345
            }]
        """
        snapshot_dir = Path(archivebox_data_dir) / 'archive' / snapshot_id

        if not snapshot_dir.exists():
            logger.warning(f"Snapshot directory not found: {snapshot_dir}")
            return []

        media_files = []

        try:
            # Scan for media files
            media_files.extend(self._scan_directory_for_media(snapshot_dir))

            logger.info(f"Found {len(media_files)} media files in snapshot {snapshot_id}")
            return media_files

        except Exception as e:
            logger.error(f"Error scanning snapshot {snapshot_id}: {e}")
            return []

    def _scan_directory_for_media(self, directory: Path) -> List[Dict]:
        """
        Scan directory for media files and return metadata.

        Args:
            directory: Path object to scan

        Returns:
            List of file metadata dictionaries
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic', '.heif'}
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}

        media_files = []

        try:
            for file_path in directory.rglob('*'):
                if not file_path.is_file():
                    continue

                ext = file_path.suffix.lower()

                # Determine file type
                file_type = None
                if ext in image_extensions:
                    file_type = 'image'
                elif ext in video_extensions:
                    file_type = 'video'

                if file_type:
                    media_files.append({
                        'path': str(file_path.absolute()),
                        'filename': file_path.name,
                        'type': file_type,
                        'size': file_path.stat().st_size
                    })

        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return media_files

    def _find_media_files(self, directory: str) -> List[str]:
        """
        Recursively find media files in a directory.

        Args:
            directory: Directory to search

        Returns:
            List of media file paths
        """
        media_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff',
            '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
            '.pdf'
        }

        media_files = []

        try:
            directory_path = Path(directory)

            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                    media_files.append(str(file_path))

        except Exception as e:
            logger.error(f"Error finding media files in {directory}: {e}")

        return media_files

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete an archived snapshot.

        Args:
            snapshot_id: Snapshot ID (timestamp)

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self._request('DELETE', f'/api/snapshots/{snapshot_id}')
            logger.info(f"Deleted snapshot: {snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            return False


def create_archivebox_adapter(
    url: str = None,
    username: str = None,
    password: str = None
) -> ArchiveBoxAdapter:
    """
    Factory function to create ArchiveBox adapter from environment or parameters.

    Args:
        url: ArchiveBox base URL (defaults to ARCHIVEBOX_URL env var or http://localhost:8001)
        username: Username (defaults to ARCHIVEBOX_USERNAME env var)
        password: Password (defaults to ARCHIVEBOX_PASSWORD env var)

    Returns:
        Configured ArchiveBoxAdapter instance
    """
    if url is None:
        url = os.environ.get('ARCHIVEBOX_URL', 'http://localhost:8001')

    if username is None:
        username = os.environ.get('ARCHIVEBOX_USERNAME')

    if password is None:
        password = os.environ.get('ARCHIVEBOX_PASSWORD')

    return ArchiveBoxAdapter(url, username, password)
