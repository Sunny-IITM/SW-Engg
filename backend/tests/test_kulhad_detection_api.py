from io import BytesIO

import pytest


@pytest.fixture()
def kulhad_image_upload():
    return {"image": (BytesIO(b"fake-image-bytes"), "kulhad.jpg")}


def test_detect_kulhad_api_returns_structured_json(client, monkeypatch, kulhad_image_upload):
    import routes.kulhad_detection as kulhad_detection_module

    monkeypatch.setattr(
        kulhad_detection_module,
        "detect_kulhad",
        lambda image_path, **kwargs: {
            "success": True,
            "kulhad_count": 2,
            "detections": [
                {"x": 212, "y": 180, "width": 110, "height": 140, "confidence": 0.87, "class": "kulhad"},
                {"x": 140, "y": 120, "width": 90, "height": 100, "confidence": 0.76, "class": "kulhad"},
            ],
        },
    )

    response = client.post("/detect-kulhad", data=kulhad_image_upload, content_type="multipart/form-data")

    assert response.status_code == 200
    assert response.get_json()["kulhad_count"] == 2
    assert len(response.get_json()["detections"]) == 2


def test_detect_kulhad_api_handles_zero_detection(client, monkeypatch, kulhad_image_upload):
    import routes.kulhad_detection as kulhad_detection_module

    monkeypatch.setattr(
        kulhad_detection_module,
        "detect_kulhad",
        lambda image_path, **kwargs: {"success": True, "kulhad_count": 0, "detections": []},
    )

    response = client.post("/api/production/detect", data=kulhad_image_upload, content_type="multipart/form-data")

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "kulhad_count": 0, "detections": []}


def test_detect_kulhad_api_handles_missing_upload(client):
    response = client.post("/detect-kulhad", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json() == {
        "success": False,
        "error": "missing_file",
        "message": "Image file is required",
    }


def test_detect_kulhad_api_handles_empty_upload(client):
    response = client.post(
        "/detect-kulhad",
        data={"image": (BytesIO(b""), "kulhad.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "success": False,
        "error": "empty_file",
        "message": "Uploaded image is empty",
    }


def test_detect_kulhad_api_rejects_invalid_file_type(client):
    response = client.post(
        "/detect-kulhad",
        data={"image": (BytesIO(b"plain-text"), "notes.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    actual_output = response.get_json()
    assert actual_output["success"] is False
    assert actual_output["error"] == "invalid_file_type"
    assert "Unsupported image format" in actual_output["message"]


def test_detect_kulhad_api_handles_inference_errors(client, monkeypatch, kulhad_image_upload):
    import routes.kulhad_detection as kulhad_detection_module

    monkeypatch.setattr(
        kulhad_detection_module,
        "detect_kulhad",
        lambda image_path, **kwargs: {"success": False, "error": "inference_failed"},
    )

    response = client.post("/detect-kulhad", data=kulhad_image_upload, content_type="multipart/form-data")

    assert response.status_code == 500
    assert response.get_json() == {"success": False, "error": "inference_failed"}
