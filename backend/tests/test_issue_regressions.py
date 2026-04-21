from datetime import date

def test_register_should_reject_admin_role(client, seeded_data):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Escalated User",
            "email": "escalated@example.com",
            "password": "secret123",
            "role": "admin",
        },
    )

    assert response.status_code == 400


def test_register_should_reject_duplicate_email_with_different_case(client, seeded_data):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Duplicate Case User",
            "email": "CUSTOMER@example.com",
            "password": "secret123",
            "role": "customer",
        },
    )

    assert response.status_code == 400


def test_admin_update_user_should_reject_blank_email(client, seeded_data, auth_headers):
    response = client.put(
        f"/api/admin/users/{seeded_data['customer']['id']}",
        json={"email": ""},
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_create_product_should_reject_negative_price(client, seeded_data, auth_headers):
    response = client.post(
        "/api/products/",
        json={
            "name": "Broken Price Product",
            "category": "Kulhad",
            "price": -5,
            "stock": 3,
            "wage_per_kulhad": 10,
        },
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_adjust_inventory_should_preserve_existing_min_stock_when_not_provided(client, seeded_data, auth_headers):
    response = client.post(
        "/api/inventory/adjust",
        json={
            "product_id": seeded_data["products"]["kulhad"],
            "type": "add",
            "quantity": 1,
            "reason": "Restock without threshold change",
        },
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200
    assert response.get_json()["product"]["min_stock"] == 5


def test_adjust_inventory_should_reject_negative_quantity(client, seeded_data, auth_headers):
    response = client.post(
        "/api/inventory/adjust",
        json={
            "product_id": seeded_data["products"]["kulhad"],
            "type": "add",
            "quantity": -3,
            "reason": "Invalid negative restock",
            "min_stock": 5,
        },
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_create_order_should_reject_negative_shipping(client, seeded_data, auth_headers):
    response = client.post(
        "/api/orders/",
        json={
            "items": [{"id": seeded_data["products"]["kulhad"], "qty": 1}],
            "phone": "9999999999",
            "address": "Main Street",
            "city": "Jaipur",
            "state": "Rajasthan",
            "postal_code": "302001",
            "payment_method": "UPI",
            "shipping": -50,
        },
        headers=auth_headers["customer"],
    )

    assert response.status_code == 400


def test_update_order_status_should_reject_invalid_payment_status(client, seeded_data, auth_headers):
    response = client.put(
        f"/api/orders/{seeded_data['order_id']}/status",
        json={"status": "confirmed", "payment": "totally-invalid"},
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_update_payroll_record_should_reject_invalid_status(client, seeded_data, auth_headers):
    response = client.put(
        f"/api/payroll/{seeded_data['employee_profile_id']}",
        json={"status": "invalid-status", "month": date.today().month, "year": date.today().year},
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_bulk_payroll_status_should_reject_paid_on_outside_selected_month(client, seeded_data, auth_headers):
    response = client.put(
        "/api/payroll/bulk-status",
        json={
            "status": "paid",
            "current_statuses": ["pending"],
            "month": 4,
            "year": 2026,
            "paid_on": "2026-05-01",
        },
        headers=auth_headers["admin"],
    )

    assert response.status_code == 400


def test_get_production_entries_should_reject_invalid_month(client, seeded_data, auth_headers):
    response = client.get("/api/production/entries?month=13&year=2026", headers=auth_headers["employee"])

    assert response.status_code == 400


def test_get_payroll_should_reject_invalid_month(client, seeded_data, auth_headers):
    response = client.get("/api/payroll/?month=13&year=2026", headers=auth_headers["admin"])

    assert response.status_code == 400
