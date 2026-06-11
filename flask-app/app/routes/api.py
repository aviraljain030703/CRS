"""
REST API endpoints (JSON) — for frontend JS and external integrations.

Demonstrates: Functions, Exception Handling, OOP (uses model .to_dict())
"""

import logging
from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    JWTManager,
)
from app import db, bcrypt
from app.models.user import User
from app.models.complaint import Complaint, CATEGORIES, STATUSES, PRIORITIES
from app.models.complaint_log import ComplaintLog
from app.models.notification import Notification
from app.utils.analytics import analytics_service
from app.utils.validators import sanitize_input, RegistrationValidator

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


def _json_error(message: str, code: int = 400):
    return jsonify({"error": message}), code


def _json_ok(data=None, message: str = "ok", code: int = 200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), code


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@api_bp.route("/auth/register", methods=["POST"])
def api_register():
    """POST /api/auth/register"""
    data = request.get_json(silent=True) or {}
    validator = RegistrationValidator()
    if not validator.validate(data):
        return _json_error("; ".join(validator.errors))
    if User.query.filter_by(email=data["email"].lower()).first():
        return _json_error("Email already registered.", 409)
    try:
        user = User(
            name=sanitize_input(data["name"]),
            email=data["email"].lower(),
            role="student",
        )
        user.password = data["password"]
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        return _json_ok({"token": token, "user": user.to_dict()}, "Registered successfully.", 201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("API register error: %s", exc)
        return _json_error("Registration failed.", 500)


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    """POST /api/auth/login"""
    data    = request.get_json(silent=True) or {}
    email   = data.get("email", "").lower()
    password = data.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return _json_error("Invalid credentials.", 401)
    token = create_access_token(identity=str(user.id))
    return _json_ok({"token": token, "user": user.to_dict()})


# ---------------------------------------------------------------------------
# Complaints endpoints
# ---------------------------------------------------------------------------

@api_bp.route("/complaints", methods=["GET"])
@jwt_required()
def api_list_complaints():
    """GET /api/complaints — list complaints (own for students, all for admins)."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    query = Complaint.query if user.is_admin else Complaint.query.filter_by(user_id=user_id)
    complaints = query.order_by(Complaint.created_at.desc()).all()
    return _json_ok([c.to_dict() for c in complaints])


@api_bp.route("/complaints", methods=["POST"])
@jwt_required()
def api_create_complaint():
    """POST /api/complaints"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    try:
        c = Complaint(
            user_id=user_id,
            title=sanitize_input(data.get("title", "")),
            description=sanitize_input(data.get("description", "")),
            category=data.get("category", "Other"),
            priority=data.get("priority", "Low"),
        )
        db.session.add(c)
        db.session.flush()
        ComplaintLog.record(c.id, None, "Pending", str(user_id), "Created via API")
        db.session.commit()
        return _json_ok(c.to_dict(), "Complaint created.", 201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("API create complaint: %s", exc)
        return _json_error("Failed to create complaint.", 500)


@api_bp.route("/complaints/<int:cid>", methods=["GET"])
@jwt_required()
def api_get_complaint(cid: int):
    """GET /api/complaints/<id>"""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    c = Complaint.query.get_or_404(cid)
    if not user.is_admin and c.user_id != user_id:
        return _json_error("Forbidden.", 403)
    return _json_ok(c.to_dict())


@api_bp.route("/complaints/<int:cid>", methods=["PATCH"])
@jwt_required()
def api_update_complaint(cid: int):
    """PATCH /api/complaints/<id> — admin updates status/priority."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if not user.is_admin:
        return _json_error("Admin only.", 403)
    c = Complaint.query.get_or_404(cid)
    data = request.get_json(silent=True) or {}
    try:
        old_status = c.status
        if "status" in data:
            c.status = data["status"]
        if "priority" in data:
            c.priority = data["priority"]
        if "admin_response" in data:
            c.admin_response = sanitize_input(data["admin_response"])
        ComplaintLog.record(c.id, old_status, c.status, user.email, data.get("remarks", ""))
        db.session.commit()
        return _json_ok(c.to_dict(), "Updated.")
    except Exception as exc:
        db.session.rollback()
        return _json_error(str(exc), 500)


@api_bp.route("/complaints/<int:cid>", methods=["DELETE"])
@jwt_required()
def api_delete_complaint(cid: int):
    """DELETE /api/complaints/<id> — admin only."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if not user.is_admin:
        return _json_error("Admin only.", 403)
    c = Complaint.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return _json_ok(message="Deleted.")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@api_bp.route("/notifications", methods=["GET"])
@jwt_required()
def api_notifications():
    user_id = int(get_jwt_identity())
    notifs = (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    return _json_ok([n.to_dict() for n in notifs])


@api_bp.route("/notifications/mark-read", methods=["POST"])
@jwt_required()
def api_mark_notifications_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return _json_ok(message="All notifications marked as read.")


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@api_bp.route("/analytics", methods=["GET"])
@jwt_required()
def api_analytics():
    """GET /api/analytics — admin only."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if not user.is_admin:
        return _json_error("Admin only.", 403)
    return _json_ok(analytics_service.full_dashboard())


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@api_bp.route("/meta", methods=["GET"])
def api_meta():
    return _json_ok({
        "categories": CATEGORIES,
        "statuses": STATUSES,
        "priorities": PRIORITIES,
    })
