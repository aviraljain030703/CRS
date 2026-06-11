"""
Application configuration.

Demonstrates: OOP (Classes), Inheritance, Encapsulation, Abstraction
"""

import os
import logging
from datetime import timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


def _validate_secrets(env_name: str) -> None:
    """Validate that required secrets are configured for production."""
    if env_name == "production":
        secret_key = os.environ.get("SECRET_KEY", "").strip()
        jwt_secret = os.environ.get("JWT_SECRET_KEY", "").strip()
        
        if not secret_key or len(secret_key) < 16:
            raise ValueError(
                "ERROR: SECRET_KEY must be set and at least 16 characters in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if not jwt_secret or len(jwt_secret) < 16:
            raise ValueError(
                "ERROR: JWT_SECRET_KEY must be set and at least 16 characters in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


class BaseConfig(ABC):
    """
    Abstract base configuration.
    Demonstrates: Abstraction, Encapsulation
    """

    # Encapsulated secret — never exposed directly
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-2024")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}

    # Mail settings (optional)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    
    # Security headers
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True

    @property
    @abstractmethod
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Subclasses must define the database URI."""

    @staticmethod
    def init_app(app) -> None:
        """Hook for app-level initialisation."""
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


class DevelopmentConfig(BaseConfig):
    """
    Development configuration — SQLite for zero-dependency local dev.
    Demonstrates: Inheritance
    """

    DEBUG = True
    TESTING = False

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:  # type: ignore[override]
        # Use CMS_DATABASE_URL environment variable for database configuration
        return os.environ.get(
            "CMS_DATABASE_URL",
            "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "complaints_dev.db"),
        )


class ProductionConfig(BaseConfig):
    """
    Production configuration — MySQL via environment variable.
    Demonstrates: Inheritance, Polymorphism (overrides SQLALCHEMY_DATABASE_URI)
    """

    DEBUG = False
    TESTING = False
    PROPAGATE_EXCEPTIONS = True
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # Enforce security in production
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    def __init__(self):
        """Validate production configuration."""
        super().__init__()
        _validate_secrets("production")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:  # type: ignore[override]
        # CMS_DATABASE_URL takes precedence; falls back to SQLite
        uri = os.environ.get("CMS_DATABASE_URL")
        if not uri:
            logger.warning("CMS_DATABASE_URL not set; falling back to SQLite. Use MySQL for production!")
            return "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "complaints_prod.db")
        return uri


class TestingConfig(BaseConfig):
    """Testing configuration — in-memory SQLite."""

    TESTING = True
    DEBUG = True

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:  # type: ignore[override]
        return "sqlite:///:memory:"


# Registry of config objects — polymorphic dispatch by name
config_registry: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
