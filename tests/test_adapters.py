"""
Unit tests for Immich and ArchiveBox adapters

Tests:
- Adapter initialization
- Health check functionality
- Retry logic on failures
- Error handling
- HTTP communication (mocked)
- Graceful degradation
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from adapters.immich_adapter import (
    ImmichAdapter,
    ImmichError,
    ImmichConnectionError,
    ImmichUploadError,
    create_immich_adapter
)
from adapters.archivebox_adapter import (
    ArchiveBoxAdapter,
    ArchiveBoxError,
    ArchiveBoxConnectionError,
    create_archivebox_adapter
)


# Immich Adapter Tests

def test_immich_adapter_initialization():
    """Test Immich adapter can be initialized."""
    adapter = ImmichAdapter('http://localhost:2283', api_key='test-key')

    assert adapter.base_url == 'http://localhost:2283'
    assert adapter.api_key == 'test-key'
    assert adapter.session.headers.get('x-api-key') == 'test-key'


def test_immich_adapter_strips_trailing_slash():
    """Test that base URL trailing slash is stripped."""
    adapter = ImmichAdapter('http://localhost:2283/')

    assert adapter.base_url == 'http://localhost:2283'


@patch('adapters.immich_adapter.requests.Session.request')
def test_immich_health_check_success(mock_request):
    """Test successful health check."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'res': 'pong'}
    mock_request.return_value = mock_response

    adapter = ImmichAdapter('http://localhost:2283')
    healthy = adapter.health_check()

    assert healthy is True
    mock_request.assert_called_once()


@patch('adapters.immich_adapter.requests.Session.request')
def test_immich_health_check_failure(mock_request):
    """Test health check handles failures gracefully."""
    mock_request.side_effect = requests.exceptions.ConnectionError("Service unavailable")

    adapter = ImmichAdapter('http://localhost:2283')
    healthy = adapter.health_check()

    assert healthy is False


@patch('adapters.immich_adapter.requests.Session.request')
def test_immich_upload_success(mock_request, tmp_path):
    """Test successful photo upload."""
    # Create test file
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"fake image data")

    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'asset-uuid-123', 'duplicate': False}
    mock_request.return_value = mock_response

    adapter = ImmichAdapter('http://localhost:2283')
    asset_id = adapter.upload(str(test_file))

    assert asset_id == 'asset-uuid-123'
    mock_request.assert_called_once()


@patch('adapters.immich_adapter.requests.Session.request')
def test_immich_upload_duplicate(mock_request, tmp_path):
    """Test upload handles duplicates correctly."""
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"fake image data")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'asset-uuid-123', 'duplicate': True}
    mock_request.return_value = mock_response

    adapter = ImmichAdapter('http://localhost:2283')
    asset_id = adapter.upload(str(test_file))

    assert asset_id == 'asset-uuid-123'


def test_immich_upload_file_not_found():
    """Test upload fails gracefully if file doesn't exist."""
    adapter = ImmichAdapter('http://localhost:2283')

    with pytest.raises(FileNotFoundError):
        adapter.upload('/nonexistent/file.jpg')


@pytest.mark.skip(reason="TODO: Retry logic not yet implemented in adapters (Phase 2)")
@patch('adapters.immich_adapter.requests.Session')
def test_immich_retry_logic(mock_session_class):
    """Test that adapter retries on network failures."""
    # First two calls fail, third succeeds
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'res': 'pong'}

    mock_session = Mock()
    mock_session.request = Mock(side_effect=[
        requests.exceptions.ConnectionError("Connection failed"),
        requests.exceptions.ConnectionError("Connection failed"),
        mock_response
    ])
    mock_session.headers = Mock()
    mock_session.headers.update = Mock()
    mock_session_class.return_value = mock_session

    adapter = ImmichAdapter('http://localhost:2283')
    healthy = adapter.health_check()

    assert healthy is True
    assert mock_session.request.call_count == 3


@pytest.mark.skip(reason="TODO: Retry logic not yet implemented in adapters (Phase 2)")
@patch('adapters.immich_adapter.requests.Session')
def test_immich_retry_exhaustion(mock_session_class):
    """Test that adapter gives up after max retries."""
    mock_session = Mock()
    mock_session.request = Mock(side_effect=requests.exceptions.ConnectionError("Connection failed"))
    mock_session.headers = Mock()
    mock_session.headers.update = Mock()
    mock_session_class.return_value = mock_session

    adapter = ImmichAdapter('http://localhost:2283')

    with pytest.raises(ImmichConnectionError):
        adapter._request('GET', '/api/server-info/ping')

    assert mock_session.request.call_count == 3  # Max retries


def test_immich_get_thumbnail_url():
    """Test thumbnail URL generation."""
    adapter = ImmichAdapter('http://localhost:2283')
    url = adapter.get_thumbnail_url('asset-123', 'preview')

    assert url == 'http://localhost:2283/api/asset/thumbnail/asset-123?size=preview'


def test_immich_get_original_url():
    """Test original file URL generation."""
    adapter = ImmichAdapter('http://localhost:2283')
    url = adapter.get_original_url('asset-123')

    assert url == 'http://localhost:2283/api/asset/file/asset-123'


