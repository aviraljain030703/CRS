"""
Analytics service — aggregates complaint data for the dashboard.

Demonstrates: Functions, OOP, Lambda Functions, Generators, Exception Handling
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from app.models.complaint import Complaint, CATEGORIES, STATUSES, PRIORITIES
from app import db

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Computes statistics and chart data from the complaints table.

    Demonstrates: OOP, Lambda, Generator, Exception Handling
    """

    # ------------------------------------------------------------------ #
    # Summary KPIs                                                        #
    # ------------------------------------------------------------------ #
    def summary(self) -> dict:
        """Return top-level KPI counts."""
        try:
            total    = Complaint.query.count()
            pending  = Complaint.query.filter_by(status="Pending").count()
            progress = Complaint.query.filter_by(status="In Progress").count()
            resolved = Complaint.query.filter_by(status="Resolved").count()
            rejected = Complaint.query.filter_by(status="Rejected").count()

            # Lambda: compute resolution rate
            resolution_rate = (lambda r, t: round(r / t * 100, 1) if t else 0)(resolved, total)

            # Complaints in last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent = Complaint.query.filter(Complaint.created_at >= week_ago).count()

            return {
                "total": total,
                "pending": pending,
                "in_progress": progress,
                "resolved": resolved,
                "rejected": rejected,
                "resolution_rate": resolution_rate,
                "recent_7d": recent,
            }
        except Exception as exc:
            logger.exception("summary() failed: %s", exc)
            return {}

    # ------------------------------------------------------------------ #
    # Chart data                                                           #
    # ------------------------------------------------------------------ #
    def by_category(self) -> dict:
        """Count complaints per category — used for pie/bar chart."""
        try:
            counts = {cat: 0 for cat in CATEGORIES}
            rows = (
                db.session.query(Complaint.category, db.func.count())
                .group_by(Complaint.category)
                .all()
            )
            for cat, cnt in rows:
                counts[cat] = cnt
            return {"labels": list(counts.keys()), "data": list(counts.values())}
        except Exception as exc:
            logger.exception("by_category() failed: %s", exc)
            return {"labels": [], "data": []}

    def by_status(self) -> dict:
        """Count complaints per status."""
        try:
            counts = {s: 0 for s in STATUSES}
            rows = (
                db.session.query(Complaint.status, db.func.count())
                .group_by(Complaint.status)
                .all()
            )
            for status, cnt in rows:
                counts[status] = cnt
            return {"labels": list(counts.keys()), "data": list(counts.values())}
        except Exception as exc:
            logger.exception("by_status() failed: %s", exc)
            return {"labels": [], "data": []}

    def by_priority(self) -> dict:
        """Count complaints per priority."""
        try:
            counts = {p: 0 for p in PRIORITIES}
            rows = (
                db.session.query(Complaint.priority, db.func.count())
                .group_by(Complaint.priority)
                .all()
            )
            for p, cnt in rows:
                counts[p] = cnt
            return {"labels": list(counts.keys()), "data": list(counts.values())}
        except Exception as exc:
            logger.exception("by_priority() failed: %s", exc)
            return {"labels": [], "data": []}

    def monthly_trend(self, months: int = 6) -> dict:
        """
        Count complaints per month for the last N months.
        Demonstrates: Generator, Lambda
        """
        try:
            now = datetime.utcnow()

            # Generator that yields (label, start_dt, end_dt) for each month
            def month_ranges():
                for i in range(months - 1, -1, -1):
                    first = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
                    if first.month == 12:
                        last = first.replace(year=first.year + 1, month=1)
                    else:
                        last = first.replace(month=first.month + 1)
                    label = first.strftime("%b %Y")
                    yield label, first, last

            labels, data = [], []
            for label, start, end in month_ranges():
                cnt = Complaint.query.filter(
                    Complaint.created_at >= start,
                    Complaint.created_at < end,
                ).count()
                labels.append(label)
                data.append(cnt)

            return {"labels": labels, "data": data}
        except Exception as exc:
            logger.exception("monthly_trend() failed: %s", exc)
            return {"labels": [], "data": []}

    def top_categories(self, n: int = 5) -> list[dict]:
        """
        Return top N categories by complaint volume.
        Demonstrates: Lambda (sorting key)
        """
        try:
            rows = (
                db.session.query(Complaint.category, db.func.count().label("cnt"))
                .group_by(Complaint.category)
                .all()
            )
            # Lambda as sort key
            sorted_rows = sorted(rows, key=lambda r: r.cnt, reverse=True)[:n]
            return [{"category": r.category, "count": r.cnt} for r in sorted_rows]
        except Exception as exc:
            logger.exception("top_categories() failed: %s", exc)
            return []

    def full_dashboard(self) -> dict:
        """Aggregate all analytics into a single dict for the dashboard."""
        return {
            "summary": self.summary(),
            "by_category": self.by_category(),
            "by_status": self.by_status(),
            "by_priority": self.by_priority(),
            "monthly_trend": self.monthly_trend(),
            "top_categories": self.top_categories(),
        }


analytics_service = AnalyticsService()
