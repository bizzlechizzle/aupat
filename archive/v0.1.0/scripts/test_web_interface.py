#!/usr/bin/env python3
"""
Test script for AUPAT Web Interface
Validates dependencies, startup, and basic functionality.
"""

import importlib
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


class WebInterfaceTest:
    """Test suite for web interface health checks."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def test(self, description: str, func):
        """Run a test and track results."""
        print(f"Testing: {description}...", end=" ")
        try:
            result = func()
            if result:
                print("PASS")
                self.passed += 1
                return True
            else:
                print("FAIL")
                self.failed += 1
                self.errors.append(f"Test failed: {description}")
                return False
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
            self.errors.append(f"{description}: {e}")
            return False

    def check_dependency(self, module_name: str) -> bool:
        """Check if a Python module is installed."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def check_flask_installed(self) -> bool:
        """Verify Flask is installed."""
        return self.check_dependency('flask')

    def check_all_dependencies(self) -> bool:
        """Check all required dependencies."""
        required = [
            'flask',
            'unidecode',
            'dateutil',
            'pytest',
        ]

        missing = []
        for module in required:
            if not self.check_dependency(module):
                missing.append(module)

        if missing:
            self.errors.append(f"Missing dependencies: {', '.join(missing)}")
            return False
        return True

    def check_web_interface_file(self) -> bool:
        """Verify web_interface.py exists."""
        web_file = Path(__file__).parent.parent / 'web_interface.py'
        return web_file.exists()

    def check_web_interface_syntax(self) -> bool:
        """Check if web_interface.py has valid Python syntax."""
        web_file = Path(__file__).parent.parent / 'web_interface.py'
        try:
            with open(web_file, 'r') as f:
                compile(f.read(), str(web_file), 'exec')
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error in web_interface.py: {e}")
            return False

    def check_can_import_web_interface(self) -> bool:
        """Test if web_interface module can be imported."""
        try:
            # Add parent directory to path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            # Try importing just to check syntax
            import web_interface
            return True
        except ImportError as e:
            self.errors.append(f"Cannot import web_interface: {e}")
            return False
        except Exception as e:
            # Other errors during import (like missing config) are OK
            # We just want to make sure Flask dependencies work
            if 'flask' in str(e).lower():
                self.errors.append(f"Flask-related error: {e}")
                return False
            return True

    def find_free_port(self) -> int:
        """Find a free port to use for testing."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def check_server_can_start(self) -> bool:
        """Test if server can start (quick start/stop test)."""
        proc = None
        try:
            # Find an available port
            port = self.find_free_port()
            web_file = Path(__file__).parent.parent / 'web_interface.py'

            # Start server in background on free port
            proc = subprocess.Popen(
                [sys.executable, str(web_file), '--no-browser', '--port', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a moment for startup
            time.sleep(3)

            # Check if process is still running
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                self.errors.append(f"Server exited immediately. Error: {stderr}")
                return False

            # Try to connect
            try:
                response = urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=5)
                html = response.read().decode('utf-8')

                # Verify we got HTML, not blank
                has_content = (
                    len(html) > 100 and
                    '<!DOCTYPE html>' in html and
                    'AUPAT' in html
                )

                if not has_content:
                    self.errors.append("Server returned blank or invalid HTML")
                    return False

                return True
            except urllib.error.URLError as e:
                self.errors.append(f"Cannot connect to server: {e}")
                return False
        except Exception as e:
            self.errors.append(f"Server start test failed: {e}")
            return False
        finally:
            # Always kill the server
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

    def run_all_tests(self) -> bool:
        """Run complete test suite."""
        print("=" * 60)
        print("AUPAT Web Interface Health Check")
        print("=" * 60)
        print()

        # Dependency checks
        print("1. Dependency Tests")
        self.test("Flask is installed", self.check_flask_installed)
        self.test("All dependencies installed", self.check_all_dependencies)
        print()

        # File checks
        print("2. File Tests")
        self.test("web_interface.py exists", self.check_web_interface_file)
        self.test("web_interface.py has valid syntax", self.check_web_interface_syntax)
        print()

        # Import checks
        print("3. Import Tests")
        self.test("web_interface module can be imported", self.check_can_import_web_interface)
        print()

        # Server tests
        print("4. Server Tests")
        self.test("Server can start and serve content", self.check_server_can_start)
        print()

        # Results
        print("=" * 60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        return self.failed == 0


def main():
    """Run web interface tests."""
    tester = WebInterfaceTest()
    success = tester.run_all_tests()

    if success:
        print("\nAll tests passed! Web interface is healthy.")
        return 0
    else:
        print("\nSome tests failed. Please fix errors before running web interface.")
        print("\nTo fix missing dependencies, run:")
        print("  pip3 install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
