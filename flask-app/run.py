"""
Entry point for the Smart Digital Complaint Management System.

Demonstrates: Functions, Decorators, Exception Handling, Logging
"""

import os
import logging
from app import create_app, db
from app.utils.seed import seed_database

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


def initialize_app(app):
    """Initialize the application: create tables and optionally seed data."""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created / verified.")
        if os.environ.get("SEED_DB", "true").lower() == "true":
            seed_database()


def main():
    """Bootstrap and run the Flask development server."""
    config_name = os.environ.get("FLASK_ENV", "development")
    app = create_app(config_name)

    try:
        initialize_app(app)
        port = int(os.environ.get("PORT", 5000))
        debug = config_name == "development"
        logger.info("Starting Complaint Management System on port %d", port)
        app.run(host="0.0.0.0", port=port, debug=debug)
    except Exception as exc:
        logger.exception("Failed to start application: %s", exc)
        raise


if __name__ == "__main__":
    main()
