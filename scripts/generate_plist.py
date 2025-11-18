#!/usr/bin/env python3
"""
Generate macOS LaunchAgent plist from template.

This script generates com.aupat.worker.plist from the template file,
replacing placeholders with actual system paths. This ensures the
LaunchAgent works on any machine without hardcoded user paths.

Usage:
    python scripts/generate_plist.py
    python scripts/generate_plist.py --output /path/to/output.plist

The script automatically detects:
- Project root directory
- Python interpreter path (preferring venv if available)
- Virtual environment path

Following LILBITS principle: One script, one purpose.

Version: 1.0.0
Last Updated: 2025-11-18
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_project_root() -> Path:
    """
    Find the AUPAT project root directory.

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root cannot be determined
    """
    # Start from script location
    current = Path(__file__).parent.parent.resolve()

    # Look for marker files
    markers = ['claude.md', 'techguide.md', 'app.py']

    # Check current directory
    if any((current / marker).exists() for marker in markers):
        return current

    # Check parent directories (up to 3 levels)
    for _ in range(3):
        current = current.parent
        if any((current / marker).exists() for marker in markers):
            return current

    raise RuntimeError("Cannot find AUPAT project root. Run from project directory.")


def find_python_path() -> str:
    """
    Find the best Python interpreter to use.

    Preference order:
    1. Virtual environment Python (if active or exists)
    2. Current Python interpreter
    3. System python3

    Returns:
        Absolute path to Python interpreter
    """
    # Check if running in venv
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        return sys.executable

    # Check for venv in project
    project_root = find_project_root()
    venv_python = project_root / 'venv' / 'bin' / 'python3'
    if venv_python.exists():
        return str(venv_python)

    # Use current interpreter
    if sys.executable:
        return sys.executable

    # Fallback to system python3
    python3 = shutil.which('python3')
    if python3:
        return python3

    # Last resort
    return '/usr/bin/python3'


def find_venv_path() -> str:
    """
    Find virtual environment path.

    Returns:
        Absolute path to venv directory, or empty string if not found
    """
    project_root = find_project_root()
    venv_path = project_root / 'venv'

    if venv_path.exists() and venv_path.is_dir():
        return str(venv_path)

    return ""


def generate_plist(output_path: str = None) -> None:
    """
    Generate plist file from template.

    Args:
        output_path: Optional custom output path. If None, uses default location.

    Raises:
        FileNotFoundError: If template file not found
        IOError: If cannot write output file
    """
    project_root = find_project_root()
    template_path = project_root / 'com.aupat.worker.plist.template'

    # Default output path
    if output_path is None:
        output_path = project_root / 'com.aupat.worker.plist'
    else:
        output_path = Path(output_path)

    logger.info(f"Project root: {project_root}")
    logger.info(f"Template: {template_path}")
    logger.info(f"Output: {output_path}")

    # Check template exists
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()

    # Get paths
    python_path = find_python_path()
    venv_path = find_venv_path()

    logger.info(f"Python path: {python_path}")
    logger.info(f"Venv path: {venv_path or '(not found)'}")

    # Replace placeholders
    plist_content = template_content
    plist_content = plist_content.replace('{{PYTHON_PATH}}', python_path)
    plist_content = plist_content.replace('{{PROJECT_PATH}}', str(project_root))
    plist_content = plist_content.replace('{{VENV_PATH}}', venv_path or str(project_root / 'venv'))

    # Ensure logs directory exists
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"Ensured logs directory exists: {logs_dir}")

    # Write output
    with open(output_path, 'w') as f:
        f.write(plist_content)

    logger.info(f"Generated plist file: {output_path}")

    # Show installation instructions
    print("")
    print("Plist file generated successfully!")
    print("")
    print("To install the LaunchAgent on macOS:")
    print(f"  cp {output_path} ~/Library/LaunchAgents/")
    print("  launchctl load ~/Library/LaunchAgents/com.aupat.worker.plist")
    print("")
    print("To uninstall:")
    print("  launchctl unload ~/Library/LaunchAgents/com.aupat.worker.plist")
    print("  rm ~/Library/LaunchAgents/com.aupat.worker.plist")
    print("")
    print("To check status:")
    print("  launchctl list | grep aupat")
    print("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate macOS LaunchAgent plist from template'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output path for generated plist (default: com.aupat.worker.plist)',
        default=None
    )

    args = parser.parse_args()

    try:
        generate_plist(args.output)
        return 0
    except Exception as e:
        logger.error(f"Failed to generate plist: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
