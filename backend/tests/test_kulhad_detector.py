import pytest

import kulhad_detector as kulhad_detector_module
from kulhad_detector import (
    KulhadDetectorConfigurationError,
    count_kulhads,
    detect_kulhad,
    format_response,
    initialize_client,
    parse_predictions,
)


class StubInferenceClient:
    def __init__(self, result=None, error=None):
        self.result = result or {"predictions": []}
        self.error = error

    def infer(self, image_path, model_id):
        if self.error:
            raise self.error
        return self.result


class FakeInferenceClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def infer(self, image_path, model_id):
        return {"predictions": []}


def test_parse_predictions_handles_empty_predictions():
    actual_output = parse_predictions({"predictions": []})
    assert actual_output == []


def test_format_response_returns_zero_detection_payload():
    actual_output = format_response([])
    assert actual_output == {"success": True, "kulhad_count": 0, "detections": []}


def test_count_kulhads_counts_only_kulhad_predictions():
    assert count_kulhads([{"class": "kulhad"}, {"class": "cup"}]) == 1


def test_detect_kulhad_returns_structured_results(tmp_path):
    image_path = tmp_path / "kulhad.jpg"
    image_path.write_bytes(b"fake-image")

    stub_client = StubInferenceClient(
        result={
            "predictions": [
                {"x": 212.4, "y": 180.2, "width": 110.1, "height": 140.4, "confidence": 0.8731},
                {"x": 120.0, "y": 95.0, "width": 80.0, "height": 90.0, "confidence": 0.5528},
            ]
        }
    )

    actual_output = detect_kulhad(str(image_path), client=stub_client, model_id="kulhad-detector/1")
    assert actual_output == {
        "success": True,
        "kulhad_count": 2,
        "detections": [
            {"x": 212, "y": 180, "width": 110, "height": 140, "confidence": 0.8731, "class": "kulhad"},
            {"x": 120, "y": 95, "width": 80, "height": 90, "confidence": 0.5528, "class": "kulhad"},
        ],
    }


def test_detect_kulhad_returns_zero_detection_payload(tmp_path):
    image_path = tmp_path / "kulhad.jpg"
    image_path.write_bytes(b"fake-image")

    actual_output = detect_kulhad(str(image_path), client=StubInferenceClient(result={"predictions": []}))
    assert actual_output == {"success": True, "kulhad_count": 0, "detections": []}


def test_detect_kulhad_rejects_unsupported_file_extension(tmp_path):
    file_path = tmp_path / "kulhad.txt"
    file_path.write_text("not-an-image", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported image format"):
        detect_kulhad(str(file_path), client=StubInferenceClient())


def test_detect_kulhad_returns_failure_payload_on_inference_error(tmp_path):
    image_path = tmp_path / "kulhad.png"
    image_path.write_bytes(b"fake-image")

    actual_output = detect_kulhad(str(image_path), client=StubInferenceClient(error=RuntimeError("network down")))
    assert actual_output == {"success": False, "error": "inference_failed"}


def test_detect_kulhad_returns_failure_payload_on_malformed_response(tmp_path):
    image_path = tmp_path / "kulhad.png"
    image_path.write_bytes(b"fake-image")

    actual_output = detect_kulhad(str(image_path), client=StubInferenceClient(result={"unexpected": []}))
    assert actual_output == {"success": False, "error": "inference_failed"}


def test_initialize_client_requires_api_key():
    initialize_client.cache_clear()

    with pytest.raises(KulhadDetectorConfigurationError, match="ROBOFLOW_API_KEY is not configured"):
        initialize_client(api_url="https://serverless.roboflow.com", api_key="")


def test_initialize_client_reuses_cached_instance(monkeypatch):
    initialize_client.cache_clear()
    monkeypatch.setattr(kulhad_detector_module, "InferenceHTTPClient", FakeInferenceClient)

    first_client = initialize_client(api_url="https://serverless.roboflow.com", api_key="test-key")
    second_client = initialize_client(api_url="https://serverless.roboflow.com", api_key="test-key")

    assert first_client is second_client
