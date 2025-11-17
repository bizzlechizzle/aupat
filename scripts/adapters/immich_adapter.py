"""
Immich Photo Storage Adapter
Provides abstraction layer for Immich API calls.

This adapter handles:
- Photo/video uploads to Immich
- Thumbnail URL generation
- Original file URL generation
- Asset metadata retrieval
- Error handling and retries

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


class ImmichError(Exception):
    """Base exception for Immich adapter errors."""
    pass


class ImmichConnectionError(ImmichError):
    """Raised when cannot connect to Immich service."""
    pass


class ImmichUploadError(ImmichError):
    """Raised when photo upload fails."""
    pass


class ImmichAdapter:
    """
    Adapter for Immich photo storage service.

    Provides methods to:
    - Upload photos and videos
    - Generate thumbnail URLs
    - Retrieve asset metadata
    - Handle API authentication
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize Immich adapter.

        Args:
            base_url: Base URL of Immich server (e.g., http://localhost:2283)
            api_key: API key for authentication (optional for local deployments)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # Set headers
        if api_key:
            self.session.headers.update({
                'x-api-key': api_key
            })

        logger.info(f"Initialized Immich adapter: {self.base_url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to Immich API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /api/asset)
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            ImmichConnectionError: If cannot connect after retries
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Immich at {url}: {e}")
            raise ImmichConnectionError(f"Immich service unavailable: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Immich API error: {e}")
            raise ImmichError(f"Immich API error: {e}")

    def health_check(self) -> bool:
        """
        Check if Immich service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self._request('GET', '/api/server/ping')
            return response.json().get('res') == 'pong'
        except Exception as e:
            logger.warning(f"Immich health check failed: {e}")
            return False

    def upload(self, file_path: str, device_id: str = 'aupat') -> str:
        """
        Upload photo or video to Immich.

        Args:
            file_path: Path to file to upload
            device_id: Device identifier (default: 'aupat')

        Returns:
            Asset ID (UUID) of uploaded file

        Raises:
            ImmichUploadError: If upload fails
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Uploading to Immich: {file_path.name}")

        try:
            with open(file_path, 'rb') as f:
                files = {
                    'assetData': (file_path.name, f, self._get_mime_type(file_path))
                }

                data = {
                    'deviceAssetId': f"{file_path.stem}-{file_path.stat().st_mtime}",
                    'deviceId': device_id,
                    'fileCreatedAt': self._get_file_created_at(file_path),
                    'fileModifiedAt': self._get_file_modified_at(file_path),
                    'isFavorite': 'false'
                }

                response = self._request('POST', '/api/asset/upload', files=files, data=data)

            result = response.json()

            if result.get('duplicate'):
                logger.info(f"  Duplicate detected, using existing asset: {result.get('id')}")
            else:
                logger.info(f"  Upload successful: {result.get('id')}")

            return result.get('id')

        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            raise ImmichUploadError(f"Upload failed: {e}")

    def get_thumbnail_url(self, asset_id: str, size: str = 'preview') -> str:
        """
        Get thumbnail URL for an asset.

        Args:
            asset_id: Asset ID (UUID)
            size: Thumbnail size ('preview' or 'thumbnail')

        Returns:
            URL to thumbnail
        """
        return f"{self.base_url}/api/asset/thumbnail/{asset_id}?size={size}"

    def get_original_url(self, asset_id: str) -> str:
        """
        Get original file URL for an asset.

        Args:
            asset_id: Asset ID (UUID)

        Returns:
            URL to original file
        """
        return f"{self.base_url}/api/asset/file/{asset_id}"

    def get_asset_info(self, asset_id: str) -> Dict:
        """
        Get detailed asset information.

        Args:
            asset_id: Asset ID (UUID)

        Returns:
            Dictionary with asset metadata
        """
        try:
            response = self._request('GET', f'/api/asset/assetById/{asset_id}')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get asset info for {asset_id}: {e}")
            return {}

    def search_assets(self, query: str = None, limit: int = 100) -> List[Dict]:
        """
        Search assets by text query.

        Args:
            query: Search query (tags, filename, etc.)
            limit: Maximum number of results

        Returns:
            List of asset dictionaries
        """
        try:
            params = {'q': query} if query else {}
            params['take'] = limit

            response = self._request('GET', '/api/search', params=params)
            return response.json().get('assets', {}).get('items', [])
        except Exception as e:
            logger.error(f"Asset search failed: {e}")
            return []

    def _get_mime_type(self, file_path: Path) -> str:
        """Determine MIME type from file extension."""
        ext = file_path.suffix.lower()

        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.bmp': 'image/bmp',
            '.heic': 'image/heic',
            '.heif': 'image/heif',
            '.dng': 'image/x-adobe-dng',
            '.nef': 'image/x-nikon-nef',
            '.cr2': 'image/x-canon-cr2',
            '.arw': 'image/x-sony-arw',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
        }

        return mime_types.get(ext, 'application/octet-stream')

    def _get_file_created_at(self, file_path: Path) -> str:
        """Get file creation timestamp in ISO format."""
        from datetime import datetime
        stat = file_path.stat()
        timestamp = datetime.fromtimestamp(stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime)
        return timestamp.isoformat()

    def _get_file_modified_at(self, file_path: Path) -> str:
        """Get file modification timestamp in ISO format."""
        from datetime import datetime
        stat = file_path.stat()
        timestamp = datetime.fromtimestamp(stat.st_mtime)
        return timestamp.isoformat()


def create_immich_adapter(url: str = None, api_key: str = None) -> ImmichAdapter:
    """
    Factory function to create Immich adapter from environment or parameters.

    Args:
        url: Immich base URL (defaults to IMMICH_URL env var or http://localhost:2283)
        api_key: API key (defaults to IMMICH_API_KEY env var)

    Returns:
        Configured ImmichAdapter instance
    """
    if url is None:
        url = os.environ.get('IMMICH_URL', 'http://localhost:2283')

    if api_key is None:
        api_key = os.environ.get('IMMICH_API_KEY')

    return ImmichAdapter(url, api_key)
