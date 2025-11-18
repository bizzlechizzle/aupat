#!/usr/bin/env python3
"""
AUPAT v0.1.2 Flask Application
Main entry point for AUPAT Core API server

Serves REST API endpoints for:
- Health checks
- Map marker data
- Location details
- Media queries
- Search functionality
"""

import os
import logging
from pathlib import Path
from flask import Flask
from flasgger import Swagger
from scripts.api_routes_v012 import register_api_routes
from scripts.api_sync_mobile import register_mobile_sync_routes
from scripts.api_routes_bookmarks import bookmarks_bp
from scripts.api_maps import api_maps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_external_tools_on_startup():
    """
    Check for optional external tools and log warnings if missing.

    This provides immediate feedback on startup rather than waiting for
    users to discover missing tools when trying to upload media.

    Tools checked:
    - exiftool: Required for EXIF GPS extraction from photos
    - ffmpeg/ffprobe: Required for video metadata extraction

    Note: Missing tools don't prevent app startup (graceful degradation).
    """
    import subprocess

    tools_status = []

    # Check exiftool
    try:
        result = subprocess.run(['exiftool', '-ver'], capture_output=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.decode().strip()
            logger.info(f"exiftool found (version {version})")
            tools_status.append(True)
        else:
            logger.warning("exiftool found but not working properly")
            logger.warning("  Install: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Linux)")
            tools_status.append(False)
    except FileNotFoundError:
        logger.warning("exiftool NOT FOUND - GPS/EXIF extraction will not work")
        logger.warning("  Install: brew install exiftool (macOS) or apt-get install libimage-exiftool-perl (Linux)")
        tools_status.append(False)
    except Exception as e:
        logger.warning(f"Could not check exiftool: {e}")
        tools_status.append(False)

    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.decode().split('\n')[0]
            logger.info(f"ffmpeg found ({version_line.split()[2]})")
            tools_status.append(True)
        else:
            logger.warning("ffmpeg found but not working properly")
            logger.warning("  Install: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
            tools_status.append(False)
    except FileNotFoundError:
        logger.warning("ffmpeg NOT FOUND - video metadata extraction will not work")
        logger.warning("  Install: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        tools_status.append(False)
    except Exception as e:
        logger.warning(f"Could not check ffmpeg: {e}")
        tools_status.append(False)

    # Summary
    if all(tools_status):
        logger.info("All external media tools available")
    elif any(tools_status):
        logger.warning("Some external media tools missing - functionality will be limited")
    else:
        logger.warning("No external media tools found - metadata extraction disabled")


# Create Flask app
app = Flask(__name__)

# Configure app
app.config['DB_PATH'] = os.environ.get('DB_PATH', '/app/data/aupat.db')
app.config['JSON_SORT_KEYS'] = False

# Configure Swagger/OpenAPI documentation
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "AUPAT Core API",
        "description": "Location-centric digital archive management system for abandoned and historical places",
        "version": "0.1.2",
        "contact": {
            "name": "AUPAT Project",
            "url": "https://github.com/bizzlechizzle/aupat"
        }
    },
    "host": os.environ.get('API_HOST', 'localhost:5002'),
    "basePath": "/",
    "schemes": ["http", "https"],
    "tags": [
        {"name": "health", "description": "Health check and service status endpoints"},
        {"name": "locations", "description": "Location CRUD operations"},
        {"name": "map", "description": "Map markers and GeoJSON data"},
        {"name": "media", "description": "Images, videos, and archives"},
        {"name": "search", "description": "Location search and autocomplete"},
        {"name": "bookmarks", "description": "Browser bookmark integration"},
        {"name": "maps", "description": "Map file import (KML, GeoJSON, CSV)"},
        {"name": "mobile", "description": "Mobile app sync endpoints"},
        {"name": "config", "description": "Configuration management"}
    ]
}

# Initialize Swagger
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Register v0.1.2 API routes
register_api_routes(app)

# Register mobile sync API routes
register_mobile_sync_routes(app)

# Register bookmarks API routes
app.register_blueprint(bookmarks_bp, url_prefix='/api')

# Register map import API routes
app.register_blueprint(api_maps)

# Root endpoint
@app.route('/')
def index():
    """Root endpoint - API information"""
    return {
        'name': 'AUPAT Core API',
        'version': '0.1.2',
        'description': 'Location-centric digital archive management system',
        'endpoints': {
            'health': '/api/health',
            'services': '/api/health/services',
            'map_markers': '/api/map/markers',
            'locations': '/api/locations/{loc_uuid}',
            'search': '/api/search',
            'mobile_sync_push': '/api/sync/mobile',
            'mobile_sync_pull': '/api/sync/mobile/pull'
        },
        'documentation': {
            'interactive_api_docs': '/api/docs',
            'openapi_spec': '/api/apispec.json',
            'github': 'https://github.com/bizzlechizzle/aupat'
        }
    }

if __name__ == '__main__':
    # Ensure database path exists
    db_path = Path(app.config['DB_PATH'])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database if it doesn't exist
    if not db_path.exists():
        logger.warning(f"Database not found at {db_path}")
        logger.info("Run 'python scripts/db_migrate_v012.py' to initialize the database")
        logger.info("Alternatively, the database will be created automatically on first write operation")

    # Check external tools availability
    check_external_tools_on_startup()

    logger.info(f"Starting AUPAT Core API v0.1.2")
    logger.info(f"Database: {app.config['DB_PATH']}")
    logger.info(f"Server will listen on http://0.0.0.0:5002")
    logger.info(f"Desktop app should connect to http://localhost:5002")

    # Run Flask app
    # Use 0.0.0.0 to bind to all interfaces (required for Docker)
    app.run(host='0.0.0.0', port=5002, debug=False)
