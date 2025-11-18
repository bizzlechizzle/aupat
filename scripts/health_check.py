#!/usr/bin/env python3
"""
Comprehensive Health Check Script for AUPAT

Checks all critical systems:
- Database connectivity and write capability
- File system access
- Disk space
- External tools (exiftool, ffmpeg)
- External services (Immich, ArchiveBox)

Returns detailed JSON with pass/fail for each check.
"""

import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
except ImportError:
    requests = None

# Configuration
DB_PATH = os.environ.get('DB_PATH', 'data/aupat.db')
IMMICH_URL = os.environ.get('IMMICH_URL', '')
IMMICH_API_KEY = os.environ.get('IMMICH_API_KEY', '')
ARCHIVEBOX_URL = os.environ.get('ARCHIVEBOX_URL', '')

# Thresholds
MIN_DISK_SPACE_GB = 1  # Warn if less than 1GB free

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health check system."""

    def __init__(self):
        self.results = {
            'overall_status': 'unknown',
            'checks': {},
            'warnings': [],
            'errors': []
        }

    def check_database_connectivity(self) -> bool:
        """Check if database exists and is accessible."""
        check_name = 'database_connectivity'
        try:
            db_path = Path(DB_PATH)

            if not db_path.exists():
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': f'Database not found at {DB_PATH}'
                }
                self.results['errors'].append(f'Database not found: {DB_PATH}')
                return False

            # Try to connect
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()

            # Try a simple query
            cursor.execute("SELECT COUNT(*) FROM locations")
            count = cursor.fetchone()[0]

            conn.close()

            self.results['checks'][check_name] = {
                'status': 'pass',
                'message': f'Database accessible ({count} locations)'
            }
            return True

        except sqlite3.Error as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Database error: {str(e)}'
            }
            self.results['errors'].append(f'Database error: {str(e)}')
            return False
        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Unexpected error: {str(e)}'
            }
            self.results['errors'].append(f'Database check failed: {str(e)}')
            return False

    def check_database_write(self) -> bool:
        """Check if database is writable."""
        check_name = 'database_write'
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()

            # Create temporary test table
            test_table = '__health_check_temp__'
            cursor.execute(f"CREATE TEMP TABLE {test_table} (id INTEGER)")
            cursor.execute(f"INSERT INTO {test_table} VALUES (1)")
            cursor.execute(f"SELECT * FROM {test_table}")
            result = cursor.fetchone()

            conn.close()

            if result and result[0] == 1:
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': 'Database is writable'
                }
                return True
            else:
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'Database write test failed'
                }
                self.results['errors'].append('Database write test failed')
                return False

        except sqlite3.Error as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Write test error: {str(e)}'
            }
            self.results['errors'].append(f'Database write error: {str(e)}')
            return False
        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Unexpected error: {str(e)}'
            }
            self.results['errors'].append(f'Database write check failed: {str(e)}')
            return False

    def check_filesystem_access(self) -> bool:
        """Check if data directory is accessible and writable."""
        check_name = 'filesystem_access'
        try:
            data_dir = Path('data')

            # Check if data directory exists
            if not data_dir.exists():
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'Data directory not found'
                }
                self.results['errors'].append('Data directory not found')
                return False

            # Check if readable
            if not os.access(data_dir, os.R_OK):
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'Data directory not readable'
                }
                self.results['errors'].append('Data directory not readable')
                return False

            # Check if writable
            if not os.access(data_dir, os.W_OK):
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'Data directory not writable'
                }
                self.results['errors'].append('Data directory not writable')
                return False

            # Try to create a temporary file
            try:
                with tempfile.NamedTemporaryFile(dir=data_dir, delete=True) as tmp:
                    tmp.write(b'health check test')
                    tmp.flush()

                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': 'Filesystem is accessible and writable'
                }
                return True

            except IOError as e:
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': f'Cannot write to data directory: {str(e)}'
                }
                self.results['errors'].append(f'Filesystem write error: {str(e)}')
                return False

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Unexpected error: {str(e)}'
            }
            self.results['errors'].append(f'Filesystem check failed: {str(e)}')
            return False

    def check_disk_space(self) -> bool:
        """Check available disk space."""
        check_name = 'disk_space'
        try:
            stat = shutil.disk_usage('.')
            free_gb = stat.free / (1024 ** 3)

            if free_gb < MIN_DISK_SPACE_GB:
                self.results['checks'][check_name] = {
                    'status': 'warn',
                    'message': f'Low disk space: {free_gb:.2f}GB free (minimum: {MIN_DISK_SPACE_GB}GB)'
                }
                self.results['warnings'].append(f'Low disk space: {free_gb:.2f}GB')
                return True  # Warning, not failure
            else:
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': f'Adequate disk space: {free_gb:.2f}GB free'
                }
                return True

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'fail',
                'message': f'Cannot check disk space: {str(e)}'
            }
            self.results['errors'].append(f'Disk space check failed: {str(e)}')
            return False

    def check_exiftool(self) -> bool:
        """Check if exiftool is installed and accessible."""
        check_name = 'exiftool'
        try:
            result = subprocess.run(
                ['exiftool', '-ver'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': f'exiftool found (version {version})'
                }
                return True
            else:
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'exiftool command failed'
                }
                self.results['warnings'].append('exiftool not working (EXIF extraction disabled)')
                return False

        except FileNotFoundError:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'exiftool not found (EXIF extraction will not work)'
            }
            self.results['warnings'].append('exiftool not installed')
            return True  # Warning, not failure (app can work without it)

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': f'Cannot check exiftool: {str(e)}'
            }
            self.results['warnings'].append('exiftool check failed')
            return True

    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed and accessible."""
        check_name = 'ffmpeg'
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse version from first line
                version_line = result.stdout.split('\n')[0]
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': f'ffmpeg found ({version_line})'
                }
                return True
            else:
                self.results['checks'][check_name] = {
                    'status': 'fail',
                    'message': 'ffmpeg command failed'
                }
                self.results['warnings'].append('ffmpeg not working (video metadata disabled)')
                return False

        except FileNotFoundError:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'ffmpeg not found (video metadata will not work)'
            }
            self.results['warnings'].append('ffmpeg not installed')
            return True  # Warning, not failure

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': f'Cannot check ffmpeg: {str(e)}'
            }
            self.results['warnings'].append('ffmpeg check failed')
            return True

    def check_immich_service(self) -> bool:
        """Check if Immich service is available."""
        check_name = 'immich_service'

        if not IMMICH_URL:
            self.results['checks'][check_name] = {
                'status': 'skip',
                'message': 'Immich not configured (optional)'
            }
            return True

        if not requests:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'Cannot check Immich (requests library not installed)'
            }
            return True

        try:
            # Try ping endpoint
            response = requests.get(
                f'{IMMICH_URL}/api/server-info/ping',
                timeout=5
            )

            if response.status_code == 200:
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': 'Immich service is healthy'
                }
                return True
            else:
                self.results['checks'][check_name] = {
                    'status': 'warn',
                    'message': f'Immich returned status {response.status_code}'
                }
                self.results['warnings'].append('Immich service not healthy')
                return True  # Warning, not failure (optional service)

        except requests.exceptions.ConnectionError:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'Cannot connect to Immich service'
            }
            self.results['warnings'].append('Immich service unavailable')
            return True

        except requests.exceptions.Timeout:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'Immich service timeout'
            }
            self.results['warnings'].append('Immich service timeout')
            return True

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': f'Immich check error: {str(e)}'
            }
            self.results['warnings'].append('Immich check failed')
            return True

    def check_archivebox_service(self) -> bool:
        """Check if ArchiveBox service is available."""
        check_name = 'archivebox_service'

        if not ARCHIVEBOX_URL:
            self.results['checks'][check_name] = {
                'status': 'skip',
                'message': 'ArchiveBox not configured (optional)'
            }
            return True

        if not requests:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'Cannot check ArchiveBox (requests library not installed)'
            }
            return True

        try:
            # Try health endpoint
            response = requests.get(
                f'{ARCHIVEBOX_URL}/health/',
                timeout=5
            )

            if response.status_code == 200:
                self.results['checks'][check_name] = {
                    'status': 'pass',
                    'message': 'ArchiveBox service is healthy'
                }
                return True
            else:
                self.results['checks'][check_name] = {
                    'status': 'warn',
                    'message': f'ArchiveBox returned status {response.status_code}'
                }
                self.results['warnings'].append('ArchiveBox service not healthy')
                return True

        except requests.exceptions.ConnectionError:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'Cannot connect to ArchiveBox service'
            }
            self.results['warnings'].append('ArchiveBox service unavailable')
            return True

        except requests.exceptions.Timeout:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': 'ArchiveBox service timeout'
            }
            self.results['warnings'].append('ArchiveBox service timeout')
            return True

        except Exception as e:
            self.results['checks'][check_name] = {
                'status': 'warn',
                'message': f'ArchiveBox check error: {str(e)}'
            }
            self.results['warnings'].append('ArchiveBox check failed')
            return True

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        logger.info("Starting comprehensive health check...")

        # Run all checks
        checks = [
            ('Database Connectivity', self.check_database_connectivity),
            ('Database Write', self.check_database_write),
            ('Filesystem Access', self.check_filesystem_access),
            ('Disk Space', self.check_disk_space),
            ('exiftool', self.check_exiftool),
            ('ffmpeg', self.check_ffmpeg),
            ('Immich Service', self.check_immich_service),
            ('ArchiveBox Service', self.check_archivebox_service),
        ]

        passed = 0
        failed = 0
        warnings = 0
        skipped = 0

        for name, check_func in checks:
            logger.info(f"Checking {name}...")
            try:
                check_func()

                # Count status
                status = self.results['checks'].get(name.lower().replace(' ', '_'), {}).get('status', 'unknown')
                if status == 'pass':
                    passed += 1
                elif status == 'fail':
                    failed += 1
                elif status == 'warn':
                    warnings += 1
                elif status == 'skip':
                    skipped += 1

            except Exception as e:
                logger.error(f"Check {name} raised exception: {e}")
                failed += 1
                self.results['errors'].append(f'{name} check exception: {str(e)}')

        # Determine overall status
        if failed > 0:
            self.results['overall_status'] = 'fail'
        elif warnings > 0:
            self.results['overall_status'] = 'warn'
        else:
            self.results['overall_status'] = 'pass'

        # Add summary
        self.results['summary'] = {
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'skipped': skipped,
            'total': len(checks)
        }

        logger.info("Health check complete")
        return self.results


