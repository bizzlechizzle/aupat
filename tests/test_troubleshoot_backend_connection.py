#!/usr/bin/env python3
"""
Troubleshooting Tests: Backend Connection Issues
Tests for regression prevention of port mismatch and validation issues.

This test module ensures:
1. Port configuration matches between desktop and API server
2. State validation is permissive (warnings, not errors)
3. Type validation is permissive (warnings, not errors)
4. API server provides clear startup instructions
"""

import unittest
import json
from pathlib import Path
import sys

from scripts.normalize import normalize_state_code, normalize_location_type


class TestBackendConnectionConfiguration(unittest.TestCase):
    """Test that backend connection configuration is correct"""

    def test_desktop_api_url_uses_port_5000(self):
        """Desktop app should default to port 5000 (Flask default)"""
        desktop_main = Path(__file__).parent.parent / 'desktop' / 'src' / 'main' / 'index.js'

        if not desktop_main.exists():
            self.skipTest("Desktop app not found")

        content = desktop_main.read_text()

        # Check that port 5001 is NOT used
        self.assertNotIn('5001', content,
            "Desktop app should not use port 5001 - Flask defaults to 5000")

        # Check that localhost:5000 is present
        self.assertIn('localhost:5000', content,
            "Desktop app should connect to localhost:5000")

    def test_flask_app_runs_on_port_5000(self):
        """Flask app should run on port 5000"""
        app_py = Path(__file__).parent.parent / 'app.py'

        if not app_py.exists():
            self.skipTest("app.py not found")

        content = app_py.read_text()

        # Check that port 5000 is used
        self.assertIn('port=5000', content,
            "Flask app should run on port 5000")


class TestStateValidationPermissive(unittest.TestCase):
    """Test that state validation is permissive per LOGSEC spec"""

    def test_standard_state_codes_accepted(self):
        """Standard USPS state codes should be accepted"""
        test_cases = ['ny', 'NY', 'ca', 'CA', 'tx', 'TX']

        for state in test_cases:
            result = normalize_state_code(state)
            self.assertEqual(result.lower(), state.lower(),
                f"State code {state} should be normalized to lowercase")

    def test_custom_state_codes_allowed(self):
        """Custom/non-standard state codes should be allowed (not raise errors)"""
        # Per LOGSEC spec: state should be "based off folder name"
        # Therefore custom codes should be allowed
        custom_states = ['xx', 'zz', 'aa', 'bb']

        for state in custom_states:
            # Should not raise ValueError
            result = normalize_state_code(state)
            self.assertEqual(result, state.lower(),
                f"Custom state code {state} should be allowed per LOGSEC spec")

    def test_empty_state_raises_error(self):
        """Empty state should raise ValueError"""
        with self.assertRaises(ValueError):
            normalize_state_code('')

        with self.assertRaises(ValueError):
            normalize_state_code('   ')


class TestTypeValidationPermissive(unittest.TestCase):
    """Test that type validation is permissive per LOGSEC spec"""

    def test_standard_types_accepted(self):
        """Standard location types should be accepted"""
        standard_types = [
            'industrial', 'residential', 'commercial',
            'military', 'healthcare', 'educational'
        ]

        for loc_type in standard_types:
            result = normalize_location_type(loc_type)
            self.assertEqual(result, loc_type.lower(),
                f"Standard type {loc_type} should be normalized")

    def test_custom_types_allowed(self):
        """Custom/non-standard types should be allowed (not raise errors)"""
        # Per LOGSEC spec: type should be "based off folder name"
        # Therefore custom types should be allowed
        custom_types = [
            'spaceship-factory', 'underground-bunker',
            'secret-lab', 'alien-base', 'time-machine'
        ]

        for loc_type in custom_types:
            # Should not raise ValueError
            result = normalize_location_type(loc_type)
            # Should be normalized to lowercase with hyphens
            expected = loc_type.lower().replace(' ', '-')
            self.assertEqual(result, expected,
                f"Custom type {loc_type} should be allowed per LOGSEC spec")

    def test_empty_type_raises_error(self):
        """Empty type should raise ValueError"""
        with self.assertRaises(ValueError):
            normalize_location_type('')

        with self.assertRaises(ValueError):
            normalize_location_type('   ')

    def test_type_auto_correction_still_works(self):
        """Auto-correction from mapping should still work"""
        # These mappings should still be applied
        test_mappings = {
            'hospital': 'healthcare',
            'factory': 'industrial',
            'school': 'educational'
        }

        for input_type, expected_output in test_mappings.items():
            result = normalize_location_type(input_type)
            self.assertEqual(result, expected_output,
                f"Type mapping {input_type} → {expected_output} should work")


class TestAPIServerStartupMessages(unittest.TestCase):
    """Test that API server provides helpful startup messages"""

    def test_app_py_logs_port_information(self):
        """app.py should log port information on startup"""
        app_py = Path(__file__).parent.parent / 'app.py'

        if not app_py.exists():
            self.skipTest("app.py not found")

        content = app_py.read_text()

        # Check for helpful logging
        self.assertIn('Server will listen', content,
            "app.py should log server listening address")
        self.assertIn('Desktop app should connect', content,
            "app.py should provide connection instructions")

    def test_app_py_checks_for_database(self):
        """app.py should check if database exists and provide instructions"""
        app_py = Path(__file__).parent.parent / 'app.py'

        if not app_py.exists():
            self.skipTest("app.py not found")

        content = app_py.read_text()

        # Check for database existence check
        self.assertIn('if not db_path.exists()', content,
            "app.py should check if database exists")
        self.assertIn('db_migrate', content,
            "app.py should suggest running migration script")


class TestRegressionPreventionOriginalIssue(unittest.TestCase):
    """
    Regression tests for original reported issue:
    'Cannot read properties of undefined (reading 'locations')'
    """

    def test_port_mismatch_resolved(self):
        """Original issue: Desktop connected to 5001, server ran on 5000"""
        desktop_main = Path(__file__).parent.parent / 'desktop' / 'src' / 'main' / 'index.js'
        app_py = Path(__file__).parent.parent / 'app.py'

        if not desktop_main.exists() or not app_py.exists():
            self.skipTest("Source files not found")

        desktop_content = desktop_main.read_text()
        app_content = app_py.read_text()

        # Both should use port 5000
        self.assertIn('localhost:5000', desktop_content,
            "Desktop should connect to port 5000")
        self.assertIn('port=5000', app_content,
            "Server should listen on port 5000")

        # Desktop should NOT reference 5001
        self.assertNotIn('5001', desktop_content,
            "Desktop should not reference port 5001")


if __name__ == '__main__':
    unittest.main()
