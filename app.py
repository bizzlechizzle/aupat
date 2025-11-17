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
            'search': '/api/search'
        },
        'documentation': 'https://github.com/bizzlechizzle/aupat'
    }

if __name__ == '__main__':
    # Ensure database path exists
    db_path = Path(app.config['DB_PATH'])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting AUPAT Core API v0.1.2")
    logger.info(f"Database: {app.config['DB_PATH']}")

    # Run Flask app
    # Use 0.0.0.0 to bind to all interfaces (required for Docker)
    app.run(host='0.0.0.0', port=5000, debug=False)
