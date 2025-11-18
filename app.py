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

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['DB_PATH'] = os.environ.get('DB_PATH', '/app/data/aupat.db')
app.config['JSON_SORT_KEYS'] = False

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
        'documentation': 'https://github.com/bizzlechizzle/aupat'
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

    logger.info(f"Starting AUPAT Core API v0.1.2")
    logger.info(f"Database: {app.config['DB_PATH']}")
    logger.info(f"Server will listen on http://0.0.0.0:5002")
    logger.info(f"Desktop app should connect to http://localhost:5002")

    # Run Flask app
    # Use 0.0.0.0 to bind to all interfaces (required for Docker)
    app.run(host='0.0.0.0', port=5002, debug=False)
