"""
Secure file upload handler.

Demonstrates: Functions, OOP, Exception Handling, File Handling
"""

import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}


def allowed_file(filename: str) -> bool:
    """
    Check that the file extension is permitted.
    Demonstrates: Function, Lambda-style logic
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


class FileHandler:
    """
    Handles secure file upload, retrieval, and deletion.

    Demonstrates: OOP, Encapsulation, File Handling, Exception Handling
    """

    def __init__(self, upload_folder: str | None = None):
        self._upload_folder = upload_folder  # Encapsulated

    @property
    def upload_folder(self) -> str:
        """Lazy-resolve upload folder from app config if not set."""
        if self._upload_folder:
            return self._upload_folder
        return current_app.config.get("UPLOAD_FOLDER", "/tmp/uploads")

    def save(self, file_storage) -> str | None:
        """
        Validate and save an uploaded file.
        Returns the saved filename or None on failure.

        Demonstrates: File Handling, Exception Handling
        """
        if not file_storage or not file_storage.filename:
            return None

        if not allowed_file(file_storage.filename):
            raise ValueError(
                f"File type not allowed. Permitted: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        try:
            original = secure_filename(file_storage.filename)
            ext = original.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"

            os.makedirs(self.upload_folder, exist_ok=True)
            save_path = os.path.join(self.upload_folder, unique_name)
            file_storage.save(save_path)

            logger.info("Saved upload: %s -> %s", original, unique_name)
            return unique_name

        except OSError as exc:
            logger.exception("Failed to save file: %s", exc)
            raise RuntimeError("Could not save the uploaded file.") from exc

    def delete(self, filename: str) -> bool:
        """
        Delete a previously uploaded file.
        Demonstrates: File Handling, Exception Handling
        """
        if not filename:
            return False
        path = os.path.join(self.upload_folder, filename)
        try:
            if os.path.isfile(path):
                os.remove(path)
                logger.info("Deleted file: %s", filename)
                return True
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", filename, exc)
        return False

    def exists(self, filename: str) -> bool:
        """Check whether an uploaded file exists on disk."""
        if not filename:
            return False
        return os.path.isfile(os.path.join(self.upload_folder, filename))

    def read_bytes(self, filename: str) -> bytes:
        """
        Read raw bytes from an uploaded file.
        Demonstrates: File Handling
        """
        path = os.path.join(self.upload_folder, filename)
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except OSError as exc:
            logger.error("Cannot read file %s: %s", filename, exc)
            raise FileNotFoundError(f"File not found: {filename}") from exc


# Module-level singleton (initialised lazily with app config)
file_handler = FileHandler()
