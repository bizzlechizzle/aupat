#!/usr/bin/env python3
"""
AUPAT Web Interface
Professional web application matching Abandoned Upstate design system.

Design System:
- Light: Cream (#fffbf7) background, dark gray (#454545) text
- Dark: Dark gray (#474747) background, cream (#fffbf7) text
- Accent: Warm brown (#b9975c)
- Typography: Roboto Mono (headings), Lora (body)

Features:
- Dashboard with statistics
- Locations browser
- Archive manager
- Import interface
- Real-time progress tracking

Version: 3.0.0
Last Updated: 2025-11-16
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
from typing import Dict, List, Optional

from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session
)

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from utils import generate_uuid
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


def load_config(config_path: str = 'user/user.json') -> dict:
    """Load user configuration."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def get_db_connection(config: dict):
    """Get database connection."""
    db_path = config.get('db_loc', 'aupat.db')
    if not Path(db_path).exists():
        return None
    return sqlite3.connect(db_path)


def get_dashboard_stats(config: dict) -> Dict:
    """Get dashboard statistics."""
    stats = {
        'locations': 0,
        'sub_locations': 0,
        'images': 0,
        'videos': 0,
        'documents': 0,
        'total_files': 0,
        'recent_imports': [],
        'storage_used': '0 GB'
    }

    try:
        conn = get_db_connection(config)
        if not conn:
            return stats

        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM locations")
        stats['locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sub_locations")
        stats['sub_locations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM images")
        stats['images'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM videos")
        stats['videos'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents")
        stats['documents'] = cursor.fetchone()[0]

        stats['total_files'] = stats['images'] + stats['videos'] + stats['documents']

        # Get recent imports
        cursor.execute("""
            SELECT loc_name, state, type, loc_add
            FROM locations
            ORDER BY loc_add DESC
            LIMIT 5
        """)
        stats['recent_imports'] = [
            {'name': row[0], 'state': row[1], 'type': row[2], 'date': row[3]}
            for row in cursor.fetchall()
        ]

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")

    return stats


def get_locations_list(config: dict, page: int = 1, per_page: int = 20) -> tuple:
    """Get paginated locations list."""
    locations = []
    total = 0

    try:
        conn = get_db_connection(config)
        if not conn:
            return locations, total

        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM locations")
        total = cursor.fetchone()[0]

        # Get page of locations
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT
                loc_uuid,
                loc_name,
                aka_name,
                state,
                type,
                sub_type,
                loc_add,
                (SELECT COUNT(*) FROM images WHERE loc_uuid = locations.loc_uuid) as img_count,
                (SELECT COUNT(*) FROM videos WHERE loc_uuid = locations.loc_uuid) as vid_count
            FROM locations
            ORDER BY loc_add DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        locations = [
            {
                'uuid': row[0],
                'uuid8': row[0][:8],
                'name': row[1],
                'aka_name': row[2],
                'state': row[3],
                'type': row[4],
                'sub_type': row[5],
                'added': row[6],
                'images': row[7],
                'videos': row[8]
            }
            for row in cursor.fetchall()
        ]

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get locations: {e}")

    return locations, total


# Base HTML template with Abandoned Upstate design
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AUPAT{% endblock %} - Archive Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Lora:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root, html[data-theme="light"] {
            --background: #fffbf7;
            --foreground: #454545;
            --accent: #b9975c;
            --muted: #e6e6e6;
            --border: #b9975c;
            --header-bg: #45372b;
            --header-fg: #fbfbfb;
        }

        html[data-theme="dark"] {
            --background: #474747;
            --foreground: #fffbf7;
            --accent: #b9975c;
            --muted: #343f60;
            --border: #b9975c;
            --header-bg: #45372b;
            --header-fg: #fbfbfb;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Lora', Georgia, serif;
            font-size: clamp(1rem, 0.95rem + 0.4vw, 1.125rem);
            line-height: 1.65;
            background: var(--background);
            color: var(--foreground);
            transition: background 0.3s, color 0.3s;
        }

        h1, h2, h3 {
            font-family: 'Roboto Mono', monospace;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: 0.05em;
            margin: 0 0 0.5em;
        }

        h1 {
            font-size: clamp(2.25rem, 1.6rem + 3.5vw, 3.5rem);
            text-transform: uppercase;
        }

        h2 {
            font-size: clamp(1.6rem, 1.3rem + 2vw, 2.25rem);
        }

        h3 {
            font-size: clamp(1.25rem, 1.1rem + 1.2vw, 1.6rem);
        }

        .header {
            background: var(--header-bg);
            color: var(--header-fg);
            padding: 1.5rem 2rem;
            border-bottom: 3px solid var(--accent);
        }

        .header-content {
            max-width: 64rem;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .site-title {
            font-size: 1.5rem;
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin: 0;
        }

        .nav {
            display: flex;
            gap: 2rem;
            align-items: center;
        }

        .nav a {
            color: var(--header-fg);
            text-decoration: none;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 0.5rem 0;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }

        .nav a:hover,
        .nav a.active {
            border-bottom-color: var(--accent);
        }

        /* File explorer modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--background);
            border: 2px solid var(--accent);
            border-radius: 8px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }

        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            margin: 0;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--foreground);
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }

        .modal-footer {
            padding: 1.5rem;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 1rem;
        }

        .file-explorer {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .current-path {
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            padding: 0.75rem;
            background: var(--muted);
            border-radius: 4px;
            word-break: break-all;
        }

        .directory-list {
            list-style: none;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 4px;
        }

        .directory-item {
            padding: 0.75rem 1rem;
            cursor: pointer;
            border-bottom: 1px solid var(--muted);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            transition: background 0.2s;
        }

        .directory-item:last-child {
            border-bottom: none;
        }

        .directory-item:hover {
            background: rgba(185, 151, 92, 0.1);
        }

        .directory-item.parent {
            color: var(--accent);
            font-weight: 600;
        }

        .directory-icon {
            font-size: 1.2rem;
        }

        .input-with-browse {
            display: flex;
            gap: 0.5rem;
            align-items: stretch;
        }

        .input-with-browse input {
            flex: 1;
        }

        .btn-browse {
            padding: 0.75rem 1rem;
            white-space: nowrap;
        }

        .settings-info {
            background: rgba(185, 151, 92, 0.1);
            border: 1px solid var(--accent);
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        .settings-info p {
            margin: 0;
            font-size: 0.9rem;
        }

        .theme-toggle {
            background: none;
            border: 2px solid var(--header-fg);
            color: var(--header-fg);
            width: 36px;
            height: 36px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .theme-toggle:hover {
            background: var(--accent);
            border-color: var(--accent);
        }

        .container {
            max-width: 64rem;
            margin: 0 auto;
            padding: 2rem;
        }

        .card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.2s;
        }

        .card:hover {
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(185, 151, 92, 0.15);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--background);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }

        .stat-number {
            font-family: 'Roboto Mono', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }

        .stat-label {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--foreground);
            opacity: 0.8;
        }

        .btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: var(--accent);
            color: var(--background);
            text-decoration: none;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover {
            background: var(--foreground);
            color: var(--background);
        }

        .btn-secondary {
            background: var(--muted);
            color: var(--foreground);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .location-list {
            list-style: none;
        }

        .location-item {
            border-bottom: 1px solid var(--muted);
            padding: 1rem 0;
        }

        .location-item:last-child {
            border-bottom: none;
        }

        .location-name {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 0.25rem;
        }

        .location-meta {
            font-size: 0.85rem;
            color: var(--foreground);
            opacity: 0.7;
            font-family: 'Roboto Mono', monospace;
        }

        .flash {
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            background: rgba(185, 151, 92, 0.1);
            border: 1px solid var(--accent);
        }

        .flash.error {
            background: rgba(220, 53, 69, 0.1);
            border-color: #dc3545;
            color: #dc3545;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--foreground);
            font-family: 'Lora', Georgia, serif;
            font-size: 1rem;
        }

        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(185, 151, 92, 0.1);
        }

        .help-text {
            font-size: 0.85rem;
            margin-top: 0.25rem;
            opacity: 0.7;
        }

        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 1rem;
            }

            .nav {
                flex-wrap: wrap;
                justify-content: center;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script>
        // Theme toggle functionality
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            const icon = document.querySelector('.theme-toggle');
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀' : '☾';
            }
        }

        // Load saved theme on page load
        document.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcon(savedTheme);
        });

        // File explorer functionality
        let currentPath = '/';
        let currentInputField = null;

        function openFileExplorer(inputId) {
            currentInputField = inputId;
            const input = document.getElementById(inputId);
            const startPath = input.value || '/home';
            currentPath = startPath;

            const modal = document.getElementById('fileExplorerModal');
            modal.classList.add('active');

            loadDirectory(currentPath);
        }

        function closeFileExplorer() {
            const modal = document.getElementById('fileExplorerModal');
            modal.classList.remove('active');
            currentInputField = null;
        }

        function selectDirectory() {
            if (currentInputField && currentPath) {
                const input = document.getElementById(currentInputField);
                input.value = currentPath;
            }
            closeFileExplorer();
        }

        async function loadDirectory(path) {
            try {
                const response = await fetch('/api/browse?path=' + encodeURIComponent(path));
                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }

                currentPath = data.current_path;
                displayDirectory(data);
            } catch (error) {
                alert('Failed to load directory: ' + error);
            }
        }

        function displayDirectory(data) {
            document.getElementById('currentPath').textContent = data.current_path;

            const list = document.getElementById('directoryList');
            list.innerHTML = '';

            // Add parent directory link if not at root
            if (data.parent_path) {
                const li = document.createElement('li');
                li.className = 'directory-item parent';
                li.innerHTML = '<span class="directory-icon">⬆️</span> ..';
                li.onclick = () => loadDirectory(data.parent_path);
                list.appendChild(li);
            }

            // Add directories
            data.directories.forEach(dir => {
                const li = document.createElement('li');
                li.className = 'directory-item';
                li.innerHTML = '<span class="directory-icon">📁</span> ' + dir.name;
                li.onclick = () => loadDirectory(dir.path);
                list.appendChild(li);
            });

            // Show message if no directories
            if (data.directories.length === 0 && !data.parent_path) {
                const li = document.createElement('li');
                li.className = 'directory-item';
                li.style.opacity = '0.6';
                li.style.cursor = 'default';
                li.textContent = 'No subdirectories';
                list.appendChild(li);
            }
        }

        // Close modal when clicking outside
        document.addEventListener('DOMContentLoaded', () => {
            const modal = document.getElementById('fileExplorerModal');
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        closeFileExplorer();
                    }
                });
            }
        });
    </script>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1 class="site-title">AUPAT</h1>
            <nav class="nav">
                <a href="/" class="{{ 'active' if request.path == '/' else '' }}">Dashboard</a>
                <a href="/locations" class="{{ 'active' if request.path == '/locations' else '' }}">Locations</a>
                <a href="/archives" class="{{ 'active' if request.path == '/archives' else '' }}">Archives</a>
                <a href="/import" class="{{ 'active' if request.path == '/import' else '' }}">Import</a>
                <a href="/settings" class="{{ 'active' if request.path == '/settings' else '' }}">Settings</a>
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">☾</button>
            </nav>
        </div>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer style="text-align: center; padding: 2rem; opacity: 0.6; font-size: 0.9rem;">
        <p>&copy; 2025 Abandoned Upstate Project Archive Tool</p>
    </footer>
</body>
</html>
"""

# Dashboard page
DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Archive Dashboard</h2>
<p style="margin-bottom: 2rem; opacity: 0.8;">Overview of your media archive and recent activity</p>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{{ stats.locations }}</div>
        <div class="stat-label">Locations</div>
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
        <div class="stat-number">{{ stats.total_files }}</div>
        <div class="stat-label">Total Files</div>
    </div>
</div>

<div class="card">
    <h3>Recent Imports</h3>
    {% if stats.recent_imports %}
        <ul class="location-list">
            {% for location in stats.recent_imports %}
                <li class="location-item">
                    <div class="location-name">{{ location.name }}</div>
                    <div class="location-meta">
                        {{ location.state | upper }} · {{ location.type | title }} · {{ location.date[:10] }}
                    </div>
                </li>
            {% endfor %}
        </ul>
    {% else %}
        <p style="opacity: 0.6;">No locations imported yet. <a href="/import" style="color: var(--accent);">Start importing</a></p>
    {% endif %}
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
    <div class="card">
        <h3>Quick Actions</h3>
        <p style="margin-bottom: 1rem;">Import new media or manage existing locations</p>
        <a href="/import" class="btn">Import Media</a>
    </div>
    <div class="card">
        <h3>System Status</h3>
        <p style="margin-bottom: 1rem;">
            {% if stats.locations > 0 %}
                <span style="color: var(--accent);">✓</span> Database initialized<br>
                <span style="color: var(--accent);">✓</span> {{ stats.total_files }} files archived
            {% else %}
                <span style="opacity: 0.6;">No data yet - import your first location to get started</span>
            {% endif %}
        </p>
    </div>
</div>
{% endblock %}
""")

# Locations page
LOCATIONS_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
    <div>
        <h2>Locations</h2>
        <p style="opacity: 0.8;">{{ total }} locations in archive</p>
    </div>
    <a href="/import" class="btn">Import New</a>
</div>

{% if locations %}
    <div class="card">
        {% for location in locations %}
            <div class="location-item">
                <div class="location-name">{{ location.name }}</div>
                {% if location.aka_name %}
                    <div style="font-style: italic; font-size: 0.9rem; margin-bottom: 0.25rem;">
                        Also known as: {{ location.aka_name }}
                    </div>
                {% endif %}
                <div class="location-meta">
                    UUID: {{ location.uuid8 }} ·
                    {{ location.state | upper }} ·
                    {{ location.type | title }}{% if location.sub_type %} ({{ location.sub_type | title }}){% endif %} ·
                    {{ location.images }} images ·
                    {{ location.videos }} videos
                </div>
            </div>
        {% endfor %}
    </div>

    {% if total > 20 %}
        <div style="text-align: center; margin-top: 2rem;">
            <p style="opacity: 0.6;">Showing first 20 locations</p>
        </div>
    {% endif %}
{% else %}
    <div class="card">
        <p style="text-align: center; opacity: 0.6;">
            No locations found. <a href="/import" style="color: var(--accent);">Import your first location</a>
        </p>
    </div>
{% endif %}
{% endblock %}
""")

# Import page
IMPORT_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Import Media</h2>
<p style="margin-bottom: 2rem; opacity: 0.8;">Import a new location and associated media files</p>

<div class="card">
    <form method="POST" action="/import/submit">
        <div class="form-group">
            <label>Location UUID</label>
            <input type="text" name="loc_uuid" value="{{ uuid }}" readonly style="opacity: 0.6; cursor: not-allowed;">
            <div class="help-text">Auto-generated unique identifier</div>
        </div>

        <div class="form-group">
            <label>Location Name *</label>
            <input type="text" name="loc_name" required placeholder="Abandoned Factory Building">
        </div>

        <div class="form-group">
            <label>Also Known As</label>
            <input type="text" name="aka_name" placeholder="Alternative names">
        </div>

        <div class="form-group">
            <label>State *</label>
            <input type="text" name="state" required maxlength="2" placeholder="NY" style="text-transform: uppercase;">
            <div class="help-text">Two-letter state code (e.g., NY, PA, VT)</div>
        </div>

        <div class="form-group">
            <label>Location Type *</label>
            <select name="type" required>
                <option value="">Select type...</option>
                <option value="industrial">Industrial</option>
                <option value="residential">Residential</option>
                <option value="commercial">Commercial</option>
                <option value="institutional">Institutional</option>
                <option value="recreational">Recreational</option>
                <option value="other">Other</option>
            </select>
        </div>

        <div class="form-group">
            <label>Sub Type</label>
            <input type="text" name="sub_type" placeholder="e.g., Factory, School, Hotel">
        </div>

        <div class="form-group">
            <label>Source Directory *</label>
            <input type="text" name="source_dir" required placeholder="/absolute/path/to/media">
            <div class="help-text">Absolute path to directory containing media files</div>
        </div>

        <div class="form-group">
            <label>Author</label>
            <input type="text" name="imp_author" placeholder="Your name">
        </div>

        <div style="display: flex; gap: 1rem; margin-top: 2rem;">
            <button type="submit" class="btn">Import Media</button>
            <a href="/" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
""")

# Settings page
SETTINGS_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Settings</h2>
<p style="margin-bottom: 2rem; opacity: 0.8;">Configure AUPAT system paths and options</p>

<div class="settings-info">
    <p><strong>Note:</strong> These settings are stored in <code>user/user.json</code>. All paths should be absolute paths.</p>
</div>

<div class="card">
    <form method="POST" action="/settings/save">
        <div class="form-group">
            <label>Database Name</label>
            <input type="text" name="db_name" id="db_name" value="{{ config.get('db_name', 'aupat.db') }}" required>
            <div class="help-text">Database filename (e.g., aupat.db)</div>
        </div>

        <div class="form-group">
            <label>Database Location</label>
            <div class="input-with-browse">
                <input type="text" name="db_loc" id="db_loc" value="{{ config.get('db_loc', '') }}" required placeholder="/absolute/path/to/database/aupat.db">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_loc')">Browse</button>
            </div>
            <div class="help-text">Absolute path to database file</div>
        </div>

        <div class="form-group">
            <label>Backup Location</label>
            <div class="input-with-browse">
                <input type="text" name="db_backup" id="db_backup" value="{{ config.get('db_backup', '') }}" required placeholder="/absolute/path/to/backups/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_backup')">Browse</button>
            </div>
            <div class="help-text">Directory for database backups</div>
        </div>

        <div class="form-group">
            <label>Ingest/Staging Location</label>
            <div class="input-with-browse">
                <input type="text" name="db_ingest" id="db_ingest" value="{{ config.get('db_ingest', '') }}" required placeholder="/absolute/path/to/ingest/staging/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('db_ingest')">Browse</button>
            </div>
            <div class="help-text">Staging area for incoming files before import</div>
        </div>

        <div class="form-group">
            <label>Archive Location</label>
            <div class="input-with-browse">
                <input type="text" name="arch_loc" id="arch_loc" value="{{ config.get('arch_loc', '') }}" required placeholder="/absolute/path/to/archive/">
                <button type="button" class="btn btn-browse" onclick="openFileExplorer('arch_loc')">Browse</button>
            </div>
            <div class="help-text">Archive root directory for organized media storage</div>
        </div>

        <div style="display: flex; gap: 1rem; margin-top: 2rem;">
            <button type="submit" class="btn">Save Settings</button>
            <a href="/" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>

<!-- File Explorer Modal -->
<div id="fileExplorerModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Select Directory</h3>
            <button class="modal-close" onclick="closeFileExplorer()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="file-explorer">
                <div class="current-path" id="currentPath">/</div>
                <ul class="directory-list" id="directoryList">
                    <li class="directory-item" style="opacity: 0.6;">Loading...</li>
                </ul>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeFileExplorer()">Cancel</button>
            <button class="btn" onclick="selectDirectory()">Select This Directory</button>
        </div>
    </div>
</div>
{% endblock %}
""")


# Routes
@app.route('/')
def dashboard():
    """Dashboard page."""
    config = load_config()
    stats = get_dashboard_stats(config)
    return render_template_string(DASHBOARD_TEMPLATE, stats=stats)


@app.route('/locations')
def locations():
    """Locations list page."""
    config = load_config()
    page = request.args.get('page', 1, type=int)
    locations_list, total = get_locations_list(config, page=page)
    return render_template_string(LOCATIONS_TEMPLATE, locations=locations_list, total=total)


@app.route('/archives')
def archives():
    """Archives page (placeholder)."""
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<h2>Archives</h2>
<p>Archive management coming soon...</p>
{% endblock %}
"""))


@app.route('/import')
def import_form():
    """Import form page."""
    config = load_config()
    conn = get_db_connection(config)
    if conn:
        cursor = conn.cursor()
        uuid = str(generate_uuid(cursor, 'locations', 'loc_uuid'))
        conn.close()
    else:
        uuid = 'database-not-initialized'
    return render_template_string(IMPORT_TEMPLATE, uuid=uuid)


@app.route('/import/submit', methods=['POST'])
def import_submit():
    """Handle import submission."""
    try:
        config = load_config()

        # Get and normalize form data
        data = {
            'loc_uuid': request.form.get('loc_uuid'),
            'loc_name': normalize_location_name(request.form.get('loc_name')),
            'aka_name': normalize_location_name(request.form.get('aka_name')) if request.form.get('aka_name') else None,
            'state': normalize_state_code(request.form.get('state')),
            'type': normalize_location_type(request.form.get('type')),
            'sub_type': normalize_sub_type(request.form.get('sub_type')) if request.form.get('sub_type') else None,
            'source_dir': request.form.get('source_dir'),
            'imp_author': normalize_author(request.form.get('imp_author')) if request.form.get('imp_author') else None
        }

        # Validate source directory
        if not Path(data['source_dir']).exists():
            flash('Source directory does not exist', 'error')
            return redirect(url_for('import_form'))

        # Run import script
        result = subprocess.run(
            [
                sys.executable,
                'scripts/db_import.py',
                '--source', data['source_dir'],
                '--config', 'user/user.json'
            ],
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result.returncode == 0:
            flash(f'Successfully imported {data["loc_name"]}', 'success')
            return redirect(url_for('locations'))
        else:
            flash(f'Import failed: {result.stderr}', 'error')
            return redirect(url_for('import_form'))

    except Exception as e:
        flash(f'Import error: {str(e)}', 'error')
        return redirect(url_for('import_form'))


@app.route('/settings')
def settings():
    """Settings page."""
    config = load_config()
    return render_template_string(SETTINGS_TEMPLATE, config=config)


@app.route('/settings/save', methods=['POST'])
def settings_save():
    """Save settings to user.json."""
    try:
        # Get form data
        new_config = {
            'db_name': request.form.get('db_name'),
            'db_loc': request.form.get('db_loc'),
            'db_backup': request.form.get('db_backup'),
            'db_ingest': request.form.get('db_ingest'),
            'arch_loc': request.form.get('arch_loc')
        }

        # Validate paths exist or can be created
        paths_to_check = ['db_backup', 'db_ingest', 'arch_loc']
        for path_key in paths_to_check:
            path = new_config.get(path_key)
            if path:
                path_obj = Path(path)
                # If it's a directory that doesn't exist, try to create it
                if not path_obj.exists():
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created directory: {path}")
                    except Exception as e:
                        flash(f'Warning: Could not create directory {path}: {str(e)}', 'error')

        # Save to user/user.json
        config_path = 'user/user.json'
        config_dir = Path('user')
        config_dir.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)

        flash('Settings saved successfully!', 'success')
        logger.info(f"Settings saved to {config_path}")
        return redirect(url_for('settings'))

    except Exception as e:
        flash(f'Failed to save settings: {str(e)}', 'error')
        logger.error(f"Failed to save settings: {e}")
        return redirect(url_for('settings'))


@app.route('/api/browse')
def api_browse():
    """Browse filesystem directories for file explorer."""
    try:
        path = request.args.get('path', '/home')
        path_obj = Path(path).resolve()

        # Security: Prevent directory traversal attacks
        # Only allow browsing within reasonable directories
        allowed_prefixes = ['/home', '/mnt', '/media', '/opt', '/var', '/srv']
        path_str = str(path_obj)
        if not any(path_str.startswith(prefix) for prefix in allowed_prefixes):
            return jsonify({'error': 'Access denied to this directory'}), 403

        if not path_obj.exists() or not path_obj.is_dir():
            return jsonify({'error': 'Directory does not exist'}), 404

        # Get directories
        directories = []
        try:
            for item in sorted(path_obj.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append({
                        'name': item.name,
                        'path': str(item)
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403

        # Get parent directory
        parent_path = None
        if path_obj != Path('/'):
            parent_path = str(path_obj.parent)

        return jsonify({
            'current_path': str(path_obj),
            'parent_path': parent_path,
            'directories': directories
        })

    except Exception as e:
        logger.error(f"Browse error: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """Start the web interface."""
    import argparse

    parser = argparse.ArgumentParser(description='AUPAT Web Interface v3.0')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AUPAT Web Interface v3.0 - Abandoned Upstate Design")
    logger.info("=" * 60)
    logger.info(f"URL: http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
