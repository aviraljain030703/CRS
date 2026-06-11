"""
Notification model.

Demonstrates: OOP, Encapsulation
"""

from datetime import datetime
from app import db


class Notification(db.Model):
    """
    In-app notification delivered to a user.

    Demonstrates: OOP, Encapsulation (is_read managed via method)
    """

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default="info")  # info|success|warning|danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="notifications")

    # ------------------------------------------------------------------ #
    # Encapsulated state transition                                        #
    # ------------------------------------------------------------------ #
    def mark_read(self) -> None:
        """Mark this notification as read (encapsulates state mutation)."""
        self.is_read = True

    @classmethod
    def create(
        cls,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
    ) -> "Notification":
        """Factory method to build and stage a notification."""
        from app import db as _db

        notif = cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        _db.session.add(notif)
        return notif

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Notification {self.id} user={self.user_id} read={self.is_read}>"
