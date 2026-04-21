import shutil
from io import BytesIO
from pathlib import Path

from tests.helpers import assert_api_response


def test_get_products_returns_seeded_catalog(client, seeded_data):
    response = client.get("/api/products/")
    actual_output = response.get_json()
    assert response.status_code == 200
    assert len(actual_output) >= 2
    assert "wage_per_kulhad" in actual_output[0]


def test_get_product_image_returns_static_file(client, seeded_data):
    response = client.get("/api/products/images/default.jpg")
    actual_output = {"status_code": response.status_code, "content_type": response.content_type}
    assert response.status_code == 200, actual_output


def test_upload_product_image_saves_file(client, seeded_data, auth_headers, monkeypatch, tmp_path):
    import routes.products as products_module

    upload_dir = Path(tmp_path)
    monkeypatch.setattr(products_module, "PRODUCT_IMAGE_DIR", upload_dir)
    response = client.post(
        "/api/products/upload-image",
        headers=auth_headers["admin"],
        data={"image": (BytesIO(b"fake-image-bytes"), "upload.jpg")},
        content_type="multipart/form-data",
    )
    actual_output = assert_api_response(response, 201, {"filename": "upload.jpg"}, {"image_filename": "upload.jpg"})
    assert (upload_dir / actual_output["filename"]).exists()


def test_get_product_history_returns_entries(client, seeded_data, auth_headers):
    response = client.get("/api/products/history", headers=auth_headers["admin"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert len(actual_output) >= 1


def test_create_product_as_admin(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Premium Mug",
        "category": "Cup",
        "price": 22.5,
        "wage_per_kulhad": 12,
        "stock": 12,
        "image": "premium.jpg",
    }
    response = client.post("/api/products/", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 201, {"message": "Product created"}, input_payload)
    assert actual_output == {"message": "Product created"}


def test_update_product_as_admin(client, seeded_data, auth_headers):
    input_payload = {"name": "Updated Kulhad", "category": "Kulhad", "price": 19.0, "wage_per_kulhad": 30, "image": "updated.jpg"}
    response = client.put(f"/api/products/{seeded_data['products']['kulhad']}", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, {"message": "Product updated"}, input_payload)
    assert actual_output == {"message": "Product updated"}


def test_update_product_stock_should_persist_new_stock_value(client, seeded_data, auth_headers):
    from extensions import db
    from models import Product

    response = client.put(f"/api/products/{seeded_data['products']['kulhad']}", json={"stock": 99}, headers=auth_headers["admin"])
    assert response.status_code == 200
    product = db.session.get(Product, seeded_data["products"]["kulhad"])
    assert {"stock": product.stock} == {"stock": 99}


def test_delete_product_as_admin(client, seeded_data, auth_headers):
    response = client.delete(f"/api/products/{seeded_data['products']['cup']}", headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, {"message": "Product deleted"}, {"product_id": seeded_data["products"]["cup"]})
    assert actual_output == {"message": "Product deleted"}
