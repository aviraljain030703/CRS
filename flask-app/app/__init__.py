"""
Flask application factory.

Demonstrates: Functions, Decorators, OOP
"""

import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail

from app.config import config_registry, BaseConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extension singletons (initialised per-app via init_app pattern)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
login_manager = LoginManager()
mail = Mail()


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory — creates and configures a Flask instance.

    :param config_name: One of 'development', 'production', 'testing'.
    :returns: Configured Flask application.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    cfg_class = config_registry.get(config_name, config_registry["development"])
    cfg = cfg_class()
    app.config.from_object(cfg)
    # Materialise property-based URI into the config dict
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg.SQLALCHEMY_DATABASE_URI
    cfg.init_app(app)

    # ------------------------------------------------------------------
    # Initialise extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure CORS with security in mind
    cors_config = {
        r"/api/*": {
            "origins": "*" if config_name == "development" else app.config.get("CORS_ORIGINS", "").split(","),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    }
    CORS(app, resources=cors_config)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # ------------------------------------------------------------------
    # Security headers for all responses
    # ------------------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains" if app.config.get("PREFERRED_URL_SCHEME") == "https" else ""
        return response

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        logger.warning(f"404 Not Found: {error}")
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"500 Internal Server Error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors."""
        logger.warning(f"403 Forbidden: {error}")
        return jsonify({"error": "Access denied"}), 403

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.complaints import complaints_bp
    from app.routes.admin import admin_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ------------------------------------------------------------------
    # User loader for Flask-Login
    # ------------------------------------------------------------------
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # ------------------------------------------------------------------
    # Health check endpoint
    # ------------------------------------------------------------------
    @app.route("/api/meta", methods=["GET"])
    def meta():
        """Health check endpoint for monitoring."""
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "environment": config_name
        })

    logger.info("Flask app created with config: %s", config_name)
    return app
