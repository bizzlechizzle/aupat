#!/usr/bin/env python3
"""
Unit Tests for Input Validation Module
Tests all validation functions to ensure they handle edge cases correctly.

Run with: pytest tests/test_validation.py -v
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from validation import (
    validate_location_name,
    validate_state_code,
    validate_location_type,
    validate_file_size,
    validate_filename,
    validate_author_name,
    validate_url,
    validate_import_form_data
)


class TestLocationNameValidation:
    """Test location name validation."""

    def test_valid_location_names(self):
        """Valid location names should pass."""
        assert validate_location_name("Middletown State Hospital") == "Middletown State Hospital"
        assert validate_location_name("  Test Location  ") == "Test Location"
        assert validate_location_name("A" * 200) == "A" * 200  # Max length

    def test_empty_location_name(self):
        """Empty names should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_location_name("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_location_name(None)

    def test_short_location_name(self):
        """Names < 2 chars should fail."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            validate_location_name("A")

    def test_long_location_name(self):
        """Names > 200 chars should fail."""
        with pytest.raises(ValueError, match="too long"):
            validate_location_name("A" * 201)

    def test_invalid_characters(self):
        """Names with path separators should fail."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location_name("../etc/passwd")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location_name("test\\location")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location_name("test\x00location")


class TestStateCodeValidation:
    """Test state code validation."""

    def test_valid_state_codes(self):
        """Valid state codes should pass and be lowercase."""
        assert validate_state_code("NY") == "ny"
        assert validate_state_code("ca") == "ca"
        assert validate_state_code("VT") == "vt"
        assert validate_state_code("  PA  ") == "pa"

    def test_empty_state_code(self):
        """Empty codes should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_state_code("")

    def test_wrong_length_state_code(self):
        """Codes not 2 letters should fail."""
        with pytest.raises(ValueError, match="must be 2 letters"):
            validate_state_code("N")
        with pytest.raises(ValueError, match="must be 2 letters"):
            validate_state_code("NYC")

    def test_non_alpha_state_code(self):
        """Non-alphabetic codes should fail."""
        with pytest.raises(ValueError, match="letters only"):
            validate_state_code("12")
        with pytest.raises(ValueError, match="letters only"):
            validate_state_code("N1")


class TestLocationTypeValidation:
    """Test location type validation."""

    def test_valid_location_types(self):
        """Valid types should pass and be lowercase."""
        assert validate_location_type("Industrial") == "industrial"
        assert validate_location_type("State-Hospital") == "state-hospital"
        assert validate_location_type("  residential  ") == "residential"

    def test_empty_location_type(self):
        """Empty types should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_location_type("")

    def test_short_location_type(self):
        """Types < 2 chars should fail."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            validate_location_type("a")

    def test_long_location_type(self):
        """Types > 50 chars should fail."""
        with pytest.raises(ValueError, match="too long"):
            validate_location_type("a" * 51)

    def test_invalid_characters_in_type(self):
        """Types with numbers or special chars should fail."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location_type("industrial123")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location_type("industrial/commercial")


class TestFileSizeValidation:
    """Test file size validation."""

    class MockFile:
        """Mock file object for testing."""
        def __init__(self, size_bytes):
            self.size = size_bytes
            self.position = 0

        def seek(self, pos, whence=0):
            if whence == 0:  # SEEK_SET
                self.position = pos
            elif whence == 2:  # SEEK_END
                self.position = self.size

        def tell(self):
            return self.position

    def test_valid_file_sizes(self):
        """Files under limit should pass."""
        # 1MB file
        mock_file = self.MockFile(1024 * 1024)
        assert validate_file_size(mock_file, max_size_gb=10.0) == 1024 * 1024

        # 1GB file
        mock_file = self.MockFile(1024 * 1024 * 1024)
        assert validate_file_size(mock_file, max_size_gb=10.0) == 1024 * 1024 * 1024

    def test_oversized_file(self):
        """Files over limit should fail."""
        # 11GB file (over 10GB limit)
        mock_file = self.MockFile(11 * 1024 * 1024 * 1024)
        with pytest.raises(ValueError, match="too large"):
            validate_file_size(mock_file, max_size_gb=10.0)


class TestFilenameValidation:
    """Test filename validation."""

    def test_valid_filenames(self):
        """Valid filenames should pass."""
        assert validate_filename("photo.jpg") == "photo.jpg"
        assert validate_filename("my_file-2025.dng") == "my_file-2025.dng"

    def test_empty_filename(self):
        """Empty filenames should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_filename("")

    def test_path_traversal_attempts(self):
        """Filenames with path separators should fail."""
        with pytest.raises(ValueError, match="path separators"):
            validate_filename("../../../etc/passwd")
        with pytest.raises(ValueError, match="path separators"):
            validate_filename("dir/file.jpg")
        with pytest.raises(ValueError, match="path separators"):
            validate_filename("C:\\Windows\\System32\\file.exe")

    def test_null_bytes(self):
        """Filenames with null bytes should fail."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_filename("file\x00.jpg")

    def test_long_filename(self):
        """Filenames > 255 chars should fail."""
        with pytest.raises(ValueError, match="too long"):
            validate_filename("a" * 256 + ".jpg")


class TestAuthorNameValidation:
    """Test author name validation."""

    def test_valid_author_names(self):
        """Valid author names should pass."""
        assert validate_author_name("John Doe") == "John Doe"
        assert validate_author_name("user_123") == "user_123"
        assert validate_author_name("  test-user  ") == "test-user"

    def test_empty_author_name(self):
        """Empty names should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_author_name("")

    def test_short_author_name(self):
        """Names < 2 chars should fail."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            validate_author_name("A")

    def test_long_author_name(self):
        """Names > 100 chars should fail."""
        with pytest.raises(ValueError, match="too long"):
            validate_author_name("A" * 101)

    def test_invalid_characters_in_author(self):
        """Names with special chars should fail."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_author_name("user@example.com")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_author_name("user/admin")


class TestURLValidation:
    """Test URL validation."""

    def test_valid_urls(self):
        """Valid URLs should pass."""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("http://test.org/path?query=1") == "http://test.org/path?query=1"
        assert validate_url("  https://site.com  ") == "https://site.com"

    def test_empty_url(self):
        """Empty URLs should fail."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_url("")

    def test_invalid_url_scheme(self):
        """URLs without http:// or https:// should fail."""
        with pytest.raises(ValueError, match="must start with http"):
            validate_url("ftp://example.com")
        with pytest.raises(ValueError, match="must start with http"):
            validate_url("example.com")
        with pytest.raises(ValueError, match="must start with http"):
            validate_url("javascript:alert(1)")

    def test_long_url(self):
        """URLs > 2000 chars should fail."""
        with pytest.raises(ValueError, match="too long"):
            validate_url("https://example.com/" + "a" * 2000)


class TestImportFormDataValidation:
    """Test complete form data validation."""

    def test_valid_form_data(self):
        """Valid form data should pass."""
        data = {
            'loc_name': 'Test Location',
            'state': 'NY',
            'type': 'industrial',
            'aka_name': 'Also Known As',
            'sub_type': 'hospital',
            'imp_author': 'test_user',
            'web_urls': 'https://example.com\nhttps://test.org'
        }

        result = validate_import_form_data(data)

        assert result['loc_name'] == 'Test Location'
        assert result['state'] == 'ny'
        assert result['type'] == 'industrial'
        assert result['aka_name'] == 'Also Known As'
        assert result['sub_type'] == 'hospital'
        assert result['imp_author'] == 'test_user'
        assert len(result['web_urls']) == 2

    def test_minimal_form_data(self):
        """Form data with only required fields should pass."""
        data = {
            'loc_name': 'Minimal Location',
            'state': 'VT',
            'type': 'residential'
        }

        result = validate_import_form_data(data)

        assert result['loc_name'] == 'Minimal Location'
        assert result['state'] == 'vt'
        assert result['type'] == 'residential'
        assert result['aka_name'] is None
        assert result['sub_type'] is None
        assert result['imp_author'] is None
        assert result['web_urls'] == []

    def test_invalid_required_field(self):
        """Form data with invalid required field should fail."""
        data = {
            'loc_name': 'A',  # Too short
            'state': 'NY',
            'type': 'industrial'
        }

        with pytest.raises(ValueError):
            validate_import_form_data(data)

    def test_missing_required_field(self):
        """Form data missing required field should fail."""
        data = {
            'loc_name': 'Test Location',
            # Missing state
            'type': 'industrial'
        }

        with pytest.raises(ValueError):
            validate_import_form_data(data)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
