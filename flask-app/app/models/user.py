"""
User model.

Demonstrates: OOP, Encapsulation, Inheritance, Exception Handling
"""

import logging
from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt

logger = logging.getLogger(__name__)


class TimestampMixin:
    """
    Mixin providing created_at / updated_at timestamps.
    Demonstrates: Inheritance (used as mixin base)
    """
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    """
    Represents a system user (student or admin).

    Demonstrates:
    - OOP: class with attributes and methods
    - Encapsulation: _password_hash is private
    - Inheritance: extends UserMixin, TimestampMixin, db.Model
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # Encapsulated — never stored plain-text
    _password_hash = db.Column("password_hash", db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="student")  # student | admin
    is_active = db.Column(db.Boolean, default=True)

    # Relationships — foreign_keys specified to avoid ambiguity with assigned_to
    complaints = db.relationship(
        "Complaint",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="Complaint.user_id",
    )
    notifications = db.relationship(
        "Notification", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------ #
    # Password encapsulation (property + setter)                          #
    # ------------------------------------------------------------------ #
    @property
    def password(self):
        """Encapsulation: password is write-only."""
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_text: str) -> None:
        """Hash and store password securely (bcrypt)."""
        if len(plain_text) < 6:
            raise ValueError("Password must be at least 6 characters.")
        self._password_hash = bcrypt.generate_password_hash(plain_text).decode("utf-8")

    def check_password(self, plain_text: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        try:
            return bcrypt.check_password_hash(self._password_hash, plain_text)
        except Exception as exc:
            logger.warning("Password check failed for user %s: %s", self.email, exc)
            return False

    # ------------------------------------------------------------------ #
    # Role helpers                                                         #
    # ------------------------------------------------------------------ #
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        """Return a JSON-safe representation (excludes password)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "student_id": self.student_id,
            "department": self.department,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
