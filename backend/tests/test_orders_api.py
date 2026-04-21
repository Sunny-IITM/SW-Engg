from tests.helpers import assert_api_response


def test_get_checkout_profile(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {
        "name": "Customer User",
        "email": "customer@example.com",
        "phone": "9999999999",
        "address": "Main Street",
        "city": "Jaipur",
        "state": "Rajasthan",
        "postal_code": "302001",
        "has_saved_address": True,
    }

    response = client.get("/api/orders/checkout-profile", headers=auth_headers["customer"])
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output == expected_output


def test_update_checkout_profile(client, seeded_data, auth_headers):
    input_payload = {
        "phone": "3333333333",
        "address": "Checkout Street",
        "city": "Udaipur",
        "state": "Rajasthan",
        "postal_code": "313001",
    }
    expected_output = {
        "phone": "3333333333",
        "address": "Checkout Street",
        "city": "Udaipur",
        "state": "Rajasthan",
        "postal_code": "313001",
        "has_saved_address": True,
    }

    response = client.put("/api/orders/checkout-profile", json=input_payload, headers=auth_headers["customer"])
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["name"] == "Customer User", (
        f"input={input_payload}\nexpected_output=name Customer User\nactual_output={actual_output}"
    )


def test_create_order_as_customer(client, seeded_data, auth_headers):
    input_payload = {
        "items": [{"id": seeded_data["products"]["kulhad"], "qty": 2}],
        "phone": "9999999999",
        "address": "Main Street",
        "city": "Jaipur",
        "state": "Rajasthan",
        "postal_code": "302001",
        "payment_method": "Cash on Delivery",
        "shipping": 5,
    }
    expected_output = {
        "message": "Order placed successfully",
        "status": "Pending",
        "payment": "Pending",
        "method": "Cash on Delivery",
        "amount": 71.0,
    }

    response = client.post("/api/orders/", json=input_payload, headers=auth_headers["customer"])
    actual_output = assert_api_response(response, 201, expected_output, input_payload)

    assert len(actual_output["items"]) == 1, (
        f"input={input_payload}\nexpected_output=one created order item\nactual_output={actual_output}"
    )


def test_get_admin_orders(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_orders": 1}

    response = client.get("/api/orders/admin", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_get_customer_order_history(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {"minimum_orders": 1}

    response = client.get("/api/orders/my-history", headers=auth_headers["customer"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_update_admin_order_status(client, seeded_data, auth_headers):
    input_payload = {"status": "shipped", "payment": "paid"}
    expected_output = {"message": "Order updated", "id": seeded_data["order_id"], "status": "Shipped", "payment": "Paid"}

    response = client.put(
        f"/api/orders/{seeded_data['order_id']}/status",
        json=input_payload,
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output == expected_output


def test_update_bulk_payment_status(client, seeded_data, auth_headers):
    input_payload = {"order_ids": [seeded_data["order_id"]], "payment": "refunded"}
    expected_output = {"message": "Updated payment status for 1 order(s)"}

    response = client.put(
        "/api/orders/bulk-payment-status",
        json=input_payload,
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["orders"][0]["payment"] == "Refunded", (
        f"input={input_payload}\nexpected_output=first order payment Refunded\nactual_output={actual_output}"
    )
