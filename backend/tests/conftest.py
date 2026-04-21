import importlib
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from config import Config
from tests.helpers import assert_api_response


def utc_now():
    return datetime.now(UTC)


def _sqlite_uri(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


@pytest.fixture(scope="session")
def app():
    db_dir = Path(__file__).resolve().parents[2] / ".tmp" / "test-db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / "backend-test.sqlite"
    if db_file.exists():
        db_file.unlink()

    Config.SQLALCHEMY_DATABASE_URI = _sqlite_uri(db_file)

    import app as app_module

    app_module = importlib.reload(app_module)
    flask_app = app_module.app
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def tmp_path():
    base_dir = Path(__file__).resolve().parent / "_tmp_artifacts"
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = base_dir / f"tmp-{uuid4().hex}"
    temp_dir.mkdir()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _seed_database():
    from extensions import bcrypt, db
    from models import (
        Customer,
        Employee,
        Inventory,
        InventoryHistory,
        InventorySetting,
        Order,
        OrderItem,
        Payment,
        Product,
        ProductHistory,
        ProductionEntry,
        RawMaterialHistory,
        User,
    )

    # Clear any pooled SQLite connections before recreating the schema so
    # function-scoped seeds don't leak state across tests.
    db.session.remove()
    db.engine.dispose()
    db.drop_all()
    db.create_all()

    admin = User(name="Admin User", email="admin@example.com", password=bcrypt.generate_password_hash("adminpass").decode("utf-8"), role="admin", is_active=True)
    customer_user = User(name="Customer User", email="customer@example.com", password=bcrypt.generate_password_hash("customerpass").decode("utf-8"), role="customer", is_active=True)
    employee_user = User(name="Employee User", email="employee@example.com", password=bcrypt.generate_password_hash("employeepass").decode("utf-8"), role="employee", is_active=True)

    db.session.add_all([admin, customer_user, employee_user])
    db.session.flush()

    customer = Customer(user_id=customer_user.id, name=customer_user.name, phone_number="9999999999", address="Main Street", city="Jaipur", state="Rajasthan", postal_code="302001")
    employee = Employee(user_id=employee_user.id, name=employee_user.name, role="Wheel Operator", phone="8888888888", address="Workshop Lane", department="Production", job_title="Wheel Operator", daily_wage=25)
    db.session.add_all([customer, employee])
    db.session.flush()

    product_one = Product(name="Classic Kulhad", category="Kulhad", price=10.5, wage_per_kulhad=25, stock=20, image="default.jpg")
    product_two = Product(name="Tea Cup", category="Cup", price=15.0, wage_per_kulhad=10, stock=5, image="classic.png")
    db.session.add_all([product_one, product_two])
    db.session.flush()

    db.session.add_all([
        InventorySetting(product_id=product_one.id, min_stock=5),
        InventorySetting(product_id=product_two.id, min_stock=2),
    ])

    raw_material = Inventory(raw_material_name="Clay Mix", quantity_available=100, unit="kg", category="Clay", supplier_name="Soil Suppliers", reorder_level=25, cost_per_unit=4.5, last_restocked=date.today())
    db.session.add(raw_material)
    db.session.flush()

    db.session.add(ProductHistory(product_id=product_one.id, product_name=product_one.name, action="create", description=f"Created product {product_one.name}", actor_name=admin.name))
    db.session.add(InventoryHistory(product_id=product_one.id, change=5, previous_stock=15, new_stock=20, reason="Initial stock load", entry_type="manual", actor_name=admin.name, created_at=utc_now() - timedelta(days=1)))
    db.session.add(RawMaterialHistory(inventory_id=raw_material.id, material_name=raw_material.raw_material_name, action="create", description=f"Created raw material {raw_material.raw_material_name}", quantity_change=100, previous_quantity=0, new_quantity=100, unit=raw_material.unit, actor_name=admin.name))

    order = Order(customer_id=customer.id, order_date=date.today(), status="pending", total_amount=31.5)
    db.session.add(order)
    db.session.flush()

    db.session.add(OrderItem(order_id=order.id, product_id=product_one.id, quantity=3, subtotal=31.5))
    db.session.add(Payment(order_id=order.id, payment_date=date.today(), amount=31.5, payment_method="UPI", status="Paid"))
    db.session.add(ProductionEntry(employee_id=employee.id, product_id=product_one.id, product_name=product_one.name, entry_date=date.today(), status="present", entry_type="regular", kulhad_quantity=12, cup_quantity=0, total_quantity=12, wage_per_kulhad=25, wage_amount=300, notes="Seed entry"))

    db.session.commit()

    return {
        "admin": {"id": admin.id, "email": admin.email, "password": "adminpass"},
        "customer": {"id": customer_user.id, "email": customer_user.email, "password": "customerpass"},
        "employee": {"id": employee_user.id, "email": employee_user.email, "password": "employeepass"},
        "customer_profile_id": customer.id,
        "employee_profile_id": employee.id,
        "products": {"kulhad": product_one.id, "cup": product_two.id},
        "raw_material_id": raw_material.id,
        "order_id": order.id,
    }


@pytest.fixture()
def seeded_data(app):
    from extensions import db

    with app.app_context():
        data = _seed_database()
        db.session.remove()
        yield data
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def auth_headers(client, seeded_data):
    def _login(email, password):
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        token = response.get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    return {
        "admin": _login(seeded_data["admin"]["email"], seeded_data["admin"]["password"]),
        "customer": _login(seeded_data["customer"]["email"], seeded_data["customer"]["password"]),
        "employee": _login(seeded_data["employee"]["email"], seeded_data["employee"]["password"]),
    }
