"""
Complaint model.

Demonstrates: OOP, Encapsulation, Generators (complaint_history_generator)
"""

import logging
from datetime import datetime
from app import db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enumerations (using plain string constants + lists for Flask/SQLite compat)
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Hostel", "Library", "Transport", "Network", "Canteen",
    "Academic", "Infrastructure", "Sports", "Medical", "Other",
]

PRIORITIES = ["Low", "Medium", "High", "Critical"]

STATUSES = ["Pending", "In Progress", "Resolved", "Rejected", "Escalated"]


def generate_complaint_number() -> str:
    """
    Generate a unique complaint number.
    Demonstrates: Function
    """
    import random, string
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CMP-{ts}-{suffix}"


class Complaint(db.Model):
    """
    Represents a student complaint.

    Demonstrates: OOP, Encapsulation, Properties
    """

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    complaint_number = db.Column(
        db.String(40), unique=True, nullable=False, default=generate_complaint_number
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Other")
    priority = db.Column(db.String(20), nullable=False, default="Low")
    status = db.Column(db.String(30), nullable=False, default="Pending")
    attachment = db.Column(db.String(300), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    admin_response = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], back_populates="complaints")
    assignee = db.relationship("User", foreign_keys=[assigned_to])
    logs = db.relationship(
        "ComplaintLog", back_populates="complaint", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------ #
    # Properties (Encapsulation)                                          #
    # ------------------------------------------------------------------ #
    @property
    def is_resolved(self) -> bool:
        return self.status == "Resolved"

    @property
    def priority_badge(self) -> str:
        """Return Bootstrap badge class for priority."""
        badges = {
            "Low": "success", "Medium": "warning",
            "High": "danger", "Critical": "dark"
        }
        return badges.get(self.priority, "secondary")

    @property
    def status_badge(self) -> str:
        """Return Bootstrap badge class for status."""
        badges = {
            "Pending": "warning", "In Progress": "info",
            "Resolved": "success", "Rejected": "danger", "Escalated": "primary"
        }
        return badges.get(self.status, "secondary")

    # ------------------------------------------------------------------ #
    # Generator — lazily yields log history                               #
    # Demonstrates: Generators                                            #
    # ------------------------------------------------------------------ #
    def complaint_history_generator(self):
        """
        Generator that yields complaint log entries one at a time.
        Demonstrates: Generators (yield)
        """
        for log in self.logs.order_by("timestamp"):
            yield {
                "old_status": log.old_status,
                "new_status": log.new_status,
                "updated_by": log.updated_by,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "remarks": log.remarks,
            }

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "complaint_number": self.complaint_number,
            "user_id": self.user_id,
            "student_name": self.user.name if self.user else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "attachment": self.attachment,
            "admin_response": self.admin_response,
            "assigned_to": self.assigned_to,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Complaint {self.complaint_number} [{self.status}]>"
