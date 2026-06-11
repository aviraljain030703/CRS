"""
Authentication routes — register, login, logout.

Demonstrates: Functions, Exception Handling, Decorators, OOP
"""

import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.validators import RegistrationValidator, sanitize_input
from app.utils.decorators import log_execution_time

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Root redirect — send authenticated users to their dashboard."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("complaints.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
@log_execution_time
def login():
    """Student / admin login."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        email    = sanitize_input(request.form.get("email", ""))
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        try:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password) and user.is_active:
                login_user(user, remember=remember)
                logger.info("User %s logged in.", email)
                next_page = request.args.get("next")
                if user.is_admin:
                    return redirect(next_page or url_for("admin.dashboard"))
                return redirect(next_page or url_for("complaints.dashboard"))
            else:
                flash("Invalid email or password. Please try again.", "danger")
        except Exception as exc:
            logger.exception("Login error for %s: %s", email, exc)
            flash("An error occurred during login. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@log_execution_time
def register():
    """Student self-registration."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        data = {
            "name":             sanitize_input(request.form.get("name", "")),
            "email":            sanitize_input(request.form.get("email", "")).lower(),
            "student_id":       sanitize_input(request.form.get("student_id", "")),
            "department":       sanitize_input(request.form.get("department", "")),
            "phone":            sanitize_input(request.form.get("phone", "")),
            "password":         request.form.get("password", ""),
            "confirm_password": request.form.get("confirm_password", ""),
        }

        validator = RegistrationValidator()
        if not validator.validate(data):
            for err in validator.errors:
                flash(err, "danger")
            return render_template("auth/register.html", form_data=data)

        try:
            if User.query.filter_by(email=data["email"]).first():
                flash("An account with this email already exists.", "warning")
                return render_template("auth/register.html", form_data=data)

            user = User(
                name=data["name"],
                email=data["email"],
                student_id=data["student_id"] or None,
                department=data["department"] or None,
                phone=data["phone"] or None,
                role="student",
            )
            user.password = data["password"]
            db.session.add(user)
            db.session.commit()

            flash("Account created successfully! Please log in.", "success")
            logger.info("New student registered: %s", data["email"])
            return redirect(url_for("auth.login"))

        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception as exc:
            db.session.rollback()
            logger.exception("Registration error: %s", exc)
            flash("Registration failed. Please try again.", "danger")

    return render_template("auth/register.html", form_data={})


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logger.info("User %s logged out.", current_user.email)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
