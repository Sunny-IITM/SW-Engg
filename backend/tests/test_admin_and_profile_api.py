from tests.helpers import assert_api_response


def test_get_admin_users_list(client, seeded_data, auth_headers):
    input_payload = {"role": "customer"}
    expected_output = {"minimum_users": 1}

    response = client.get("/api/admin/users?role=customer", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 200, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )
    assert len(actual_output) >= 1, (
        f"input={input_payload}\nexpected_output={expected_output}\nactual_output={actual_output}"
    )


def test_create_admin_managed_user(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Worker Two",
        "email": "worker.two@example.com",
        "password": "workerpass",
        "role": "employee",
        "phone": "1234567890",
        "address": "Factory Road",
        "department": "Production",
        "job_title": "Painter",
        "per_unit_wage": 18,
    }
    expected_output = {
        "name": "Worker Two",
        "email": "worker.two@example.com",
        "role": "employee",
        "department": "Production",
        "job_title": "Painter",
    }

    response = client.post("/api/admin/users", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 201, expected_output, input_payload)

    assert actual_output["per_unit_wage"] == 18.0, (
        f"input={input_payload}\nexpected_output=per_unit_wage 18.0\nactual_output={actual_output}"
    )


def test_update_admin_managed_user(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Customer User Updated",
        "phone": "1111111111",
        "address": "Updated Street",
        "is_active": True,
    }
    expected_output = {
        "name": "Customer User Updated",
        "phone": "1111111111",
        "address": "Updated Street",
        "is_active": True,
    }

    response = client.put(
        f"/api/admin/users/{seeded_data['customer']['id']}",
        json=input_payload,
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["role"] == "customer", (
        f"input={input_payload}\nexpected_output=role customer\nactual_output={actual_output}"
    )


def test_delete_admin_managed_user(client, seeded_data, auth_headers):
    input_payload = {"user_id": seeded_data["employee"]["id"]}
    expected_output = {"message": "User deleted"}

    response = client.delete(
        f"/api/admin/users/{seeded_data['employee']['id']}",
        headers=auth_headers["admin"],
    )
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output == expected_output


def test_get_my_profile_for_customer(client, seeded_data, auth_headers):
    input_payload = None
    expected_output = {
        "name": "Customer User",
        "email": "customer@example.com",
        "role": "customer",
        "phone": "9999999999",
        "address": "Main Street",
    }

    response = client.get("/api/profile/me", headers=auth_headers["customer"])
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["city"] == "Jaipur", (
        f"input={input_payload}\nexpected_output=city Jaipur\nactual_output={actual_output}"
    )


def test_update_my_profile_for_customer(client, seeded_data, auth_headers):
    input_payload = {
        "name": "Customer Prime",
        "phone": "2222222222",
        "address": "Prime Street",
        "city": "Jodhpur",
        "state": "Rajasthan",
        "postal_code": "342001",
        "current_password": "customerpass",
        "new_password": "newcustomerpass",
    }
    expected_output = {
        "name": "Customer Prime",
        "phone": "2222222222",
        "address": "Prime Street",
        "city": "Jodhpur",
        "state": "Rajasthan",
        "postal_code": "342001",
    }

    response = client.put("/api/profile/me", json=input_payload, headers=auth_headers["customer"])
    actual_output = assert_api_response(response, 200, expected_output, input_payload)

    assert actual_output["email"] == "customer@example.com", (
        f"input={input_payload}\nexpected_output=email customer@example.com\nactual_output={actual_output}"
    )
