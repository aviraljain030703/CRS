"""
Notification dispatcher — in-app + optional email.

Demonstrates: Multithreading, OOP, Generators
"""

import logging
import threading
from app import db
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Dispatches notifications to users.

    Demonstrates:
    - OOP (class with methods)
    - Multithreading (background thread for email)
    - Generators (notify_multiple uses a generator expression)
    """

    def send_in_app(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
    ) -> Notification:
        """Create and persist an in-app notification."""
        notif = Notification.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        try:
            db.session.commit()
            logger.info("In-app notification sent to user %d: %s", user_id, title)
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to save notification: %s", exc)
        return notif

    def send_email_async(self, recipient: str, subject: str, body: str) -> None:
        """
        Send an email in a background thread so the web request is not blocked.
        Demonstrates: Multithreading
        """
        def _worker():
            try:
                from flask_mail import Message
                from app import mail
                msg = Message(subject, recipients=[recipient], body=body)
                mail.send(msg)
                logger.info("Email sent to %s: %s", recipient, subject)
            except Exception as exc:
                logger.warning("Email delivery failed for %s: %s", recipient, exc)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def notify_status_change(
        self,
        complaint,
        new_status: str,
    ) -> None:
        """
        Notify a student that their complaint status changed.
        Combines in-app + optional async email.
        """
        messages = {
            "In Progress": ("Your complaint is being reviewed", "info"),
            "Resolved":    ("Your complaint has been resolved", "success"),
            "Rejected":    ("Your complaint has been rejected", "danger"),
            "Escalated":   ("Your complaint has been escalated", "warning"),
        }
        title, ntype = messages.get(new_status, ("Complaint status updated", "info"))
        body = (
            f"Your complaint #{complaint.complaint_number} — "
            f'"{complaint.title}" has been updated to: {new_status}.'
        )
        self.send_in_app(complaint.user_id, title, body, ntype)

        if complaint.user and complaint.user.email:
            self.send_email_async(
                complaint.user.email,
                f"[CMS] Complaint {complaint.complaint_number} — {new_status}",
                body,
            )

    def notify_multiple(self, user_ids: list[int], title: str, message: str) -> None:
        """
        Send the same notification to many users.
        Demonstrates: Generator expression
        """
        # Generator expression — creates notifications lazily
        notifications = (
            Notification(user_id=uid, title=title, message=message)
            for uid in user_ids
        )
        try:
            for notif in notifications:
                db.session.add(notif)
            db.session.commit()
            logger.info("Bulk notification sent to %d users.", len(user_ids))
        except Exception as exc:
            db.session.rollback()
            logger.exception("Bulk notification failed: %s", exc)


notification_service = NotificationService()
