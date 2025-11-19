#!/usr/bin/env python3
"""
AUPAT v0.1.0 API Routes Registration

Registers all v0.1.0 API blueprints:
- Import (POST /api/import)
- Locations (GET/PUT/DELETE /api/locations)
- Map (GET /api/map/markers, /api/map/states, /api/map/types)
- Notes (GET/POST/PUT/DELETE /api/notes)
- Settings (GET/PUT /api/settings)
- Bookmarks (uses existing api_routes_bookmarks.py)

LILBITS: One function - register all v0.1.0 routes
"""

import logging

from scripts.api_v010_import import import_bp
from scripts.api_v010_locations import locations_bp
from scripts.api_v010_map import map_bp
from scripts.api_v010_notes import notes_bp
from scripts.api_v010_settings import settings_bp
from scripts.api_v010_stats import stats_bp
from scripts.api_routes_bookmarks import bookmarks_bp


logger = logging.getLogger(__name__)


def register_v010_routes(app):
    """
    Register all v0.1.0 API routes.

    This is a clean implementation with ONLY v0.1.0 features.
    NO v0.1.2+ features (Google Maps import, mobile sync, etc.)

    Args:
        app: Flask application instance
    """
    # Register import routes
    app.register_blueprint(import_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 import routes")

    # Register locations routes
    app.register_blueprint(locations_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 locations routes")

    # Register map routes
    app.register_blueprint(map_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 map routes")

    # Register notes routes
    app.register_blueprint(notes_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 notes routes")

    # Register settings routes
    app.register_blueprint(settings_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 settings routes")

    # Register bookmarks routes (reuses existing)
    app.register_blueprint(bookmarks_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 bookmarks routes")

    # Register stats routes
    app.register_blueprint(stats_bp, url_prefix='/api')
    logger.info("Registered v0.1.0 stats routes")

    logger.info("All v0.1.0 API routes registered successfully")