def test_immich_mime_type_detection():
    """Test MIME type detection from file extension."""
    adapter = ImmichAdapter('http://localhost:2283')

    assert adapter._get_mime_type(Path('test.jpg')) == 'image/jpeg'
    assert adapter._get_mime_type(Path('test.png')) == 'image/png'
    assert adapter._get_mime_type(Path('test.mp4')) == 'video/mp4'
    assert adapter._get_mime_type(Path('test.mov')) == 'video/quicktime'
    assert adapter._get_mime_type(Path('test.dng')) == 'image/x-adobe-dng'
    assert adapter._get_mime_type(Path('test.unknown')) == 'application/octet-stream'


def test_create_immich_adapter_from_env():
    """Test factory function uses environment variables."""
    with patch.dict('os.environ', {'IMMICH_URL': 'http://test:2283', 'IMMICH_API_KEY': 'test-key'}):
        adapter = create_immich_adapter()

        assert adapter.base_url == 'http://test:2283'
        assert adapter.api_key == 'test-key'


def test_create_immich_adapter_defaults():
    """Test factory function uses defaults when env vars not set."""
    with patch.dict('os.environ', {}, clear=True):
        adapter = create_immich_adapter()

        assert adapter.base_url == 'http://localhost:2283'
        assert adapter.api_key is None


# ArchiveBox Adapter Tests

def test_archivebox_adapter_initialization():
    """Test ArchiveBox adapter can be initialized."""
    adapter = ArchiveBoxAdapter('http://localhost:8001', 'user', 'pass')

    assert adapter.base_url == 'http://localhost:8001'
    assert adapter.session.auth == ('user', 'pass')


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_health_check_success(mock_request):
    """Test successful ArchiveBox health check."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    adapter = ArchiveBoxAdapter('http://localhost:8001')
    healthy = adapter.health_check()

    assert healthy is True


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_health_check_failure(mock_request):
    """Test health check handles failures."""
    mock_request.side_effect = requests.exceptions.ConnectionError("Service unavailable")

    adapter = ArchiveBoxAdapter('http://localhost:8001')
    healthy = adapter.health_check()

    assert healthy is False


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_archive_url_success(mock_request):
    """Test successful URL archiving."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'snapshot_id': '20240101120000',
        'status': 'succeeded'
    }
    mock_request.return_value = mock_response

    adapter = ArchiveBoxAdapter('http://localhost:8001')
    snapshot_id = adapter.archive_url('https://example.com')

    assert snapshot_id == '20240101120000'


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_archive_url_alternative_format(mock_request):
    """Test archive URL with alternative response format."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'snapshots': [
            {'timestamp': '20240101120000'}
        ]
    }
    mock_request.return_value = mock_response

    adapter = ArchiveBoxAdapter('http://localhost:8001')
    snapshot_id = adapter.archive_url('https://example.com')

    assert snapshot_id == '20240101120000'


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_get_snapshot(mock_request):
    """Test getting snapshot details."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'timestamp': '20240101120000',
        'url': 'https://example.com',
        'status': 'succeeded'
    }
    mock_request.return_value = mock_response

    adapter = ArchiveBoxAdapter('http://localhost:8001')
    snapshot = adapter.get_snapshot('20240101120000')

    assert snapshot['timestamp'] == '20240101120000'
    assert snapshot['url'] == 'https://example.com'


@patch('adapters.archivebox_adapter.requests.Session.request')
def test_archivebox_get_archive_status(mock_request):
    """Test archive status mapping."""
    mock_response = Mock()
    mock_response.status_code = 200

    adapter = ArchiveBoxAdapter('http://localhost:8001')

    # Test 'succeeded' maps to 'archived'
    mock_response.json.return_value = {'status': 'succeeded'}
    mock_request.return_value = mock_response
    assert adapter.get_archive_status('123') == 'archived'

    # Test 'failed' maps to 'failed'
    mock_response.json.return_value = {'status': 'failed'}
    assert adapter.get_archive_status('123') == 'failed'

    # Test 'pending' maps to 'pending'
    mock_response.json.return_value = {'status': 'pending'}
    assert adapter.get_archive_status('123') == 'pending'


@pytest.mark.skip(reason="TODO: Retry logic not yet implemented in adapters (Phase 2)")
def test_archivebox_retry_logic():
    """Test that ArchiveBox adapter retries on failures."""
    with patch('adapters.archivebox_adapter.requests.Session') as mock_session_class:
        mock_response = Mock()
        mock_response.status_code = 200

        mock_session = Mock()
        # First two calls fail, third succeeds
        mock_session.request = Mock(side_effect=[
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response
        ])
        mock_session.headers = Mock()
        mock_session.headers.update = Mock()
        mock_session_class.return_value = mock_session

        adapter = ArchiveBoxAdapter('http://localhost:8001')
        healthy = adapter.health_check()

        assert healthy is True
        assert mock_session.request.call_count == 3


def test_create_archivebox_adapter_from_env():
    """Test factory function uses environment variables."""
    with patch.dict('os.environ', {
        'ARCHIVEBOX_URL': 'http://test:8001',
        'ARCHIVEBOX_USERNAME': 'user',
        'ARCHIVEBOX_PASSWORD': 'pass'
    }):
        adapter = create_archivebox_adapter()

        assert adapter.base_url == 'http://test:8001'
        assert adapter.session.auth == ('user', 'pass')


def test_create_archivebox_adapter_defaults():
    """Test factory function uses defaults."""
    with patch.dict('os.environ', {}, clear=True):
        adapter = create_archivebox_adapter()

        assert adapter.base_url == 'http://localhost:8001'
        assert adapter.session.auth is None
