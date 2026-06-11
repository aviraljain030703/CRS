"""
ComplaintLog model — audit trail for every status change.

Demonstrates: OOP, Inheritance (TimestampMixin reuse), Encapsulation
"""

from datetime import datetime
from app import db


class ComplaintLog(db.Model):
    """
    Immutable audit record of a complaint status transition.

    Demonstrates: OOP, Inheritance (reuses db.Model)
    """

    __tablename__ = "complaint_logs"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False, index=True
    )
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    updated_by = db.Column(db.String(120), nullable=False)  # name / email of actor
    remarks = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    complaint = db.relationship("Complaint", back_populates="logs")

    @classmethod
    def record(
        cls,
        complaint_id: int,
        old_status: str,
        new_status: str,
        updated_by: str,
        remarks: str = "",
    ) -> "ComplaintLog":
        """
        Factory class-method — create and persist a log entry.
        Demonstrates: Class method, Factory pattern
        """
        from app import db as _db

        entry = cls(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=updated_by,
            remarks=remarks,
        )
        _db.session.add(entry)
        return entry

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "updated_by": self.updated_by,
            "remarks": self.remarks,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self) -> str:
        return f"<Log {self.complaint_id}: {self.old_status} → {self.new_status}>"
