"""
WSGI entry point for Gunicorn production server.

Usage:
    gunicorn "wsgi:application" --bind 0.0.0.0:5000 --workers 4
"""

import os
from app import create_app, db
from app.utils.seed import seed_database

application = create_app(os.environ.get("FLASK_ENV", "production"))

with application.app_context():
    db.create_all()
    seed_database()
