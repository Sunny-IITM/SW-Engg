"""Reusable helpers for Roboflow kulhad detection."""

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from inference_sdk import InferenceHTTPClient
except ImportError:  # pragma: no cover - handled gracefully at runtime
    InferenceHTTPClient = None

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None


DEFAULT_API_URL = "https://serverless.roboflow.com"
DEFAULT_MODEL_ID = "kulhad-detector/1"
SUPPORTED_IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
DEFAULT_CLASS_NAME = "kulhad"

logger = logging.getLogger(__name__)


class KulhadDetectionError(Exception):
    """Base exception for kulhad detection failures."""


class KulhadDetectorConfigurationError(KulhadDetectionError):
    """Raised when Roboflow client configuration is invalid."""


class KulhadDetectorInferenceError(KulhadDetectionError):
    """Raised when Roboflow inference fails."""


def _resolve_setting(value: Optional[str], default: str) -> str:
    """Return a trimmed configuration value or a fallback default."""
    return (value or default).strip()


def _validate_image_path(image_path: str) -> Path:
    """Validate that the provided image path exists and is a supported format."""
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        raise ValueError("Image file does not exist")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        allowed_extensions = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ValueError(f"Unsupported image format. Allowed formats: {allowed_extensions}")

    return path


@lru_cache(maxsize=1)
def initialize_client(api_url: Optional[str] = None, api_key: Optional[str] = None) -> Any:
    """Create and cache the Roboflow inference client."""
    resolved_api_url = _resolve_setting(api_url, DEFAULT_API_URL)
    resolved_api_key = (api_key or "").strip()

    if not resolved_api_key:
        logger.error("Roboflow API key is missing")
        raise KulhadDetectorConfigurationError("ROBOFLOW_API_KEY is not configured")

    if not resolved_api_url:
        logger.error("Roboflow API URL is missing")
        raise KulhadDetectorConfigurationError("Roboflow API URL is not configured")

    if InferenceHTTPClient is None:
        logger.error("inference-sdk dependency is not installed")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        version_hint = (
            " Roboflow inference-sdk is currently supported on Python versions below 3.13."
            if sys.version_info >= (3, 13)
            else ""
        )
        raise KulhadDetectorConfigurationError(
            f"inference-sdk is not installed for Python {python_version}. Add it with 'pip install inference-sdk' in a supported environment.{version_hint}"
        )

    logger.info("Initializing Roboflow inference client")
    return InferenceHTTPClient(api_url=resolved_api_url, api_key=resolved_api_key)


def count_kulhads(predictions: Iterable[Dict[str, Any]]) -> int:
    """Count kulhad detections from a prediction collection."""
    return sum(1 for prediction in predictions if prediction.get("class") == DEFAULT_CLASS_NAME)


def _safe_float(value: Any) -> float:
    """Convert numeric-like values to float without failing on malformed input."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_predictions(result: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert raw Roboflow predictions into a normalized detection list."""
    if not isinstance(result, dict) or "predictions" not in result:
        logger.error("Unexpected Roboflow response structure: missing predictions")
        raise KulhadDetectorInferenceError("Unexpected Roboflow response structure")

    raw_predictions = result.get("predictions")
    if raw_predictions is None:
        return []

    if not isinstance(raw_predictions, list):
        logger.error("Unexpected Roboflow response structure: predictions is not a list")
        raise KulhadDetectorInferenceError("Unexpected Roboflow response structure")

    parsed_predictions: List[Dict[str, Any]] = []
    for prediction in raw_predictions:
        if not isinstance(prediction, dict):
            continue

        class_name = str(
            prediction.get("class")
            or prediction.get("class_name")
            or DEFAULT_CLASS_NAME
        ).strip().lower() or DEFAULT_CLASS_NAME

        parsed_predictions.append({
            "x": int(round(_safe_float(prediction.get("x", 0)))),
            "y": int(round(_safe_float(prediction.get("y", 0)))),
            "width": int(round(_safe_float(prediction.get("width", 0)))),
            "height": int(round(_safe_float(prediction.get("height", 0)))),
            "confidence": round(_safe_float(prediction.get("confidence", 0)), 4),
            "class": class_name,
        })

    return parsed_predictions


def format_response(
    predictions: Optional[List[Dict[str, Any]]] = None,
    *,
    success: bool = True,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardized response payload for kulhad detection."""
    if not success:
        return {
            "success": False,
            "error": error or "inference_failed",
        }

    normalized_predictions = predictions or []
    return {
        "success": True,
        "kulhad_count": count_kulhads(normalized_predictions),
        "detections": normalized_predictions,
    }


def draw_bounding_boxes(
    image_path: str,
    predictions: Iterable[Dict[str, Any]],
    output_path: Optional[str] = None,
) -> Optional[str]:
    """Draw bounding boxes on an image and return the annotated file path."""
    if cv2 is None:
        logger.warning("OpenCV is not installed; skipping annotated image generation")
        return None

    source_path = _validate_image_path(image_path)
    image = cv2.imread(str(source_path))
    if image is None:
        raise ValueError("Unable to load image for annotation")

    for prediction in predictions:
        center_x = int(_safe_float(prediction.get("x")))
        center_y = int(_safe_float(prediction.get("y")))
        width = int(_safe_float(prediction.get("width")))
        height = int(_safe_float(prediction.get("height")))
        confidence = round(_safe_float(prediction.get("confidence")), 2)
        class_name = str(prediction.get("class") or DEFAULT_CLASS_NAME)

        top_left = (max(center_x - width // 2, 0), max(center_y - height // 2, 0))
        bottom_right = (max(center_x + width // 2, 0), max(center_y + height // 2, 0))
        label = f"{class_name}: {confidence:.2f}"

        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(image, label, (top_left[0], max(top_left[1] - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    annotated_path = Path(output_path) if output_path else source_path.with_name(f"{source_path.stem}_annotated{source_path.suffix}")
    cv2.imwrite(str(annotated_path), image)
    return str(annotated_path)


def detect_kulhad(
    image_path: str,
    *,
    client: Optional[Any] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run kulhad detection for an image and return a standardized response."""
    validated_image_path = _validate_image_path(image_path)
    resolved_model_id = _resolve_setting(model_id, DEFAULT_MODEL_ID)

    if not resolved_model_id:
        logger.error("Roboflow model ID is missing")
        raise KulhadDetectorConfigurationError("ROBOFLOW_MODEL_ID is not configured")

    inference_client = client or initialize_client(api_url=api_url, api_key=api_key)
    logger.info("Kulhad inference started for %s", validated_image_path.name)

    try:
        raw_result = inference_client.infer(str(validated_image_path), model_id=resolved_model_id)
        predictions = parse_predictions(raw_result)
    except (TimeoutError, ConnectionError):
        logger.exception("Kulhad inference request timed out or lost connection")
        return format_response(success=False, error="inference_failed")
    except KulhadDetectorInferenceError:
        logger.exception("Kulhad inference failed because of an unexpected response structure")
        return format_response(success=False, error="inference_failed")
    except Exception:
        logger.exception("Kulhad inference request failed")
        return format_response(success=False, error="inference_failed")

    logger.info("Kulhad inference completed for %s with %s detections", validated_image_path.name, count_kulhads(predictions))
    return format_response(predictions)


def format_detection_result(raw_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Backward-compatible alias for earlier integration code paths."""
    formatted_detections = parse_predictions(raw_result)
    return {
        "success": True,
        "kulhad_count": count_kulhads(formatted_detections),
        "detections": formatted_detections,
    }
