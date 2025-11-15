#!/usr/bin/env python3
"""
AUPAT Workflow Orchestration Script
Runs the complete AUPAT workflow in the correct sequence.

This script orchestrates the entire AUPAT workflow:
1. db_migrate.py   - Create/update database schema
2. db_import.py    - Import location and media
3. db_organize.py  - Extract metadata and categorize
4. db_folder.py    - Create archive folder structure
5. db_ingest.py    - Move files to archive
6. db_verify.py    - Verify integrity and cleanup staging
7. db_identify.py  - Generate JSON exports
8. backup.py       - (Optional) Create database backup

Version: 1.0.0
Last Updated: 2025-11-15
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates the AUPAT workflow execution."""

    def __init__(self, config_path: Optional[str] = None, scripts_dir: Optional[str] = None):
        """
        Initialize the workflow orchestrator.

        Args:
            config_path: Path to user.json config file
            scripts_dir: Path to scripts directory (defaults to ./scripts)
        """
        self.config_path = config_path or 'user/user.json'
        self.scripts_dir = Path(scripts_dir or 'scripts').resolve()
        self.config = self._load_config()
        self.workflow_steps = self._define_workflow()

    def _load_config(self) -> dict:
        """Load user configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            logger.error("Please create user/user.json from user/user.json.template")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)

    def _define_workflow(self) -> List[Dict]:
        """Define the workflow steps in execution order."""
        return [
            {
                'name': 'Database Migration',
                'script': 'db_migrate.py',
                'description': 'Create or update database schema',
                'required': True,
                'args': []
            },
            {
                'name': 'Import Media',
                'script': 'db_import.py',
                'description': 'Import location and media files',
                'required': False,  # Can be skipped if no new imports
                'args': [],  # Will be populated with --source if provided
                'needs_source': True
            },
            {
                'name': 'Organize Metadata',
                'script': 'db_organize.py',
                'description': 'Extract metadata and categorize files',
                'required': True,
                'args': []
            },
            {
                'name': 'Create Folder Structure',
                'script': 'db_folder.py',
                'description': 'Generate archive folder structure',
                'required': True,
                'args': []
            },
            {
                'name': 'Ingest Files',
                'script': 'db_ingest.py',
                'description': 'Move files to archive',
                'required': True,
                'args': []
            },
            {
                'name': 'Verify Archive',
                'script': 'db_verify.py',
                'description': 'Verify integrity and cleanup staging',
                'required': True,
                'args': []
            },
            {
                'name': 'Export JSON',
                'script': 'db_identify.py',
                'description': 'Generate JSON exports',
                'required': True,
                'args': []
            }
        ]

    def _run_script(self, step: Dict) -> Tuple[bool, str]:
        """
        Run a single workflow script.

        Args:
            step: Workflow step definition

        Returns:
            Tuple of (success: bool, output: str)
        """
        script_path = self.scripts_dir / step['script']

        if not script_path.exists():
            return False, f"Script not found: {script_path}"

        # Build command
        cmd = [sys.executable, str(script_path)]

        # Add config path
        if self.config_path:
            cmd.extend(['--config', self.config_path])

        # Add step-specific arguments
        if step.get('args'):
            cmd.extend(step['args'])

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                error_msg = f"Script failed with exit code {result.returncode}\n"
                error_msg += f"STDOUT: {result.stdout}\n"
                error_msg += f"STDERR: {result.stderr}"
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "Script timed out after 1 hour"
        except Exception as e:
            return False, f"Exception running script: {str(e)}"

    def run_workflow(
        self,
        source_dir: Optional[str] = None,
        skip_steps: Optional[List[str]] = None,
        run_backup: bool = False,
        dry_run: bool = False,
        interactive: bool = False
    ) -> bool:
        """
        Run the complete workflow.

        Args:
            source_dir: Source directory for import (required for db_import step)
            skip_steps: List of step names to skip
            run_backup: Whether to run backup at the end
            dry_run: Show what would be executed without running
            interactive: Prompt before each step

        Returns:
            True if all steps succeeded, False otherwise
        """
        skip_steps = skip_steps or []

        logger.info("="*60)
        logger.info("AUPAT Workflow Orchestration")
        logger.info("="*60)
        logger.info(f"Config: {self.config_path}")
        logger.info(f"Scripts: {self.scripts_dir}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("="*60)

        # Add source to import step if provided
        for step in self.workflow_steps:
            if step.get('needs_source') and source_dir:
                step['args'] = ['--source', source_dir]
            elif step.get('needs_source') and not source_dir:
                logger.warning(f"No source directory provided - {step['name']} will be skipped")
                skip_steps.append(step['name'])

        total_steps = len(self.workflow_steps)
        completed_steps = 0
        failed_steps = []

        for idx, step in enumerate(self.workflow_steps, 1):
            step_name = step['name']

            # Skip if in skip list
            if step_name in skip_steps:
                logger.info(f"\n[{idx}/{total_steps}] Skipping: {step_name}")
                continue

            logger.info(f"\n[{idx}/{total_steps}] {step_name}")
            logger.info(f"  Description: {step['description']}")
            logger.info(f"  Script: {step['script']}")

            # Interactive mode - prompt before running
            if interactive and not dry_run:
                response = input(f"  Run this step? [Y/n/q]: ").strip().lower()
                if response == 'q':
                    logger.info("Workflow cancelled by user")
                    return False
                elif response == 'n':
                    logger.info(f"  Skipped by user")
                    continue

            if dry_run:
                logger.info(f"  [DRY RUN] Would execute: {step['script']}")
                completed_steps += 1
                continue

            # Run the step
            success, output = self._run_script(step)

            if success:
                logger.info(f"  ✓ {step_name} completed successfully")
                completed_steps += 1

                # Show last few lines of output
                output_lines = output.strip().split('\n')
                if len(output_lines) > 5:
                    logger.info("  Last 5 lines of output:")
                    for line in output_lines[-5:]:
                        logger.info(f"    {line}")
            else:
                logger.error(f"  ✗ {step_name} failed!")
                logger.error(f"  Error: {output}")
                failed_steps.append(step_name)

                if step.get('required'):
                    logger.error(f"  {step_name} is required - stopping workflow")
                    break
                else:
                    logger.warning(f"  {step_name} is optional - continuing workflow")

        # Optional backup at the end
        if run_backup and not dry_run and not failed_steps:
            logger.info(f"\n[OPTIONAL] Running backup...")
            backup_step = {
                'name': 'Backup',
                'script': 'backup.py',
                'description': 'Create database backup',
                'args': []
            }
            success, output = self._run_script(backup_step)
            if success:
                logger.info(f"  ✓ Backup completed successfully")
            else:
                logger.warning(f"  ✗ Backup failed: {output}")

        # Summary
        logger.info("\n" + "="*60)
        logger.info("Workflow Summary")
        logger.info("="*60)
        logger.info(f"Completed: {completed_steps}/{total_steps} steps")

        if failed_steps:
            logger.error(f"Failed steps: {', '.join(failed_steps)}")
            logger.info("="*60)
            return False
        else:
            logger.info("✓ All steps completed successfully!")
            logger.info("="*60)
            return True


def main():
    """Main entry point for workflow orchestration."""
    parser = argparse.ArgumentParser(
        description='AUPAT Workflow Orchestration - Run the complete AUPAT workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow with new media import
  python run_workflow.py --source /path/to/media

  # Run workflow without import (just process existing data)
  python run_workflow.py

  # Interactive mode - confirm each step
  python run_workflow.py --interactive --source /path/to/media

  # Dry run to see what would execute
  python run_workflow.py --dry-run --source /path/to/media

  # Skip specific steps
  python run_workflow.py --skip "Import Media" --skip "Export JSON"

  # Run with backup at the end
  python run_workflow.py --source /path/to/media --backup

Workflow Steps (in order):
  1. Database Migration    - Create/update schema
  2. Import Media         - Import new files (optional)
  3. Organize Metadata    - Extract and categorize
  4. Create Folders       - Generate archive structure
  5. Ingest Files         - Move to archive
  6. Verify Archive       - Check integrity
  7. Export JSON          - Generate exports
  8. Backup              - Database backup (optional)
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='user/user.json',
        help='Path to user.json config file (default: user/user.json)'
    )

    parser.add_argument(
        '--source',
        type=str,
        help='Source directory containing media files to import'
    )

    parser.add_argument(
        '--scripts-dir',
        type=str,
        default='scripts',
        help='Path to scripts directory (default: scripts)'
    )

    parser.add_argument(
        '--skip',
        action='append',
        dest='skip_steps',
        help='Skip a specific workflow step (can be used multiple times)'
    )

    parser.add_argument(
        '--backup',
        action='store_true',
        help='Run database backup after successful workflow completion'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be executed without actually running scripts'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Prompt before executing each step'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create orchestrator
    try:
        orchestrator = WorkflowOrchestrator(
            config_path=args.config,
            scripts_dir=args.scripts_dir
        )
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        return 1

    # Run workflow
    success = orchestrator.run_workflow(
        source_dir=args.source,
        skip_steps=args.skip_steps,
        run_backup=args.backup,
        dry_run=args.dry_run,
        interactive=args.interactive
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
