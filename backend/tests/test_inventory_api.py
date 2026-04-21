from tests.helpers import assert_api_response


def test_get_inventory_returns_product_stock(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_items": 2}

    response = client.get("/api/inventory/", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 2, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_get_inventory_history_returns_seeded_changes(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_history_count": 1}

    response = client.get("/api/inventory/history", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_adjust_inventory_updates_stock_and_threshold(client, seeded_data, auth_headers):
    input_payload = {
        "product_id": seeded_data["products"]["kulhad"],
        "type": "add",
        "quantity": 4,
        "reason": "Restock",
        "min_stock": 6,
    }
    expected_output = {"message": "Inventory updated"}

    response = client.post("/api/inventory/adjust", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["product"]["stock"] == 24, (
        f"input={input_payload}\nexpected_output=product stock 24\nactual_output={actual_output}"
    )


def test_get_raw_inventory_returns_seeded_material(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_items": 1}

    response = client.get("/api/inventory/raw", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_get_raw_inventory_history_returns_seeded_changes(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_history_count": 1}

    response = client.get("/api/inventory/raw/history", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_create_raw_material(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Glaze Powder",
        "category": "Glaze",
        "quantity": 40,
        "unit": "kg",
        "reorder_level": 10,
        "cost_per_unit": 8.25,
        "supplier": "Glaze Depot",
    }
    expected_output = {
        "name": "Glaze Powder",
        "category": "Glaze",
        "quantity": 40.0,
        "unit": "kg",
        "reorder_level": 10.0,
        "cost_per_unit": 8.25,
        "supplier": "Glaze Depot",
    }

    response = client.post("/api/inventory/raw", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 201, expected_output, input_payload)

    assert actual_output["inventory_value"] == 330.0, (
        f"input={input_payload}\nexpected_output=inventory value 330.0\nactual_output={actual_output}"
    )


def test_update_raw_material(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Clay Mix Fine",
        "category": "Clay",
        "quantity": 100,
        "unit": "kg",
        "reorder_level": 30,
        "cost_per_unit": 5.5,
        "supplier": "Soil Suppliers",
    }
    expected_output = {
        "name": "Clay Mix Fine",
        "category": "Clay",
        "unit": "kg",
        "reorder_level": 30.0,
        "cost_per_unit": 5.5,
    }

    response = client.put(
        f"/api/inventory/raw/{seeded_data['raw_material_id']}",
        json=input_payload,
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["supplier"] == "Soil Suppliers", (
        f"input={input_payload}\nexpected_output=supplier Soil Suppliers\nactual_output={actual_output}"
    )


def test_adjust_raw_material_stock(client, seeded_data, auth_headers):
    input_payload = {"adjustment": 15, "reason": "Fresh delivery"}
    expected_output = {"message": "Fresh delivery"}

    response = client.put(
        f"/api/inventory/raw/{seeded_data['raw_material_id']}/adjust",
        json=input_payload,
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["material"]["quantity"] == 115.0, (
        f"input={input_payload}\nexpected_output=material quantity 115.0\nactual_output={actual_output}"
    )


def test_delete_raw_material(client, seeded_data, auth_headers):
    input_payload = {"item_id": seeded_data["raw_material_id"]}
    expected_output = {"message": "Raw material deleted", "id": seeded_data["raw_material_id"]}

    response = client.delete(
        f"/api/inventory/raw/{seeded_data['raw_material_id']}",
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output == expected_output
