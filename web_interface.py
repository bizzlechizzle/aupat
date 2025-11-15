#!/usr/bin/env python3
"""
AUPAT Web Interface
Simple Flask web interface for importing media and managing the AUPAT workflow.

Features:
- Import media with location details via web form
- Real-time progress tracking
- View database statistics
- Run workflow steps
- View logs

Version: 1.0.0
Last Updated: 2025-11-15
"""

import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, Optional

from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    send_from_directory,
    redirect,
    url_for,
    flash
)

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from utils import generate_uuid, calculate_sha256
from normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_sub_type,
    normalize_author
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global state
WORKFLOW_STATUS = {
    'running': False,
    'current_step': None,
    'progress': 0,
    'logs': [],
    'error': None
}

LOG_QUEUE = Queue()


def load_config(config_path: str = 'user/user.json') -> dict:
    """Load user configuration."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def get_db_stats(config: dict) -> Dict:
    """Get database statistics."""
    stats = {
        'locations': 0,
        'sub_locations': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'live_videos': 0,
        'total_files': 0
    }

    try:
        db_path = config.get('db_loc', 'aupat.db')
        if not Path(db_path).exists():
            return stats

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get counts
        tables = ['locations', 'sub_locations', 'images', 'videos', 'documents', 'live_videos']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                pass  # Table doesn't exist yet

        stats['total_files'] = stats['images'] + stats['videos'] + stats['documents'] + stats['live_videos']

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get DB stats: {e}")

    return stats


def run_workflow_step(script: str, args: list, config_path: str):
    """Run a single workflow step in background."""
    global WORKFLOW_STATUS

    try:
        WORKFLOW_STATUS['running'] = True
        WORKFLOW_STATUS['current_step'] = script
        WORKFLOW_STATUS['error'] = None

        scripts_dir = Path(__file__).parent / 'scripts'
        script_path = scripts_dir / script

        cmd = [sys.executable, str(script_path), '--config', config_path] + args

        logger.info(f"Running: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Stream output
        for line in process.stdout:
            line = line.strip()
            if line:
                WORKFLOW_STATUS['logs'].append({
                    'time': datetime.now().isoformat(),
                    'message': line
                })
                LOG_QUEUE.put(line)

        process.wait()

        if process.returncode == 0:
            WORKFLOW_STATUS['logs'].append({
                'time': datetime.now().isoformat(),
                'message': f"✓ {script} completed successfully"
            })
        else:
            WORKFLOW_STATUS['error'] = f"{script} failed with exit code {process.returncode}"
            WORKFLOW_STATUS['logs'].append({
                'time': datetime.now().isoformat(),
                'message': f"✗ {WORKFLOW_STATUS['error']}"
            })

    except Exception as e:
        WORKFLOW_STATUS['error'] = str(e)
        WORKFLOW_STATUS['logs'].append({
            'time': datetime.now().isoformat(),
            'message': f"✗ Error: {str(e)}"
        })

    finally:
        WORKFLOW_STATUS['running'] = False
        WORKFLOW_STATUS['current_step'] = None


# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AUPAT - Abandoned Upstate Project Archive Tool</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #333;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #fff;
            font-family: monospace;
        }
        .subtitle {
            color: #888;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #4a9eff;
        }
        .stat-label {
            color: #888;
            text-transform: uppercase;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .action-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 25px;
        }
        .action-card h2 {
            color: #fff;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .action-card p {
            color: #888;
            margin-bottom: 20px;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #4a9eff;
            color: #fff;
            text-decoration: none;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #357abd;
        }
        .btn-secondary {
            background: #333;
        }
        .btn-secondary:hover {
            background: #444;
        }
        .status {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status.running {
            border-color: #4a9eff;
        }
        .status.error {
            border-color: #ff4444;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #444;
            margin-right: 8px;
        }
        .status-indicator.running {
            background: #4a9eff;
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .flash {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            background: #1a4d1a;
            border: 1px solid #2d662d;
            color: #90ee90;
        }
        .flash.error {
            background: #4d1a1a;
            border-color: #662d2d;
            color: #ff9090;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AUPAT</h1>
            <div class="subtitle">Abandoned Upstate Project Archive Tool</div>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="status {% if status.running %}running{% elif status.error %}error{% endif %}">
            <h2>
                <span class="status-indicator {% if status.running %}running{% endif %}"></span>
                System Status
            </h2>
            <p>
                {% if status.running %}
                    Running: {{ status.current_step }}
                {% elif status.error %}
                    Error: {{ status.error }}
                {% else %}
                    Ready
                {% endif %}
            </p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.locations }}</div>
                <div class="stat-label">Locations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.sub_locations }}</div>
                <div class="stat-label">Sub-Locations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.images }}</div>
                <div class="stat-label">Images</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.videos }}</div>
                <div class="stat-label">Videos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.documents }}</div>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_files }}</div>
                <div class="stat-label">Total Files</div>
            </div>
        </div>

        <div class="actions">
            <div class="action-card">
                <h2>Import Media</h2>
                <p>Import new location and associated media files into the archive.</p>
                <a href="/import" class="btn">Start Import</a>
            </div>

            <div class="action-card">
                <h2>Run Workflow</h2>
                <p>Execute the complete AUPAT workflow to process and organize media.</p>
                <a href="/workflow" class="btn">Run Workflow</a>
            </div>

            <div class="action-card">
                <h2>View Logs</h2>
                <p>View recent activity logs and workflow execution details.</p>
                <a href="/logs" class="btn btn-secondary">View Logs</a>
            </div>

            <div class="action-card">
                <h2>Database</h2>
                <p>Initialize or update the database schema.</p>
                <a href="/migrate" class="btn btn-secondary">Run Migration</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

IMPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Import Media - AUPAT</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #333;
        }
        h1 {
            font-size: 2em;
            color: #fff;
        }
        .form-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 30px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #ccc;
            font-weight: 500;
        }
        input[type="text"],
        input[type="file"],
        select,
        textarea {
            width: 100%;
            padding: 12px;
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 1em;
        }
        input[type="text"]:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #4a9eff;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        .btn {
            padding: 12px 24px;
            background: #4a9eff;
            color: #fff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #357abd;
        }
        .btn-secondary {
            background: #333;
            margin-left: 10px;
        }
        .btn-secondary:hover {
            background: #444;
        }
        .help-text {
            font-size: 0.9em;
            color: #888;
            margin-top: 5px;
        }
        .back-link {
            color: #4a9eff;
            text-decoration: none;
            margin-bottom: 20px;
            display: inline-block;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .uuid-display {
            background: #0a0a0a;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            color: #4a9eff;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>

        <header>
            <h1>Import Media</h1>
        </header>

        <div class="form-card">
            <form method="POST" action="/import/submit">
                <div class="form-group">
                    <label>Location UUID</label>
                    <div class="uuid-display">{{ uuid }}</div>
                    <input type="hidden" name="loc_uuid" value="{{ uuid }}">
                    <div class="help-text">Automatically generated unique identifier</div>
                </div>

                <div class="form-group">
                    <label for="loc_name">Location Name *</label>
                    <input type="text" id="loc_name" name="loc_name" required>
                    <div class="help-text">E.g., "Abandoned Factory Building"</div>
                </div>

                <div class="form-group">
                    <label for="aka_name">Also Known As (AKA)</label>
                    <input type="text" id="aka_name" name="aka_name">
                    <div class="help-text">Alternative names for this location</div>
                </div>

                <div class="form-group">
                    <label for="state">State *</label>
                    <input type="text" id="state" name="state" required maxlength="2" placeholder="NY">
                    <div class="help-text">Two-letter state code (e.g., NY, PA, MA)</div>
                </div>

                <div class="form-group">
                    <label for="type">Location Type *</label>
                    <select id="type" name="type" required>
                        <option value="">Select type...</option>
                        <option value="commercial">Commercial</option>
                        <option value="residential">Residential</option>
                        <option value="industrial">Industrial</option>
                        <option value="institutional">Institutional</option>
                        <option value="recreational">Recreational</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="sub_type">Sub Type</label>
                    <input type="text" id="sub_type" name="sub_type">
                    <div class="help-text">E.g., "Factory", "School", "Hotel"</div>
                </div>

                <div class="form-group">
                    <label for="source_dir">Source Directory *</label>
                    <input type="text" id="source_dir" name="source_dir" required>
                    <div class="help-text">Absolute path to directory containing media files</div>
                </div>

                <div class="form-group">
                    <label for="imp_author">Author</label>
                    <input type="text" id="imp_author" name="imp_author">
                    <div class="help-text">Person/organization importing this media</div>
                </div>

                <div class="form-group">
                    <button type="submit" class="btn">Import Media</button>
                    <a href="/" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

LOGS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Logs - AUPAT</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 2px solid #333;
        }
        h1 {
            color: #fff;
        }
        .back-link {
            color: #4a9eff;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 15px;
        }
        .log-container {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #222;
        }
        .log-time {
            color: #888;
            margin-right: 10px;
        }
        .log-message {
            color: #ccc;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>

        <header>
            <h1>Activity Logs</h1>
            <p style="color: #888;">Auto-refreshes every 5 seconds</p>
        </header>

        <div class="log-container">
            {% if logs %}
                {% for log in logs %}
                    <div class="log-entry">
                        <span class="log-time">{{ log.time }}</span>
                        <span class="log-message">{{ log.message }}</span>
                    </div>
                {% endfor %}
            {% else %}
                <div style="color: #888;">No log entries yet</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


# Routes
@app.route('/')
def index():
    """Home page with dashboard."""
    config = load_config()
    stats = get_db_stats(config)

    return render_template_string(
        HOME_TEMPLATE,
        stats=stats,
        status=WORKFLOW_STATUS
    )


@app.route('/import')
def import_form():
    """Show import form."""
    uuid = generate_uuid()
    return render_template_string(IMPORT_TEMPLATE, uuid=uuid)


@app.route('/import/submit', methods=['POST'])
def import_submit():
    """Handle import form submission."""
    try:
        # Get form data
        data = {
            'loc_uuid': request.form.get('loc_uuid'),
            'loc_name': request.form.get('loc_name'),
            'aka_name': request.form.get('aka_name'),
            'state': request.form.get('state'),
            'type': request.form.get('type'),
            'sub_type': request.form.get('sub_type'),
            'source_dir': request.form.get('source_dir'),
            'imp_author': request.form.get('imp_author')
        }

        # Validate source directory
        if not Path(data['source_dir']).exists():
            flash('Source directory does not exist', 'error')
            return redirect(url_for('import_form'))

        # Normalize data
        data['loc_name'] = normalize_location_name(data['loc_name'])
        data['state'] = normalize_state_code(data['state'])
        data['type'] = normalize_location_type(data['type'])
        if data['sub_type']:
            data['sub_type'] = normalize_sub_type(data['sub_type'])
        if data['imp_author']:
            data['imp_author'] = normalize_author(data['imp_author'])

        # Run import in background
        args = ['--source', data['source_dir']]
        thread = threading.Thread(
            target=run_workflow_step,
            args=('db_import.py', args, 'user/user.json')
        )
        thread.daemon = True
        thread.start()

        flash(f"Import started for {data['loc_name']}", 'success')
        return redirect(url_for('logs'))

    except Exception as e:
        flash(f"Import failed: {str(e)}", 'error')
        return redirect(url_for('import_form'))


@app.route('/workflow')
def run_workflow():
    """Run the complete workflow."""
    if WORKFLOW_STATUS['running']:
        flash('Workflow is already running', 'error')
        return redirect(url_for('index'))

    # Run workflow in background
    thread = threading.Thread(
        target=run_workflow_step,
        args=('run_workflow.py', [], 'user/user.json')
    )
    thread.daemon = True
    thread.start()

    flash('Workflow started', 'success')
    return redirect(url_for('logs'))


@app.route('/migrate')
def run_migrate():
    """Run database migration."""
    if WORKFLOW_STATUS['running']:
        flash('A script is already running', 'error')
        return redirect(url_for('index'))

    # Run migration in background
    thread = threading.Thread(
        target=run_workflow_step,
        args=('db_migrate.py', [], 'user/user.json')
    )
    thread.daemon = True
    thread.start()

    flash('Database migration started', 'success')
    return redirect(url_for('logs'))


@app.route('/logs')
def logs():
    """Show activity logs."""
    return render_template_string(
        LOGS_TEMPLATE,
        logs=WORKFLOW_STATUS['logs'][-100:]  # Last 100 entries
    )


@app.route('/api/status')
def api_status():
    """API endpoint for status."""
    return jsonify(WORKFLOW_STATUS)


def main():
    """Start the web interface."""
    import argparse

    parser = argparse.ArgumentParser(description='AUPAT Web Interface')
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("AUPAT Web Interface Starting")
    logger.info("="*60)
    logger.info(f"URL: http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
