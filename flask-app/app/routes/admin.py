"""
Admin routes — dashboard, complaint management, analytics.

Demonstrates: Functions, Decorators, OOP, Exception Handling, Lambda
"""

import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify,
)
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.complaint import Complaint, CATEGORIES, PRIORITIES, STATUSES
from app.models.complaint_log import ComplaintLog
from app.models.notification import Notification
from app.utils.decorators import admin_required, log_execution_time
from app.utils.validators import sanitize_input
from app.utils.analytics import analytics_service
from app.utils.notifications import notification_service

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@admin_required
@log_execution_time
def dashboard():
    """Admin home — KPIs and recent activity."""
    summary  = analytics_service.summary()
    recent   = (
        Complaint.query
        .order_by(Complaint.created_at.desc())
        .limit(8)
        .all()
    )
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        recent_complaints=recent,
        unread_notifications=unread,
    )


@admin_bp.route("/complaints")
@login_required
@admin_required
def complaints():
    """Paginated, searchable, filterable list of all complaints."""
    page     = request.args.get("page", 1, type=int)
    search   = request.args.get("search", "").strip()
    status   = request.args.get("status", "")
    category = request.args.get("category", "")
    priority = request.args.get("priority", "")
    sort_by  = request.args.get("sort", "newest")

    query = Complaint.query
    if search:
        like = f"%{search}%"
        query = query.join(User, Complaint.user_id == User.id).filter(
            db.or_(
                Complaint.title.ilike(like),
                Complaint.complaint_number.ilike(like),
                User.name.ilike(like),
                User.email.ilike(like),
            )
        )
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if priority:
        query = query.filter_by(priority=priority)

    # Lambda for sort direction
    order_fn = {
        "newest":   lambda: Complaint.created_at.desc(),
        "oldest":   lambda: Complaint.created_at.asc(),
        "priority": lambda: Complaint.priority.desc(),
    }.get(sort_by, lambda: Complaint.created_at.desc())()

    pagination = query.order_by(order_fn).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        "admin/complaints.html",
        pagination=pagination,
        complaints=pagination.items,
        categories=CATEGORIES,
        statuses=STATUSES,
        priorities=PRIORITIES,
        search=search,
        filter_status=status,
        filter_category=category,
        filter_priority=priority,
        sort_by=sort_by,
    )


@admin_bp.route("/complaints/<int:complaint_id>", methods=["GET", "POST"])
@login_required
@admin_required
@log_execution_time
def complaint_detail(complaint_id: int):
    """View and update a single complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    admins = User.query.filter_by(role="admin").all()

    if request.method == "POST":
        new_status   = sanitize_input(request.form.get("status", complaint.status))
        admin_resp   = sanitize_input(request.form.get("admin_response", ""))
        assigned_to  = request.form.get("assigned_to", type=int)
        priority_upd = sanitize_input(request.form.get("priority", complaint.priority))
        remarks      = sanitize_input(request.form.get("remarks", ""))

        try:
            old_status = complaint.status

            complaint.status        = new_status
            complaint.admin_response = admin_resp or complaint.admin_response
            complaint.priority      = priority_upd
            if assigned_to:
                complaint.assigned_to = assigned_to

            if new_status == "Resolved" and old_status != "Resolved":
                from datetime import datetime
                complaint.resolved_at = datetime.utcnow()

            ComplaintLog.record(
                complaint_id=complaint.id,
                old_status=old_status,
                new_status=new_status,
                updated_by=current_user.email,
                remarks=remarks,
            )
            db.session.commit()

            if old_status != new_status:
                notification_service.notify_status_change(complaint, new_status)

            flash("Complaint updated successfully.", "success")
            logger.info(
                "Admin %s updated complaint %s: %s → %s",
                current_user.email, complaint.complaint_number, old_status, new_status,
            )
            return redirect(url_for("admin.complaint_detail", complaint_id=complaint_id))

        except Exception as exc:
            db.session.rollback()
            logger.exception("Admin update error: %s", exc)
            flash("Failed to update complaint.", "danger")

    history = list(complaint.complaint_history_generator())
    return render_template(
        "admin/complaint_detail.html",
        complaint=complaint,
        history=history,
        statuses=STATUSES,
        priorities=PRIORITIES,
        admins=admins,
    )


@admin_bp.route("/complaints/<int:complaint_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_complaint(complaint_id: int):
    """Permanently delete a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    try:
        if complaint.attachment:
            from app.utils.file_handler import file_handler
            file_handler.delete(complaint.attachment)
        db.session.delete(complaint)
        db.session.commit()
        flash(f"Complaint {complaint.complaint_number} deleted.", "success")
        logger.info("Complaint %s deleted by %s.", complaint.complaint_number, current_user.email)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete complaint error: %s", exc)
        flash("Failed to delete complaint.", "danger")
    return redirect(url_for("admin.complaints"))


@admin_bp.route("/analytics")
@login_required
@admin_required
@log_execution_time
def analytics():
    """Full analytics dashboard with chart data."""
    data = analytics_service.full_dashboard()
    return render_template("admin/analytics.html", analytics=data)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """List all registered users."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(User.name.ilike(like), User.email.ilike(like))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "admin/users.html",
        pagination=pagination,
        users=pagination.items,
        search=search,
    )


@admin_bp.route("/notifications")
@login_required
@admin_required
def notifications():
    """Admin notifications."""
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    for n in notifs:
        n.mark_read()
    db.session.commit()
    return render_template("admin/notifications.html", notifications=notifs)
