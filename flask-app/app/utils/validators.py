"""
Input validation utilities.

Demonstrates: Functions, OOP, Exception Handling, Encapsulation
"""

import re
import logging
import bleach
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sanitisation helper
# ---------------------------------------------------------------------------

def sanitize_input(text: str) -> str:
    """
    Strip dangerous HTML from user input.
    Demonstrates: Function, Exception Handling
    """
    if not isinstance(text, str):
        return ""
    return bleach.clean(text.strip(), tags=[], strip=True)


# ---------------------------------------------------------------------------
# Abstract validator hierarchy
# Demonstrates: Abstraction, Inheritance, Polymorphism
# ---------------------------------------------------------------------------

class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    Demonstrates: Abstraction (abstract method)
    """

    @abstractmethod
    def validate(self, value) -> tuple[bool, str]:
        """Return (is_valid, error_message)."""


class EmailValidator(BaseValidator):
    """Validates email addresses using a regex pattern."""

    _PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: str) -> tuple[bool, str]:
        if not value or not isinstance(value, str):
            return False, "Email is required."
        if not self._PATTERN.match(value.strip()):
            return False, "Please enter a valid email address."
        return True, ""


class PasswordValidator(BaseValidator):
    """Validates password strength."""

    def validate(self, value: str) -> tuple[bool, str]:
        if not value or len(value) < 6:
            return False, "Password must be at least 6 characters."
        if len(value) > 128:
            return False, "Password must be fewer than 128 characters."
        return True, ""


class TextValidator(BaseValidator):
    """Validates a generic non-empty text field."""

    def __init__(self, field_name: str, min_len: int = 1, max_len: int = 2000):
        self._field_name = field_name
        self._min_len = min_len
        self._max_len = max_len

    def validate(self, value: str) -> tuple[bool, str]:
        if not value or not isinstance(value, str):
            return False, f"{self._field_name} is required."
        cleaned = value.strip()
        if len(cleaned) < self._min_len:
            return False, f"{self._field_name} must be at least {self._min_len} characters."
        if len(cleaned) > self._max_len:
            return False, f"{self._field_name} must not exceed {self._max_len} characters."
        return True, ""


# ---------------------------------------------------------------------------
# Composite form validator — demonstrates Polymorphism (calls .validate())
# ---------------------------------------------------------------------------

class ComplaintFormValidator:
    """
    Validates complaint submission form data.
    Demonstrates: OOP, Polymorphism (calls validate() on different subclasses)
    """

    def __init__(self):
        self._title_v = TextValidator("Title", min_len=5, max_len=200)
        self._desc_v = TextValidator("Description", min_len=10, max_len=2000)
        self._errors: list[str] = []

    @property
    def errors(self) -> list[str]:
        return self._errors

    def validate(self, data: dict) -> bool:
        """Run all validators; collect errors. Demonstrates Lambda for filtering."""
        self._errors = []
        checks = [
            self._title_v.validate(data.get("title", "")),
            self._desc_v.validate(data.get("description", "")),
        ]
        # Lambda: extract error messages from failed checks
        self._errors = list(
            map(lambda r: r[1], filter(lambda r: not r[0], checks))
        )
        return len(self._errors) == 0


class RegistrationValidator:
    """Validates user registration form. Demonstrates OOP, Polymorphism."""

    def __init__(self):
        self._email_v = EmailValidator()
        self._password_v = PasswordValidator()
        self._name_v = TextValidator("Name", min_len=2, max_len=120)
        self._errors: list[str] = []

    @property
    def errors(self) -> list[str]:
        return self._errors

    def validate(self, data: dict) -> bool:
        self._errors = []
        pairs = [
            self._name_v.validate(data.get("name", "")),
            self._email_v.validate(data.get("email", "")),
            self._password_v.validate(data.get("password", "")),
        ]
        self._errors = [msg for ok, msg in pairs if not ok]
        if not self._errors and data.get("password") != data.get("confirm_password"):
            self._errors.append("Passwords do not match.")
        return len(self._errors) == 0