def main():
    """Main entry point."""
    print("AUPAT Comprehensive Health Check")
    print("=" * 50)
    print("")

    checker = HealthChecker()
    results = checker.run_all_checks()

    # Print results
    print("")
    print("=" * 50)
    print("HEALTH CHECK RESULTS")
    print("=" * 50)
    print("")

    for check_name, check_result in results['checks'].items():
        status = check_result['status']
        message = check_result['message']

        # Color coding
        if status == 'pass':
            symbol = '✓'
            color = '\033[0;32m'  # Green
        elif status == 'fail':
            symbol = '✗'
            color = '\033[0;31m'  # Red
        elif status == 'warn':
            symbol = '⚠'
            color = '\033[1;33m'  # Yellow
        elif status == 'skip':
            symbol = '○'
            color = '\033[0;34m'  # Blue
        else:
            symbol = '?'
            color = '\033[0m'    # No color

        print(f"{color}{symbol}\033[0m {check_name}: {message}")

    # Print summary
    print("")
    print("=" * 50)
    summary = results['summary']
    print(f"Summary: {summary['passed']} passed, {summary['failed']} failed, {summary['warnings']} warnings, {summary['skipped']} skipped")
    print(f"Overall Status: {results['overall_status'].upper()}")

    # Print warnings
    if results['warnings']:
        print("")
        print("Warnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")

    # Print errors
    if results['errors']:
        print("")
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")

    print("")

    # Output JSON to file
    with open('health_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Detailed results saved to: health_check_results.json")
    print("")

    # Exit code based on overall status
    if results['overall_status'] == 'fail':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
