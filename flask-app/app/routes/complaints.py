"""
Student-facing complaint routes.

Demonstrates: Functions, Exception Handling, Decorators, File Handling
"""

import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app,
)
from flask_login import login_required, current_user
from app import db
from app.models.complaint import Complaint, CATEGORIES, PRIORITIES, generate_complaint_number
from app.models.complaint_log import ComplaintLog
from app.models.notification import Notification
from app.utils.validators import ComplaintFormValidator, sanitize_input
from app.utils.file_handler import file_handler
from app.utils.decorators import student_required, log_execution_time
from app.utils.notifications import notification_service

logger = logging.getLogger(__name__)

complaints_bp = Blueprint("complaints", __name__, url_prefix="/student")


@complaints_bp.route("/dashboard")
@login_required
@log_execution_time
def dashboard():
    """Student home — shows their complaint stats and recent activity."""
    complaints = (
        Complaint.query
        .filter_by(user_id=current_user.id)
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )
    # Lambda: compute counts by status
    count_by = lambda status: Complaint.query.filter_by(
        user_id=current_user.id, status=status
    ).count()

    stats = {
        "total":       Complaint.query.filter_by(user_id=current_user.id).count(),
        "pending":     count_by("Pending"),
        "in_progress": count_by("In Progress"),
        "resolved":    count_by("Resolved"),
    }
    unread_notifications = (
        Notification.query
        .filter_by(user_id=current_user.id, is_read=False)
        .count()
    )
    return render_template(
        "student/dashboard.html",
        recent_complaints=complaints,
        stats=stats,
        unread_notifications=unread_notifications,
    )


@complaints_bp.route("/complaints")
@login_required
def list_complaints():
    """Paginated list of the current student's complaints."""
    page     = request.args.get("page", 1, type=int)
    status   = request.args.get("status", "")
    category = request.args.get("category", "")
    priority = request.args.get("priority", "")

    query = Complaint.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if priority:
        query = query.filter_by(priority=priority)

    pagination = query.order_by(Complaint.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template(
        "student/my_complaints.html",
        pagination=pagination,
        complaints=pagination.items,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        filter_status=status,
        filter_category=category,
        filter_priority=priority,
    )


@complaints_bp.route("/complaints/new", methods=["GET", "POST"])
@login_required
@student_required
@log_execution_time
def submit_complaint():
    """Submit a new complaint."""
    if request.method == "POST":
        data = {
            "title":       sanitize_input(request.form.get("title", "")),
            "description": sanitize_input(request.form.get("description", "")),
            "category":    sanitize_input(request.form.get("category", "Other")),
            "priority":    sanitize_input(request.form.get("priority", "Low")),
        }

        validator = ComplaintFormValidator()
        if not validator.validate(data):
            for err in validator.errors:
                flash(err, "danger")
            return render_template(
                "student/submit_complaint.html",
                categories=CATEGORIES, priorities=PRIORITIES, form_data=data
            )

        try:
            # Secure file upload
            attachment_filename = None
            uploaded_file = request.files.get("attachment")
            if uploaded_file and uploaded_file.filename:
                attachment_filename = file_handler.save(uploaded_file)

            complaint = Complaint(
                user_id=current_user.id,
                title=data["title"],
                description=data["description"],
                category=data["category"],
                priority=data["priority"],
                attachment=attachment_filename,
                status="Pending",
            )
            db.session.add(complaint)
            db.session.flush()

            ComplaintLog.record(
                complaint_id=complaint.id,
                old_status=None,
                new_status="Pending",
                updated_by=current_user.email,
                remarks="Complaint submitted by student",
            )
            Notification.create(
                user_id=current_user.id,
                title="Complaint Submitted",
                message=f"Your complaint '{complaint.title}' (#{complaint.complaint_number}) has been submitted.",
                notification_type="success",
            )
            db.session.commit()

            flash(f"Complaint submitted successfully! Reference: {complaint.complaint_number}", "success")
            logger.info("Complaint %s submitted by user %d.", complaint.complaint_number, current_user.id)
            return redirect(url_for("complaints.list_complaints"))

        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception as exc:
            db.session.rollback()
            logger.exception("Submit complaint error: %s", exc)
            flash("Failed to submit complaint. Please try again.", "danger")

    return render_template(
        "student/submit_complaint.html",
        categories=CATEGORIES, priorities=PRIORITIES, form_data={}
    )


@complaints_bp.route("/complaints/<int:complaint_id>")
@login_required
def view_complaint(complaint_id: int):
    """Detail view of a single complaint for the student who owns it."""
    complaint = Complaint.query.filter_by(
        id=complaint_id, user_id=current_user.id
    ).first_or_404()

    # Use the generator method from the model
    history = list(complaint.complaint_history_generator())

    return render_template(
        "student/complaint_detail.html",
        complaint=complaint,
        history=history,
    )


@complaints_bp.route("/notifications")
@login_required
def notifications():
    """List all notifications for the current user and mark them read."""
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    # Mark all as read
    for n in notifs:
        if not n.is_read:
            n.mark_read()
    db.session.commit()

    return render_template("student/notifications.html", notifications=notifs)
