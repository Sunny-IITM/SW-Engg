from datetime import date, datetime, timedelta
import os

from flask_bcrypt import Bcrypt

from extensions import db
from models import (
    Customer,
    Employee,
    Inventory,
    InventoryHistory,
    InventorySetting,
    Order,
    OrderItem,
    Payment,
    PayrollRecord,
    Product,
    ProductHistory,
    ProductionEntry,
    RawMaterialHistory,
    User,
)


bcrypt = Bcrypt()


def get_database_path(app):
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite:///"):
        return None

    relative_path = database_uri.replace("sqlite:///", "", 1)
    if os.path.isabs(relative_path):
        return relative_path

    return os.path.join(app.instance_path, relative_path)


def create_password_hash(value):
    return bcrypt.generate_password_hash(value).decode("utf-8")


def seed_database(app, reset=False):
    with app.app_context():
        if reset:
            db.drop_all()

        db.create_all()

        if User.query.first():
            return "Database already contains data. Skipped seeding."

        today = date.today()
        current_month = today.month
        current_year = today.year
        previous_month_date = today.replace(day=1) - timedelta(days=1)

        users = [
            User(name="Admin User", email="admin@admin", password=create_password_hash("password123"), role="admin", is_active=True),
            User(name="Priya Sharma", email="priya@gmail.com", password=create_password_hash("password123"), role="customer", is_active=True),
            User(name="Amit Verma", email="amit@gmail.com", password=create_password_hash("password123"), role="customer", is_active=True),
            User(name="Neha Singh", email="neha@gmail.com", password=create_password_hash("password123"), role="customer", is_active=True),
            User(name="Ravi Kumar", email="ravi@gmail.com", password=create_password_hash("password123"), role="employee", is_active=True),
            User(name="Sonal Yadav", email="sonal@gmail.com", password=create_password_hash("password123"), role="employee", is_active=True),
            User(name="Deepak Joshi", email="deepak@gmail.com", password=create_password_hash("password123"), role="employee", is_active=True),
        ]

        db.session.add_all(users)
        db.session.flush()

        admin_user = users[0]
        customer_users = users[1:4]
        employee_users = users[4:]

        customers = [
            Customer(user_id=customer_users[0].id, name=customer_users[0].name, phone_number="9876543210", address="22 Craft Street", city="Jaipur", state="Rajasthan", postal_code="302001"),
            Customer(user_id=customer_users[1].id, name=customer_users[1].name, phone_number="9898989898", address="14 Civil Lines", city="Delhi", state="Delhi", postal_code="110054"),
            Customer(user_id=customer_users[2].id, name=customer_users[2].name, phone_number="9765432101", address="8 Lake View", city="Udaipur", state="Rajasthan", postal_code="313001"),
        ]
        employees = [
            Employee(user_id=employee_users[0].id, name=employee_users[0].name, role="Wheel Operator", phone="9988776655", address="Workshop Colony", department="Production", job_title="Wheel Operator", daily_wage=25),
            Employee(user_id=employee_users[1].id, name=employee_users[1].name, role="Kiln Supervisor", phone="9988665544", address="Pottery Nagar", department="Firing", job_title="Kiln Supervisor", daily_wage=28),
            Employee(user_id=employee_users[2].id, name=employee_users[2].name, role="Packing Assistant", phone="9988554433", address="Market Road", department="Packaging", job_title="Packing Assistant", daily_wage=16),
        ]
        db.session.add_all(customers + employees)
        db.session.flush()

        products = [
            Product(name="Classic Kulhad", category="Kulhad", price=20.0, wage_per_kulhad=25, stock=120, image="classic.png"),
            Product(name="Masala Chai Kulhad", category="Kulhad", price=28.0, wage_per_kulhad=30, stock=35, image="Chai_Kulhad.jpg"),
            Product(name="Festive Cup", category="Cup", price=35.0, wage_per_kulhad=18, stock=12, image="Artisan_kulhad.jpg"),
            Product(name="Lassi Kulhad", category="Kulhad", price=42.0, wage_per_kulhad=35, stock=0, image="Lassi_Kulhad.jpg"),
            Product(name="Mini Tea Kulhad", category="Kulhad", price=16.0, wage_per_kulhad=14, stock=160, image="Kulhad_Set.webp"),
            Product(name="Premium Serving Kulhad", category="Kulhad", price=65.0, wage_per_kulhad=40, stock=18, image="prenium_kulhad.webp"),
            Product(name="Designer Cup Set", category="Cup", price=75.0, wage_per_kulhad=22, stock=25, image="Artisan_kulhad.jpg"),
        ]
        db.session.add_all(products)
        db.session.flush()

        inventory_settings = [
            InventorySetting(product_id=products[0].id, min_stock=30),
            InventorySetting(product_id=products[1].id, min_stock=20),
            InventorySetting(product_id=products[2].id, min_stock=15),
            InventorySetting(product_id=products[3].id, min_stock=10),
            InventorySetting(product_id=products[4].id, min_stock=40),
            InventorySetting(product_id=products[5].id, min_stock=12),
            InventorySetting(product_id=products[6].id, min_stock=10),
        ]
        db.session.add_all(inventory_settings)

        db.session.add_all([
            ProductHistory(product_id=products[0].id, product_name=products[0].name, action="create", description="Seeded product Classic Kulhad", actor_name=admin_user.name),
            ProductHistory(product_id=products[1].id, product_name=products[1].name, action="create", description="Seeded product Masala Chai Kulhad", actor_name=admin_user.name),
            ProductHistory(product_id=products[4].id, product_name=products[4].name, action="create", description="Seeded product Mini Tea Kulhad", actor_name=admin_user.name),
            ProductHistory(product_id=products[5].id, product_name=products[5].name, action="create", description="Seeded product Premium Serving Kulhad", actor_name=admin_user.name),
            ProductHistory(product_id=products[1].id, product_name=products[1].name, action="update", description="Updated pricing and stock for Masala Chai Kulhad", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=3)),
        ])

        raw_materials = [
            Inventory(raw_material_name="Red Clay", quantity_available=180, unit="kg", category="Clay", supplier_name="Rajasthan Clay Co.", reorder_level=60, cost_per_unit=18, last_restocked=today - timedelta(days=2)),
            Inventory(raw_material_name="Food Safe Glaze", quantity_available=48, unit="liters", category="Glaze", supplier_name="Craft Coat Supplies", reorder_level=25, cost_per_unit=110, last_restocked=today - timedelta(days=4)),
            Inventory(raw_material_name="Packaging Sleeves", quantity_available=320, unit="pieces", category="Packaging", supplier_name="WrapRight India", reorder_level=120, cost_per_unit=4, last_restocked=today - timedelta(days=1)),
            Inventory(raw_material_name="Black Paint", quantity_available=22, unit="liters", category="Paint", supplier_name="Color Pot Depot", reorder_level=18, cost_per_unit=145, last_restocked=today - timedelta(days=6)),
            Inventory(raw_material_name="Fine Sand", quantity_available=140, unit="bags", category="Other", supplier_name="Earth Base Traders", reorder_level=50, cost_per_unit=22, last_restocked=today - timedelta(days=3)),
        ]
        db.session.add_all(raw_materials)
        db.session.flush()

        db.session.add_all([
            RawMaterialHistory(inventory_id=raw_materials[0].id, material_name=raw_materials[0].raw_material_name, action="create", description="Created raw material Red Clay", quantity_change=180, previous_quantity=0, new_quantity=180, unit="kg", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=2)),
            RawMaterialHistory(inventory_id=raw_materials[1].id, material_name=raw_materials[1].raw_material_name, action="create", description="Created raw material Food Safe Glaze", quantity_change=48, previous_quantity=0, new_quantity=48, unit="liters", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=4)),
            RawMaterialHistory(inventory_id=raw_materials[3].id, material_name=raw_materials[3].raw_material_name, action="adjust", description="Fresh color delivery", quantity_change=6, previous_quantity=16, new_quantity=22, unit="liters", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=1)),
            RawMaterialHistory(inventory_id=raw_materials[4].id, material_name=raw_materials[4].raw_material_name, action="update", description="Updated supplier details", quantity_change=0, previous_quantity=140, new_quantity=140, unit="bags", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=2)),
        ])

        production_entries = [
            ProductionEntry(employee_id=employees[0].id, product_id=products[0].id, product_name=products[0].name, entry_date=today, status="present", entry_type="regular", kulhad_quantity=16, cup_quantity=0, total_quantity=16, wage_per_kulhad=25, wage_amount=400, notes="Morning batch"),
            ProductionEntry(employee_id=employees[0].id, product_id=products[1].id, product_name=products[1].name, entry_date=today - timedelta(days=1), status="present", entry_type="regular", kulhad_quantity=12, cup_quantity=0, total_quantity=12, wage_per_kulhad=30, wage_amount=360, notes="Restock support"),
            ProductionEntry(employee_id=employees[0].id, product_id=products[2].id, product_name=products[2].name, entry_date=today - timedelta(days=5), status="present", entry_type="manual", kulhad_quantity=0, cup_quantity=10, total_quantity=10, wage_per_kulhad=18, wage_amount=180, notes="Cup line"),
            ProductionEntry(employee_id=employees[0].id, product_id=products[0].id, product_name=products[0].name, entry_date=previous_month_date.replace(day=min(12, previous_month_date.day)), status="present", entry_type="regular", kulhad_quantity=14, cup_quantity=0, total_quantity=14, wage_per_kulhad=25, wage_amount=350, notes="Previous month sample"),
            ProductionEntry(employee_id=employees[1].id, product_id=products[5].id, product_name=products[5].name, entry_date=today - timedelta(days=2), status="present", entry_type="overtime", kulhad_quantity=8, cup_quantity=0, total_quantity=8, wage_per_kulhad=40, wage_amount=320, notes="Premium firing batch"),
            ProductionEntry(employee_id=employees[1].id, product_id=products[4].id, product_name=products[4].name, entry_date=previous_month_date.replace(day=max(5, min(18, previous_month_date.day))), status="present", entry_type="regular", kulhad_quantity=20, cup_quantity=0, total_quantity=20, wage_per_kulhad=14, wage_amount=280, notes="Mini kulhad batch"),
            ProductionEntry(employee_id=employees[2].id, product_id=products[6].id, product_name=products[6].name, entry_date=today - timedelta(days=3), status="present", entry_type="manual", kulhad_quantity=0, cup_quantity=15, total_quantity=15, wage_per_kulhad=22, wage_amount=330, notes="Packed designer cup sets"),
        ]
        db.session.add_all(production_entries)

        payroll_records = [
            PayrollRecord(employee_id=employees[0].id, payroll_month=current_month, payroll_year=current_year, bonus=250, deductions=50, status="processed"),
            PayrollRecord(employee_id=employees[0].id, payroll_month=previous_month_date.month, payroll_year=previous_month_date.year, bonus=200, deductions=30, status="paid", paid_on=previous_month_date),
            PayrollRecord(employee_id=employees[1].id, payroll_month=current_month, payroll_year=current_year, bonus=180, deductions=20, status="pending"),
            PayrollRecord(employee_id=employees[1].id, payroll_month=previous_month_date.month, payroll_year=previous_month_date.year, bonus=150, deductions=15, status="paid", paid_on=previous_month_date.replace(day=min(20, previous_month_date.day))),
            PayrollRecord(employee_id=employees[2].id, payroll_month=current_month, payroll_year=current_year, bonus=90, deductions=10, status="processed"),
        ]
        db.session.add_all(payroll_records)

        orders = [
            Order(customer_id=customers[0].id, order_date=today, status="pending", total_amount=124.0),
            Order(customer_id=customers[0].id, order_date=today - timedelta(days=1), status="completed", total_amount=168.0),
            Order(customer_id=customers[1].id, order_date=today - timedelta(days=2), status="confirmed", total_amount=205.0),
            Order(customer_id=customers[2].id, order_date=today - timedelta(days=4), status="delivered", total_amount=310.0),
            Order(customer_id=customers[1].id, order_date=today - timedelta(days=6), status="cancelled", total_amount=56.0),
        ]
        db.session.add_all(orders)
        db.session.flush()

        db.session.add_all([
            OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=2, subtotal=40.0),
            OrderItem(order_id=orders[0].id, product_id=products[1].id, quantity=3, subtotal=84.0),
            OrderItem(order_id=orders[1].id, product_id=products[2].id, quantity=2, subtotal=70.0),
            OrderItem(order_id=orders[1].id, product_id=products[0].id, quantity=3, subtotal=60.0),
            OrderItem(order_id=orders[2].id, product_id=products[5].id, quantity=2, subtotal=130.0),
            OrderItem(order_id=orders[2].id, product_id=products[4].id, quantity=4, subtotal=64.0),
            OrderItem(order_id=orders[3].id, product_id=products[6].id, quantity=2, subtotal=150.0),
            OrderItem(order_id=orders[3].id, product_id=products[1].id, quantity=4, subtotal=112.0),
            OrderItem(order_id=orders[4].id, product_id=products[0].id, quantity=2, subtotal=40.0),
        ])

        db.session.add_all([
            Payment(order_id=orders[0].id, payment_date=today, amount=124.0, payment_method="Cash on Delivery", status="Pending"),
            Payment(order_id=orders[1].id, payment_date=today - timedelta(days=1), amount=168.0, payment_method="Cash on Delivery", status="Pending"),
            Payment(order_id=orders[2].id, payment_date=today - timedelta(days=2), amount=205.0, payment_method="Cash on Delivery", status="Pending"),
            Payment(order_id=orders[3].id, payment_date=today - timedelta(days=4), amount=310.0, payment_method="Cash on Delivery", status="Pending"),
            Payment(order_id=orders[4].id, payment_date=today - timedelta(days=6), amount=56.0, payment_method="Cash on Delivery", status="Pending"),
        ])

        db.session.add_all([
            InventoryHistory(product_id=products[0].id, change=20, previous_stock=100, new_stock=120, reason="Seed restock for Classic Kulhad", entry_type="manual", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=2)),
            InventoryHistory(product_id=products[1].id, change=-8, previous_stock=43, new_stock=35, reason="Recent customer orders", entry_type="manual", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=1)),
            InventoryHistory(product_id=products[3].id, change=-5, previous_stock=5, new_stock=0, reason="Sold out", entry_type="manual", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=1)),
            InventoryHistory(product_id=products[4].id, change=30, previous_stock=130, new_stock=160, reason="Added mini kulhad inventory", entry_type="manual", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=3)),
            InventoryHistory(product_id=products[5].id, change=-4, previous_stock=22, new_stock=18, reason="Premium order dispatch", entry_type="manual", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=2)),
            InventoryHistory(product_id=products[6].id, change=0, previous_stock=25, new_stock=25, reason="Minimum stock threshold updated", entry_type="threshold-update", actor_name=admin_user.name, created_at=datetime.utcnow() - timedelta(days=1)),
        ])

        db.session.commit()

        return (
            "Database seeded successfully with demo data. "
            "Accounts: admin@admin / password123, "
            "priya@gmail.com / password123, "
            "ravi@gmail.com / password123."
        )


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    print(seed_database(app, reset=True))
