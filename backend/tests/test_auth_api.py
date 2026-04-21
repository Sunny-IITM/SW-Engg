import pytest

from tests.helpers import assert_api_response


def test_register_user_success(client, seeded_data):
    input_payload = {
        "name": "New Customer",
        "email": "newcustomer@example.com",
        "password": "secret123",
        "role": "customer",
        "phone": "7777777777",
        "address": "New Address",
    }
    expected_output = {"message": "User registered successfully"}

    response = client.post("/api/auth/register", json=input_payload)
    actual_output = assert_api_response(response, 201, expected_output, input_payload)

    assert actual_output == expected_output


def test_login_success_returns_profile_details(client, seeded_data):
    input_payload = {
        "email": seeded_data["customer"]["email"],
        "password": seeded_data["customer"]["password"],
    }
    expected_output = {
        "name": "Customer User",
        "role": "customer",
        "email": "customer@example.com",
        "phone": "9999999999",
        "address": "Main Street",
        "city": "Jaipur",
        "state": "Rajasthan",
        "postal_code": "302001",
    }

    response = client.post("/api/auth/login", json=input_payload)
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert "token" in actual_output, (
        f"input={input_payload}\n"
        f"expected_output=token key in response\n"
        f"actual_output={actual_output}"
    )
