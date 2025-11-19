#!/usr/bin/env python3
"""
AUPAT v0.1.0 Simple Health Check
Checks system readiness for running AUPAT.

Returns exit code 0 if healthy, 1 if problems found.

LILBITS: One script = one function (health check)
Lines: <200 (LILBITS compliant)
"""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[FAIL] Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_venv():
    """Check if virtual environment is active"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[OK] Virtual environment active")
        return True
    else:
        print("[WARN] Virtual environment not active - run 'source venv/bin/activate'")
        return False


def check_user_config():
    """Check if user.json exists and is valid"""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'

    if not config_path.exists():
        print(f"[FAIL] user.json not found at {config_path}")
        print("       Run ./bootstrap_v010.sh to create it")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        required = ['db_name', 'db_loc']
        missing = [k for k in required if k not in config]
        if missing:
            print(f"[FAIL] user.json missing required keys: {missing}")
            return False

        print("[OK] user.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"[FAIL] user.json is not valid JSON: {e}")
        return False


def check_database():
    """Check if database exists and is accessible"""
    config_path = Path(__file__).parent.parent / 'user' / 'user.json'

    if not config_path.exists():
        print("[SKIP] Database check (user.json missing)")
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)

    db_path = Path(config['db_loc']) / config['db_name']

    if not db_path.exists():
        print(f"[FAIL] Database not found at {db_path}")
        print("       Run: python scripts/db_migrate_v010.py")
        print("       Or run: ./bootstrap_v010.sh")
        return False

    # Try to open database
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if locations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='locations'")
        if cursor.fetchone():
            # Count locations
            cursor.execute("SELECT COUNT(*) FROM locations")
            count = cursor.fetchone()[0]
            print(f"[OK] Database accessible ({count} locations)")
            conn.close()
            return True
        else:
            print(f"[FAIL] Database exists but schema is missing")
            print("       Run: python scripts/db_migrate_v010.py")
            conn.close()
            return False
    except sqlite3.Error as e:
        print(f"[FAIL] Database error: {e}")
        return False


def check_external_tool(tool_name, version_flag='-version'):
    """Check if external tool is available"""
    try:
        result = subprocess.run(
            [tool_name, version_flag],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] {tool_name} is available")
            return True
        else:
            print(f"[WARN] {tool_name} found but not working")
            return False
    except FileNotFoundError:
        print(f"[WARN] {tool_name} not found (optional but recommended)")
        return False
    except Exception as e:
        print(f"[WARN] Could not check {tool_name}: {e}")
        return False


def check_desktop_deps():
    """Check if desktop dependencies are installed"""
    desktop_dir = Path(__file__).parent.parent / 'desktop'
    node_modules = desktop_dir / 'node_modules'

    if not node_modules.exists():
        print("[FAIL] Desktop dependencies not installed")
        print("       Run: cd desktop && npm install")
        return False

    print("[OK] Desktop dependencies installed")
    return True


def main():
    """Run all health checks"""
    print("AUPAT v0.1.0 Health Check")
    print("=" * 40)
    print()

    checks = []

    # Critical checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("Virtual Environment", check_venv()))
    checks.append(("User Config", check_user_config()))
    checks.append(("Database", check_database()))
    checks.append(("Desktop Dependencies", check_desktop_deps()))

    print()

    # Optional checks
    print("Optional Tools:")
    check_external_tool('exiftool', '-ver')
    check_external_tool('ffmpeg', '-version')

    print()
    print("=" * 40)

    # Count results
    critical_checks = [c[1] for c in checks if c[1] is not None]
    passed = sum(1 for x in critical_checks if x is True)
    failed = sum(1 for x in critical_checks if x is False)
    total = len(critical_checks)

    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed > 0:
        print("\nStatus: FAILED - Fix issues above before starting")
        return 1
    else:
        print("\nStatus: HEALTHY - Ready to run AUPAT")
        return 0


if __name__ == '__main__':
    sys.exit(main())
