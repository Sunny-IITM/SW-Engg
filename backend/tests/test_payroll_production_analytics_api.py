from datetime import date

from tests.helpers import assert_api_response


def test_get_payroll_returns_employee_records(client, seeded_data, auth_headers):
    response = client.get("/api/payroll/", headers=auth_headers["admin"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert len(actual_output) >= 1
    assert actual_output[0]["gross_wages"] >= 300


def test_get_my_payroll_returns_employee_record(client, seeded_data, auth_headers):
    response = client.get("/api/payroll/me", headers=auth_headers["employee"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert actual_output["id"] == seeded_data["employee_profile_id"]
    assert actual_output["gross_wages"] >= 300


def test_update_payroll_record(client, seeded_data, auth_headers):
    requested_paid_on = date.today().replace(day=1).isoformat()
    input_payload = {"bonus": 1000, "deductions": 500, "paid_on": requested_paid_on, "status": "paid"}
    response = client.put(f"/api/payroll/{seeded_data['employee_profile_id']}", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, {"id": seeded_data["employee_profile_id"], "bonus": 1000.0, "deductions": 500.0, "status": "paid", "paid_on": requested_paid_on}, input_payload)
    assert actual_output["gross_wages"] == 300.0
    assert actual_output["net_wages"] == 800.0


def test_update_bulk_payroll_status(client, seeded_data, auth_headers):
    input_payload = {"status": "processed", "current_statuses": ["pending"], "month": date.today().month, "year": date.today().year}
    response = client.put("/api/payroll/bulk-status", json=input_payload, headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, {"message": "Updated 1 payroll record(s)"}, input_payload)
    assert actual_output["records"][0]["status"] == "processed"


def test_get_production_entries_for_employee(client, seeded_data, auth_headers):
    response = client.get(f"/api/production/entries?month={date.today().month}&year={date.today().year}", headers=auth_headers["employee"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert len(actual_output) >= 1


def test_log_production_entry_for_employee(client, seeded_data, auth_headers):
    input_payload = {"date": date.today().isoformat(), "product_id": seeded_data["products"]["kulhad"], "product": "Classic Kulhad", "quantity": 8, "method": "manual", "entry_type": "manual", "status": "present", "notes": "Manual logging"}
    response = client.post("/api/production/log", json=input_payload, headers=auth_headers["employee"])
    actual_output = assert_api_response(response, 201, {"date": date.today().isoformat(), "product_name": "Classic Kulhad", "total_quantity": 8, "notes": "Manual logging"}, input_payload)
    assert actual_output["daily_wage"] == 200.0


def test_get_dashboard_summary(client, seeded_data, auth_headers):
    response = client.get("/api/analytics/dashboard", headers=auth_headers["admin"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert actual_output["stats"] == {"products": 2, "orders": 1, "customers": 1, "employees": 1}


def test_get_analytics_summary(client, seeded_data, auth_headers):
    response = client.get("/api/analytics/summary", headers=auth_headers["admin"])
    actual_output = response.get_json()
    assert response.status_code == 200
    assert actual_output["sales"]["total_orders"] == 1
    assert actual_output["sales"]["total_revenue"] == 31.5


def test_send_daily_report_posts_google_chat_message(client, seeded_data, auth_headers, monkeypatch, app):
    captured = {}

    class FakeResponse:
        def read(self):
            return b'{"name":"spaces/mock/messages/123"}'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse()

    app.config["GOOGLE_CHAT_WEBHOOK_URL"] = "https://chat.googleapis.com/mock-webhook"
    monkeypatch.setattr("routes.analytics.urlopen", fake_urlopen)

    response = client.post("/api/analytics/daily-report/send", headers=auth_headers["admin"])
    actual_output = assert_api_response(response, 200, {"message": "Daily report sent successfully"}, None)

    assert captured["url"] == "https://chat.googleapis.com/mock-webhook"
    assert captured["timeout"] == 15
    assert "Daily Overall Report" in captured["body"]
    assert "Pending orders" in captured["body"]
    assert "Immediate Attention" in captured["body"]
    assert "preview" in actual_output


def test_send_daily_report_requires_webhook_configuration(client, seeded_data, auth_headers, app):
    app.config["GOOGLE_CHAT_WEBHOOK_URL"] = ""

    response = client.post("/api/analytics/daily-report/send", headers=auth_headers["admin"])
    actual_output = response.get_json()

    assert response.status_code == 400
    assert actual_output["error"] == "GOOGLE_CHAT_WEBHOOK_URL is not configured"
