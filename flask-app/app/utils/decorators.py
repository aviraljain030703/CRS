"""
Custom decorators for the application.

Demonstrates: Decorators, Higher-Order Functions, Exception Handling
"""

import logging
import functools
import time
from flask import redirect, url_for, flash, abort
from flask_login import current_user

logger = logging.getLogger(__name__)


def admin_required(f):
    """
    Decorator that restricts a view to admin users only.
    Demonstrates: Decorator pattern, Closures
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """Restrict view to authenticated students."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_student:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def log_execution_time(f):
    """
    Decorator that logs how long a function takes to execute.
    Demonstrates: Decorator pattern, Logging
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        start = time.perf_counter()
        result = f(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug("%s completed in %.2f ms", f.__name__, elapsed)
        return result
    return decorated


def handle_exceptions(default_message: str = "An unexpected error occurred."):
    """
    Parameterised decorator factory for unified exception handling.
    Demonstrates: Decorator with arguments (factory pattern), Exception Handling
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as exc:
                logger.warning("ValueError in %s: %s", f.__name__, exc)
                flash(str(exc), "warning")
                return redirect(url_for("complaints.list_complaints"))
            except Exception as exc:
                logger.exception("Unhandled error in %s", f.__name__)
                flash(default_message, "danger")
                return redirect(url_for("complaints.list_complaints"))
        return decorated
    return decorator


def cache_result(timeout_seconds: int = 60):
    """
    Simple in-memory cache decorator.
    Demonstrates: Decorator pattern, Closures, Lambda
    """
    cache: dict = {}

    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            key = (f.__name__,) + args + tuple(sorted(kwargs.items()))
            now = time.time()
            if key in cache:
                result, stored_at = cache[key]
                if now - stored_at < timeout_seconds:
                    logger.debug("Cache hit for %s", f.__name__)
                    return result
            result = f(*args, **kwargs)
            cache[key] = (result, now)
            return result
        # Expose a lambda to clear the cache
        decorated.clear_cache = lambda: cache.clear()
        return decorated
    return decorator
