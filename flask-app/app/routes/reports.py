"""
Report generation routes — PDF and Excel exports.

Demonstrates: File Handling, Exception Handling, Polymorphism (report generators)
"""

import logging
from flask import Blueprint, request, send_file, flash, redirect, url_for, Response
from flask_login import login_required
import io
from datetime import datetime
from app.models.complaint import Complaint, CATEGORIES, STATUSES, PRIORITIES
from app.utils.decorators import admin_required
from app.utils.report_generator import get_report_generator

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _build_query(args: dict):
    """
    Build a filtered Complaint query from request args.
    Demonstrates: Function, Exception Handling
    """
    query = Complaint.query
    if args.get("status"):
        query = query.filter_by(status=args["status"])
    if args.get("category"):
        query = query.filter_by(category=args["category"])
    if args.get("priority"):
        query = query.filter_by(priority=args["priority"])
    return query.order_by(Complaint.created_at.desc())


@reports_bp.route("/pdf")
@login_required
@admin_required
def generate_pdf():
    """
    Generate and stream a PDF report.
    Demonstrates: File Handling (io.BytesIO), Polymorphism (get_report_generator)
    """
    try:
        complaints = _build_query(request.args).all()
        title = f"Complaint Report — {datetime.utcnow().strftime('%d %b %Y')}"
        generator = get_report_generator("pdf", title)
        pdf_bytes = generator.generate(complaints)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"complaints_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
        )
    except Exception as exc:
        logger.exception("PDF generation failed: %s", exc)
        flash("Failed to generate PDF report.", "danger")
        return redirect(url_for("admin.complaints"))


@reports_bp.route("/excel")
@login_required
@admin_required
def generate_excel():
    """
    Generate and stream an XLSX report.
    Demonstrates: File Handling (io.BytesIO), Polymorphism (get_report_generator)
    """
    try:
        complaints = _build_query(request.args).all()
        title = f"Complaint Report — {datetime.utcnow().strftime('%d %b %Y')}"
        generator = get_report_generator("excel", title)
        xlsx_bytes = generator.generate(complaints)

        return send_file(
            io.BytesIO(xlsx_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"complaints_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
        )
    except Exception as exc:
        logger.exception("Excel generation failed: %s", exc)
        flash("Failed to generate Excel report.", "danger")
        return redirect(url_for("admin.complaints"))
