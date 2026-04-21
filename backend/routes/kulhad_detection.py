"""Flask routes for kulhad image detection."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple

from flask import Blueprint, current_app, jsonify, request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from kulhad_detector import (
    SUPPORTED_IMAGE_EXTENSIONS,
    KulhadDetectorConfigurationError,
    detect_kulhad,
)

kulhad_detection = Blueprint("kulhad_detection", __name__)
logger = logging.getLogger(__name__)


def _create_temp_upload_path(filename: str) -> Path:
    """Create a temporary file path for the uploaded image."""
    suffix = Path(filename).suffix.lower()
    temp_file = tempfile.NamedTemporaryFile(prefix="kulhad-upload-", suffix=suffix, delete=False)
    temp_file.close()
    return Path(temp_file.name)


def _get_file_size(image_file: FileStorage) -> int:
    """Return the size of an uploaded file stream without consuming it."""
    current_position = image_file.stream.tell()
    image_file.stream.seek(0, os.SEEK_END)
    file_size = image_file.stream.tell()
    image_file.stream.seek(current_position)
    return file_size


def _error_response(error: str, message: str, status_code: int):
    """Return a standardized JSON error response."""
    return jsonify({"success": False, "error": error, "message": message}), status_code


def _validate_uploaded_image() -> Tuple[FileStorage, str]:
    """Validate the incoming multipart image upload."""
    image_file = request.files.get("image")
    if image_file is None:
        raise ValueError("missing_file")

    if not image_file.filename:
        raise ValueError("missing_filename")

    safe_filename = secure_filename(image_file.filename)
    if not safe_filename:
        raise ValueError("invalid_filename")

    if _get_file_size(image_file) <= 0:
        raise ValueError("empty_file")

    extension = Path(safe_filename).suffix.lower()
    is_supported_extension = extension in SUPPORTED_IMAGE_EXTENSIONS
    is_image_mimetype = bool(image_file.mimetype and image_file.mimetype.startswith("image/"))
    if not is_supported_extension or (image_file.mimetype and not is_image_mimetype):
        raise ValueError("invalid_file_type")

    return image_file, safe_filename


@kulhad_detection.route("/detect-kulhad", methods=["POST"])
@kulhad_detection.route("/api/production/detect", methods=["POST"])
def detect_kulhad_api():
    """Accept an uploaded image, run Roboflow inference, and return JSON results."""
    temp_path = None
    logger.info("Kulhad detection request received")

    try:
        image_file, safe_filename = _validate_uploaded_image()
        temp_path = _create_temp_upload_path(safe_filename)
        image_file.save(temp_path)

        logger.info("Kulhad detection inference started")
        result = detect_kulhad(
            str(temp_path),
            api_url=current_app.config.get("ROBOFLOW_API_URL"),
            api_key=current_app.config.get("ROBOFLOW_API_KEY"),
            model_id=current_app.config.get("ROBOFLOW_MODEL_ID"),
        )

        if not result.get("success", False):
            logger.error("Kulhad detection inference failed")
            return jsonify(result), 500

        logger.info("Kulhad detection inference completed")
        return jsonify(result), 200
    except ValueError as error:
        error_code = str(error)
        logger.warning("Kulhad detection request validation failed: %s", error_code)
        if error_code == "missing_file":
            return _error_response("missing_file", "Image file is required", 400)
        if error_code == "missing_filename":
            return _error_response("missing_filename", "Image filename is required", 400)
        if error_code == "invalid_filename":
            return _error_response("invalid_filename", "Invalid image filename", 400)
        if error_code == "empty_file":
            return _error_response("empty_file", "Uploaded image is empty", 400)
        if error_code == "invalid_file_type":
            allowed_extensions = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
            return _error_response("invalid_file_type", f"Unsupported image format. Allowed formats: {allowed_extensions}", 400)
        return _error_response("invalid_request", error_code, 400)
    except KulhadDetectorConfigurationError as error:
        logger.exception("Kulhad detector configuration error: %s", error)
        return _error_response("configuration_error", str(error), 500)
    except Exception as error:  # pragma: no cover - defensive fallback
        logger.exception("Unexpected kulhad detection error: %s", error)
        return _error_response("unexpected_error", "Unexpected error while processing image", 500)
    finally:
        # Remove the temporary upload even if inference fails.
        if temp_path and temp_path.exists():
            os.remove(temp_path)
