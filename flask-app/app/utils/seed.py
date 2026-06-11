"""
Database seeder — inserts sample data on first run.

Demonstrates: Functions, Exception Handling, Generators
"""

import logging
import random
from datetime import datetime, timedelta
from app import db, bcrypt
from app.models.user import User
from app.models.complaint import Complaint, generate_complaint_number
from app.models.complaint_log import ComplaintLog
from app.models.notification import Notification

logger = logging.getLogger(__name__)

SAMPLE_COMPLAINTS = [
    ("Hostel water supply issue", "There is no water supply in Block C for 3 days.", "Hostel", "High"),
    ("WiFi not working in library", "The WiFi in the reading hall has been down.", "Network", "Medium"),
    ("Bus timing issue", "Bus No. 4 is always 30 minutes late.", "Transport", "Low"),
    ("Canteen food quality", "The food served in canteen is substandard.", "Canteen", "Medium"),
    ("Projector broken in Lab 3", "The projector in Computer Lab 3 is not working.", "Academic", "High"),
    ("Street light not working", "The street light near the hostel gate is broken.", "Infrastructure", "Low"),
    ("Library books damaged", "Several reference books in the library are damaged.", "Library", "Medium"),
    ("Sports equipment missing", "Cricket equipment from the sports room is missing.", "Sports", "Low"),
    ("Medical room closed", "The medical room is locked during exam periods.", "Medical", "Critical"),
    ("Network speed very slow", "Internet speed in the hostel rooms is very slow.", "Network", "High"),
]


def _user_generator(count: int):
    """Generator that yields sample User objects. Demonstrates: Generators."""
    departments = ["Computer Science", "Mechanical", "Civil", "Electrical", "MBA"]
    for i in range(1, count + 1):
        yield User(
            name=f"Student {i}",
            email=f"student{i}@college.edu",
            student_id=f"CS{2024000 + i}",
            department=random.choice(departments),
            phone=f"98{random.randint(10000000, 99999999)}",
            role="student",
            _password_hash=bcrypt.generate_password_hash("student123").decode(),
        )


def seed_database() -> None:
    """
    Seed the database with sample data if empty.
    Demonstrates: Functions, Exception Handling, Generators, File Handling
    """
    try:
        if User.query.first():
            logger.info("Database already seeded — skipping.")
            return

        logger.info("Seeding database with sample data …")

        # ----- Admin user -----
        admin = User(
            name="Admin User",
            email="admin@college.edu",
            role="admin",
            _password_hash=bcrypt.generate_password_hash("admin123").decode(),
        )
        db.session.add(admin)

        # ----- Students (using generator) -----
        students = list(_user_generator(10))
        db.session.add_all(students)
        db.session.flush()  # get IDs

        statuses = ["Pending", "In Progress", "Resolved", "Rejected", "Escalated"]

        # ----- Complaints -----
        for idx, (title, desc, cat, prio) in enumerate(SAMPLE_COMPLAINTS):
            student = random.choice(students)
            status = random.choice(statuses)
            created = datetime.utcnow() - timedelta(days=random.randint(1, 60))
            c = Complaint(
                complaint_number=generate_complaint_number(),
                user_id=student.id,
                title=title,
                description=desc,
                category=cat,
                priority=prio,
                status=status,
                created_at=created,
                admin_response="Thank you for reporting this issue." if status in ("Resolved", "Rejected") else None,
                resolved_at=datetime.utcnow() if status == "Resolved" else None,
            )
            db.session.add(c)
            db.session.flush()

            # Audit log
            log = ComplaintLog.record(
                complaint_id=c.id,
                old_status=None,
                new_status="Pending",
                updated_by=student.email,
                remarks="Complaint submitted",
            )
            if status != "Pending":
                ComplaintLog.record(
                    complaint_id=c.id,
                    old_status="Pending",
                    new_status=status,
                    updated_by=admin.email,
                    remarks="Status updated by admin",
                )

            # Notification
            Notification.create(
                user_id=student.id,
                title="Complaint Submitted",
                message=f"Your complaint '{title}' has been submitted.",
                notification_type="success",
            )

        db.session.commit()
        logger.info("Database seeded successfully.")

    except Exception as exc:
        db.session.rollback()
        logger.exception("Seeding failed: %s", exc)
